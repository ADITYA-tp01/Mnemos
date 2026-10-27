# Mnemos
> Agents forget. The graph remembers.

**Track:** [WeMakeDevs — Graph Hacks](https://wemakedevs.org/hackathons/falkordb) — **Track 02: Agent Memory and Coordination**

(📅 NOTE: the original plan targeted a September 2026 hackathon. The live event was **Oct 15–18, 2026** — submissions closed Oct 18. Mnemos is built as a complete, runnable project regardless.)

## The Problem

Agents and LLMs have no persistent memory between sessions. Every conversation starts a blank slate: an investigator re-discovers an attacker it already attributed, re-analyzes an IoC it already saw, re-learns a playbook it already ran. Vector memory retrieves "similar-looking text" but can't traverse *relationships*. The result is an agent that forgets the moment its context window closes.

## Demo Video

_Placeholder — will be linked once recorded._

## How It Works (The Agentic-RAG Loop)

1. **Perceive** — an alert enters the queue.
2. **Recall** — the agent runs multi-hop Cypher recall queries (R1–R4) against FalkorDB and serializes the results into structured LLM context.
3. **Reason** — a single LLM call reasons over graph context + the alert, then selects a tool via function calling.
4. **Act** — the agent executes the selected tool(s) (analysis, scan, playbook).
5. **Write** — findings are persisted back to the graph as episodic memory (R5).

The graph is the memory. The LLM is the reasoning. Neither works alone.

### Three Memory Types

All stored as one graph in FalkorDB, color-coded in the UI:

| Type | Nodes | Purpose |
|---|---|---|
| 🔵 **Semantic** | ThreatActor, TTP, IoC, Asset | What the agent *knows* |
| 🟢 **Episodic** | Alert, Investigation | What the agent *experienced* |
| 🟣 **Procedural** | Playbook, Action | What the agent *knows how to do* |

```cypher
// ── SEMANTIC ──
(:ThreatActor {id, name})-[:USES]->(:TTP {mitre_id, name})
(:ThreatActor)-[:ASSOCIATED_WITH]->(:IoC {type, value})
(:IoC)-[:OBSERVED_ON]->(:Asset {id, ip, subnet})

// ── EPISODIC ──
(:Alert)-[:FLAGGED]->(:IoC)
(:Investigation)-[:TRIGGERED_BY]->(:Alert)
(:Investigation)-[:ATTRIBUTED_TO]->(:ThreatActor)
(:Investigation)-[:FOUND]->(:IoC)

// ── PROCEDURAL ──
(:Playbook {name, success_rate})-[:EFFECTIVE_AGAINST]->(:TTP)
(:Playbook)-[:CONTAINS]->(:Action)
```

## The Recall Queries

**R1 — Episodic recall:** "Have I seen this IoC before?"
```cypher
MATCH (ioc:IoC {value: $ioc_value})<-[:FOUND]-(inv:Investigation)
-[:ATTRIBUTED_TO]->(actor:ThreatActor)
OPTIONAL MATCH (actor)-[:USES]->(ttp:TTP)
RETURN actor.name, collect(DISTINCT ttp.mitre_id), inv.conclusion
```

**R2 — Procedural recall:** "What playbook worked against this TTP?"
```cypher
MATCH (p:Playbook)-[:EFFECTIVE_AGAINST]->(t:TTP {mitre_id: $technique})
RETURN p.name, p.success_rate ORDER BY p.success_rate DESC LIMIT 1
```

**R3 — Multi-hop recall:** "Is this asset tied to a known actor?"
```cypher
MATCH path = (a:Asset {id: $asset_id})<-[:OBSERVED_ON]-(:IoC)
-[:ASSOCIATED_WITH]-(actor:ThreatActor)
RETURN path
```

**R4 — Cross-session recall (the money shot):**
```cypher
MATCH (past:Investigation)-[:FOUND]->(ioc:IoC)<-[:FOUND]-(now:Investigation {id:$current})
MATCH (past)-[:ATTRIBUTED_TO]->(actor)
RETURN actor.name, count(past), collect(DISTINCT ioc.value)
```

**R5 — Memory write:**
```cypher
MERGE (ioc:IoC {value: $value}) SET ioc.type = $type
MERGE (actor:ThreatActor {name: $actor})
MERGE (actor)-[:ASSOCIATED_WITH]->(ioc)
```

## Memory Integration

No official agent-memory integration (Mem0 / LangChain / LlamaIndex) ships with FalkorDB. Mnemos treats the graph as the cognitive layer and drives it directly with the Cypher queries above — recall feeds the LLM as structured context; the LLM's conclusions are written back as new graph nodes/edges. Remove FalkorDB and the agent loses all memory, recall, and persistence (Golden Rule ✓).

## Architecture

```
 ┌─────────────┐ REST ┌──────────────┐ Redis proto ┌──────────────┐
 │  Next.js UI │─────▶│  FastAPI     │────────────▶│  FalkorDB    │
 │  (console)  │      │  Agent Loop  │   :6379     │  "mnemos"    │
 └─────────────┘      │  tools.py    │      ┌──────│  ┌memory────┐│
                       │  memory.py   │      │      │  └─R1–R5───┘│
                       └──────────────┘      │      └────────────┘
                          │                   │
                       ┌──┴──┐ seed_scenario. │
                       │seed │ py             │
                       └─────┘                 │
```

## Tech Stack

| Layer | Choice |
|---|---|
| Graph DB / memory | FalkorDB (Docker local) |
| Agent backend | Python 3.11 + FastAPI |
| LLM | OpenAI (gpt-4o-mini) — key required |
| Frontend | Next.js 15 (App Router) + Tailwind + shadcn/ui |
| Memory viz | react-cytoscapejs |
| Judge setup | docker-compose |

## Setup

### Prerequisites
- Docker Desktop
- Python 3.11+
- Node 20+
- An OpenAI API key (for the full agent loop)

### One-command start
```bash
# 1. Configure env
cp .env.example .env
# Edit .env — set your LLM_API_KEY

# 2. Seed the graph
python scripts/seed_scenario.py

# 3. Run everything
docker compose up
```

| Service | URL |
|---|---|
| Backend API | http://localhost:8000 |
| Health check | http://localhost:8000/health |
| UI | http://localhost:3000 (when built Day 5+) |

## Features

- ✅ Three cognitive memory types (semantic / episodic / procedural) in one graph
- ✅ Multi-hop recall queries R1–R4 with sub-millisecond latency tracking
- ✅ Memory write-back (R5) grows the graph after every investigation
- ✅ `/agent/restart` clears in-memory state, **keeps the graph** — the persistence moment
- ✅ Cross-session recall: a restart agent recalls prior attributions in ~2ms
- ✅ Concurrency verified — 3 parallel writers, zero corruption

## AI Usage Disclosure

Mnemos uses OpenAI's gpt-4o-mini via function calling for the agent's reasoning step. The memory model (3 memory types), all Cypher queries (R1–R5), the seed data, the scenario design, and the UI are human-authored. Claude Code (Anthropic) assisted with scaffolding, testing, and documentation.

## Challenges & Learnings

- **Dates shifted:** the hackathon ran Oct 15–18, 2026, not September. Building regardless for portfolio quality.
- **Client API quirk:** `falkordb-py` v1.7.1's `query()` takes `{cypher, params}` as positional args, not kwargs. `g.delete()` raises on non-existent graphs — wrap in try/except.
- **Concurrency:** verified clean — FalkorDB handles simultaneous writes without corruption.

## ⚠️ Disclaimer

This is a portfolio rebuild of a hackathon entry whose event has closed. All code, data, and design are new work authored for learning and demonstration.
