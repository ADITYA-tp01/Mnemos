"""Test cross-session persistence: Session 1 → Restart → Session 2, run 3 times."""
import sys
sys.path.insert(0, 'scripts')
sys.path.insert(0, '.')

from backend.app.agent.memory import Memory
from backend.app.agent.tools import ToolRouter
from backend.app.agent.loop import AgentLoop
from falkordb import FalkorDB
import seed_scenario

db = FalkorDB()
seed_scenario.seed(db)
memory = Memory(db)
tools = ToolRouter(memory)
agent = AgentLoop(memory, tools)

alerts = [
    {'id': 'ALERT-001', 'type': 'suspicious_process', 'severity': 'high',
     'description': 'PowerShell process spawning', 'iocs': ['powershell-loader-7d3a9b.exe'],
     'assets': ['ASSET-001']},
    {'id': 'ALERT-002', 'type': 'auth_anomaly', 'severity': 'critical',
     'description': 'External IP brute-forcing', 'iocs': ['185.220.101.45'],
     'assets': ['ASSET-013', 'ASSET-017']},
]

for run_num in range(1, 4):
    print(f'=== Run {run_num} ===')

    # Session 1
    r1 = agent.run(alerts[0])
    s1 = memory.get_stats()
    print(f'  S1: Fresh={r1["is_fresh_session"]}, Inv={s1["Investigation"]}, Edges={s1["edges"]}')

    # Restart
    agent.reset()
    print(f'  Restart: Count={agent.session_count}')

    # Session 2
    r2 = agent.run(alerts[1])
    s2 = memory.get_stats()
    print(f'  S2: Fresh={r2["is_fresh_session"]}, Prev={r2["previous_session_count"]}, Inv={s2["Investigation"]}, Edges={s2["edges"]}')

    # R4 cross-session
    r4 = memory.recall_cross_session(alerts[1]['id'])
    print(f'  R4: {r4["result"]}')
    print()

# Final stats
final = memory.get_stats()
print(f'Final graph: {final}')