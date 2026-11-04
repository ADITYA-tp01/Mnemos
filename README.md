# Mnemos

> Agents forget. The graph remembers.

Mnemos is an autonomous threat-hunting agent with **persistent graph memory**. It investigates security alerts, recalls what it learned in earlier sessions by traversing a [FalkorDB](https://www.falkordb.com/) graph, and writes new findings back so the next investigation starts smarter. Restart the agent and the graph keeps everything.

Vector memory retrieves "similar-looking text" but can't follow relationships (asset → IoC → threat actor → playbook). A graph can.

## How it works

Each alert goes through a five-step loop:

1. **Perceive**: an alert enters the queue.
2. **Recall**: multi-hop Cypher queries (R1–R4) pull relevant memory out of FalkorDB and are serialized into structured LLM context.
3. **Reason**: one LLM call reasons over the alert plus recalled memory and picks tools via function calling.
4. **Act**: the selected tools run (IoC analysis, asset scan, playbook; these three are simulated).
5. **Write**: findings are persisted back to the graph as new nodes and edges (R5).

The graph is the memory; the LLM is the reasoning. If the LLM is unavailable the agent degrades gracefully (recall-only or deterministic fallback) and still records its finding.

### Three memory types

All stored in one graph and color-coded in the UI:

| Type | Nodes | Purpose |
|---|---|---|
| 🔵 **Semantic** | ThreatActor, TTP, IoC, Asset | What the agent *knows* |
| 🟢 **Episodic** | Alert, Investigation | What the agent *experienced* |
| 🟣 **Procedural** | Playbook, Action | What the agent *knows how to do* |

```cypher
// ── SEMANTIC ──
(:ThreatActor {id, name})-[:USES]->(:TTP {mitre_id, name})
(:ThreatActor)-[:ASSOCIATED_WITH]->(:IoC {type, value})
(:TTP)-[:PRODUCES]->(:IoC)
(:IoC)-[:OBSERVED_ON]->(:Asset {id, ip, subnet})   // written by the agent after each investigation

// ── EPISODIC ──
(:Alert)-[:FLAGGED]->(:IoC)
(:Alert)-[:INVOLVES]->(:Asset)
(:Alert)-[:SHARED_IOC]->(:IoC)                      // seeded bridge between related alerts (used by R4)
(:Investigation)-[:TRIGGERED_BY]->(:Alert)
(:Investigation)-[:ATTRIBUTED_TO]->(:ThreatActor)
(:Investigation)-[:FOUND]->(:IoC)

// ── PROCEDURAL ──
(:Playbook {name, success_rate})-[:EFFECTIVE_AGAINST]->(:TTP)
(:Playbook)-[:CONTAINS]->(:Action)
```

## The recall queries

**R1 — Episodic recall:** "Have I seen this IoC before?"
```cypher
MATCH (ioc:IoC {value: $ioc})<-[r:FOUND]-(inv:Investigation)
-[:ATTRIBUTED_TO]->(actor:ThreatActor)
OPTIONAL MATCH (actor)-[:USES]->(ttp:TTP)
RETURN actor.name, collect(DISTINCT ttp.mitre_id), inv.conclusion, r.weight
```

**R2 — Procedural recall:** "What playbook worked against this TTP?"
```cypher
MATCH (p:Playbook)-[r:EFFECTIVE_AGAINST]->(t:TTP {mitre_id: $technique})
RETURN p.name, p.success_rate, r.weight ORDER BY p.success_rate DESC LIMIT 1
```

**R3 — Multi-hop recall:** "Is this asset tied to a known actor?"
```cypher
MATCH path = (a:Asset {id: $asset})<-[:OBSERVED_ON]-(:IoC)
<-[:ASSOCIATED_WITH]-(actor:ThreatActor)
RETURN path
```
Empty until an investigation has recorded where an IoC was observed.

**R4 — Cross-session recall:** "What did earlier sessions learn about this alert's IoCs?"
```cypher
MATCH (past:Investigation)-[:FOUND]->(ioc:IoC)
MATCH (al:Alert {id: $alert_id})-[:SHARED_IOC]->(ioc)
WHERE past.id <> $current_inv
MATCH (past)-[:ATTRIBUTED_TO]->(actor)
RETURN actor.name, count(past), collect(DISTINCT ioc.value)
```
The current investigation doesn't exist yet at recall time, so the bridge to earlier sessions is the alert's `SHARED_IOC` edges.

**R5 — Memory write:**
```cypher
MERGE (ioc:IoC {value: $value}) SET ioc.type = $type
MERGE (actor:ThreatActor {name: $actor})
MERGE (actor)-[:ASSOCIATED_WITH {weight: 1.0, last_recalled: 0}]->(ioc)
```
plus an `Investigation` node with `FOUND` / `ATTRIBUTED_TO` / `TRIGGERED_BY` edges and `OBSERVED_ON` edges to the alert's assets.

No agent-memory integration (Mem0, LangChain, LlamaIndex) ships with FalkorDB, so Mnemos drives the graph directly with the Cypher above.

## Architecture

```
 ┌─────────────┐ REST ┌──────────────┐ Redis proto ┌──────────────┐
 │  Next.js UI │─────▶│  FastAPI     │────────────▶│  FalkorDB    │
 │  (console)  │      │  agent loop  │    :6379    │  graph       │
 └─────────────┘      │  tools.py    │             │  "mnemos"    │
                      │  memory.py   │             └──────────────┘
                      └──────┬───────┘
                             │ HTTP
                       ┌─────▼─────┐
                       │    LLM    │  Ollama / OpenAI / any OpenAI-compatible API
                       └───────────┘
```

See [`Docs/Design.md`](Docs/Design.md) for design notes.

## Tech stack

| Layer | Choice |
|---|---|
| Graph DB / memory | FalkorDB |
| Backend | Python 3.11 + FastAPI |
| LLM | Ollama (default, `qwen3:8b`), OpenAI, or any OpenAI-compatible API (e.g. NVIDIA NIM) |
| Frontend | Next.js 14 (App Router) + Tailwind |
| Graph visualization | Cytoscape.js |
| Deployment | Docker Compose |

## Getting started

### Prerequisites
- Docker Desktop
- An LLM for the full agent loop: a local [Ollama](https://ollama.com) server, an OpenAI API key, or any OpenAI-compatible endpoint. Without one the agent still runs in fallback mode.
- Optional, for running outside Docker: Python 3.11+ and Node 20+

### With Docker
```bash
cp .env.example .env     # then edit .env (see Configuration)
docker compose up --build
```
The backend seeds a demo scenario automatically when the graph is empty. To reset the demo at any time: `pip install falkordb && python scripts/seed_scenario.py`.

| Service | URL |
|---|---|
| UI | http://localhost:3000 |
| Backend API | http://localhost:8000 (docs at `/docs`) |
| Health check | http://localhost:8000/health |

### Without Docker
```bash
docker run -p 6379:6379 -d falkordb/falkordb:latest
pip install -r backend/requirements.txt
uvicorn backend.app.main:app --port 8000      # from the project root
cd web && npm install && npm run dev          # UI on :3000, proxies to BACKEND_URL (default http://localhost:8000)
```

### Try it
1. Open the UI and click an alert (e.g. `ALERT-001`) to investigate it. The transcript, recall inspector, graph and stats update.
2. Click **Restart Agent**. In-memory state is cleared; the graph is kept.
3. Investigate `ALERT-002`. Recall R4 now returns what the earlier session learned (APT-CRIMSON).
4. Click **Run swarm** to run several hunters in parallel on the same graph.

## Configuration

Set these in `.env` (all optional unless noted):

| Variable | Default | Purpose |
|---|---|---|
| `LLM_PROVIDER` | `ollama` | `ollama` or `openai` |
| `LLM_MODEL` | `qwen3:8b` / `gpt-4o-mini` | Model name |
| `LLM_API_KEY` | – | Required for `openai` (also accepts `OPENAI_API_KEY`) |
| `LLM_BASE_URL` | – | OpenAI-compatible endpoint, e.g. `https://integrate.api.nvidia.com/v1` |
| `LLM_TIMEOUT` | `90` | Seconds per LLM call (a cold local model needs more) |
| `OLLAMA_HOST` | `http://localhost:11434` | Ollama server (outside Docker) |
| `OLLAMA_HOST_DOCKER` | `http://host.docker.internal:11434` | Ollama server as seen from the backend container |
| `FALKORDB_HOST` / `FALKORDB_PORT` | `localhost` / `6379` | FalkorDB connection (set by compose in Docker) |
| `BACKEND_URL` | `http://localhost:8000` | Where the web app proxies API calls (set by compose in Docker) |
| `MNEMOS_AUTO_SEED` | `true` | Seed the demo scenario when the graph is empty |
| `MNEMOS_DECAY_ON_RESTART` | `true` | Decay edge weights on each agent restart |

## API

| Method | Path | Description |
|---|---|---|
| GET | `/alerts` | List alerts |
| POST | `/investigate/{alert_id}` | Run the agent loop on an alert |
| GET | `/investigate/{id}/transcript` | Transcript for an investigation or alert |
| POST | `/swarm/hunt` | Run parallel hunters (`{"alert_ids": [...], "num_hunters": 3}`, both optional) |
| GET | `/memory/stats` | Node counts by type and edge count |
| GET | `/memory/graph` | Nodes and edges for visualization |
| GET | `/agent/session` | Current in-memory session info |
| POST | `/agent/restart` | Clear in-memory state, keep the graph |
| GET | `/health` | Liveness check |

## Features

- Three memory types in one graph, with multi-hop recall (R1–R4) and write-back (R5)
- Per-query recall latency (about 1–2 ms on the seeded graph; 8–20 ms per hunter when 3 hunters run concurrently)
- Cross-session memory: restart the agent and it still recalls earlier attributions
- Memory decay and reinforcement: each restart decays weighted edges (×0.9, pruned below 0.1) and edges a recall traverses are boosted (×1.2, capped at 5.0)
- R3 learns: after each investigation the IoC is linked `OBSERVED_ON` the alert's assets
- Swarm mode: up to 5 hunters in parallel, one per alert, all reading and writing the same graph; the UI shows per-hunter recall latency and lets you open any hunter's transcript
- Graceful degradation when the LLM is slow or down (recall-only / deterministic fallback)
- Console UI: alert feed, step-by-step transcript with source attribution, live memory graph, recall inspector (exact Cypher + latency), memory stats

## Known limitations

- **Procedural memory isn't populated by the agent yet.** `Memory.write_playbook_result` and R2 exist and are tested, but the loop never calls them (`apply_playbook` is a simulated tool that doesn't write to the graph), so Playbook/Action nodes stay empty.
- `analyze_ioc`, `scan_asset` and `apply_playbook` return synthetic data.
- One investigation or swarm runs at a time (they share a lock).
- LLM speed varies a lot: a hosted model answers in seconds, a local 8B model on CPU can take about a minute per call.

## Tests

```bash
pip install -r backend/requirements-dev.txt
pytest backend/tests                        # offline: fake graph, no DB or LLM needed
python scripts/test_memory.py               # needs FalkorDB on :6379 (re-seeds the graph)
python scripts/test_cross_session.py        # session 1 → restart → session 2, x3
python scripts/demo_critical_path.py        # scripted fallback run
```

## Project layout

```
backend/app/
  main.py            FastAPI app, health, error handling
  api/routes.py      REST endpoints, agent lifecycle, swarm endpoint
  agent/loop.py      perceive → recall → reason → act → write
  agent/memory.py    Cypher recall/write queries, decay, reinforcement
  agent/tools.py     tool schema + router (memory tools and simulated tools)
  agent/swarm.py     parallel hunters sharing one graph
backend/tests/       offline API and agent-loop tests
scripts/             seed_scenario.py and verification / demo scripts
web/app/             Next.js console (components, API proxy routes)
Docs/Design.md       design notes
```

## Notes & learnings

- `falkordb-py`'s `query()` takes the Cypher string and a params dict as positional arguments. `Graph.delete()` raises on a graph that doesn't exist yet.
- `MERGE` on a relationship pattern can create new nodes instead of matching existing ones. Always `MATCH` the nodes first, then `CREATE` or `MERGE` the edge.
- FalkorDB handled 3 threads × 20 simultaneous writes to one graph without corruption.
- Concurrent recall is slower than a lone query because the hunters share one connection and graph.

## AI assistance

An LLM is used at runtime for the agent's reasoning step. AI coding assistants (Claude Code and the Zed agent) helped build parts of the backend, UI, tests and documentation.
