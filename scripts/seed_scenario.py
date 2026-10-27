"""Mnemos — deterministic scenario seeder.

Seed contract:
  1. Connect to FalkorDB, select_graph("mnemos"), wipe all nodes
  2. Create indexes on IoC.value, TTP.mitre_id, Asset.id, Playbook.name
  3. Seed 10 MITRE ATT&CK TTPs
  4. Seed threat actor APT-CRIMSON linked to 10 TTPs + 2 IoCs
  5. Seed 20 assets across 3 subnets, varied criticality
  6. Seed alert queue: Alert #1 (Session 1), Alert #2 (Session 2, related) +2 extras
  7. Leave episodic (Investigation) and procedural (Playbook) memory EMPTY
  8. Print verification counts, exit 0 on success

FalkorDB quirk: MERGE on a relationship pattern can CREATE new nodes
instead of matching. Always MATCH existing nodes first, then CREATE edges.
"""
import os
import random
import sys

from falkordb import FalkorDB

random.seed(42)

GRAPH_NAME = "mnemos"


def connect():
    host = os.environ.get("FALKORDB_HOST", "localhost")
    port = int(os.environ.get("FALKORDB_PORT", "6379"))
    return FalkorDB(host=host, port=port)


TTPS = [
    ("T1059.001", "PowerShell"),
    ("T1078", "Valid Accounts"),
    ("T1059.003", "Windows Command Shell"),
    ("T1071.001", "Web Protocols"),
    ("T1027", "Obfuscated Files or Information"),
    ("T1005", "Data from Local System"),
    ("T1566.001", "Phishing: Spearphishing Attachment"),
    ("T1133", "External Remote Services"),
    ("T1078.004", "Valid Accounts: Cloud Accounts"),
    ("T1059.005", "Visual Basic"),
]

IoC_ACTOR_LINKS = [
    ("185.220.101.45", "ip", "T1071.001"),
    ("powershell-loader-7d3a9b.exe", "file_hash", "T1059.001"),
]

ALERTS = [
    {
        "id": "ALERT-001", "type": "suspicious_process", "sev": "high",
        "desc": "PowerShell process spawning from unusual parent on web-01",
        "iocs": ["powershell-loader-7d3a9b.exe"],
        "assets": ["ASSET-001"], "session": 1,
    },
    {
        "id": "ALERT-002", "type": "auth_anomaly", "sev": "critical",
        "desc": "External IP 185.220.101.45 brute-forcing cloud accounts",
        "iocs": ["185.220.101.45"],
        "assets": ["ASSET-013", "ASSET-017"], "session": 2,
    },
    {
        "id": "ALERT-003", "type": "data_exfil", "sev": "medium",
        "desc": "Unusual outbound traffic on port 443",
        "iocs": ["104.21.5.30"],
        "assets": ["ASSET-005", "ASSET-008"], "session": 3,
    },
    {
        "id": "ALERT-004", "type": "privilege_escalation", "sev": "high",
        "desc": "Token manipulation detected on database host",
        "iocs": ["t1055-process"],
        "assets": ["ASSET-012"], "session": 4,
    },
]


def seed(db):
    g = db.select_graph(GRAPH_NAME)

    # --- Clean slate ---
    try:
        g.query("MATCH (n) DETACH DELETE n")
    except Exception:
        pass

    # --- Indexes (idempotent) ---
    for label, prop in [("IoC", "value"), ("TTP", "mitre_id"),
                        ("Asset", "id"), ("Playbook", "name")]:
        try:
            g.query(f"CREATE INDEX FOR (x:{label}) ON (x.{prop})")
        except Exception:
            pass  # index already exists

    # --- Semantic: threat actor (exactly one) ---
    g.query(
        "CREATE (:ThreatActor {id: 'TA-1', name: 'APT-CRIMSON', "
        "alias: 'CrimsonGroup', first_seen: '2025-03-01'})"
    )

    # --- Semantic: TTPs + USES edges (MATCH then CREATE, never MERGE on edges) ---
    for mitre_id, name in TTPS:
        g.query("CREATE (:TTP {mitre_id: $mitre_id, name: $name})",
                {"mitre_id": mitre_id, "name": name})
        g.query(
            "MATCH (a:ThreatActor {id: 'TA-1'}), (t:TTP {mitre_id: $mitre_id}) "
            "CREATE (a)-[:USES]->(t)",
            {"mitre_id": mitre_id},
        )

    # --- Semantic: IoCs linked to actor + producing TTP ---
    for value, ioc_type, ttp in IoC_ACTOR_LINKS:
        g.query("CREATE (:IoC {value: $value, type: $type, source: 'actor'})",
                {"value": value, "type": ioc_type})
        g.query(
            "MATCH (a:ThreatActor {id: 'TA-1'}), (i:IoC {value: $value}) "
            "CREATE (a)-[:ASSOCIATED_WITH]->(i)",
            {"value": value},
        )
        g.query(
            "MATCH (t:TTP {mitre_id: $ttp}), (i:IoC {value: $value}) "
            "CREATE (t)-[:PRODUCES]->(i)",
            {"ttp": ttp, "value": value},
        )

    # --- Semantic: 20 assets across 3 subnets ---
    subnets = ["10.0.1", "10.0.2", "10.0.3"]
    asset_types = ["server", "workstation", "database", "web"]
    for i in range(20):
        subnet = subnets[i % 3]
        ip = f"{subnet}.{(i // 3) * 7 + 10}"
        g.query(
            "CREATE (:Asset {id: $id, name: $name, ip: $ip, subnet: $subnet, "
            "type: $type, criticality: $crit})",
            {
                "id": f"ASSET-{i+1:03d}",
                "name": f"host-{ip.replace('.', '-')}",
                "ip": ip,
                "subnet": f"{subnet}.0/24",
                "type": random.choice(asset_types),
                "crit": random.choices(["low", "medium", "high"], weights=[2, 3, 2])[0],
            },
        )

    # --- Episodic: alert queue (4 alerts; Alert #1 = Session 1, Alert #2 = Session 2) ---
    for a in ALERTS:
        g.query(
            "CREATE (:Alert {id: $id, type: $type, severity: $sev, "
            "description: $desc, session_target: $sess, status: 'pending'})",
            {"id": a["id"], "type": a["type"], "sev": a["sev"],
             "desc": a["desc"], "sess": a["session"]},
        )
        # Alert -> flagged IoC. Flagged IoCs that aren't actor-linked get created here.
        for ioc_val in a["iocs"]:
            exists = g.query("MATCH (i:IoC {value: $v}) RETURN i LIMIT 1",
                             {"v": ioc_val}).result_set
            if not exists:
                g.query("CREATE (:IoC {value: $v, type: 'alert', source: 'alert'})",
                        {"v": ioc_val})
            g.query(
                "MATCH (al:Alert {id: $aid}), (i:IoC {value: $val}) "
                "CREATE (al)-[:FLAGGED]->(i)",
                {"aid": a["id"], "val": ioc_val},
            )
        # Alert -> involved asset
        for asset_id in a["assets"]:
            g.query(
                "MATCH (al:Alert {id: $aid}), (as:Asset {id: $asid}) "
                "CREATE (al)-[:INVOLVES]->(as)",
                {"aid": a["id"], "asid": asset_id},
            )

    # --- Cross-session bridge: Alert #2 shares Alert #1's actor IoCs ---
    for ioc_val in ["185.220.101.45", "powershell-loader-7d3a9b.exe"]:
        g.query(
            "MATCH (al:Alert {id: 'ALERT-002'}), (i:IoC {value: $v}) "
            "CREATE (al)-[:SHARED_IOC]->(i)",
            {"v": ioc_val},
        )

    # --- Episodic + procedural stay EMPTY: no Investigation, no Playbook nodes ---

    return g


def verify(g):
    counts = {}
    for label in ["ThreatActor", "TTP", "IoC", "Asset", "Alert",
                  "Investigation", "Playbook"]:
        counts[label] = g.query(
            f"MATCH (n:{label}) RETURN count(n)"
        ).result_set[0][0]
    edges = g.query("MATCH ()-->() RETURN count(*)").result_set[0][0]

    print("\n=== Mnemos Seed Verification ===")
    for label, count in counts.items():
        print(f"  {label:20s}: {count}")
    print(f"  {'edges':20s}: {edges}\n")

    assert counts["ThreatActor"] == 1, f"Expected 1 actor, got {counts['ThreatActor']}"
    assert counts["TTP"] == 10, f"Expected 10 TTPs, got {counts['TTP']}"
    assert counts["Asset"] == 20, f"Expected 20 assets, got {counts['Asset']}"
    assert counts["Alert"] == 4, f"Expected 4 alerts, got {counts['Alert']}"
    assert counts["Investigation"] == 0, "Episodic memory must start empty"
    assert counts["Playbook"] == 0, "Procedural memory must start empty"

    uses = g.query(
        "MATCH (:ThreatActor)-[r:USES]->() RETURN count(r)"
    ).result_set[0][0]
    assert uses == 10, f"Expected 10 USES edges, got {uses}"

    shared = g.query(
        "MATCH (:Alert {id: 'ALERT-002'})-[r:SHARED_IOC]->() RETURN count(r)"
    ).result_set[0][0]
    assert shared == 2, f"Expected 2 SHARED_IOC edges, got {shared}"

    print("=== All assertions passed ===\n")
    return counts


if __name__ == "__main__":
    db = connect()
    g = seed(db)
    verify(g)
    sys.exit(0)
