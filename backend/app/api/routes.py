"""Mnemos — API routes for agent investigation and memory management.

Endpoints:
  POST /investigate/{alert_id} — trigger investigation for an alert
  POST /swarm/hunt — run several parallel hunters on one shared graph
  GET  /alerts — list alerts from the seed
  GET  /memory/stats — return node/edge counts by memory type
  GET  /memory/graph — nodes + edges for the graph visualization
  POST /agent/restart — clear in-memory agent state (graph is kept)
  GET  /investigate/{id}/transcript — get investigation transcript
                                       (id = investigation id or alert id)
"""
import logging
import os
import sys
import threading
import time
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from falkordb import FalkorDB
from pydantic import BaseModel, Field
from redis.exceptions import ResponseError

from backend.app.agent.tools import ToolRouter
from backend.app.agent.loop import AgentLoop
from backend.app.agent.memory import Memory
from backend.app.agent.swarm import SwarmCoordinator

logger = logging.getLogger("mnemos.api")

router = APIRouter()

# Global state (initialized on startup, or lazily on first request)
db: Optional[FalkorDB] = None
memory: Optional[Memory] = None
tool_router: Optional[ToolRouter] = None
agent_loop: Optional[AgentLoop] = None

_init_lock = threading.RLock()
_run_lock = threading.Lock()  # one investigation at a time per agent session
MAX_TRANSCRIPTS = 100
_transcripts: Dict[str, List[Dict[str, Any]]] = {}


def _env_flag(name: str, default: bool = True) -> bool:
    return os.environ.get(name, str(default)).strip().lower() in ("1", "true", "yes", "on")


def _store_transcript(keys: List[str], transcript: List[Dict[str, Any]]) -> None:
    for key in keys:
        _transcripts.pop(key, None)
        _transcripts[key] = transcript
    while len(_transcripts) > MAX_TRANSCRIPTS:  # evict oldest
        _transcripts.pop(next(iter(_transcripts)))


def _seed_if_empty(new_db: FalkorDB) -> bool:
    """Seed the demo scenario when the graph is completely empty (MNEMOS_AUTO_SEED)."""
    if not _env_flag("MNEMOS_AUTO_SEED", True):
        return False
    graph = new_db.select_graph("mnemos")
    try:
        empty = graph.query("MATCH (n) RETURN count(n)").result_set[0][0] == 0
    except ResponseError:
        empty = True  # graph key doesn't exist yet
    if not empty:
        return False
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "scripts"))
    import seed_scenario
    seed_scenario.seed(new_db)
    logger.info("Graph was empty - seeded the demo scenario")
    return True


def init_agent():
    """Initialize the agent with FalkorDB connection."""
    global db, memory, tool_router, agent_loop
    with _init_lock:
        host = os.environ.get("FALKORDB_HOST", "localhost")
        port = int(os.environ.get("FALKORDB_PORT", "6379"))
        new_db = FalkorDB(host=host, port=port)
        _seed_if_empty(new_db)
        new_memory = Memory(new_db)
        new_tools = ToolRouter(new_memory)
        new_loop = AgentLoop(new_memory, new_tools)
        db, memory, tool_router = new_db, new_memory, new_tools
        agent_loop = new_loop  # set last: its presence means "fully initialised"


def _ensure_agent():
    """Initialise the agent on demand; clear 503 if FalkorDB can't be set up."""
    if agent_loop is not None:
        return
    with _init_lock:
        if agent_loop is None:
            try:
                init_agent()
            except Exception as e:
                logger.exception("Agent initialisation failed")
                raise HTTPException(
                    status_code=503,
                    detail=f"Cannot initialise agent / connect to FalkorDB: {e}",
                )


# ---------------------------------------------------------------------------
# Routes (sync handlers run in FastAPI's threadpool, so slow LLM calls
# don't block the event loop)
# ---------------------------------------------------------------------------

ALERT_QUERY = (
    "MATCH (a:Alert {id: $aid}) "
    "OPTIONAL MATCH (a)-[:FLAGGED]->(i:IoC) "
    "OPTIONAL MATCH (a)-[:INVOLVES]->(s:Asset) "
    "RETURN a.id, a.type, a.severity, a.description, "
    "collect(DISTINCT i.value), collect(DISTINCT s.id), a.session_target"
)


def _load_alert(alert_id: str) -> Optional[Dict[str, Any]]:
    """Load an alert with its IoCs / assets (stored as FLAGGED / INVOLVES edges)."""
    r = memory.graph.query(ALERT_QUERY, {"aid": alert_id})
    if not r.result_set:
        return None
    row = r.result_set[0]
    return {
        "id": row[0],
        "type": row[1],
        "severity": row[2],
        "description": row[3],
        "iocs": row[4] or [],
        "assets": row[5] or [],
        "session_target": row[6] if row[6] is not None else 1,
    }


@router.get("/alerts")
def list_alerts() -> Dict[str, Any]:
    """List all alerts from the seeded graph."""
    _ensure_agent()
    r = memory.graph.query(
        "MATCH (a:Alert) RETURN a.id, a.type, a.severity, a.status ORDER BY a.id"
    )
    alerts = []
    for row in r.result_set:
        alerts.append({
            "id": row[0],
            "type": row[1],
            "severity": row[2],
            "status": row[3],
        })
    return {"alerts": alerts}


@router.post("/investigate/{alert_id}")
def investigate(alert_id: str) -> Dict[str, Any]:
    """Trigger investigation for an alert."""
    _ensure_agent()

    alert = _load_alert(alert_id)
    if alert is None:
        raise HTTPException(status_code=404, detail=f"Alert {alert_id} not found")

    with _run_lock:
        memory.graph.query(
            "MATCH (a:Alert {id: $aid}) SET a.status = 'investigating'",
            {"aid": alert_id}
        )
        try:
            result = agent_loop.run(alert)
        except Exception:
            memory.graph.query(
                "MATCH (a:Alert {id: $aid}) SET a.status = 'pending'",
                {"aid": alert_id}
            )
            raise
        memory.graph.query(
            "MATCH (a:Alert {id: $aid}) SET a.status = 'investigated'",
            {"aid": alert_id}
        )
        _store_transcript([result["investigation_id"], alert_id], result["transcript"])

    return {
        "investigation_id": result["investigation_id"],
        "session_id": result["session_id"],
        "session_start": result["session_start"],
        "is_fresh_session": result["is_fresh_session"],
        "previous_session_count": result["previous_session_count"],
        "transcript": result["transcript"],
        "success": True,
    }


class SwarmRequest(BaseModel):
    alert_ids: Optional[List[str]] = None  # default: pending alerts first
    num_hunters: int = Field(3, ge=1, le=5)


@router.post("/swarm/hunt")
def swarm_hunt(req: Optional[SwarmRequest] = None) -> Dict[str, Any]:
    """Run parallel hunters (one per alert) that share the one FalkorDB graph."""
    _ensure_agent()
    req = req or SwarmRequest()

    if req.alert_ids:
        ids = list(dict.fromkeys(req.alert_ids))[:5]
    else:
        rows = memory.graph.query(
            "MATCH (a:Alert) RETURN a.id, a.type, a.severity, a.status ORDER BY a.id"
        ).result_set
        pending = [r[0] for r in rows if r[3] == "pending"]
        others = [r[0] for r in rows if r[3] != "pending"]
        ids = (pending + others)[:req.num_hunters]

    alerts = []
    for alert_id in ids:
        alert = _load_alert(alert_id)
        if alert is None:
            raise HTTPException(status_code=404, detail=f"Alert {alert_id} not found")
        alerts.append(alert)
    if not alerts:
        raise HTTPException(status_code=404, detail="No alerts to hunt")

    with _run_lock:
        for alert in alerts:
            memory.graph.query(
                "MATCH (a:Alert {id: $aid}) SET a.status = 'investigating'",
                {"aid": alert["id"]},
            )
        start = time.perf_counter()
        try:
            result = SwarmCoordinator(memory, tool_router,
                                      num_hunters=len(alerts)).hunt(alerts)
        except Exception:
            for alert in alerts:  # don't leave alerts stuck in 'investigating'
                memory.graph.query(
                    "MATCH (a:Alert {id: $aid}) SET a.status = 'pending'",
                    {"aid": alert["id"]},
                )
            raise
        wall_ms = round((time.perf_counter() - start) * 1000, 2)
        result["results"].sort(key=lambda r: r.get("alert_id") or "")
        for hunter in result["results"]:
            ok = hunter.get("success")
            memory.graph.query(
                "MATCH (a:Alert {id: $aid}) SET a.status = $status",
                {"aid": hunter.get("alert_id"),
                 "status": "investigated" if ok else "pending"},
            )
            if ok:
                _store_transcript([hunter["investigation_id"], hunter["alert_id"]],
                                  hunter["transcript"])

    result["wall_time_ms"] = wall_ms
    result["alert_ids"] = [a["id"] for a in alerts]
    return result


@router.get("/investigate/{inv_id}/transcript")
def get_transcript(inv_id: str) -> Dict[str, Any]:
    """Return the transcript for an investigation (or the latest one for an alert)."""
    _ensure_agent()
    transcript = _transcripts.get(inv_id)
    if transcript is None:
        raise HTTPException(status_code=404, detail=f"No transcript for {inv_id}")
    return {"investigation_id": inv_id, "transcript": transcript}


@router.get("/memory/stats")
def memory_stats() -> Dict[str, int]:
    """Return node counts by memory type and total edge count."""
    _ensure_agent()
    return memory.get_stats()


@router.get("/memory/graph")
def memory_graph() -> Dict[str, Any]:
    """Return nodes and edges for Cytoscape.js visualization."""
    _ensure_agent()
    return memory.get_graph_data()


@router.get("/agent/session")
def agent_session() -> Dict[str, Any]:
    """Current in-memory session info (for the UI header on page load)."""
    _ensure_agent()
    return {
        "session_id": agent_loop.session_id,
        "session_start": agent_loop.session_start,
        "is_fresh_session": agent_loop.session_count == 0,
        "previous_session_count": agent_loop.session_count,
    }


@router.post("/agent/restart")
def agent_restart() -> Dict[str, Any]:
    """Clear in-memory agent state, keep the FalkorDB graph.

    Memories fade between sessions: unless MNEMOS_DECAY_ON_RESTART=false, every
    weighted edge decays once per restart (recalled edges are reinforced).
    """
    _ensure_agent()
    with _run_lock:
        agent_loop.reset()
        _transcripts.clear()
        decay = memory.decay_memory() if _env_flag("MNEMOS_DECAY_ON_RESTART", True) else None
        return {
            "status": "restarted",
            "session_id": agent_loop.session_id,
            "session_start": agent_loop.session_start,
            "is_fresh_session": True,
            "previous_session_count": agent_loop.session_count,
            "memory_decay": decay,
        }
