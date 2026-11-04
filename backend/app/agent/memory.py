"""Mnemos — Memory Reader/Writer module.

Implements the five Cypher queries (R1-R5) that form the agent's
cognitive memory layer on FalkorDB. All queries now include edge
weights for memory decay and reinforcement.
"""
import time
from typing import Any, Dict, List, Optional, Tuple

from falkordb import FalkorDB


def jsonable(value: Any) -> Any:
    """Convert FalkorDB result values (Node / Edge / Path) into plain JSON types."""
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, (list, tuple, set)):
        return [jsonable(v) for v in value]
    if isinstance(value, dict):
        return {str(k): jsonable(v) for k, v in value.items()}
    # falkordb Path
    if callable(getattr(value, "nodes", None)) and callable(getattr(value, "edges", None)):
        return {
            "nodes": [jsonable(n) for n in value.nodes()],
            "edges": [jsonable(e) for e in value.edges()],
        }
    # falkordb Node / Edge
    if hasattr(value, "properties"):
        out: Dict[str, Any] = {"properties": jsonable(value.properties)}
        labels = getattr(value, "labels", None)
        if labels:
            out["labels"] = list(labels)
        relation = getattr(value, "relation", None)
        if relation:
            out["relation"] = relation
        return out
    return str(value)


class Memory:
    """Manages all FalkorDB reads and writes for the agent."""

    def __init__(self, db: FalkorDB, graph_name: str = "mnemos"):
        self.db = db
        self.graph = db.select_graph(graph_name)
        self.decay_rate = 0.9

    def _timed(self, cypher: str, params: Optional[dict] = None) -> dict[str, Any]:
        """Run a query and return {result, cypher, latency_ms} (JSON-safe)."""
        start = time.perf_counter()
        result = self.graph.query(cypher, params)
        latency_ms = (time.perf_counter() - start) * 1000
        return {"result": jsonable(result.result_set), "cypher": cypher,
                "latency_ms": round(latency_ms, 2)}

    def recall_ioc(self, ioc_value: str) -> dict[str, Any]:
        """R1: Episodic recall - 'Have I seen this IoC before?'"""
        cypher = (
            "MATCH (ioc:IoC {value: $ioc})<-[r:FOUND]-"
            "(inv:Investigation) "
            "-[:ATTRIBUTED_TO]->(actor:ThreatActor) "
            "OPTIONAL MATCH (actor)-[:USES]->(ttp:TTP) "
            "RETURN actor.name, collect(DISTINCT ttp.mitre_id), "
            "inv.conclusion, r.weight"
        )
        return self._timed(cypher, {"ioc": ioc_value})

    def recall_playbook(self, technique: str) -> dict[str, Any]:
        """R2: Procedural recall - 'What playbook worked against this TTP?'"""
        cypher = (
            "MATCH (p:Playbook)-[r:EFFECTIVE_AGAINST]->"
            "(t:TTP {mitre_id: $technique}) "
            "RETURN p.name, p.success_rate, r.weight "
            "ORDER BY p.success_rate DESC LIMIT 1"
        )
        return self._timed(cypher, {"technique": technique})

    def recall_asset_actor(self, asset_id: str) -> dict[str, Any]:
        """R3: Multi-hop recall - 'Is this asset tied to a known actor?'"""
        cypher = (
            "MATCH path = (a:Asset {id: $asset})<-[:OBSERVED_ON]-"
            "(:IoC)<-[:ASSOCIATED_WITH]-(actor:ThreatActor) "
            "RETURN path"
        )
        return self._timed(cypher, {"asset": asset_id})

    def recall_cross_session(self, alert_id: str, current_inv_id: str = None) -> dict[str, Any]:
        """R4: Cross-session recall - 'What have I learned from past sessions?'

        The current investigation does not exist yet at recall time, so the
        link to prior work goes through the alert's SHARED_IOC edges.
        """
        cypher = (
            "MATCH (past:Investigation)-[:FOUND]->(ioc:IoC) "
            "MATCH (al:Alert {id: $alert_id})-[:SHARED_IOC]->(ioc) "
            "WHERE past.id <> $current_inv "
            "MATCH (past)-[:ATTRIBUTED_TO]->(actor) "
            "RETURN actor.name, count(past), collect(DISTINCT ioc.value)"
        )
        return self._timed(cypher, {"alert_id": alert_id,
                                    "current_inv": current_inv_id or ""})

    def lookup_actor_for_ioc(self, ioc_value: str) -> Tuple[Optional[str], Optional[str]]:
        """Semantic lookup: (actor name, producing TTP) already linked to an IoC."""
        r = self.graph.query(
            "MATCH (a:ThreatActor)-[:ASSOCIATED_WITH]->(i:IoC {value: $v}) "
            "OPTIONAL MATCH (t:TTP)-[:PRODUCES]->(i) "
            "RETURN a.name, t.mitre_id LIMIT 1",
            {"v": ioc_value},
        )
        if r.result_set:
            return r.result_set[0][0], r.result_set[0][1]
        return None, None

    def write_memory(self, ioc_value: str, ioc_type: str, actor_name: str) -> dict[str, Any]:
        """R5: Memory write - persist a new finding."""
        cypher = (
            "MERGE (ioc:IoC {value: $value}) SET ioc.type = $type "
            "MERGE (actor:ThreatActor {name: $actor}) "
            "MERGE (actor)-[:ASSOCIATED_WITH {weight: 1.0, last_recalled: 0}]->(ioc)"
        )
        return self._timed(cypher, {"value": ioc_value, "type": ioc_type,
                                    "actor": actor_name})

    def write_investigation(self, inv_id: str, alert_id: str,
                            findings: list[str], conclusion: str,
                            actor_name: str = None) -> dict[str, Any]:
        """Create an Investigation node with optional actor attribution."""
        start = time.perf_counter()

        cypher = (
            "CREATE (inv:Investigation { "
            "  id: $inv_id, alert_id: $alert_id, "
            "  findings: $findings, conclusion: $conclusion, "
            "  created_at: timestamp()}) "
            "WITH inv "
            "MATCH (al:Alert {id: $alert_id}) "
            "CREATE (inv)-[:TRIGGERED_BY]->(al)"
        )
        result = self.graph.query(cypher,
                                  {"inv_id": inv_id, "alert_id": alert_id,
                                   "findings": findings, "conclusion": conclusion})

        for finding in findings:
            self.graph.query(
                "MATCH (ioc:IoC {value: $val}) "
                "MATCH (inv:Investigation {id: $inv_id}) "
                "CREATE (inv)-[:FOUND {weight: 1.0, last_recalled: 0}]->(ioc)",
                {"val": finding, "inv_id": inv_id}
            )
        if actor_name:
            self.graph.query(
                "MATCH (inv:Investigation {id: $inv_id}) "
                "MATCH (a:ThreatActor {name: $actor}) "
                "CREATE (inv)-[:ATTRIBUTED_TO]->(a)",
                {"inv_id": inv_id, "actor": actor_name}
            )

        latency_ms = (time.perf_counter() - start) * 1000
        return {"result": jsonable(result.result_set), "cypher": cypher,
                "latency_ms": round(latency_ms, 2)}

    def write_playbook_result(self, playbook_name: str,
                              success: bool,
                              ttps: list[str] = None) -> dict[str, Any]:
        """Update a Playbook's success rate and optionally link to TTPs."""
        cypher = (
            "MERGE (p:Playbook {name: $name}) "
            "ON CREATE SET p.count = 0, p.successes = 0, p.success_rate = 0.0 "
            "WITH p "
            "SET p.count = p.count + 1, "
            "    p.successes = p.successes + $success "
            "WITH p, CASE WHEN p.count > 0 "
            "    THEN p.successes * 1.0 / p.count "
            "    ELSE 1.0 END AS rate "
            "SET p.success_rate = rate"
        )
        ret = self._timed(cypher, {"name": playbook_name,
                                   "success": 1.0 if success else 0.0})

        if ttps:
            for ttp in ttps:
                self.graph.query(
                    "MATCH (p:Playbook {name: $name}) "
                    "MATCH (t:TTP {mitre_id: $mitre_id}) "
                    "MERGE (p)-[:EFFECTIVE_AGAINST {weight: 1.0}]->(t)",
                    {"name": playbook_name, "mitre_id": ttp}
                )

        return ret

    def decay_memory(self) -> Dict[str, Any]:
        """Reduce edge weights over time to simulate memory decay.

        Returns count of edges decayed and pruned.
        """
        # Count edges with weight > 0 before decaying (SET returns no rows)
        before = self.graph.query(
            "MATCH ()-[r]->() WHERE r.weight > 0 RETURN count(r)"
        )
        decayed_edges = before.result_set[0][0] if before.result_set else 0

        decay_cypher = (
            "MATCH ()-[r]->() WHERE r.weight > 0 "
            "SET r.weight = r.weight * $rate, r.last_decayed = timestamp()"
        )
        self.graph.query(decay_cypher, {"rate": self.decay_rate})

        # DELETE returns no rows, so count the weak edges first
        weak = self.graph.query(
            "MATCH ()-[r]->() WHERE r.weight < 0.1 RETURN count(r)"
        )
        pruned_edges = weak.result_set[0][0] if weak.result_set else 0
        self.graph.query("MATCH ()-[r]->() WHERE r.weight < 0.1 DELETE r")

        return {"edges_decayed": decayed_edges, "edges_pruned": pruned_edges}

    def link_ioc_to_assets(self, ioc_value: str, asset_ids: List[str]) -> int:
        """Episodic learning: record that an IoC was observed on assets (feeds R3)."""
        linked = 0
        for asset_id in asset_ids or []:
            self.graph.query(
                "MATCH (i:IoC {value: $v}) MATCH (a:Asset {id: $a}) "
                "MERGE (i)-[:OBSERVED_ON {weight: 1.0, last_recalled: 0}]->(a)",
                {"v": ioc_value, "a": asset_id},
            )
            linked += 1
        return linked

    _BOOST = ("SET r.weight = CASE WHEN r.weight * 1.2 > 5.0 "
              "THEN 5.0 ELSE r.weight * 1.2 END, r.last_recalled = timestamp()")

    def reinforce(self, ioc_values: List[str] = (), asset_ids: List[str] = ()) -> int:
        """Boost only the edges a recall actually traversed (x1.2, capped at 5.0)."""
        n = 0
        for value in ioc_values:
            for rel in ("FOUND", "ASSOCIATED_WITH"):
                self.graph.query(
                    f"MATCH ()-[r:{rel}]->(:IoC {{value: $v}}) "
                    f"WHERE r.weight > 0 {self._BOOST}", {"v": value})
                n += 1
        for asset_id in asset_ids:
            self.graph.query(
                "MATCH (:IoC)-[r:OBSERVED_ON]->(:Asset {id: $a}) "
                f"WHERE r.weight > 0 {self._BOOST}", {"a": asset_id})
            n += 1
        return n

    def boost_recall(self, edge_type: str = None) -> int:
        """Boost edge weights when a recall query traverses them."""
        if edge_type == "all":
            cypher = (
                "MATCH ()-[r]->() WHERE r.weight > 0 "
                "SET r.weight = CASE WHEN r.weight * 1.2 > 5.0 "
                "THEN 5.0 ELSE r.weight * 1.2 END"
            )
        elif edge_type == "found":
            cypher = (
                "MATCH ()-[r:FOUND]->() WHERE r.weight > 0 "
                "SET r.weight = CASE WHEN r.weight * 1.2 > 5.0 "
                "THEN 5.0 ELSE r.weight * 1.2 END"
            )
        elif edge_type == "associated":
            cypher = (
                "MATCH ()-[r:ASSOCIATED_WITH]->() WHERE r.weight > 0 "
                "SET r.weight = CASE WHEN r.weight * 1.2 > 5.0 "
                "THEN 5.0 ELSE r.weight * 1.2 END"
            )
        else:
            return 0

        self.graph.query(cypher)
        return 1

    def get_stats(self) -> dict[str, int]:
        """Return node counts by label and total edge count."""
        counts = {}
        for label in ["ThreatActor", "TTP", "IoC", "Asset", "Alert",
                      "Investigation", "Playbook", "Action"]:
            r = self.graph.query(f"MATCH (n:{label}) RETURN count(n)")
            counts[label] = r.result_set[0][0] if r.result_set else 0
        r = self.graph.query("MATCH ()-->() RETURN count(*)")
        counts["edges"] = r.result_set[0][0] if r.result_set else 0
        return counts

    def get_graph_data(self) -> dict[str, Any]:
        """Return nodes and edges for Cytoscape.js visualization."""
        nodes = []
        r = self.graph.query(
            "MATCH (n) RETURN labels(n)[0], id(n), n")
        for label, node_id, node in r.result_set:
            props = getattr(node, "properties", None) or {}
            nodes.append({
                "id": str(node_id),
                "label": label,
                "properties": {k: jsonable(v) for k, v in props.items()
                               if v is not None},
            })
        edges = []
        r = self.graph.query(
            "MATCH (a)-[r]->(b) RETURN id(r), id(a), id(b), type(r), r.weight")
        for edge_id, source, target, edge_type, weight in r.result_set:
            edges.append({"id": f"e{edge_id}",
                          "source": str(source),
                          "target": str(target),
                          "type": edge_type,
                          "weight": weight if weight is not None else 1.0})
        return {"nodes": nodes, "edges": edges}
