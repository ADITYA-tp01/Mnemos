"""Mnemos — Dynamic tool router for LLM function calling.

Dispatches LLM tool calls to the appropriate Python functions.
Memory tools connect to real FalkorDB; simulated tools return
deterministic synthetic data for demo purposes.
"""
import random
from typing import Any, Callable, Dict, List

from falkordb import FalkorDB
from backend.app.agent.memory import Memory


# ---------------------------------------------------------------------------
# Simulated tools (return deterministic synthetic data)
# ---------------------------------------------------------------------------

def simulate_ioc_analysis(ioc_value: str) -> Dict[str, Any]:
    """Simulate IoC analysis — returns realistic threat intel."""
    ioc_types = {
        "185.220.101.45": {"type": "ip", "threat_level": "high", "tags": ["tor_exit_node", "bruteforce"]},
        "powershell-loader-7d3a9b.exe": {"type": "file_hash", "threat_level": "critical", "tags": ["malware", "loader", "apt"]},
    }
    if ioc_value in ioc_types:
        return ioc_types[ioc_value]
    return {"type": "unknown", "threat_level": "medium", "tags": ["needs_further_analysis"]}


def simulate_asset_scan(asset_id: str) -> Dict[str, Any]:
    """Simulate asset scan — returns realistic findings."""
    random.seed(hash(asset_id) % 2**32)
    findings = []
    if random.random() > 0.5:
        findings.append("Unusual outbound traffic detected on port 443")
    if random.random() > 0.7:
        findings.append("Suspicious process execution logged")
    if not findings:
        findings.append("No anomalies detected")
    return {"asset_id": asset_id, "findings": findings, "risk_score": round(random.uniform(0, 1), 2)}


def simulate_playbook_application(playbook_name: str) -> Dict[str, Any]:
    """Simulate running a playbook — returns deterministic results."""
    playbooks = {
        "Network_Segment_Isolation": {"status": "completed", "duration_sec": 45, "outcome": "isolated_affected_segment"},
        "Credential_Rotation": {"status": "completed", "duration_sec": 120, "outcome": "credentials_rotated"},
        "IOC_Blacklisting": {"status": "completed", "duration_sec": 30, "outcome": "ioc_blocked"},
    }
    return playbooks.get(playbook_name, {"status": "completed", "duration_sec": 60, "outcome": "actions_taken"})


# ---------------------------------------------------------------------------
# Tool Router
# ---------------------------------------------------------------------------

class ToolRouter:
    """Routes LLM function calls to the appropriate implementation."""

    def __init__(self, memory: Memory):
        self.memory = memory
        self._tools: Dict[str, Callable] = {}
        self._register_builtins()

    def _register_builtins(self):
        """Register all available tools."""
        # Memory tools (connect to FalkorDB)
        self._tools["recall_ioc"] = self.memory.recall_ioc
        self._tools["recall_asset"] = self.memory.recall_asset_actor
        self._tools["recall_playbook"] = self.memory.recall_playbook
        self._tools["recall_cross_session"] = self.memory.recall_cross_session
        self._tools["write_finding"] = self._write_finding

        # Simulated tools
        self._tools["analyze_ioc"] = simulate_ioc_analysis
        self._tools["scan_asset"] = simulate_asset_scan
        self._tools["apply_playbook"] = simulate_playbook_application

    def _write_finding(self, ioc: str, actor: str, ttp: str, conclusion: str) -> Dict[str, Any]:
        """Write a finding to memory (R5 + investigation write)."""
        self.memory.write_memory(ioc, "finding", actor)
        self.memory.write_investigation(
            inv_id=f"INV-{int(random.random()*10000):04d}",
            alert_id="ALERT-001",
            findings=[ioc],
            conclusion=conclusion,
            actor_name=actor
        )
        return {"status": "written", "actor": actor, "ttp": ttp}

    def get_tools_schema(self) -> List[Dict[str, Any]]:
        """Return OpenAI-compatible tool schema for LLM function calling."""
        return [
            {
                "type": "function",
                "function": {
                    "name": "recall_ioc",
                    "description": "Check if an IoC has been seen before in prior investigations",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "ioc_value": {"type": "string", "description": "The IoC value to look up"}
                        },
                        "required": ["ioc_value"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "recall_asset",
                    "description": "Check if an asset is tied to known threat actors via IoCs",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "asset_id": {"type": "string", "description": "The asset identifier"}
                        },
                        "required": ["asset_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "recall_playbook",
                    "description": "Find the most successful playbook for a given MITRE technique",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "technique": {"type": "string", "description": "MITRE ATT&CK technique ID"}
                        },
                        "required": ["technique"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "recall_cross_session",
                    "description": "Recall shared actors and IoCs from all prior investigations",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "current_inv_id": {"type": "string", "description": "Current investigation ID for context"}
                        },
                        "required": ["current_inv_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "analyze_ioc",
                    "description": "Analyze an IoC using threat intelligence (simulated)",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "ioc_value": {"type": "string", "description": "The IoC value to analyze"}
                        },
                        "required": ["ioc_value"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "scan_asset",
                    "description": "Scan an asset for indicators of compromise (simulated)",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "asset_id": {"type": "string", "description": "The asset to scan"}
                        },
                        "required": ["asset_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "apply_playbook",
                    "description": "Apply an incident response playbook (simulated)",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "playbook_name": {"type": "string", "description": "Name of the playbook to apply"}
                        },
                        "required": ["playbook_name"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "write_finding",
                    "description": "Persist findings to memory graph (IoC, actor, TTP, conclusion)",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "ioc": {"type": "string", "description": "IoC value"},
                            "actor": {"type": "string", "description": "Attributed actor"},
                            "ttp": {"type": "string", "description": "MITRE TTP"},
                            "conclusion": {"type": "string", "description": "Investigation conclusion"}
                        },
                        "required": ["ioc", "actor", "ttp", "conclusion"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "investigation_complete",
                    "description": "Signal that the investigation is complete",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                }
            }
        ]

    def call_tool(self, tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """Dispatch a tool call to the appropriate function."""
        if tool_name not in self._tools:
            return {"error": f"Unknown tool: {tool_name}"}
        try:
            result = self._tools[tool_name](**args)
            return {"success": True, "result": result}
        except Exception as e:
            return {"error": str(e)}
