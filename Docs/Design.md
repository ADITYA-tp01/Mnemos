# Mnemos — design notes

## Goals
- Give an LLM agent memory that survives restarts and can follow relationships, not just match similar text.
- Keep the memory inspectable: every recall shows the exact Cypher, the result and the latency.
- Degrade gracefully: a slow or missing LLM must not stop an investigation from being recorded.

## Memory model
One FalkorDB graph (`mnemos`) holds three memory types:

- **Semantic** (`ThreatActor`, `TTP`, `IoC`, `Asset`): seeded knowledge about the world.
- **Episodic** (`Alert`, `Investigation`): what the agent has experienced. Starts empty; grows with every investigation.
- **Procedural** (`Playbook`, `Action`): how to respond. The schema, `write_playbook_result` and recall R2 exist, but the agent loop doesn't write procedural memory yet.

The full schema and the Cypher for each recall query (R1–R5) are in the README.

## Agent loop
`AgentLoop.run(alert)` runs `perceive → recall → reason → act → write` and returns only that run's transcript.

- **Recall** runs R1 per IoC, R3 per asset, and R4 per alert. Every recall returns `{result, cypher, latency_ms}`. Results are sanitized to plain JSON (FalkorDB path/node objects are converted).
- **Reason** makes one LLM call with the recalled context and the tool schema (Ollama, OpenAI, or any OpenAI-compatible endpoint). On timeout or a malformed response it retries once, then falls back to recall-only or a deterministic finding derived from the graph (never a hardcoded actor; an IoC with no known actor is recorded as `UNATTRIBUTED`).
- **Act** executes the chosen tools through `ToolRouter`. Memory tools hit FalkorDB; analysis, scan and playbook tools are simulated and deterministic.
- **Write** persists one `Investigation` per run (R5 plus `FOUND` / `ATTRIBUTED_TO` / `TRIGGERED_BY`) and links the IoC `OBSERVED_ON` the alert's assets so R3 can answer next time. If the LLM's `write_finding` is missing or invalid, a default finding is written instead.
- Investigation IDs are random (`INV-<8 hex>`), so parallel hunters can't collide.

## Sessions and restart
`POST /agent/restart` resets the in-memory state (session id, transcript, stored transcripts) and never touches the graph. By default it also applies one round of decay to weighted edges. Recall reinforces only the edges it traversed, so frequently useful memories persist and unused ones fade and are eventually pruned.

## Swarm
`SwarmCoordinator` starts N independent `AgentLoop`s (one per alert) in a thread pool, all sharing one `Memory` / graph. The API holds a single lock so a swarm and single investigations don't interleave. Concurrent writes were verified corruption-free (3 threads × 20 writes). Concurrent recall latency is higher than single-query latency because the hunters share one connection and graph.

## API and UI
- The FastAPI handlers are synchronous so slow LLM calls run in the threadpool and don't block the event loop. The agent is initialized at startup and lazily on first request; if FalkorDB is unreachable the API returns a clear 503.
- On an empty graph the backend seeds the demo scenario (`MNEMOS_AUTO_SEED`).
- The Next.js app proxies every call through `web/app/api/*` to `BACKEND_URL`, so the browser only talks to the web server.
- Cytoscape renders the graph, colored by memory type; the Recall Inspector reads the latest `recall` step of the current transcript.

## FalkorDB notes
- `MERGE` on a relationship pattern can create duplicate nodes; match the nodes first.
- `DELETE` returns no rows, so prune counts are taken with a `count()` before deleting.
- Indexes exist on `IoC.value`, `TTP.mitre_id`, `Asset.id` and `Playbook.name`.

## Possible next steps
- Write procedural memory when a playbook runs (use `write_playbook_result`) so R2 has data.
- Replace the simulated tools with real integrations.
- Stream investigation steps to the UI instead of returning the whole transcript at the end.
- Per-session locking so independent investigations can run concurrently.
