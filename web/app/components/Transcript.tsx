'use client'

import { useEffect, useState } from 'react'

interface TranscriptEntry {
  step: string
  details: any
  timestamp: string
}

interface Props {
  alertId: string | null
}

const stepColors = {
  perceive: 'bg-accent-blue',
  recall: 'bg-accent-blue',
  reason: 'bg-accent-purple',
  reason_error: 'bg-accent-red',
  act: 'bg-accent-green',
  write: 'bg-accent-orange',
}

export default function Transcript({ alertId }: Props) {
  const [entries, setEntries] = useState<TranscriptEntry[]>([])
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (!alertId) {
      setEntries([])
      return
    }

    setLoading(true)
    fetch(`/api/investigate/${alertId}/transcript`)
      .then((res) => res.json())
      .then((data) => {
        setEntries(data.transcript || [])
        setLoading(false)
      })
      .catch(() => {
        setLoading(false)
      })
  }, [alertId])

  if (!alertId) {
    return (
      <p className="text-text-secondary text-xs">Select an alert to view transcript</p>
    )
  }

  if (loading) {
    return <p className="text-text-secondary text-xs">Loading transcript...</p>
  }

  return (
    <div className="space-y-2 max-h-96 overflow-y-auto">
      {entries.length === 0 ? (
        <p className="text-text-secondary text-xs">No transcript data</p>
      ) : (
        entries.map((entry, idx) => (
          <div key={idx} className="text-xs">
            <div className="flex items-center gap-2 mb-1">
              <span className={`w-2 h-2 rounded-full ${stepColors[entry.step as keyof typeof stepColors] || 'bg-text-secondary'}`} />
              <span className="font-mono uppercase text-text-secondary">{entry.step}</span>
              <span className="text-text-secondary ml-auto">{new Date(entry.timestamp).toLocaleTimeString()}</span>
            </div>
            <div className="ml-4 bg-background p-2 rounded border border-surface-border">
              {entry.step === 'recall' && entry.details?.total_latency_ms && (
                <span className="text-accent-blue">
                  {`Recalled ${Object.keys(entry.details.results || {}).length} facts in ${entry.details.total_latency_ms}ms`}
                </span>
              )}
              {entry.step === 'reason' && entry.details?.tool_calls && (
                <div>
                  <p className="text-accent-purple">
                    {entry.details.content || 'LLM reasoning'}
                  </p>
                  <p className="text-text-secondary mt-1">
                    {`Tool calls: ${entry.details.tool_calls.map((tc: any) => tc.name).join(', ')}`}
                  </p>
                </div>
              )}
              {entry.step === 'act' && (
                <div>
                  <p className="text-accent-green">{`Tool: ${entry.details.tool}`}</p>
                  <p className="text-text-secondary">{JSON.stringify(entry.details.result?.result, null, 2)}</p>
                </div>
              )}
              {entry.step === 'write' && (
                <p className="text-accent-orange">
                  {`Persisted: ${entry.details.ioc} -> ${entry.details.actor}`}
                </p>
              )}
              {entry.step === 'perceive' && (
                <div>
                  <p>{entry.details.description}</p>
                  <p className="text-text-secondary">
                    {`IoCs: ${(entry.details.iocs || []).join(', ')}`}
                  </p>
                </div>
              )}
              {entry.step === 'reason_error' && (
                <p className="text-accent-red">{entry.details.error}</p>
              )}
            </div>
          </div>
        ))
      )}
    </div>
  )
}