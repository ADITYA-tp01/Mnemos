"""Mnemos — Memory Reader/Writer module.

Implements the five Cypher queries (R1-R5) that form the agent's
cognitive memory layer on FalkorDB. All queries now include edge
weights for memory decay and reinforcement.
"""
import time
from typing import Any, Dict, List

from falkordb import FalkorDB


class Memory:
    """Manages all FalkorDB reads and writes for the agent."""

    def __init__(self, db: FalkorDB, graph_name: str = "mnemos"):
        self.db = db
        self.graph = db.select_graph(graph_name)
        self.decay_rate = 0.9

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
        start = time.perf_counter()
        result = self.graph.query(cypher, {"ioc": ioc_value})
        latency_ms = (time.perf_counter() - start) * 1000
        return {"result": result.result_set, "cypher": cypher,
                "latency_ms": round(latency_ms, 2)}

    def recall_playbook(self, technique: str) -> dict[str, Any]:
        """R2: Procedural recall - 'What playbook worked against this TTP?'"""
        cypher = (
            "MATCH (p:Playbook)-[r:EFFECTIVE_AGAINST]->"
            "(t:TTP {mitre_id: $technique}) "
            "RETURN p.name, p.success_rate, r.weight "
            "ORDER BY p.success_rate DESC LIMIT 1"
        )
        start = time.perf_counter()
        result = self.graph.query(cypher, {"technique": technique})
        latency_ms = (time.perf_counter() - start) * 1000
        return {"result": result.result_set, "cypher": cypher,
                "latency_ms": round(latency_ms, 2)}

    def recall_asset_actor(self, asset_id: str) -> dict[str, Any]:
        """R3: Multi-hop recall - 'Is this asset tied to a known actor?'"""
        cypher = (
            "MATCH path = (a:Asset {id: $asset})<-[:OBSERVED_ON]-"
            "(:IoC)-[:ASSOCIATED_WITH]->(actor:ThreatActor) "
            "RETURN path"
        )
        start = time.perf_counter()
        result = self.graph.query(cypher, {"asset": asset_id})
        latency_ms = (time.perf_counter() - start) * 1000
        return {"result": result.result_set, "cypher": cypher,
                "latency_ms": round(latency_ms, 2)}

    def recall_cross_session(self, alert_id: str, current_inv_id: str = None) -> dict[str, Any]:
        """R4: Cross-session recall - 'What have I learned from past sessions?'"""
        cypher = (
            "MATCH (past:Investigation)-[:FOUND]->(ioc:IoC) "
            "MATCH (al:Alert {id: $alert_id})-[:SHARED_IOC]->(ioc) "
            "WHERE past.id <> $current_inv "
            "MATCH (past)-[:ATTRIBUTED_TO]->(actor) "
            "RETURN actor.name, count(past), collect(DISTINCT ioc.value)"
        )
        start = time.perf_counter()
        result = self.graph.query(cypher, {"alert_id": alert_id,
                                           "current_inv": current_inv_id or ""})
        latency_ms = (time.perf_counter() - start) * 1000
        return {"result": result.result_set, "cypher": cypher,
                "latency_ms": round(latency_ms, 2)}

    def write_memory(self, ioc_value: str, ioc_type: str, actor_name: str) -> dict[str, Any]:
        """R5: Memory write - persist a new finding."""
        cypher = (
            "MERGE (ioc:IoC {value: $value}) SET ioc.type = $type "
            "MERGE (actor:ThreatActor {name: $actor}) "
            "MERGE (actor)-[:ASSOCIATED_WITH {weight: 1.0, last_recalled: 0}]->(ioc)"
        )
        start = time.perf_counter()
        result = self.graph.query(cypher,
                                  {"value": ioc_value, "type": ioc_type,
                                   "actor": actor_name})
        latency_ms = (time.perf_counter() - start) * 1000
        return {"result": result.result_set, "cypher": cypher,
                "latency_ms": round(latency_ms, 2)}

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
        return {"result": result.result_set, "cypher": cypher,
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
        start = time.perf_counter()
        result = self.graph.query(cypher,
                                  {"name": playbook_name,
                                   "success": 1.0 if success else 0.0})
        latency_ms = (time.perf_counter() - start) * 1000
        ret = {"result": result.result_set, "cypher": cypher,
               "latency_ms": round(latency_ms, 2)}

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

        prune_cypher = (
            "MATCH ()-[r]->() WHERE r.weight < 0.1 "
            "DELETE r"
        )
        prune_result = self.graph.query(prune_cypher)
        pruned_edges = prune_result.result_set[0][0] if prune_result.result_set else 0

        return {"edges_decayed": decayed_edges, "edges_pruned": pruned_edges}

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
            "MATCH (n) RETURN labels(n)[0] AS label, id(n) AS fid, n")
        for row in r.result_set:
            label, fid, props = row[0], row[1], row[2]
            if props:
                nodes.append({
                    "id": str(fid),
                    "label": label,
                    "properties": {k: v for k, v in props.items()
                                   if v is not None},
                })
        edges = []
        r = self.graph.query(
            "MATCH (a)-->(b) RETURN id(a), id(b), type(a), type(b)")
        for row in r.result_set:
            edges.append({"id": f"e{row[0]}-{row[1]}",
                          "source": str(row[0]),
                          "target": str(row[1]),
                          "type": row[2],
                          "weight": row[3] if len(row) > 3 else 1.0})
        return {"nodes": nodes, "edges": edges}
