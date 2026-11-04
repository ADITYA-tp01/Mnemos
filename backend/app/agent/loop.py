"""Mnemos — Agent loop implementation.

Implements the perceive→recall→reason→act→write cycle for autonomous
threat investigation using LLM function calling.

LLM providers (env `LLM_PROVIDER`):
  - ollama (default): local Ollama server at `OLLAMA_HOST`, model `LLM_MODEL`
  - openai: needs `LLM_API_KEY` (or `OPENAI_API_KEY`), model `LLM_MODEL`.
    Set `LLM_BASE_URL` for any OpenAI-compatible API (e.g. NVIDIA NIM:
    https://integrate.api.nvidia.com/v1).
`LLM_TIMEOUT` (seconds, default 90) bounds each LLM call; a cold local model
needs more than a few seconds to load.
If the LLM is unavailable the loop degrades gracefully (recall-only /
deterministic fallback) and still persists a finding.
"""
import json
import os
import random
import time
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from backend.app.agent.tools import ToolRouter
from backend.app.agent.memory import Memory, jsonable


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
- recall_cross_session: Get cross-session intelligence for an alert
- analyze_ioc: Simulated IoC analysis
- scan_asset: Simulated asset scan
- apply_playbook: Simulate playbook execution
- write_finding: Persist findings to memory
- investigation_complete: Signal investigation done

When you recall prior memory, cite the source in your reasoning.
Always write findings after completing an investigation.
When done, call investigation_complete with your final summary."""


# ---------------------------------------------------------------------------
# Tool-call objects (OpenAI-style: .function.name / .function.arguments JSON)
# ---------------------------------------------------------------------------

class _Function:
    def __init__(self, name: str, arguments: Dict[str, Any]):
        self.name = name
        self.arguments = json.dumps(arguments)


class ToolCall:
    """Provider-neutral tool call."""

    def __init__(self, name: str, arguments: Dict[str, Any]):
        self.function = _Function(name, arguments)


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
        self.llm_provider = os.environ.get("LLM_PROVIDER", "ollama").lower()
        self.ollama_host = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
        default_model = "gpt-4o-mini" if self.llm_provider == "openai" else "qwen3:8b"
        self.llm_model = os.environ.get("LLM_MODEL", default_model)
        self._api_key = os.environ.get("LLM_API_KEY") or os.environ.get("OPENAI_API_KEY")
        self._base_url = os.environ.get("LLM_BASE_URL") or None
        self.llm_timeout = float(os.environ.get("LLM_TIMEOUT", "90"))
        self._openai_client = None
        # Ollama needs no key (connection errors fall back at call time);
        # OpenAI needs a key; unknown providers use the deterministic fallback.
        self.llm_enabled = (self.llm_provider == "ollama"
                            or (self.llm_provider == "openai" and bool(self._api_key)))
        self.session_id = f"session-{random.randint(1000, 9999)}"
        self.session_start = datetime.utcnow().isoformat() + "Z"
        self.session_count = 0
        self.transcript: List[TranscriptEntry] = []
        self.investigation_id: Optional[str] = None
        self.current_alert_id: Optional[str] = None
        self.recall_history: List[Dict] = []  # Track all recall results

    def reset(self):
        """Clear in-memory state (for restart). Does NOT touch FalkorDB."""
        self.transcript = []
        self.investigation_id = None
        self.current_alert_id = None
        self.session_count += 1
        self.session_id = f"session-{random.randint(1000, 9999)}"
        self.session_start = datetime.utcnow().isoformat() + "Z"
        self.recall_history = []

    def _add_transcript(self, step: str, details: Dict[str, Any]):
        entry = TranscriptEntry(step, details)
        self.transcript.append(entry)

    def serialize_transcript(self, entries: Optional[List[TranscriptEntry]] = None) -> List[Dict[str, Any]]:
        """JSON-safe transcript (defaults to the whole in-memory transcript)."""
        entries = self.transcript if entries is None else entries
        return [
            {"step": e.step, "details": jsonable(e.details), "timestamp": e.timestamp}
            for e in entries
        ]

    def perceive(self, alert: Dict[str, Any]) -> Dict[str, Any]:
        """Step 1: Receive and parse the alert."""
        self._add_transcript("perceive", {
            "alert_id": alert.get("id"),
            "type": alert.get("type"),
            "severity": alert.get("severity"),
            "description": alert.get("description"),
            "iocs": alert.get("iocs") or [],
            "assets": alert.get("assets") or [],
        })
        return alert

    def recall(self, alert: Dict[str, Any]) -> Dict[str, Any]:
        """Step 2: Run recall queries R1-R4, collect context with source attribution."""
        recall_results = {}
        query_names = {}  # key -> query name (R1/R2/R3/R4)
        total_latency = 0

        # R1: Episodic recall — "Have I seen this IoC before?"
        for ioc in alert.get("iocs") or []:
            r = self.memory.recall_ioc(ioc)
            recall_results[f"ioc_{ioc}"] = r
            query_names[f"ioc_{ioc}"] = "R1"
            total_latency += r["latency_ms"]

        # R3: Multi-hop recall — "Is this asset tied to a known actor?"
        for asset_id in alert.get("assets") or []:
            r = self.memory.recall_asset_actor(asset_id)
            recall_results[f"asset_{asset_id}"] = r
            query_names[f"asset_{asset_id}"] = "R3"
            total_latency += r["latency_ms"]

        # R4: Cross-session recall — the money shot
        r = self.memory.recall_cross_session(alert.get("id", "ALERT-001"),
                                             self.investigation_id)
        recall_results["cross_session"] = r
        query_names["cross_session"] = "R4"
        total_latency += r["latency_ms"]

        # Reinforce: edges that recall traversed (non-empty results) get stronger
        hit_iocs = [i for i in alert.get("iocs") or []
                    if recall_results[f"ioc_{i}"].get("result")]
        hit_assets = [a for a in alert.get("assets") or []
                      if recall_results[f"asset_{a}"].get("result")]
        if hit_iocs or hit_assets:
            self.memory.reinforce(hit_iocs, hit_assets)

        # Build source attribution lines for the transcript
        attribution_lines = []
        for key, result in recall_results.items():
            qname = query_names.get(key, "?")
            latency = result.get("latency_ms", 0)
            if result.get("result"):
                attribution_lines.append(
                    f"Based on recall {qname} ({latency}ms): {result['result']}"
                )
            else:
                attribution_lines.append(
                    f"Based on recall {qname} ({latency}ms): No prior memory — investigating from scratch"
                )

        self._add_transcript("recall", {
            "results": recall_results,
            "query_names": query_names,
            "attribution": attribution_lines,
            "total_latency_ms": round(total_latency, 2),
        })

        return recall_results

    # ------------------------------------------------------------------
    # Default finding (used when the LLM is off / fails / omits write_finding)
    # ------------------------------------------------------------------

    def _default_finding(self, alert: Dict[str, Any]) -> Dict[str, Any]:
        """Deterministic finding derived from semantic memory, not hardcoded."""
        iocs = alert.get("iocs") or []
        ioc = iocs[0] if iocs else f"no-ioc-{alert.get('id', 'unknown')}"
        actor, ttp = None, None
        try:
            actor, ttp = self.memory.lookup_actor_for_ioc(ioc)
        except Exception:
            pass  # memory unavailable — fall through to "unattributed"
        if actor:
            conclusion = f"Attributed to known threat actor {actor}"
        else:
            actor = "UNATTRIBUTED"
            conclusion = "No known threat actor linked to this IoC; recorded for future recall"
        return {"ioc": ioc, "actor": actor, "ttp": ttp or "unknown",
                "conclusion": conclusion, "alert_id": alert.get("id")}

    def _ensure_write_finding(self, tool_calls: List[Any], alert: Dict[str, Any]) -> List[Any]:
        """Ensure write_finding is always called, even if LLM omits it."""
        if any(getattr(tc.function, "name", "") == "write_finding" for tc in tool_calls):
            return tool_calls
        tool_calls.append(ToolCall("write_finding", self._default_finding(alert)))
        return tool_calls

    # ------------------------------------------------------------------
    # LLM providers — each returns (content, [{"name", "arguments"}])
    # ------------------------------------------------------------------

    def _call_ollama(self, messages: List[Dict], tools: List[Dict]) -> Tuple[str, List[Dict]]:
        import requests
        response = requests.post(
            f"{self.ollama_host}/api/chat",
            json={"model": self.llm_model, "messages": messages,
                  "tools": tools, "stream": False},
            timeout=self.llm_timeout,
        )
        response.raise_for_status()
        data = response.json()
        if "message" not in data:
            raise ValueError("Malformed LLM response: missing 'message' key")
        message = data["message"]
        calls = []
        for tc in message.get("tool_calls") or []:
            args = tc["function"].get("arguments") or {}
            if isinstance(args, str):
                args = json.loads(args)
            calls.append({"name": tc["function"]["name"], "arguments": args})
        return message.get("content", "") or "", calls

    def _call_openai(self, messages: List[Dict], tools: List[Dict]) -> Tuple[str, List[Dict]]:
        if self._openai_client is None:
            from openai import OpenAI
            self._openai_client = OpenAI(api_key=self._api_key, base_url=self._base_url)
        response = self._openai_client.chat.completions.create(
            model=self.llm_model,
            messages=messages,
            tools=tools,
            tool_choice="auto",
            timeout=self.llm_timeout,
        )
        message = response.choices[0].message
        calls = [
            {"name": tc.function.name,
             "arguments": json.loads(tc.function.arguments or "{}")}
            for tc in message.tool_calls or []
        ]
        return message.content or "", calls

    def reason(self, alert: Dict[str, Any], recall_context: Dict[str, Any], max_retries: int = 1) -> List[Any]:
        """Step 3: Single LLM call with recalled context + available tools.

        Edge cases handled:
        - LLM not configured → deterministic fallback (always persists findings)
        - LLM timeout / connection error → "Recall-only mode" using what recall found
        - Malformed LLM response → retry once, then graceful fallback
        """
        if not self.llm_enabled:
            finding = self._default_finding(alert)
            tool_calls = [
                ToolCall("analyze_ioc", {"ioc_value": finding["ioc"]}),
                ToolCall("recall_ioc", {"ioc_value": finding["ioc"]}),
                ToolCall("write_finding", finding),
            ]
            self._add_transcript("reason", {
                "mode": "fallback_no_llm",
                "content": "LLM not configured - using deterministic fallback",
                "tool_calls": [
                    {"name": tc.function.name, "arguments": json.loads(tc.function.arguments)}
                    for tc in tool_calls
                ],
            })
            return tool_calls

        # Serialize recall context for LLM — include source attribution
        context_summary = []
        for key, result in recall_context.items():
            if result.get("result"):
                context_summary.append(f"{key}: {result['result']}")

        has_recall = bool(context_summary)
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": (
                f"Alert ID: {alert.get('id')} Investigation ID: {self.investigation_id} "
                f"Alert: {alert.get('description')} "
                f"[{alert.get('type')}] [{alert.get('severity')}] "
                f"IoCs: {alert.get('iocs')} Assets: {alert.get('assets')} "
                f"Recalled memory: {' | '.join(context_summary) if context_summary else 'None'}"
            )},
        ]

        tools = self.tools.get_tools_schema()
        call_llm = self._call_openai if self.llm_provider == "openai" else self._call_ollama

        last_error = None
        for attempt in range(max_retries + 1):
            try:
                start = time.perf_counter()
                content, calls = call_llm(messages, tools)
                latency_ms = round((time.perf_counter() - start) * 1000, 2)
                self._add_transcript("reason", {
                    "model": self.llm_model,
                    "provider": self.llm_provider,
                    "content": content,
                    "tool_calls": calls,
                    "latency_ms": latency_ms,
                })
                tool_calls = [ToolCall(c["name"], c["arguments"]) for c in calls]
                return self._ensure_write_finding(tool_calls, alert)
            except Exception as e:
                last_error = e
                self._add_transcript("reason_error", {
                    "error": str(e),
                    "attempt": attempt + 1,
                    "max_attempts": max_retries + 1,
                })

        # All retries exhausted — graceful fallback
        if has_recall:
            self._add_transcript("reason", {
                "mode": "recall_only",
                "content": f"LLM unavailable ({last_error}). Recall-only mode: showing what memory knows.",
                "recall_context": context_summary,
                "tool_calls": [],
            })
        else:
            self._add_transcript("reason", {
                "mode": "fallback_no_llm",
                "content": f"LLM unavailable ({last_error}). No prior memory — investigating from scratch.",
                "tool_calls": [],
            })
        return self._ensure_write_finding([], alert)

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

    def write(self, actions: List[Dict], alert: Optional[Dict[str, Any]] = None):
        """Step 5: Persist findings to FalkorDB (one Investigation per run)."""
        finding = None
        for action in actions:
            if action["tool"] == "write_finding" and action["result"].get("success"):
                finding = action["args"]
                break
        if finding is None:
            # The LLM's write_finding was missing or invalid — persist a default one.
            alert = alert or {"id": self.current_alert_id}
            finding = self._default_finding(alert)

        self.memory.write_memory(finding["ioc"], "finding", finding["actor"])
        self.memory.write_investigation(
            inv_id=self.investigation_id,
            alert_id=self.current_alert_id,
            findings=[finding["ioc"]],
            conclusion=finding["conclusion"],
            actor_name=finding["actor"],
        )
        # Remember where the IoC was seen so R3 can answer next time
        self.memory.link_ioc_to_assets(finding["ioc"], (alert or {}).get("assets") or [])
        self._add_transcript("write", {
            "action": "persisted",
            "ioc": finding["ioc"],
            "actor": finding["actor"],
            "ttp": finding.get("ttp", "unknown"),
        })

    def run(self, alert: Dict[str, Any]) -> Dict[str, Any]:
        """Execute full agent loop: perceive→recall→reason→act→write."""
        self.investigation_id = f"INV-{uuid.uuid4().hex[:8].upper()}"
        self.current_alert_id = alert.get("id", "ALERT-001")
        start_index = len(self.transcript)

        # Perceive
        alert_ctx = self.perceive(alert)

        # Recall
        recall_ctx = self.recall(alert_ctx)

        # Reason (LLM call)
        tool_calls = self.reason(alert_ctx, recall_ctx)

        # Act
        actions = self.act(tool_calls)

        # Write
        self.write(actions, alert_ctx)

        return {
            "investigation_id": self.investigation_id,
            "session_id": self.session_id,
            "session_start": self.session_start,
            "is_fresh_session": self.session_count == 0,
            "previous_session_count": self.session_count,
            "transcript": self.serialize_transcript(self.transcript[start_index:]),
        }
