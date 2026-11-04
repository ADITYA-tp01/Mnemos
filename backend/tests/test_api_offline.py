"""Offline API / agent-loop tests (fake graph, no FalkorDB or LLM needed).

Run from the project root:  pytest backend/tests
"""
import json
import os

os.environ["LLM_PROVIDER"] = "ollama"
os.environ["OLLAMA_HOST"] = "http://127.0.0.1:9"  # unreachable -> exercises the fallback
os.environ["MNEMOS_AUTO_SEED"] = "false"

import pytest
from fastapi.testclient import TestClient

import backend.app.api.routes as routes
from backend.app.agent.loop import AgentLoop
from backend.app.agent.memory import Memory
from backend.app.agent.tools import ToolRouter
from backend.app.main import app

ALERT = {"id": "ALERT-001", "type": "t", "severity": "high",
         "description": "d", "iocs": ["ioc1"], "assets": ["ASSET-001"]}


class Result:
    def __init__(self, rows):
        self.result_set = rows


class Node:
    labels = ["IoC"]
    properties = {"value": "x"}


class Path:
    def nodes(self):
        return [Node()]

    def edges(self):
        return []


class FakeGraph:
    def __init__(self):
        self.calls = []

    def query(self, q, params=None):
        self.calls.append((q, params))
        if "MATCH (a:Alert {id: $aid}) OPTIONAL" in q:
            if not params["aid"].startswith("ALERT-"):
                return Result([])
            return Result([[params["aid"], "t", "high", "desc", ["ioc1"], ["ASSET-001"], 1]])
        if "RETURN a.name, t.mitre_id LIMIT 1" in q:
            return Result([["APT-CRIMSON", "T1059.001"]])
        if "RETURN path" in q:
            return Result([[Path()]])
        if "labels(n)[0], id(n), n" in q:
            return Result([["IoC", 1, Node()]])
        if "id(r), id(a)" in q:
            return Result([[7, 1, 1, "USES", None]])
        if "count(" in q:
            return Result([[3]])
        if "RETURN a.id, a.type" in q:
            return Result([["ALERT-001", "t", "high", "investigated"],
                           ["ALERT-002", "t", "high", "pending"],
                           ["ALERT-003", "t", "high", "pending"],
                           ["ALERT-004", "t", "high", "pending"]])
        return Result([])


class FakeDB:
    def __init__(self):
        self.graph = FakeGraph()

    def select_graph(self, name):
        return self.graph


@pytest.fixture
def fake():
    return FakeDB()


@pytest.fixture
def loop(fake):
    mem = Memory(fake)
    return AgentLoop(mem, ToolRouter(mem))


@pytest.fixture
def client(fake):
    routes._transcripts.clear()
    routes.db = fake
    routes.memory = Memory(fake)
    routes.tool_router = ToolRouter(routes.memory)
    routes.agent_loop = AgentLoop(routes.memory, routes.tool_router)
    return TestClient(app)


def test_loop_falls_back_and_is_json_safe(loop):
    result = loop.run(ALERT)
    json.dumps(result)  # R3 returns Path objects; must be serializable
    steps = [e["step"] for e in result["transcript"]]
    assert steps[0] == "perceive" and steps[-1] == "write"
    assert "reason_error" in steps  # unreachable LLM
    assert result["transcript"][-1]["details"]["actor"] == "APT-CRIMSON"


def test_run_returns_only_its_own_transcript_and_unique_ids(loop):
    first = loop.run(ALERT)
    second = loop.run({"id": "ALERT-001", "iocs": [], "assets": []})
    assert second["transcript"][0]["step"] == "perceive"
    assert len(second["transcript"]) < len(loop.transcript)
    assert first["investigation_id"] != second["investigation_id"]


def test_loop_links_ioc_to_assets_and_reinforces(fake, loop):
    loop.run(ALERT)
    queries = [q for q, _ in fake.graph.calls]
    assert any("OBSERVED_ON" in q and "MERGE" in q for q in queries)


def test_api_flow(client):
    assert client.get("/health").json()["status"] == "ok"
    assert client.get("/alerts").json()["alerts"][0]["id"] == "ALERT-001"
    assert client.post("/investigate/NOPE").status_code == 404

    session = client.get("/agent/session").json()
    assert session["is_fresh_session"] is True

    body = client.post("/investigate/ALERT-001")
    assert body.status_code == 200, body.text
    inv_id = body.json()["investigation_id"]
    assert client.get(f"/investigate/{inv_id}/transcript").status_code == 200
    assert client.get("/investigate/ALERT-001/transcript").status_code == 200

    assert client.get("/memory/stats").json()["edges"] == 3
    graph = client.get("/memory/graph").json()
    assert graph["nodes"][0]["properties"] == {"value": "x"}
    assert graph["edges"][0]["weight"] == 1.0 and graph["edges"][0]["type"] == "USES"

    restart = client.post("/agent/restart").json()
    assert restart["previous_session_count"] == 1
    assert restart["is_fresh_session"] is True
    assert restart["memory_decay"] is not None
    assert client.get("/investigate/ALERT-001/transcript").status_code == 404


def test_swarm_runs_parallel_hunters(client, fake):
    body = client.post("/swarm/hunt").json()  # no body: defaults
    assert body["mode"] == "swarm" and body["num_hunters"] == 3
    # pending alerts are picked first
    assert body["alert_ids"] == ["ALERT-002", "ALERT-003", "ALERT-004"]
    assert body["success"] is True and body["writes_completed"] == 3
    assert body["wall_time_ms"] >= 0 and "avg_recall_latency_ms" in body
    ids = {r["investigation_id"] for r in body["results"]}
    assert len(ids) == 3  # unique investigation ids across hunters
    assert [r["alert_id"] for r in body["results"]] == body["alert_ids"]
    json.dumps(body)
    statuses = [p for q, p in fake.graph.calls if "SET a.status = $status" in q]
    assert all(p["status"] == "investigated" for p in statuses) and len(statuses) == 3
    assert client.get(f"/investigate/{body['results'][0]['investigation_id']}/transcript").status_code == 200


def test_swarm_explicit_alerts_and_errors(client):
    body = client.post("/swarm/hunt", json={"alert_ids": ["ALERT-001", "ALERT-001", "ALERT-002"]}).json()
    assert body["alert_ids"] == ["ALERT-001", "ALERT-002"] and body["num_hunters"] == 2
    assert client.post("/swarm/hunt", json={"alert_ids": ["NOPE"]}).status_code == 404
    assert client.post("/swarm/hunt", json={"num_hunters": 9}).status_code == 422


def test_restart_decay_can_be_disabled(client, monkeypatch):
    monkeypatch.setenv("MNEMOS_DECAY_ON_RESTART", "false")
    assert client.post("/agent/restart").json()["memory_decay"] is None


def test_transcript_store_is_capped():
    routes._transcripts.clear()
    for i in range(routes.MAX_TRANSCRIPTS + 20):
        routes._store_transcript([f"k{i}"], [])
    assert len(routes._transcripts) == routes.MAX_TRANSCRIPTS
    assert "k0" not in routes._transcripts
    routes._transcripts.clear()


def test_seed_if_empty(fake, monkeypatch):
    import sys
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "scripts"))
    import seed_scenario

    seeded = []
    monkeypatch.setenv("MNEMOS_AUTO_SEED", "true")
    monkeypatch.setattr(seed_scenario, "seed", lambda db: seeded.append(db))

    fake.graph.query = lambda q, params=None: Result([[0]])  # empty graph
    assert routes._seed_if_empty(fake) is True and seeded

    seeded.clear()
    fake.graph.query = lambda q, params=None: Result([[5]])  # already populated
    assert routes._seed_if_empty(fake) is False and not seeded
