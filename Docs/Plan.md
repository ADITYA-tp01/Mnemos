Here's your **Track 2 contingency Master Plan** — built to the exact same 10/10 standard as your refined Syndicate plan, with the GraphRAG/agentic theme alignment, verification honesty layer, and fallbacks baked in.

⚠️ **Strategic note first:** Rules say *one track per submission* and *one team per person*. So Track 1 (Syndicate) and Track 2 (Mnemos) are **mutually exclusive** — you pick one to actually submit. This plan is your genuine alternative in case you decide the agentic-memory angle is the stronger play. I've added a **decision framework at the end** to help you choose.

---

# Mnemos — Master Plan (v1.0 — Verified & Hardened)

**Hackathon:** WeMakeDevs — Graph Hacks: Building Next-Gen RAG × FalkorDB (September 2026)
**Target:** Track 02 — Best Agentic AI Use Case (share of $10,000)
**Project:** Mnemos — Autonomous Threat Hunter with Persistent Graph Memory
**Tagline:** *Agents forget. The graph remembers.*
**Mode:** Solo · Fresh Start

---

## 0. HACKATHON THEME ALIGNMENT

Track 02 brief: *"Build autonomous AI agents, or a swarm of them, that use FalkorDB as a **persistent cognitive memory layer**: episodic, semantic, and procedural memory that survives across sessions."*

The hackathon theme is still **"Building Next-Gen RAG."** For Track 2, that means **Agentic RAG**: the agent doesn't retrieve via vector similarity — it *recalls* via graph traversal, and feeds that structured memory to the LLM as context.

**What this means for Mnemos:** The agent must visibly *get smarter because the graph remembered.* Every feature must prove three things:
1. FalkorDB is the agent's memory (not a log file, not a vector store).
2. The memory **survives a restart** (the money shot).
3. Recall is **multi-hop and sub-millisecond** — the thing vector memory can't do.

> **The thesis:** *An agent without memory re-discovers the world every session. Mnemos remembers every investigation, every attacker, every playbook — in a graph — and recalls it in milliseconds. The graph is the memory. The LLM is the reasoning. Neither works alone.*

### 0.1 VERIFICATION STATUS (Honesty Layer)

| Label | Meaning |
|---|---|
| ✅ **VERIFIED** | Confirmed from official hackathon rules/docs during research |
| 🔶 **CONFIDENT** | Standard FalkorDB behavior from docs knowledge — confirm at kickoff |
| 🔴 **VERIFY DAY 0** | Unverified assumption with a built-in fallback. Must be tested before coding |

**The 5 🔴 items (all have fallbacks):**
1. **Official agent-memory integration** (FalkorDB + Mem0 / LangChain memory) → Fallback: custom memory loop over raw Cypher
2. **Concurrent write behavior** (multi-agent writes to one graph) → Fallback: serialize writes or single-writer design
3. **LLM function-calling reliability** → Fallback: pre-script/cache the demo's critical path
4. **FalkorDB Cloud free tier** → Fallback: docker-compose is the official judge path
5. **Exact hackathon dates** → Plan is phase-based, maps to any window

---

## 1. HACKATHON RULES (✅ VERIFIED from wemakedevs.org/hackathons/falkordb/rules)

| # | Rule | Detail |
|---|---|---|
| 1 | When | September 2026, online, worldwide. Exact dates TBA |
| 2 | Teams | Solo or up to 4. One team per person. (You: **SOLO**) |
| 3 | FalkorDB mandatory | Must be the primary graph DB powering a **central** feature |
| 4 | **THE GOLDEN RULE (Rule 3)** | *"If the product still works once FalkorDB is taken out, the graph is decoration."* |
| 5 | Data rules | Public, synthetic, or your own ONLY. No private/personal data |
| 6 | One track per submission | We enter **Track 02: Best Agentic AI Use Case** — named explicitly |
| 7 | Pre-planning allowed | Notes, diagrams, memory-model sketches allowed before start |
| 8 | Libraries/frameworks OK | Any language, framework, deployment platform |
| 9 | AI assistants allowed | Must be **disclosed**; you must explain every decision |
| 10 | No pure AI-gen | Meaningful human contribution required. You own the memory model + queries |
| 11 | IP | Belongs to you |

### Submission Checklist (Rule 9)
- [ ] Public source-code repository
- [ ] README with setup instructions **AND your graph data model**
- [ ] **The Cypher queries / graph algorithms the product depends on** (dedicated section)
- [ ] Demo video showing the working project
- [ ] Live deployment **OR** complete local setup instructions
- [ ] Track named: *"Best Agentic AI Use Case"*
- [ ] AI usage disclosure

### Track 02 Judging Focus (what we optimize for)
| Key Focus | How Mnemos Hits It |
|---|---|
| **Persistent cognitive memory** | Episodic + semantic + procedural memory, all in FalkorDB, **survives a restart on camera** |
| Multi-agent state sharing | Swarm of hunter agents reading/writing one shared memory graph |
| High-concurrency memory lookups | Parallel agents recalling from the graph simultaneously, latency shown |
| Sub-millisecond traversals | Multi-hop memory recall with live timing in the UI |
| Dynamic tool selection | Agent picks its investigation tool **based on recalled memory** |

**Strategy:** Win Track 02 on the **"agent got smarter"** moment. The graph is provably the memory. Secondary: the swarm/concurrency angle is strong enough to stand out in any "best agentic" discussion.

---

## 2. FALKORDB — CAPABILITIES & HOW WE USE THEM (Track 2 lens)

| Feature | What It Does | Status | How Mnemos Uses It |
|---|---|---|---|
| Cypher pattern matching | `MATCH (a)-[:REL]->(b)` | 🔶 CONFIDENT | Every memory recall query |
| Variable-length paths | `[:OBSERVED_ON*1..3]` | 🔶 CONFIDENT | Multi-hop recall (asset → IoC → actor) |
| Sub-millisecond traversals | Sparse-matrix engine | ✅ VERIFIED (core pitch) | Memory recall latency shown live |
| **Memory integrations** | Mem0 / LangChain / LlamaIndex | 🔴 VERIFY DAY 0 | Use official agent-memory if solid, else custom loop |
| Indexes | `CREATE INDEX` | 🔶 CONFIDENT | Fast recall by IoC value / TTP id / asset id |
| Docker deployment | `falkordb/falkordb` on :6379 | 🔶 CONFIDENT | Local dev + judge setup |
| FalkorDB Cloud | Managed instance | 🔴 VERIFY DAY 0 | Stretch deployment |
| Python client | Official driver | 🔶 CONFIDENT | Agent backend talks to memory |
| FalkorDB Browser | Visual query explorer | 🔶 CONFIDENT | Show the memory growing + README screenshots |

### Critical Architecture Insight
FalkorDB speaks the **Redis protocol on port 6379**. The agent's memory lives in a named graph. The agent **reads** memory via Cypher recall queries and **writes** memory as new nodes/edges after each investigation. There's no ORM — your memory schema is your Cypher, created and evolved by the agent itself. **This is what makes it a cognitive memory layer, not a database.**

---

## 3. ARCHITECTURE (Solo-Optimized)

```text
┌────────────────────────────────────────────────────────────┐
│                NEXT.JS UI (investigator console)           │
│  Session indicator · Memory graph view · Agent transcript  │
└────────────────────────────┬───────────────────────────────┘
                             │ REST
                             ▼
┌────────────────────────────────────────────────────────────┐
│           PYTHON AGENT BACKEND (FastAPI)                   │
│                                                            │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  AGENT LOOP (LLM function calling)                   │  │
│  │  perceive → recall → reason → act → write memory     │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌─────────────┐ ┌──────────────┐ ┌─────────────────────┐  │
│  │ Memory      │ │ Tool Router  │ │ Swarm Coordinator   │ │
│  │ Reader/     │ │ (dynamic     │ │ (nice-to-have:      │ │
│  │ Writer      │ │  selection)  │ │  parallel hunters)  │ │
│  └─────────────┘ └──────────────┘ └─────────────────────┘  │
└────────────────────────────┬───────────────────────────────┘
                             │ Redis protocol :6379
                             ▼
┌────────────────────────────────────────────────────────────┐
│                  FALKORDB (Docker)                         │
│  Graph: "mnemos"  — THE AGENT'S MIND                       │
│  ┌────────────────┐ ┌────────────────┐ ┌────────────────┐  │
│  │ SEMANTIC       │ │ EPISODIC       │ │ PROCEDURAL     │  │
│  │ actors,TTPs,   │ │ investigations,│ │ playbooks,     │  │
│  │ IoCs, assets   │ │ alerts,findings│ │ actions,rates  │  │
│  └────────────────┘ └────────────────┘ └────────────────┘  │
└────────────────────────────────────────────────────────────┘
                             ▲
                             │ One-time scenario seed (Python)
┌────────────────────────────────────────────────────────────┐
│         SEED SCRIPT (scripts/seed_scenario.py)             │
│  Alerts, IoCs, assets, empty procedural memory             │
└────────────────────────────────────────────────────────────┘
```

**Design decisions:**
- **Python FastAPI backend** for the agent (best LLM/function-calling + FalkorDB ecosystem). **Next.js** for the polished console. Clear separation, both in docker-compose.
- The agent **writes its own memory** as it investigates — this is what makes it a cognitive layer, and it's what you'll show growing in FalkorDB Browser.
- UI never renders the whole graph; it renders **recall results** + a live "memory grew by N nodes" counter.

---

## 4. WHAT WE BUILD (Scoped for a 7-Day Sprint)

### MUST HAVE (won't ship without)
| # | Component | What | FalkorDB/Agentic Feature Proven |
|---|---|---|---|
| 1 | **Scenario seed** | Synthetic alerts, IoCs, assets, TTP catalog; empty episodic/procedural memory at start | Graph modeling, indexes |
| 2 | **3 memory types** | Semantic, episodic, procedural modeled as distinct node families in one graph | Cognitive memory layer |
| 3 | **Memory writer** | After each investigation, agent persists findings as nodes/edges | Persistent memory |
| 4 | **Memory recall** | Multi-hop Cypher recall queries feed the LLM as context | Sub-ms traversal + Agentic RAG |
| 5 | **Agent loop** | perceive → recall → reason → act → write, via LLM function calling | Autonomous agent |
| 6 | **Dynamic tool selection** | Agent picks analysis tool based on recalled memory | Dynamic tool selection |
| 7 | **Cross-session persistence** | "Restart Agent" clears in-memory state, keeps FalkorDB; agent recalls on next alert | **The money shot** |
| 8 | **Console UI** | Session indicator, memory graph view, agent transcript, recall-latency display | Explainable agent |
| 9 | **docker-compose** | One-command judge setup: FalkorDB + backend + UI | Deployment rule |
| 10 | **Demo video + README** | Per submission checklist | Rule 9 |

### NICE TO HAVE (after Day 5, only if green)
| # | Component | Why |
|---|---|---|
| 11 | **Swarm mode** | 3 parallel hunters, shared memory, concurrent recall latency | High-concurrency + multi-agent criteria |
| 12 | **Memory decay / confidence** | Edge weights = recall strength, decay over time | Realistic cognition |
| 13 | **FalkorDB Cloud deployment** | Live URL bonus (only if Day 0 verification passes) | Polish |

### WILL NOT BUILD
❌ Real SIEM/SOAR integrations (Rule 5 + time sink)
❌ Full autonomous multi-step remediation (keep actions advisory/deterministic)
❌ Vector embeddings / vector store (the point is *graph* memory, not vector RAG)
❌ Auth / multi-tenancy
❌ Custom agent framework (use clean loop or a lightweight, well-known one)
❌ Mobile layout

---

## 5. MEMORY MODEL & CYPHER — THE COGNITIVE CORE

### 5.1 Data Model (must appear in README — Rule 9)

```cypher
// ── SEMANTIC MEMORY (knowledge / facts) ────────────────
(:ThreatActor {id, name})
(:TTP         {id, mitre_id, name})          // MITRE ATT&CK technique
(:IoC         {type, value})                 // indicator of compromise
(:Asset       {id, name, type, criticality})

// ── EPISODIC MEMORY (experiences / investigations) ─────
(:Alert        {id, type, severity, timestamp})
(:Investigation{id, alert_id, timestamp, status, conclusion})

// ── PROCEDURAL MEMORY (playbooks / skills) ─────────────
(:Playbook {id, name, success_rate})
(:Action   {id, type, description})

// ── RELATIONSHIPS ──────────────────────────────────────
(:ThreatActor)-[:USES]->(:TTP)
(:ThreatActor)-[:ASSOCIATED_WITH]->(:IoC)
(:IoC)-[:OBSERVED_ON]->(:Asset)
(:Investigation)-[:TRIGGERED_BY]->(:Alert)
(:Investigation)-[:FOUND]->(:IoC)
(:Investigation)-[:ATTRIBUTED_TO]->(:ThreatActor)
(:Investigation)-[:APPLIED]->(:Playbook)
(:Playbook)-[:CONTAINS]->(:Action)
(:Playbook)-[:EFFECTIVE_AGAINST]->(:TTP)

// ── INDEXES (seed time) ────────────────────────────────
CREATE INDEX FOR (i:IoC)    ON (i.value);
CREATE INDEX FOR (t:TTP)    ON (t.mitre_id);
CREATE INDEX FOR (a:Asset)  ON (a.id);
CREATE INDEX FOR (p:Playbook) ON (p.name);
```

### 5.2 The Hero Recall Queries (go verbatim in README + demo)

**R1 — Episodic recall: "Have I seen this IoC before?"**
```cypher
MATCH (ioc:IoC {value: $ioc})<-[:FOUND]-(inv:Investigation)
      -[:ATTRIBUTED_TO]->(actor:ThreatActor)
OPTIONAL MATCH (actor)-[:USES]->(ttp:TTP)
RETURN actor.name AS attributed_actor,
       collect(DISTINCT ttp.mitre_id) AS known_ttps,
       inv.conclusion AS prior_conclusion;
```

**R2 — Procedural recall: "What playbook worked against this TTP?"**
```cypher
MATCH (p:Playbook)-[:EFFECTIVE_AGAINST]->(t:TTP {mitre_id: $technique})
RETURN p.name, p.success_rate
ORDER BY p.success_rate DESC LIMIT 1;
```

**R3 — Multi-hop recall: "Is this asset tied to a known actor?"**
```cypher
MATCH path = (a:Asset {id: $asset})<-[:OBSERVED_ON]-(:IoC)
      -[:ASSOCIATED_WITH]-(actor:ThreatActor)
RETURN path;
```

**R4 — Cross-session recall (the money-shot query):**
```cypher
// On a NEW alert, recall everything relevant from ALL past investigations
MATCH (past:Investigation)-[:FOUND]->(ioc:IoC)<-[:FOUND]-(now:Investigation {id:$current})
MATCH (past)-[:ATTRIBUTED_TO]->(actor)
RETURN actor.name, count(past) AS times_seen,
       collect(DISTINCT ioc.value) AS shared_iocs;
```

**R5 — Memory write (agent persists a new learning):**
```cypher
MERGE (ioc:IoC {value: $value}) SET ioc.type = $type
MERGE (actor:ThreatActor {name: $actor})
MERGE (actor)-[:ASSOCIATED_WITH]->(ioc);
```

### 5.3 Agent Memory Integration Strategy (the 🔴 fix)
```text
Day 0: Does FalkorDB ship an official agent-memory layer
       (Mem0 / LangChain / LlamaIndex integration)?
        │
        ├─ YES & stable ──▶ use it, cite it, show it in README
        │
        └─ NO / awkward ──▶ custom loop:
                            recall = run Cypher R1–R4 → serialize → LLM context
                            write  = parse LLM output → run Cypher R5
                            README: "We treat FalkorDB as the cognitive layer
                            and drive it directly with Cypher."
```
Either way, **remove FalkorDB and the agent loses all memory** → Rule 3 satisfied in both branches. 🔴→✅

### 5.4 The Agentic-RAG Layer (the differentiator)
This is what makes it "Next-Gen RAG," not just an agent with a database:
1. Alert arrives → agent runs **recall queries R1–R4** against FalkorDB.
2. Recalled subgraph is **serialized into structured context** (actor, TTPs, past conclusions, best playbook).
3. **Single LLM call** reasons over graph context + picks a tool + drafts findings.
4. Agent **writes new memory (R5)** back to the graph.
5. Every conclusion in the transcript cites the **exact recall query** that produced it → source attribution.

> **Why this wins:** Vector memory retrieves "similar-looking text." Mnemos *traverses relationships* — asset→IoC→actor→playbook — and recalls the exact prior experience that matters, in milliseconds. That is reasoning over structure, which is what vector RAG can't do.

### 5.5 The Framing (don't get caught)
**NEVER say:** "This is just a database the agent writes to."
**ALWAYS say:** *"Mnemos separates memory into episodic, semantic, and procedural — the way cognitive science models human memory — and stores all three in one graph. The agent reads and writes that graph every step. Restart it, and it still remembers. That's a cognitive memory layer, not a log."*

---

## 6. SYNTHETIC SCENARIO GENERATOR (`scripts/seed_scenario.py`)

**Deterministic. Reproducible. Engineered for the demo.** `random.seed(42)`.

| Element | Design | Demo Purpose |
|---|---|---|
| **TTP catalog** | ~10 MITRE ATT&CK techniques (e.g., T1059.001 PowerShell, T1078 Valid Accounts) | Semantic seed |
| **Threat actor** | `APT-CRIMSON`, pre-linked to 2 TTPs + 2 IoCs | The recurring villain |
| **Assets** | ~20 hosts across 3 subnets, varied criticality | Investigation targets |
| **Alert queue** | Alert #1 (Session 1), Alert #2 (Session 2, related), +2 for swarm | Drives the story |
| **Empty episodic/procedural** | Start with **no** investigations, **no** learned playbooks | Proves memory grows from zero |

**Seed contract:**
1. Connect → `select_graph("mnemos")` (delete if exists)
2. Create indexes + semantic seed (TTPs, actor, assets, IoCs)
3. Leave episodic + procedural **empty** (the agent fills them live)
4. Print verification counts
5. Exit 0 → docker-compose `seeded` healthcheck passes

---

## 7. CONSOLE UI (Next.js)

**Stack:** Next.js (App Router) · TypeScript · Tailwind · shadcn/ui · react-cytoscapejs

| Page/Panel | Purpose |
|---|---|
| `/` Console | Session indicator, alert feed, "Restart Agent" button, memory stats |
| Memory Graph | Cytoscape view of the agent's mind, colored by memory type |
| Transcript | Agent's perceive→recall→reason→act trace with **recall latency** |
| Recall Inspector | Shows the exact Cypher recall query + result for every decision |

**UX details that win judges:**
- **"Restart Agent" button** that visibly clears in-memory state but keeps the graph → the persistence moment
- **Recall latency badge** on every memory lookup (`recalled 4 facts in 2ms`)
- Memory graph **grows live** as the agent writes, color-coded semantic/episodic/procedural
- Dark "SOC ops center" aesthetic, monospace Cypher panels

---

## 8. DEMO SCRIPT (3 Minutes — Judge-Spoonfeeding)

| Time | On Screen | Judge Writes Down |
|---|---|---|
| 0:00–0:20 | **Hook:** "Agents forget everything between sessions. What if yours remembered every attacker it ever met?" | "Clear agentic-memory framing." |
| 0:20–0:45 | **Session 1 begins:** Alert #1 (suspicious PowerShell). Memory graph is small/empty. | "Starting from zero memory." |
| 0:45–1:25 | **Investigate from scratch:** agent recalls nothing, analyzes IoC, attributes to APT-CRIMSON, applies a playbook, **writes memory**. Graph grows. | "Semantic+episodic+procedural memory being written. Agent does real work." |
| 1:25–1:45 | **The restart:** click **Restart Agent** → in-memory state cleared. FalkorDB untouched. | "About to prove persistence." |
| 1:45–2:25 | **Session 2:** Alert #2 (related). Agent **recalls** APT-CRIMSON + T1059.001 + prior playbook in **2ms**, skips rediscovery, responds faster. Transcript shows "Recalled from memory." | "Persistent cognitive memory ✅. Sub-ms recall ✅. Cross-session ✅." |
| 2:25–2:45 | **Recall Inspector:** show the exact Cypher recall queries + source attribution behind each conclusion. | "Explainable. Graph is the memory, not decoration." |
| 2:45–3:00 | **Close:** "Agents forget. The graph remembers. Mnemos: agentic memory on FalkorDB." + repo/setup shot. | "Polished. Complete. Textbook agentic RAG." |

**Memorized 30-second judge answer:**
*"Mnemos is an autonomous threat hunter whose memory lives in FalkorDB. It stores episodic, semantic, and procedural memory as one graph, recalls it with multi-hop Cypher in milliseconds, and writes new learnings back after every investigation. Restart the agent and it still remembers — that persistence is the graph. Vector memory can't traverse asset-to-IoC-to-actor-to-playbook; a knowledge graph can. That's agentic Next-Gen RAG."*

---

## 9. FALKORDB INTEGRATION PROOF (Rule 3 armor)

| Judge Thought | Our Proof |
|---|---|
| "Is FalkorDB just a log the agent writes to?" | Memory is **recalled via multi-hop Cypher** into the LLM's context; remove FalkorDB and the agent has no recall |
| "Does memory actually persist?" | **Restart Agent** on camera → in-memory state cleared → agent still recalls |
| "Is it sub-millisecond?" | Recall-latency badge on every lookup, live in the demo |
| "Where's the agentic RAG?" | Recalled subgraph → structured LLM context → reasoning → memory write-back, with source attribution |
| "Dynamic tool selection?" | Agent picks its analysis tool based on recalled memory, shown in transcript |
| "Can I run it?" | `docker compose up` → seeded graph + backend + UI in one command |
| "Do they understand it?" | README explains the 3 memory types, every recall query, the integration choice, and the write-back loop |

---

## 10. PHASE 0 — PRE-HACKATHON (NOW → Kickoff)

**Today (Sep 1):**
- [ ] REGISTER via Google Form + join WeMakeDevs & FalkorDB Discords
- [ ] **Decide Track 1 vs Track 2** (see decision framework below) — you can only submit one

**Before kickoff — Day-0 Verification Protocol:**
- [ ] 🔴 Check for an **official FalkorDB agent-memory integration** (Mem0 / LangChain / LlamaIndex). If solid, plan to use it; else commit to custom loop
- [ ] 🔴 **Concurrent write test**: two processes writing to one graph — confirm no corruption/races (decides swarm feasibility)
- [ ] 🔶 `docker run -p 6379:6379 -d falkordb/falkordb:latest` → connect with Python client
- [ ] 🔶 `pip install falkordb` → create graph, `CREATE`/`MATCH`/`MERGE` round-trip works
- [ ] 🔶 Test LLM **function calling** from Python (OpenAI / Gemini). Confirm tool-selection works
- [ ] 🔴 FalkorDB Cloud: free tier? TLS from backend?
- [ ] 🔶 Cytoscape.js spike: render ~200-node memory graph + live append
- [ ] Confirm exact start/end times + kickoff session
- [ ] Sketch the 3-memory-type data model diagram (allowed pre-planning → README)

**Exit criteria:** every 🔴 is ✅ or its fallback is chosen. Zero unknowns when coding starts.

---

## 11. SPRINT SCHEDULE (Day 1–7)

**Day 1 — Foundation**
- New repo + README skeleton (memory-model diagram from Phase 0)
- `docker-compose.yml`: falkordb + backend + web
- `scripts/seed_scenario.py`: semantic seed, empty episodic/procedural
- ✅ SUCCESS: seeded graph verified in FalkorDB Browser

**Day 2 — The Memory Core**
- Implement recall queries R1–R4 + write R5 against real data
- Memory reader/writer module (Python) over FalkorDB client
- Recall-latency harness (`{result, cypher, ms}`)
- ✅ SUCCESS: recall + write work from CLI, latency captured

**Day 3 — The Agent Loop**
- FastAPI agent loop: perceive→recall→reason→act→write
- LLM function calling + tool router
- ✅ SUCCESS: one alert → agent recalls (empty) → investigates → writes memory

**Day 4 — Persistence + Console**
- "Restart Agent" flow (clear in-memory, keep graph)
- Next.js console: session indicator, transcript, memory graph view
- Recall Inspector (live Cypher + latency)
- ✅ SUCCESS: Session 1 → restart → Session 2 recalls ✅

**Day 5 — Agentic-RAG Layer + Hardening**
- Source attribution (transcript cites recall queries)
- Edge cases: LLM timeout → show recall only; empty recall → investigate from scratch
- Error/empty/loading states everywhere
- ✅ SUCCESS: full loop is bulletproof, restart-recall repeats cleanly

**Day 6 — Swarm (if green) + Demo Prep**
- Nice-to-have #11: 3 parallel hunters, concurrent recall latency
- Record demo 5+ times; fix what breaks
- README: setup, memory model, Cypher section, agentic-RAG explanation, track name, AI disclosure
- ✅ SUCCESS: demo lands clean 3× in a row

**Day 7 — FREEZE + SUBMIT**
- NO NEW FEATURES. Final video · README polish · docker-compose fresh-clone test
- Submit with track named: *Best Agentic AI Use Case*
- ✅ SUCCESS: submitted before deadline

---

## 12. README STRUCTURE (Rule 9-proof)

```markdown
# Mnemos
> Agents forget. The graph remembers.
**Track: Best Agentic AI Use Case**

## The Problem (stateless agents re-discover the world every session)
## Demo Video
## How It Works (The Agentic-RAG Loop)
  ### 1. Three Memory Types (episodic · semantic · procedural)
  ### 2. Multi-hop Recall (Cypher, sub-millisecond)
  ### 3. Reasoning (LLM over graph context)
  ### 4. Memory Write-back (the agent grows its own mind)
## Graph Data Model (diagram + node/edge tables)
## The Recall Queries (each hero query + what it proves)
## Memory Integration (official vs custom — explained honestly)
## Architecture
## Tech Stack
## Setup (judge path)
  ### Option A: docker compose up (one command)
  ### Option B: manual (FalkorDB + backend + web)
  ### Option C: live deployment (if Cloud works)
## Features
## AI Usage Disclosure
## Challenges & Learnings
```

---

## 13. PROJECT STRUCTURE

```text
mnemos/
 ├── backend/                     # Python FastAPI agent
 │   ├── app/
 │   │   ├── main.py             # FastAPI entry
 │   │   ├── agent/
 │   │   │   ├── loop.py         # perceive→recall→reason→act→write
 │   │   │   ├── memory.py       # recall R1–R4 + write R5
 │   │   │   ├── tools.py        # dynamic tool router
 │   │   │   └── swarm.py        # (nice-to-have) parallel hunters
 │   │   └── api/routes.py
 │   ├── requirements.txt
 │   └── Dockerfile
 ├── web/                         # Next.js console
 │   ├── app/
 │   │   ├── page.tsx            # Console
 │   │   ├── api/...             # proxies to backend
 │   │   └── components/
 │   │       ├── MemoryGraph.tsx
 │   │       ├── Transcript.tsx
 │   │       └── RecallInspector.tsx
 │   └── package.json
 ├── scripts/
 │   ├── seed_scenario.py        # deterministic scenario
 │   └── verify_seed.py
 ├── docker-compose.yml          # falkordb + backend + web
 ├── README.md
 └── .env.example                # FALKORDB_HOST/PORT, LLM_API_KEY
```

---

## 14. TECH STACK (Final)

| Layer | Choice | Why |
|---|---|---|
| Graph DB / memory | FalkorDB (Docker local; Cloud stretch) | Mandatory; the cognitive layer |
| Agent backend | Python + FastAPI + falkordb client | Best agent/LLM ecosystem |
| LLM | OpenAI GPT-4o-mini or Gemini Flash | Fast, cheap, solid function calling. Disclosed |
| Agent loop | Clean custom loop (or lightweight framework) | Explainable, no black box |
| Frontend | Next.js + Tailwind + shadcn/ui | Your proven stack |
| Memory viz | react-cytoscapejs | Live, growing memory graph |
| Judge setup | docker-compose | One command, rule-compliant |

---

## 15. CONTINGENCY TABLE

| If This Fails | Do This Instead |
|---|---|
| Official memory integration flaky | Custom Cypher recall/write loop (§5.3) — document the choice |
| Concurrent writes race | Single-writer design; swarm reads concurrently, writes serialize |
| LLM tool-selection unreliable | Constrain to 3 tools; pre-script the demo path, cache outputs |
| Restart-recall flaky live | Pre-record the recall for the video; keep live for judges running locally |
| Cytoscape lags | Render last-N memory nodes; full graph stays in DB, proven by Recall Inspector |
| FalkorDB Cloud awkward | docker-compose local IS the submission path (rule-compliant) |
| Swarm too hard | Ship single-agent-with-memory (still hits every core criterion). Swarm is bonus |
| Time collapses | Ship MUST-HAVES 1–10; cut swarm + decay. Core persistence loop still wins |

---

## 16. DECISION FILTER (Track 2 edition)

For every idea during the sprint:
1. Does the demo work without it? → YES → Cut
2. Does it make FalkorDB the **memory** (not a log)? → NO → Deprioritize
3. Does it strengthen the **"agent got smarter"** story? → NO → Deprioritize
4. Can it be built in < 2 hours? → NO → Cut
5. Will a judge see it in the 3-minute video? → NO → Cut
6. Does it risk Rule 3 (graph becomes decoration)? → YES → Kill it

---

## 17. WINNING CRITERIA ALIGNMENT (Track 02 + Theme)

### Track 02 Scorecard
| Judging Focus | Mnemos' Answer |
|---|---|
| Persistent cognitive memory | Episodic + semantic + procedural in one graph, survives restart on camera |
| Multi-agent state sharing | Swarm of hunters on one shared memory graph (nice-to-have, but designed in) |
| High-concurrency lookups | Parallel recall with live latency (swarm mode) |
| Sub-millisecond traversals | Recall-latency badge on every lookup |
| Dynamic tool selection | Tool choice driven by recalled memory, shown in transcript |
| Graph does real work (Rule 3) | Remove FalkorDB → agent has no memory, no recall, no persistence |
| Repo quality | One-command setup, memory-model diagram, Cypher section, AI disclosure |
| Demo | 3-min story: forget → investigate → remember → restart → recall |

### Hackathon Theme Scorecard ("Building Next-Gen RAG")
| Theme Element | Mnemos' Answer |
|---|---|
| "Combine knowledge graphs, LLMs, and autonomous agents" | Knowledge graph = memory. LLM = reasoning. Agent loop ties them. |
| "Vector RAG breaks down on multi-step reasoning" | Recall traverses asset→IoC→actor→playbook — multi-hop structure vector search can't do |
| "Fast, accurate, explainable" | Sub-ms recall (fast). Deterministic Cypher (accurate). Transcript cites recall queries (explainable) |
| Source attribution | Every conclusion links to the exact recall query that produced it |

---

## 🎯 TRACK 1 vs TRACK 2 — Decision Framework

Since you can only submit **one**, here's how to choose:

| Factor | Track 1 — Syndicate | Track 2 — Mnemos |
|---|---|---|
| **Core mechanism** | Graph does **reasoning** + LLM narrates | Graph is **memory** + LLM reasons over it |
| **Money shot** | Hairball snaps into fraud rings | Agent remembers across a restart |
| **Your edge** | Cybersecurity + clean deterministic demo | Agent-building experience (MissionControl) + security domain |
| **Technical risk** | Low (deterministic Cypher + 1 LLM call) | Medium (agent loop + function calling + persistence) |
| **Wow factor** | Visual (graph clustering) | Conceptual ("it got smarter") |
| **Solo safety** | Very high | High, but more moving parts |
| **Best if…** | You want the safest path to a polished win | You want the more ambitious, memorable demo |

**My honest recommendation:** **Syndicate (Track 1)** is the *safer, higher-probability* play for a solo dev — deterministic, visually dramatic, low risk. **Mnemos (Track 2)** is the *higher-ceiling* play — the "agent that remembers" story is more novel and memorable, but has more moving parts (agent loop, function calling, persistence).

If you're optimizing to **win reliably**, go Syndicate. If you're optimizing to **stand out** and you're confident in your agent-building speed, go Mnemos.

---

## EXECUTE SEQUENCE
1. Register now (Google Form) + join both Discords.
2. **Decide Track 1 vs Track 2** using the framework above — you can only build one.
3. Run the matching Phase 0 Verification Protocol — convert every 🔴 to ✅.
4. Report back the results, and we write the seed script + core module together.

Both plans are airtight because each tells you exactly what's unverified and what to do about it. Pick your weapon, verify, then go win. 🏆

Want me to adapt Mnemos to a **different domain** instead (e.g., DevOps incident memory, a personal "second brain," or customer-support swarm)? I can re-theme it in one pass.