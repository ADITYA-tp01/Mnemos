"""Mnemos — API routes for agent investigation and memory management.

Endpoints:
  POST /investigate/{alert_id} — trigger investigation for an alert
  GET  /alerts — list pending alerts from the seed
  GET  /memory/stats — return node/edge counts by memory type
  POST /agent/restart — clear in-memory agent state
  GET  /investigate/{id}/transcript — get investigation transcript
"""
import os
from typing import Dict, Any

from fastapi import APIRouter, HTTPException

from backend.app.agent.tools import ToolRouter
from backend.app.agent.loop import AgentLoop
from backend.app.agent.memory import Memory
from falkordb import FalkorDB

router = APIRouter()

# Global state (initialized on startup)
db: FalkorDB = None
memory: Memory = None
tool_router: ToolRouter = None
agent_loop: AgentLoop = None


def init_agent():
    """Initialize the agent with FalkorDB connection."""
    global db, memory, tool_router, agent_loop
    host = os.environ.get("FALKORDB_HOST", "localhost")
    port = int(os.environ.get("FALKORDB_PORT", "6379"))
    db = FalkorDB(host=host, port=port)
    memory = Memory(db)
    tool_router = ToolRouter(memory)
    agent_loop = AgentLoop(memory, tool_router)


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.get("/alerts")
async def list_alerts() -> Dict[str, Any]:
    """List all alerts from the seeded graph."""
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
async def investigate(alert_id: str) -> Dict[str, Any]:
    """Trigger investigation for an alert."""
    # Get alert details
    r = memory.graph.query(
        "MATCH (a:Alert {id: $aid}) RETURN a.id, a.type, a.severity, "
        "a.description, a.iocs, a.assets, a.session_target",
        {"aid": alert_id}
    )
    if not r.result_set:
        raise HTTPException(status_code=404, detail=f"Alert {alert_id} not found")

    alert_row = r.result_set[0]
    alert = {
        "id": alert_row[0],
        "type": alert_row[1],
        "severity": alert_row[2],
        "description": alert_row[3],
        "iocs": alert_row[4] if len(alert_row) > 4 else [],
        "assets": alert_row[5] if len(alert_row) > 5 else [],
        "session_target": alert_row[6] if len(alert_row) > 6 else 1,
    }

    # Update alert status
    memory.graph.query(
        "MATCH (a:Alert {id: $aid}) SET a.status = 'investigating'",
        {"aid": alert_id}
    )

    # Run agent loop
    result = agent_loop.run(alert)

    # Update alert status
    memory.graph.query(
        "MATCH (a:Alert {id: $aid}) SET a.status = 'investigated'",
        {"aid": alert_id}
    )

    return {
        "investigation_id": result["investigation_id"],
        "session_id": result["session_id"],
        "session_start": agent_loop.session_start,
        "is_fresh_session": agent_loop.session_count == 0,
        "previous_session_count": agent_loop.session_count,
        "transcript": result["transcript"],
        "success": True,
    }


@router.get("/investigate/{inv_id}/transcript")
async def get_transcript(inv_id: str) -> Dict[str, Any]:
    """Return the transcript for an investigation."""
    return {
        "investigation_id": inv_id,
        "transcript": agent_loop.transcript,
    }


@router.get("/memory/stats")
async def memory_stats() -> Dict[str, int]:
    """Return node counts by memory type and total edge count."""
    return memory.get_stats()


@router.get("/memory/graph")
async def memory_graph() -> Dict[str, Any]:
    """Return nodes and edges for Cytoscape.js visualization."""
    return memory.get_graph_data()


@router.post("/agent/restart")
async def agent_restart() -> Dict[str, Any]:
    """Clear in-memory agent state, keep FalkorDB intact."""
    agent_loop.reset()
    return {
        "status": "restarted",
        "session_id": agent_loop.session_id,
        "session_start": agent_loop.session_start,
        "is_fresh_session": True,
    }
