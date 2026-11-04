"""Mnemos — Swarm mode: 3 parallel hunter agents sharing one FalkorDB graph.

Each hunter runs the same perceive→recall→reason→act→write loop as a
single AgentLoop, but they all read/write the same graph concurrently
(FalkorDB serializes writes per graph, so concurrent writers don't corrupt it).
"""
import os
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Dict, List

from backend.app.agent.loop import AgentLoop
from backend.app.agent.memory import Memory
from backend.app.agent.tools import ToolRouter


class SwarmCoordinator:
    """Spawns N parallel hunter agents sharing one FalkorDB graph."""

    def __init__(self, memory: Memory, tool_router: ToolRouter,
                 num_hunters: int = 3):
        self.memory = memory
        self.tool_router = tool_router
        self.num_hunters = num_hunters
        self.hunters: List[AgentLoop] = []
        self.results: List[Dict] = []
        self.total_recall_latency_ms = 0.0
        self.writes_completed = 0

    def _create_hunter(self) -> AgentLoop:
        """Create a fresh hunter agent (each has its own session)."""
        return AgentLoop(self.memory, self.tool_router)

    def hunt(self, alerts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Run all hunters in parallel against their assigned alerts.

        Returns aggregated results with concurrency metrics.
        """
        if len(alerts) < self.num_hunters:
            alerts = alerts + [alerts[-1]] * (self.num_hunters - len(alerts))

        self.hunters = []
        self.results = []
        self.total_recall_latency_ms = 0.0
        self.writes_completed = 0
        errors: List[str] = []

        def _run_hunter(alert: Dict[str, Any], hunter: AgentLoop) -> Dict[str, Any]:
            try:
                result = hunter.run(alert)
                recall_latency = 0.0
                for entry in result.get("transcript", []):
                    if entry.get("step") == "recall":
                        recall_latency += entry.get("details", {}).get("total_latency_ms", 0)
                return {
                    "hunter": hunter.session_id,
                    "alert_id": alert.get("id"),
                    "investigation_id": result.get("investigation_id"),
                    "recall_latency_ms": round(recall_latency, 2),
                    "transcript": result.get("transcript", []),
                    "success": True,
                }
            except Exception as e:
                return {
                    "hunter": hunter.session_id,
                    "alert_id": alert.get("id"),
                    "error": str(e),
                    "success": False,
                }

        with ThreadPoolExecutor(max_workers=self.num_hunters) as executor:
            futures = {}
            for i, alert in enumerate(alerts[:self.num_hunters]):
                hunter = self._create_hunter()
                self.hunters.append(hunter)
                futures[executor.submit(_run_hunter, alert, hunter)] = i

            for future in as_completed(futures):
                result = future.result()
                self.results.append(result)
                if result.get("success"):
                    self.total_recall_latency_ms += result.get("recall_latency_ms", 0)
                    self.writes_completed += 1
                else:
                    errors.append(result.get("error", "unknown error"))

        self.results.sort(key=lambda r: r.get("hunter", ""))

        return {
            "mode": "swarm",
            "num_hunters": self.num_hunters,
            "results": self.results,
            "total_recall_latency_ms": round(self.total_recall_latency_ms, 2),
            "avg_recall_latency_ms": round(
                self.total_recall_latency_ms / max(self.writes_completed, 1), 2
            ),
            "writes_completed": self.writes_completed,
            "errors": errors,
            "success": len(errors) == 0,
        }


def run_swarm(alerts: List[Dict[str, Any]], num_hunters: int = 3) -> Dict[str, Any]:
    """Convenience entry point: seed → swarm → return aggregated results."""
    import sys
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'scripts'))
    from falkordb import FalkorDB
    import seed_scenario

    db = FalkorDB()
    seed_scenario.seed(db)
    memory = Memory(db)
    tools = ToolRouter(memory)
    coordinator = SwarmCoordinator(memory, tools, num_hunters=num_hunters)
    return coordinator.hunt(alerts)


if __name__ == "__main__":
    import json

    alerts = [
        {"id": "ALERT-001", "type": "suspicious_process", "severity": "high",
         "description": "PowerShell process spawning from unusual parent on web-01",
         "iocs": ["powershell-loader-7d3a9b.exe"], "assets": ["ASSET-001"]},
        {"id": "ALERT-002", "type": "auth_anomaly", "severity": "critical",
         "description": "External IP 185.220.101.45 brute-forcing cloud accounts",
         "iocs": ["185.220.101.45"], "assets": ["ASSET-013", "ASSET-017"]},
        {"id": "ALERT-003", "type": "data_exfil", "severity": "medium",
         "description": "Unusual outbound traffic on port 443",
         "iocs": ["104.21.5.30"], "assets": ["ASSET-005", "ASSET-008"]},
    ]

    result = run_swarm(alerts, num_hunters=3)
    print(json.dumps(result, indent=2, default=str))