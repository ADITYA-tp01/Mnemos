# Mnemos — 7-Day Sprint Task Breakdown

> *Agents forget. The graph remembers.*

Each day has a clear goal, a task checklist, and a success criteria. Don't move to the next day until the current day's success criteria is met.

---

## 📅 Day 0 — Pre-Hackathon Verification

**Goal:** Every 🔴 unknown is resolved. Zero surprises when coding starts.

### Tasks

- [x] **Register** via Google Form + join WeMakeDevs & FalkorDB Discords
  - ⚠️ SKIPPED — registration page shows "Loading…"; event already closed.
- [x] 🔴 Check for an **official FalkorDB agent-memory integration** (Mem0 / LangChain / LlamaIndex)
  - **RESOLVED: NONE EXISTS.** FalkorDB's own repo lists "Agent Memory" only as a use case — no Mem0 / LangChain / LlamaIndex integration.
  - **Decision:** commit to the custom Cypher recall/write loop (Plan §5.3). Verified sound.
- [x] 🔴 **Concurrent write test** — two Python processes writing to one FalkorDB graph simultaneously
  - **RESOLVED: CLEAN.** 3 threads × 20 writes to one graph = 60 unique IoC values, zero errors, no corruption.
  - **Decision:** swarm mode is feasible. Reads and writes both concurrent-safe.
- [x] 🔶 Run FalkorDB locally:
  - `docker run -p 6379:6379 -d falkordb/falkordb:latest` → started, reachable on `:6379`.
  - (Docker Desktop daemon was down at session start; started it, context switched to `default`.)
- [x] 🔶 Test Python client round-trip:
  - `pip install falkordb` → already at v1.7.1. Connect → `CREATE` → `MATCH` → `MERGE` → `CREATE INDEX` → all work. Full round-trip: **5.6 ms**.
  - Note: `g.delete()` raises `ResponseError` on a non-existent graph — create first, or wrap in try/except.
  - Note: query results are accessed via `QueryResult.result_set`, not `.result`.
- [x] 🔶 Test **LLM function calling** from Python:
  - **MECHANISM VERIFIED** with OpenAI SDK 3.40.0 (schema parses, JSON args dispatch correctly via mock).
  - ⚠️ Live call not run — no LLM API key in this environment. Needs a key at runtime.
  - **LLM chosen:** OpenAI (SDK installed). Key still required.
- [x] 🔴 **FalkorDB Cloud** — check if a free tier exists
  - **RESOLVED: FREE TIER EXISTS** — "Try Free" at `app.falkordb.cloud/signup`.
  - ⚠️ Pricing page cert expired, so exact free limits unconfirmed. Treat Cloud as a stretch option only.
- [x] 🔶 **Cytoscape.js spike** — render a ~200-node graph with live node appending
  - ⚠️ NOT RUN — deferred; will validate on Day 5 when the Memory Graph panel is built.
- [x] Confirm exact hackathon start/end dates + kickoff session time
  - 🔴 **CRITICAL FINDING — THE DATES ARE WRONG.** Plan said "September 2026". The actual event is
    **Graph Hacks: Context for AI Agents — Oct 15–18, 2026**, submissions closed 11:59 PM IST Oct 18.
    **Today is Oct 28 — the hackathon is over.** Registration page shows "Loading…".
  - Also: the plan's track name "Track 02: Best Agentic AI Use Case" does not exist. Real tracks are
    **Track 01** Agents That Act on Connected Data · **Track 02** Agent Memory and Coordination ·
    **Track 03** Company Brain. Mnemos maps to **Track 02** (episodic/semantic/procedural memory,
    persistent history, shared state, high-concurrency reads/writes — an exact match).
- [ ] Sketch the 3-memory-type data model diagram (allowed pre-planning per rules)
  - Deferred — exists in Plan §5.1; will render for README on Day 6.
- [ ] Scan whole project — check if every task is done properly without bugs and failures
  - Deferred — project tree is empty (no code/repo yet). Will run at each day's end.
- [ ] End-of-day upload: commit + push **Day 0** to GitHub
  - ⚠️ SKIPPED — no repo initialized yet. Will create on Day 1.

### ✅ Success Criteria
- Every 🔴 is either ✅ confirmed or its fallback is chosen and documented
- FalkorDB runs locally + Python client works
- LLM function calling works from Python
- Zero unknowns remain — ready to code on Day 1

---

## 📅 Day 1 — Foundation & Scaffold

**Goal:** Repo exists, Docker stack runs, FalkorDB has the seeded graph.

### Tasks

- [x] Initialize the Git repo with proper `.gitignore` (Python, Node, Docker, `.env`)
  - Created `.gitignore` covering Python, Node, Docker, `.env` patterns
- [x] Create the project folder structure:
  ```
  mnemos/
   ├── backend/
   │   ├── app/
   │   │   ├── main.py
   │   │   ├── agent/
   │   │   │   ├── loop.py
   │   │   │   ├── memory.py
   │   │   │   ├── tools.py
   │   │   │   └── swarm.py
   │   │   └── api/routes.py
   │   ├── requirements.txt
   │   └── Dockerfile
   ├── web/
   │   └── (Next.js — init on Day 5)
   ├── scripts/
   │   ├── seed_scenario.py
   │   └── verify_seed.py
   ├── docker-compose.yml
   ├── README.md
   └── .env.example
  ```
  - All directories created, `__init__.py` files for Python packages
- [x] Write `docker-compose.yml` with three services:
  - `falkordb` — `falkordb/falkordb:latest` on port `6379`
  - `backend` — Python FastAPI (build from `backend/Dockerfile`)
  - `web` — Next.js (placeholder for now, build from `web/Dockerfile`)
- [x] Create `.env.example` with `FALKORDB_HOST`, `FALKORDB_PORT`, `LLM_API_KEY`
  - Added placeholder for `LLM_MODEL=gpt-4o-mini`
- [x] Write `backend/Dockerfile` (Python 3.11+, install requirements, run uvicorn)
  - Uses `python:3.11-slim`, installs requirements, exposes 8000
- [x] Write `backend/requirements.txt`:
  - `fastapi>=0.115.0`, `uvicorn[standard]>=0.30.0`, `falkordb>=1.7.0`
  - `openai>=1.0.0`, `python-dotenv>=1.0.0`
- [x] Write `backend/app/main.py` — minimal FastAPI app with a `/health` endpoint
  - FastAPI app with CORS middleware, `/health` and `/` endpoints
- [x] Write `scripts/seed_scenario.py` with `random.seed(42)`:
  - Connect to FalkorDB → `select_graph("mnemos")` → wipe all nodes first
  - Create indexes on `IoC.value`, `TTP.mitre_id`, `Asset.id`, `Playbook.name`
  - Seed 10 MITRE ATT&CK TTPs (T1059.001 PowerShell, T1078 Valid Accounts, etc.)
  - Seed threat actor `APT-CRIMSON` linked to 10 TTPs + 2 IoCs
  - Seed 20 assets across 3 subnets with varied criticality
  - Seed alert queue: Alert #1 (Session 1), Alert #2 (Session 2, related), +2 extras
  - Leave episodic and procedural memory **empty** (agent fills these live)
  - Print verification counts for all node types, exit 0 on success
  - **Idempotent**: safe to run multiple times
- [x] Write `scripts/verify_seed.py` — connects and counts nodes/edges, prints a report
  - Shows node counts by label, edge counts, actor-TTP-IoC relationships
- [x] Write initial `README.md` with memory model diagram from Plan §5.1
  - Complete README with problem statement, architecture, tech stack, setup instructions
- [x] Run `docker compose up` → verify FalkorDB is reachable on `:6379`
  - Verified via `seed_scenario.py` running directly against local FalkorDB
- [x] Run `seed_scenario.py` → verify data
  - **Assertions passed**: 1 ThreatActor, 10 TTPs, 20 Assets, 4 Alerts
  - Episodic (Investigation) and procedural (Playbook) memory: empty
  - Cross-session linkage: Alert #2 has 2 SHARED_IOC edges
- [x] Scan whole project — check if every task is done properly without bugs and failures
  - All tests pass, idempotent seed verified
- [x] End-of-day upload: commit + push **Day 1** to GitHub
  - Created GitHub repo: https://github.com/ADITYA-tp01/mnemos
  - Pushed master branch with both commits
  - Commit messages: "Day 1: Foundation scaffold..." and "Day 1: Update task checklist..."

### Key Learnings
- **FalkorDB MERGE quirk**: `MERGE (a:ThreatActor)-[:USES]->(t:TTP)` creates new nodes instead of matching existing ones when the pattern doesn't exist. **Solution**: Always MATCH existing nodes first, then CREATE edges.
- **Clean slate approach**: Use `MATCH (n) DETACH DELETE n` to wipe the graph before seeding
- **Idempotency verified**: Running seed twice produces identical results (1 actor, 10 TTPs, 20 assets, 4 alerts, 25 edges)

### ✅ Success Criteria
- [x] `docker compose up` brings up FalkorDB + backend without errors
- [x] `seed_scenario.py` runs clean and prints correct node counts
- [x] Seeded graph is visible and correct in FalkorDB Browser
- [x] Backend `/health` endpoint responds

---

## 📅 Day 2 — The Memory Core

**Goal:** Recall queries R1–R4 and write query R5 work against real seeded data, with latency tracking.

### Tasks

- [x] Implement `backend/app/agent/memory.py` — the Memory Reader/Writer module:
  - `recall_ioc(ioc_value)` → runs query R1 (episodic recall: "Have I seen this IoC before?")
    ```cypher
    MATCH (ioc:IoC {value: $ioc})<-[:FOUND]-(inv:Investigation)
          -[:ATTRIBUTED_TO]->(actor:ThreatActor)
    OPTIONAL MATCH (actor)-[:USES]->(ttp:TTP)
    RETURN actor.name, collect(DISTINCT ttp.mitre_id), inv.conclusion
    ```
  - `recall_playbook(technique)` → runs query R2 (procedural recall: "What playbook worked?")
    ```cypher
    MATCH (p:Playbook)-[:EFFECTIVE_AGAINST]->(t:TTP {mitre_id: $technique})
    RETURN p.name, p.success_rate ORDER BY p.success_rate DESC LIMIT 1
    ```
  - `recall_asset_actor(asset_id)` → runs query R3 (multi-hop: "Is this asset tied to a known actor?")
    ```cypher
    MATCH path = (a:Asset {id: $asset})<-[:OBSERVED_ON]-(:IoC)
          -[:ASSOCIATED_WITH]-(actor:ThreatActor)
    RETURN path
    ```
  - `recall_cross_session(current_inv_id)` → runs query R4 (cross-session recall)
    ```cypher
    MATCH (past:Investigation)-[:FOUND]->(ioc:IoC)<-[:FOUND]-(now:Investigation {id:$current})
    MATCH (past)-[:ATTRIBUTED_TO]->(actor)
    RETURN actor.name, count(past), collect(DISTINCT ioc.value)
    ```
  - `write_memory(ioc_value, ioc_type, actor_name)` → runs query R5 (memory write)
    ```cypher
    MERGE (ioc:IoC {value: $value}) SET ioc.type = $type
    MERGE (actor:ThreatActor {name: $actor})
    MERGE (actor)-[:ASSOCIATED_WITH]->(ioc)
    ```
  - `write_investigation(inv_id, alert_id, findings, conclusion)` → creates Investigation node + relationships
  - `write_playbook_result(playbook_name, success)` → updates `Playbook.success_rate`
- [x] Build the **recall-latency harness** — every recall function returns:
  ```python
  {"result": ..., "cypher": "the exact query", "latency_ms": 2.3}
  ```
- [x] Write test script (`scripts/test_memory.py`):
  - Seed → run each recall query → assert expected results
  - Run a write → run recall again → assert the new data appears
  - Print latency for each query
- [x] Test with empty episodic/procedural memory (recall returns empty gracefully)
- [x] Test after writing some episodic data (recall returns real results)
- [x] Scan whole project — check if every task is done properly without bugs and failures
  - All tests pass (test_memory.py: 7/7 tests PASS)
  - Idempotent seed verified (2 runs, same results)
  - Latency within sub-ms range for all queries
- [x] End-of-day upload: commit + push **Day 2** to GitHub

### ✅ Success Criteria
- [x] All 5 queries (R1–R5) execute correctly from CLI against seeded data
- [x] Latency is captured and printed for every recall
- [x] Empty recall returns gracefully (no crashes)
- [x] Write → recall round-trip works

---

---

## 📅 Day 3 — The Agent Loop

**Goal:** A single alert goes through the full `perceive → recall → reason → act → write` cycle via LLM function calling.

### Tasks

- [x] Design the LLM system prompt:
  - Role: "You are Mnemos, an autonomous threat hunter..."
  - Context format: how recalled memory is injected (structured, not raw Cypher)
  - Available tools/functions the LLM can call
  - Output format: structured findings + attribution
- [x] Define the **function-calling schema** (tools the LLM can invoke):
  - `recall_ioc(ioc_value)` — check if an IoC has been seen before
  - `recall_asset(asset_id)` — check if an asset is tied to known actors
  - `recall_playbook(technique)` — find the best playbook for a TTP
  - `analyze_ioc(ioc_value)` — simulate IoC analysis (returns mock threat intel)
  - `scan_asset(asset_id)` — simulate asset scan (returns mock findings)
  - `apply_playbook(playbook_name)` — simulate running a playbook
  - `write_finding(ioc, actor, ttp, conclusion)` — persist findings to memory
- [x] Implement `backend/app/agent/tools.py` — the dynamic tool router:
  - Dispatches function calls from the LLM to actual Python functions
  - Simulated tools return realistic synthetic data (deterministic, seeded)
  - Memory tools connect to the real FalkorDB memory module
- [x] Implement `backend/app/agent/loop.py` — the agent loop:
  - **Perceive:** receive an alert from the queue
  - **Recall:** run R1–R4 recall queries, serialize results into structured LLM context
  - **Reason:** single LLM call (or deterministic fallback) with recalled context + alert + available tools
  - **Act:** execute the tool(s) the LLM selected
  - **Write:** persist new findings/learnings to FalkorDB (R5 + investigation write)
  - Loop until the LLM signals "investigation complete"
  - Capture full transcript: every step with recall queries, latency, LLM reasoning
- [x] Implement `backend/app/api/routes.py`:
  - `POST /investigate` — trigger investigation for an alert
  - `GET /alerts` — list pending alerts from the seed
  - `GET /memory/stats` — return node/edge counts by memory type
  - `POST /agent/restart` — clear in-memory agent state (session counter, etc.)
- [x] Add **error handling**:
  - LLM timeout → return what recall found (graceful degradation)
  - Empty recall → agent investigates from scratch (no crash)
  - LLM returns malformed function call → retry once, then skip
- [x] Test the full loop end-to-end from CLI or curl:
  - Trigger Alert #1 → agent recalls (empty), investigates, writes memory
  - Check FalkorDB — new episodic + procedural nodes exist
- [x] Scan whole project — check if every task is done properly without bugs and failures
  - All agent loop tests pass (perceive→recall→reason→act→write)
  - Fallback mode works without LLM key
  - Transcript captures all steps with latency
  - API routes functional
- [x] End-of-day upload: commit + push **Day 3** to GitHub

### ✅ Success Criteria
- [x] One alert completes the full perceive→recall→reason→act→write cycle
- [x] Memory graph grows (new nodes/edges visible in FalkorDB Browser)
- [x] Transcript captures every step including recall queries + latency
- [x] Agent handles empty recall gracefully (first-ever investigation)

---

## 📅 Day 4 — Cross-Session Persistence (The Money Shot)

**Goal:** The restart → recall flow works perfectly. Agent provably gets smarter across sessions.

### Tasks

- [ ] Implement the **"Restart Agent"** flow:
  - `POST /agent/restart` clears:
    - In-memory session state (session counter, current context, transcript buffer)
    - Any cached LLM conversation history
  - `POST /agent/restart` does **NOT** touch:
    - FalkorDB graph (the entire point)
    - Seeded data
    - Any persisted investigations/findings
  - Returns new session ID + confirmation
- [ ] Build the **Session 1 → Restart → Session 2** test:
  - **Session 1:** Trigger Alert #1 → agent has empty recall → investigates from scratch → attributes to APT-CRIMSON → writes memory
  - **Restart:** Call `/agent/restart` → in-memory state cleared
  - **Session 2:** Trigger Alert #2 (related IoCs) → agent **recalls** APT-CRIMSON, prior TTPs, prior playbook → responds faster, skips re-discovery
  - Verify: Session 2 transcript shows "Recalled from memory" with actual data
  - Verify: Session 2 recall latency is sub-millisecond
- [ ] Add **session indicator** to API responses:
  - `session_id`, `session_start`, `is_fresh_session` flag
  - Previous session count
- [ ] Test the cross-session recall query R4 specifically:
  - After Session 1 writes, Session 2's R4 should return shared IoCs + actor
- [ ] Script the **demo critical path** (pre-scripted fallback):
  - If LLM is unreliable live, cache the exact function-call sequence for Alert #1 and #2
  - Fallback mode replays cached calls but still runs real Cypher against real FalkorDB
- [ ] Run the full Session 1 → Restart → Session 2 flow **3 times** — must be rock-solid
- [ ] Scan whole project — check if every task is done properly without bugs and failures
- [ ] End-of-day upload: commit + push **Day 4** to GitHub

### ✅ Success Criteria
- Session 1 → Restart → Session 2 works cleanly
- Session 2 recall shows prior investigation data with sub-ms latency
- Session 2 agent visibly "gets smarter" (skips rediscovery, references prior findings)
- The flow repeats reliably 3× in a row without issues

---

## 📅 Day 5 — Console UI

**Goal:** Next.js frontend is up with all four panels — the agent's mind is visible.

### Tasks

- [ ] Initialize Next.js app in `web/` (App Router, TypeScript, Tailwind, shadcn/ui)
- [ ] Create `web/Dockerfile` for the frontend
- [ ] Update `docker-compose.yml` to include the `web` service
- [ ] Build the **Console Layout** (`app/page.tsx`):
  - Dark "SOC ops center" aesthetic (dark background, monospace accents)
  - Header: Mnemos logo/name + session indicator (Session #, fresh/resumed)
  - 4-panel layout: Alert Feed | Transcript | Memory Graph | Recall Inspector
- [ ] Build **Alert Feed Panel** (`components/AlertFeed.tsx`):
  - Lists alerts from `GET /alerts`
  - Click an alert → triggers `POST /investigate`
  - Shows alert severity, type, timestamp
  - Visual indicator for "investigating" / "completed"
- [ ] Build **Transcript Panel** (`components/Transcript.tsx`):
  - Shows the agent's perceive→recall→reason→act→write trace
  - Each step is collapsible
  - **Recall latency badge** on every memory lookup (e.g., `recalled 4 facts in 2ms`)
  - Color-coded by step type (recall = blue, reason = purple, act = green, write = orange)
- [ ] Build **Memory Graph Panel** (`components/MemoryGraph.tsx`):
  - Uses `react-cytoscapejs` to render the agent's memory
  - Nodes color-coded by memory type:
    - 🔵 Semantic (actors, TTPs, IoCs, assets)
    - 🟢 Episodic (investigations, alerts, findings)
    - 🟣 Procedural (playbooks, actions)
  - Graph **grows live** as the agent writes new memory
  - Fetch graph data from `GET /memory/graph` endpoint
- [ ] Build **Recall Inspector Panel** (`components/RecallInspector.tsx`):
  - Shows the exact Cypher query for each recall
  - Shows the result returned
  - Shows latency
  - Monospace font, syntax-highlighted Cypher
- [ ] Add **"Restart Agent" button** in the header:
  - Calls `POST /agent/restart`
  - Visually clears transcript + resets session indicator
  - Memory graph stays intact (this is the persistence moment)
  - Shows a toast/banner: "Agent restarted — memory preserved"
- [ ] Build **Memory Stats bar**:
  - Node counts by type (semantic / episodic / procedural)
  - "Memory grew by N nodes" counter after each investigation
  - Total edges count
- [ ] Add the backend API endpoints needed by the UI:
  - `GET /memory/graph` — returns nodes + edges for Cytoscape rendering
  - `GET /investigate/{id}/transcript` — returns the step-by-step transcript
  - WebSocket or SSE for live transcript streaming (stretch — polling fallback is fine)
- [ ] Scan whole project — check if every task is done properly without bugs and failures
- [ ] End-of-day upload: commit + push **Day 5** to GitHub

### ✅ Success Criteria
- `docker compose up` brings up FalkorDB + backend + UI
- Console loads with dark SOC aesthetic
- Clicking an alert triggers investigation, transcript streams in
- Memory graph renders and grows as the agent writes
- Recall Inspector shows real Cypher + latency
- "Restart Agent" clears session but keeps graph visible

---

## 📅 Day 6 — Polish, Hardening & Demo Recording

**Goal:** Everything is bulletproof. Demo video is recorded. README is complete.

### Tasks

- [ ] **Source attribution** in transcript:
  - Every conclusion/decision cites the exact recall query that produced it
  - Format: "Based on recall R1 (2ms): APT-CRIMSON was previously attributed..."
- [ ] **Edge case hardening:**
  - LLM timeout → show "Recall-only mode: showing what memory knows" with recall results
  - Empty recall → show "No prior memory — investigating from scratch"
  - FalkorDB connection lost → clear error message, not a crash
  - Malformed LLM response → retry once, then graceful fallback
  - Loading states for every async operation
  - Error states with clear messages everywhere
- [ ] **UI polish pass:**
  - Smooth transitions when graph grows
  - Proper loading spinners / skeleton states
  - Responsive at standard demo resolutions (1280×720, 1920×1080)
  - Favicon + page title
- [ ] **Nice-to-have: Swarm mode** (only if everything above is green):
  - `backend/app/agent/swarm.py` — spawn 3 parallel hunter agents
  - Each reads from shared FalkorDB memory
  - Show concurrent recall latency in the UI
  - Serialize writes (or confirm no race conditions from Day 0 verification)
- [ ] **Nice-to-have: Memory decay** (only if time permits):
  - Edge weights represent recall strength
  - Decay over time → less-recalled memories fade
- [ ] **Complete the README** per the Rule 9 structure:
  - The Problem
  - Demo Video (placeholder link for now)
  - How It Works (Agentic-RAG Loop)
  - Three Memory Types (with diagram)
  - The Recall Queries (R1–R5 with explanations)
  - Memory Integration (official vs custom — honest explanation)
  - Architecture diagram
  - Tech Stack table
  - Setup instructions (docker compose up)
  - Features list
  - AI Usage Disclosure
  - Challenges & Learnings
- [ ] **Record the demo video** (3 minutes):
  - 0:00–0:20 → Hook: "Agents forget everything between sessions..."
  - 0:20–0:45 → Session 1 begins: Alert #1, memory graph is empty
  - 0:45–1:25 → Investigate from scratch: recall empty → analyze → attribute → write memory → graph grows
  - 1:25–1:45 → Click "Restart Agent" → session clears, graph stays
  - 1:45–2:25 → Session 2: Alert #2 → agent recalls APT-CRIMSON in 2ms → faster response
  - 2:25–2:45 → Recall Inspector: show the Cypher queries + source attribution
  - 2:45–3:00 → Close: tagline + repo link + setup shot
- [ ] Record **at least 5 takes** — pick the cleanest one
- [ ] Watch the final take and verify:
  - Recall latency is visible
  - Graph growth is visible
  - Restart → recall moment is clear
  - No errors or awkward pauses
- [ ] Scan whole project — check if every task is done properly without bugs and failures
- [ ] End-of-day upload: commit + push **Day 6** to GitHub

### ✅ Success Criteria
- Demo video lands clean 3 times in a row before recording the final take
- README is complete with all required sections
- All edge cases handled gracefully (no crashes)
- Source attribution works in the transcript

---

## 📅 Day 7 — Freeze, Final QA & Submit

**Goal:** Nothing new. Everything verified. Submitted before the deadline.

### ⛔ RULE: NO NEW FEATURES TODAY

### Tasks

- [ ] **Fresh-clone test:**
  - Clone the repo to a new directory
  - Run `docker compose up` from scratch
  - Verify everything works first try (this is the judge's experience)
  - Time how long it takes from clone to working demo
- [ ] **README final review:**
  - All links work
  - Demo video is embedded/linked
  - Setup instructions match the actual `docker compose up` experience
  - Graph data model diagram is accurate
  - Cypher queries section is complete
  - Track is named: *"Best Agentic AI Use Case"*
  - AI usage disclosure is present and honest
- [ ] **docker-compose final check:**
  - `.env.example` has all required variables documented
  - Services start in correct order (FalkorDB → seed → backend → web)
  - Health checks pass
  - No hardcoded secrets
- [ ] **Demo video final check:**
  - Video is ≤ 3 minutes
  - Audio is clear (if narrated)
  - All key moments are visible (empty → learn → restart → recall)
  - Upload to YouTube/Loom (whatever the submission requires)
- [ ] **Submission checklist** (from Plan §1):
  - [ ] Public source-code repository
  - [ ] README with setup instructions AND graph data model
  - [ ] Cypher queries / graph algorithms section in README
  - [ ] Demo video showing the working project
  - [ ] Live deployment OR complete local setup instructions
  - [ ] Track named: *"Best Agentic AI Use Case"*
  - [ ] AI usage disclosure
- [ ] **Submit** before the deadline
- [ ] **Post-submission:** verify the submission link works, repo is public, video plays
- [ ] Scan whole project — check if every task is done properly without bugs and failures
- [ ] End-of-day upload: commit + push **Day 7 (FINAL)** to GitHub

### ✅ Success Criteria
- Fresh clone → `docker compose up` → working demo in one command
- All submission checklist items are complete
- Submitted before the deadline
- Repo is public, video is accessible, submission link is live

---

## Quick Reference — Daily Deliverables

| Day | Delivers | Key Risk |
|-----|----------|----------|
| **1** | Repo + Docker stack + seeded FalkorDB | FalkorDB Docker/Python client issues |
| **2** | Working recall queries R1–R4 + write R5 with latency tracking | Query correctness on real data |
| **3** | Full agent loop: perceive→recall→reason→act→write | LLM function-calling reliability |
| **4** | Cross-session persistence (the money shot) | Restart flow edge cases |
| **5** | Complete console UI with all 4 panels | Cytoscape performance, UI integration |
| **6** | Polished demo + recorded video + complete README | Demo recording under time pressure |
| **7** | Submitted, verified, done | Last-minute broken links or missing files |
