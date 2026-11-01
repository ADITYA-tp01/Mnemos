'use client'

import { useEffect, useState } from 'react'

interface RecallEntry {
  key: string
  result: any
  cypher: string
  latency_ms: number
}

export default function RecallInspector() {
  const [entries, setEntries] = useState<RecallEntry[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // Mock data for demo - in production this would come from recent transcript
    const mockEntries: RecallEntry[] = [
      {
        key: 'ioc_powershell-loader-7d3a9b.exe',
        result: [],
        cypher: `MATCH (ioc:IoC {value: $ioc})<-[:FOUND]-(inv:Investigation)\n-[:ATTRIBUTED_TO]->(actor:ThreatActor)\nOPTIONAL MATCH (actor)-[:USES]->(ttp:TTP)\nRETURN actor.name, collect(DISTINCT ttp.mitre_id), inv.conclusion`,
        latency_ms: 0.86,
      },
      {
        key: 'cross_session',
        result: [['APT-CRIMSON', 2, ['powershell-loader-7d3a9b.exe', '185.220.101.45']]],
        cypher: `MATCH (past:Investigation)-[:FOUND]->(ioc:IoC)\nMATCH (al:Alert {id: $alert_id})-[:SHARED_IOC]->(ioc)\nWHERE past.id <> $current_inv\nMATCH (past)-[:ATTRIBUTED_TO]->(actor)\nRETURN actor.name, count(past), collect(DISTINCT ioc.value)`,
        latency_ms: 2.43,
      },
    ]
    setEntries(mockEntries)
    setLoading(false)
  }, [])

  if (loading) {
    return <p className="text-text-secondary text-xs">Loading recall inspector...</p>
  }

  return (
    <div className="space-y-4 max-h-96 overflow-y-auto">
      {entries.length === 0 ? (
        <p className="text-text-secondary text-xs">No recall data yet</p>
      ) : (
        entries.map((entry, idx) => (
          <div key={idx} className="bg-background border border-surface-border rounded p-3">
            <div className="flex items-center justify-between mb-2">
              <span className="text-accent-blue text-xs font-mono truncate">{entry.key}</span>
              <span className="text-xs text-text-secondary">{`Latency: ${entry.latency_ms}ms`}</span>
            </div>
            <pre className="text-xs text-accent-purple font-mono whitespace-pre-wrap">
              {entry.cypher}
            </pre>
            <div className="mt-2">
              <p className="text-text-secondary text-xs mb-1">Result:</p>
              <pre className="text-xs text-accent-green font-mono">
                {JSON.stringify(entry.result, null, 2)}
              </pre>
            </div>
          </div>
        ))
      )}
    </div>
  )
}