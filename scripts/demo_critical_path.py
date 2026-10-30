"""Mnemos — Demo critical path: pre-scripted fallback for reliable demo.

If the LLM is unavailable or unreliable, this replays the exact
function-call sequence for Alert #1 and #2 but still executes real
Cypher against real FalkorDB.  Usage:

    python scripts/demo_critical_path.py
"""
import sys
sys.path.insert(0, 'scripts')
sys.path.insert(0, '.')

from backend.app.agent.memory import Memory
from backend.app.agent.tools import ToolRouter
from backend.app.agent.loop import AgentLoop
from falkordb import FalkorDB
import seed_scenario


# Cached tool-call sequences (captured from a successful LLM run)
CACHED_CALLS = {
    "ALERT-001": [
        {"name": "analyze_ioc", "arguments": {"ioc_value": "powershell-loader-7d3a9b.exe"}},
        {"name": "recall_ioc", "arguments": {"ioc_value": "powershell-loader-7d3a9b.exe"}},
        {"name": "scan_asset", "arguments": {"asset_id": "ASSET-001"}},
        {"name": "write_finding", "arguments": {
            "ioc": "powershell-loader-7d3a9b.exe",
            "actor": "APT-CRIMSON",
            "ttp": "T1059.001",
            "conclusion": "Attributed to known threat actor APT-CRIMSON",
            "alert_id": "ALERT-001",
        }},
    ],
    "ALERT-002": [
        {"name": "recall_ioc", "arguments": {"ioc_value": "185.220.101.45"}},
        {"name": "recall_asset", "arguments": {"asset_id": "ASSET-013"}},
        {"name": "write_finding", "arguments": {
            "ioc": "185.220.101.45",
            "actor": "APT-CRIMSON",
            "ttp": "T1071.001",
            "conclusion": "Cross-session: APT-CRIMSON already known from Session 1",
        }},
    ],
}


def replay(agent, alert, calls):
    """Replay a cached tool-call sequence through the real agent loop."""
    import json
    alert_ctx = agent.perceive(alert)
    recall_ctx = agent.recall(alert_ctx)

    # Build synthetic tool_calls matching the cached sequence
    tool_calls = []
    for c in calls:
        tc = type("TC", (), {
            "function": type("F", (), {
                "name": c["name"],
                "arguments": json.dumps(c["arguments"]),
            })()
        })()
        tool_calls.append(tc)

    actions = agent.act(tool_calls)
    agent.current_alert_id = alert["id"]
    agent.investigation_id = f"INV-{len(agent.transcript):04d}"
    agent.write(actions)
    return {
        "investigation_id": agent.investigation_id,
        "session_id": agent.session_id,
        "is_fresh_session": agent.session_count == 0,
        "previous_session_count": agent.session_count,
        "transcript": [
            {"step": e.step, "details": e.details, "timestamp": e.timestamp}
            for e in agent.transcript
        ],
    }


if __name__ == "__main__":
    import json

    db = FalkorDB()
    seed_scenario.seed(db)
    memory = Memory(db)
    tools = ToolRouter(memory)
    agent = AgentLoop(memory, tools)

    alerts = {
        "ALERT-001": {
            "id": "ALERT-001", "type": "suspicious_process", "severity": "high",
            "description": "PowerShell process spawning from unusual parent on web-01",
            "iocs": ["powershell-loader-7d3a9b.exe"], "assets": ["ASSET-001"],
        },
        "ALERT-002": {
            "id": "ALERT-002", "type": "auth_anomaly", "severity": "critical",
            "description": "External IP 185.220.101.45 brute-forcing cloud accounts",
            "iocs": ["185.220.101.45"], "assets": ["ASSET-013", "ASSET-017"],
        },
    }

    print("=== Demo Critical Path (pre-scripted fallback) ===\n")

    # Session 1
    print("--- Session 1: Alert #1 ---")
    r1 = replay(agent, alerts["ALERT-001"], CACHED_CALLS["ALERT-001"])
    s1 = memory.get_stats()
    print(f"  Session: {r1['session_id']}, Fresh: {r1['is_fresh_session']}")
    print(f"  Investigation: {r1['investigation_id']}")
    print(f"  Graph: Inv={s1['Investigation']}, Edges={s1['edges']}")

    # Restart
    print("\n--- Restart ---")
    agent.reset()
    print(f"  New session: {agent.session_id}, Count: {agent.session_count}")

    # Session 2
    print("\n--- Session 2: Alert #2 (cross-session) ---")
    r2 = replay(agent, alerts["ALERT-002"], CACHED_CALLS["ALERT-002"])
    s2 = memory.get_stats()
    print(f"  Session: {r2['session_id']}, Fresh: {r2['is_fresh_session']}")
    print(f"  Previous sessions: {r2['previous_session_count']}")
    print(f"  Graph: Inv={s2['Investigation']}, Edges={s2['edges']}")

    # R4 cross-session recall
    r4 = memory.recall_cross_session("ALERT-002")
    print(f"\n  R4 cross-session recall: {r4['result']}")

    # Verify
    print("\n=== Verification ===")
    assert s1["Investigation"] == 1, f"Expected 1 investigation, got {s1['Investigation']}"
    assert s2["Investigation"] == 2, f"Expected 2 investigations, got {s2['Investigation']}"
    assert r2["is_fresh_session"] is False, "Session 2 should not be fresh"
    assert r4["result"], "R4 should return cross-session data"
    print("  All assertions passed [OK]")