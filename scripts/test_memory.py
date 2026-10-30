"""Test script for memory module — Day 2 verification.

Seeds graph, tests all recall queries (R1-R4), writes data, then
verifies recall returns results. Prints latency for each query.
"""
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from falkordb import FalkorDB
from backend.app.agent.memory import Memory
import seed_scenario


def test_memory():
    db = FalkorDB()
    mem = Memory(db)

    # Re-seed to ensure clean state
    print("Re-seeding graph...")
    seed_scenario.seed(db)

    print("\n=== Testing Empty Recall (No Investigations) ===")
    tests = [
        ("R1: recall_ioc", lambda: mem.recall_ioc("powershell-loader-7d3a9b.exe")),
        ("R2: recall_playbook", lambda: mem.recall_playbook("T1059.001")),
        ("R3: recall_asset_actor", lambda: mem.recall_asset_actor("ASSET-001")),
        ("R4: recall_cross_session", lambda: mem.recall_cross_session("ALERT-001")),
    ]

    for name, fn in tests:
        r = fn()
        assert r["result"] == [], f"{name} should return empty list when no data"
        assert r["latency_ms"] < 10, f"{name} should be fast (<10ms), got {r['latency_ms']}ms"
        print(f"  {name}: PASS ({r['latency_ms']}ms)")

    print("\n=== Writing Episodic Memory ===")
    # Write investigation with actor attribution
    r = mem.write_investigation("INV-001", "ALERT-001",
                                ["powershell-loader-7d3a9b.exe"],
                                "APT-CRIMSON used PowerShell",
                                actor_name="APT-CRIMSON")
    print(f"  write_investigation: {r['latency_ms']}ms")

    # Write playbook result linked to TTP
    r = mem.write_playbook_result("Network_Segment_Isolation", True,
                                  ttps=["T1059.001"])
    print(f"  write_playbook_result: {r['latency_ms']}ms")

    print("\n=== Testing Recall After Write ===")
    # R1 should now return the investigation
    r = mem.recall_ioc("powershell-loader-7d3a9b.exe")
    assert len(r["result"]) == 1, f"Expected 1 result, got {len(r['result'])}"
    print(f"  R1 recall_ioc: PASS ({r['latency_ms']}ms)")

    # R2 should now return the playbook
    r = mem.recall_playbook("T1059.001")
    assert len(r["result"]) == 1, f"Expected 1 result, got {len(r['result'])}"
    print(f"  R2 recall_playbook: PASS ({r['latency_ms']}ms)")

    print("\n=== Testing Cross-Session Recall ===")
    # Simulate Session 2: write a second investigation sharing an IoC with INV-001
    mem.write_investigation("INV-002", "ALERT-002",
                            ["powershell-loader-7d3a9b.exe"],
                            "APT-CRIMSON brute-forced cloud accounts",
                            actor_name="APT-CRIMSON")
    # Now query R4 from INV-002's perspective - should find shared IoCs from INV-001
    r = mem.recall_cross_session("ALERT-002", "INV-002")
    assert len(r["result"]) >= 1, f"Expected >=1 results, got {len(r['result'])}"
    print(f"  R4 recall_cross_session: PASS ({r['latency_ms']}ms)")

    print("\n=== Stats After Write ===")
    stats = mem.get_stats()
    for k, v in stats.items():
        print(f"  {k}: {v}")

    print("\n=== All Tests Passed ===")


if __name__ == "__main__":
    try:
        test_memory()
        sys.exit(0)
    except AssertionError as e:
        print(f"\nFAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
