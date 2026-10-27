"""Verify the seeded Mnemos graph — print counts + relationship report.

Usage:  python scripts/verify_seed.py
"""
import os
import sys

from falkordb import FalkorDB

GRAPH_NAME = "mnemos"


def main():
    host = os.environ.get("FALKORDB_HOST", "localhost")
    port = int(os.environ.get("FALKORDB_PORT", "6379"))
    db = FalkorDB(host=host, port=port)

    try:
        g = db.select_graph(GRAPH_NAME)
    except Exception as e:
        print(f"ERROR: cannot select graph '{GRAPH_NAME}': {e}")
        sys.exit(1)

    print("=== Mnemos Graph Report ===\n")

    # Node counts by label (single query via Cypher UNION)
    labels = g.query("""
        MATCH (n)
        RETURN DISTINCT labels(n)[0] AS label, count(*) AS c
        ORDER BY c DESC
    """).result_set
    print("Nodes by label:")
    for label, count in labels:
        print(f"  {label:20s}: {count}")

    edges = g.query("MATCH ()-->() RETURN count(*)").result_set[0][0]
    print(f"\nTotal relationships: {edges}")

    # Actor -> TTPs
    print("\nThreat actors and their TTPs:")
    for actor_name, ttp_ids in g.query(
        "MATCH (a:ThreatActor)-[:USES]->(t:TTP) RETURN a.name, collect(t.mitre_id)"
    ).result_set:
        print(f"  {actor_name}: {ttp_ids}")

    # Actor -> IoCs
    print("\nThreat actors and their IoCs:")
    for actor_name, ioc_vals in g.query(
        "MATCH (a:ThreatActor)-[:ASSOCIATED_WITH]->(i:IoC) RETURN a.name, collect(i.value)"
    ).result_set:
        print(f"  {actor_name}: {ioc_vals}")

    # Alerts summary
    print("\nAlerts:")
    for row in g.query(
        "MATCH (a:Alert) RETURN a.id, a.severity, a.type, a.status ORDER BY a.id"
    ).result_set:
        print(f"  {row}")

    # Cross-session IoCs on ALERT-002
    print("\nCross-session IoCs on ALERT-002:")
    for row in g.query(
        "MATCH (al:Alert {id:'ALERT-002'})-[:SHARED_IOC]->(i:IoC) RETURN i.value, i.type"
    ).result_set:
        print(f"  {row}")

    print("\n=== Done ===\n")
    sys.exit(0)


if __name__ == "__main__":
    main()
