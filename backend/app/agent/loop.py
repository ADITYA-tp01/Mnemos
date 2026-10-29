"""Mnemos — Agent loop implementation.

Implements the perceive→recall→reason→act→write cycle for autonomous
threat investigation using LLM function calling.
"""
import json
import os
import random
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

from openai import OpenAI

from backend.app.agent.tools import ToolRouter
from backend.app.agent.memory import Memory


# ---------------------------------------------------------------------------
# System prompt
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """You are Mnemos, an autonomous threat hunter with persistent memory.

Your goal is to investigate security alerts by:
1. Recalling relevant past investigations and threat actor knowledge
2. Analyzing indicators of compromise (IoCs)
3. Scanning involved assets
4. Applying proven playbooks
5. Writing findings back to your memory graph

You have access to the following tools:
- recall_ioc: Check if an IoC was seen before
- recall_asset: Check asset connections to known actors
- recall_playbook: Find best playbook for a TTP
- recall_cross_session: Get cross-session intelligence
- analyze_ioc: Simulated IoC analysis
- scan_asset: Simulated asset scan
- apply_playbook: Simulate playbook execution
- write_finding: Persist findings to memory
- investigation_complete: Signal investigation done

When you recall prior memory, cite the source in your reasoning.
Always write findings after completing an investigation.
When done, call investigation_complete with your final summary."""


# ---------------------------------------------------------------------------
# Transcript entry
# ---------------------------------------------------------------------------

class TranscriptEntry:
    """One step in the agent's investigation transcript."""

    def __init__(self, step: str, details: Dict[str, Any]):
        self.step = step
        self.details = details
        self.timestamp = datetime.utcnow().isoformat() + "Z"
        self.latency_ms = details.get("latency_ms", 0)


# ---------------------------------------------------------------------------
# Agent Loop
# ---------------------------------------------------------------------------

class AgentLoop:
    """Main agent loop: perceive→recall→reason→act→write."""

    def __init__(self, memory: Memory, tool_router: ToolRouter):
        self.memory = memory
        self.tools = tool_router
        self.client = OpenAI(api_key=os.environ.get("LLM_API_KEY", ""))
        self.session_id = f"session-{random.randint(1000, 9999)}"
        self.session_start = datetime.utcnow().isoformat() + "Z"
        self.transcript: List[TranscriptEntry] = []
        self.investigation_id: Optional[str] = None

    def reset(self):
        """Clear in-memory state (for restart)."""
        self.transcript = []
        self.investigation_id = None
        self.session_id = f"session-{random.randint(1000, 9999)}"
        self.session_start = datetime.utcnow().isoformat() + "Z"

    def _add_transcript(self, step: str, details: Dict[str, Any]):
        entry = TranscriptEntry(step, details)
        self.transcript.append(entry)

    def perceive(self, alert: Dict[str, Any]) -> Dict[str, Any]:
        """Step 1: Receive and parse the alert."""
        self._add_transcript("perceive", {
            "alert_id": alert.get("id"),
            "type": alert.get("type"),
            "severity": alert.get("severity"),
            "description": alert.get("description"),
            "iocs": alert.get("iocs", []),
            "assets": alert.get("assets", []),
        })
        return alert

    def recall(self, alert: Dict[str, Any]) -> Dict[str, Any]:
        """Step 2: Run recall queries R1-R4, collect context."""
        recall_results = {}
        total_latency = 0

        # R1: Check each IoC
        for ioc in alert.get("iocs", []):
            r = self.memory.recall_ioc(ioc)
            recall_results[f"ioc_{ioc}"] = r
            total_latency += r["latency_ms"]

        # R3: Check each asset
        for asset_id in alert.get("assets", []):
            r = self.memory.recall_asset_actor(asset_id)
            recall_results[f"asset_{asset_id}"] = r
            total_latency += r["latency_ms"]

        # R4: Cross-session recall (use dummy current_inv since we're starting)
        r = self.memory.recall_cross_session("INV-START")
        recall_results["cross_session"] = r
        total_latency += r["latency_ms"]

        self._add_transcript("recall", {
            "results": recall_results,
            "total_latency_ms": round(total_latency, 2),
        })

        return recall_results

    def reason(self, alert: Dict[str, Any], recall_context: Dict[str, Any]) -> List[Dict]:
        """Step 3: Single LLM call with recalled context + available tools."""
        # Serialize recall context for LLM
        context_summary = []
        for key, result in recall_context.items():
            if result.get("result"):
                context_summary.append(f"{key}: {result['result']}")

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": (
                f"Alert: {alert.get('description')} "
                f"[{alert.get('type')}] [{alert.get('severity')}] "
                f"IoCs: {alert.get('iocs')} Assets: {alert.get('assets')} "
                f"Recalled memory: {' | '.join(context_summary) if context_summary else 'None'}"
            )},
        ]

        tools = self.tools.get_tools_schema()

        try:
            response = self.client.chat.completions.create(
                model=os.environ.get("LLM_MODEL", "gpt-4o-mini"),
                messages=messages,
                tools=tools,
                tool_choice="auto",
                timeout=30,
            )
            choice = response.choices[0]
            self._add_transcript("reason", {
                "model": os.environ.get("LLM_MODEL", "gpt-4o-mini"),
                "content": choice.message.content,
                "tool_calls": [
                    {
                        "name": tc.function.name,
                        "arguments": json.loads(tc.function.arguments)
                    }
                    for tc in choice.message.tool_calls or []
                ],
                "latency_ms": response.usage.total_tokens if response.usage else 0,
            })
            return choice.message.tool_calls or []
        except Exception as e:
            self._add_transcript("reason_error", {"error": str(e)})
            return []

    def act(self, tool_calls: List[Any]) -> List[Dict]:
        """Step 4: Execute the tools selected by the LLM."""
        actions = []
        for tc in tool_calls:
            name = tc.function.name
            args = json.loads(tc.function.arguments)
            result = self.tools.call_tool(name, args)
            actions.append({"tool": name, "args": args, "result": result})
            self._add_transcript("act", {
                "tool": name,
                "args": args,
                "result": result,
            })
        return actions

    def write(self, actions: List[Dict]):
        """Step 5: Persist findings to FalkorDB."""
        for action in actions:
            if action["tool"] == "write_finding":
                args = action["args"]
                self.memory.write_memory(args["ioc"], "finding", args["actor"])
                self.memory.write_investigation(
                    inv_id=self.investigation_id or "INV-001",
                    alert_id="ALERT-001",
                    findings=[args["ioc"]],
                    conclusion=args["conclusion"],
                    actor_name=args["actor"]
                )
                self._add_transcript("write", {
                    "action": "persisted",
                    "ioc": args["ioc"],
                    "actor": args["actor"],
                    "ttp": args["ttp"],
                })

    def run(self, alert: Dict[str, Any]) -> Dict[str, Any]:
        """Execute full agent loop: perceive→recall→reason→act→write."""
        self.investigation_id = f"INV-{int(time.time()) % 10000:04d}"

        # Perceive
        alert_ctx = self.perceive(alert)

        # Recall
        recall_ctx = self.recall(alert_ctx)

        # Reason (LLM call)
        tool_calls = self.reason(alert_ctx, recall_ctx)

        # Act
        actions = self.act(tool_calls)

        # Write
        self.write(actions)

        return {
            "investigation_id": self.investigation_id,
            "session_id": self.session_id,
            "transcript": [
                {
                    "step": e.step,
                    "details": e.details,
                    "timestamp": e.timestamp,
                }
                for e in self.transcript
            ],
        }
