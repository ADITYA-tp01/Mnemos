'use client'

import type { TranscriptEntry } from '@/lib/types'

interface Props {
  alertId: string | null
  entries: TranscriptEntry[]
  loading: boolean
  error: string | null
}

const stepColors = {
  perceive: 'bg-accent-blue',
  recall: 'bg-accent-blue',
  reason: 'bg-accent-purple',
  reason_error: 'bg-accent-red',
  act: 'bg-accent-green',
  write: 'bg-accent-orange',
}

export default function Transcript({ alertId, entries, loading, error }: Props) {
  if (loading) {
    return (
      <p className="text-accent-orange text-xs animate-pulse">
        {`Investigating ${alertId}...`}
      </p>
    )
  }

  if (error) {
    return <p className="text-accent-red text-xs">{`Investigation failed: ${error}`}</p>
  }

  if (!alertId) {
    return (
      <p className="text-text-secondary text-xs">Select an alert to investigate it</p>
    )
  }

  return (
    <div className="space-y-2 max-h-96 overflow-y-auto">
      {entries.length === 0 ? (
        <p className="text-text-secondary text-xs">No transcript data</p>
      ) : (
        entries.map((entry, idx) => (
          <details key={idx} open className="text-xs">
            <summary className="flex items-center gap-2 mb-1 cursor-pointer">
              <span className={`w-2 h-2 rounded-full ${stepColors[entry.step as keyof typeof stepColors] || 'bg-text-secondary'}`} />
              <span className="font-mono uppercase text-text-secondary">{entry.step}</span>
              <span className="text-text-secondary ml-auto">{new Date(entry.timestamp).toLocaleTimeString()}</span>
            </summary>
            <div className="ml-4 bg-background p-2 rounded border border-surface-border">
              {entry.step === 'recall' && (
                <div className="space-y-1">
                  <span className="text-accent-blue">
                    {`Recalled ${Object.keys(entry.details?.results || {}).length} queries in ${entry.details?.total_latency_ms ?? 0}ms`}
                  </span>
                  {(entry.details?.attribution || []).map((line: string, i: number) => (
                    <p key={i} className="text-text-secondary break-words">{line}</p>
                  ))}
                </div>
              )}
              {entry.step === 'reason' && (
                <div>
                  <p className="text-accent-purple">
                    {entry.details?.content || 'LLM reasoning'}
                  </p>
                  <p className="text-text-secondary mt-1">
                    {`Tool calls: ${(entry.details?.tool_calls || []).map((tc: any) => tc.name).join(', ') || 'none'}`}
                  </p>
                </div>
              )}
              {entry.step === 'act' && (
                <div>
                  <p className="text-accent-green">{`Tool: ${entry.details?.tool}`}</p>
                  <pre className="text-text-secondary whitespace-pre-wrap break-words">
                    {JSON.stringify(entry.details?.result?.result ?? entry.details?.result, null, 2)}
                  </pre>
                </div>
              )}
              {entry.step === 'write' && (
                <p className="text-accent-orange">
                  {`Persisted: ${entry.details?.ioc} -> ${entry.details?.actor}`}
                </p>
              )}
              {entry.step === 'perceive' && (
                <div>
                  <p>{entry.details?.description}</p>
                  <p className="text-text-secondary">
                    {`IoCs: ${(entry.details?.iocs || []).join(', ')}`}
                  </p>
                </div>
              )}
              {entry.step === 'reason_error' && (
                <p className="text-accent-red">{entry.details?.error}</p>
              )}
            </div>
          </details>
        ))
      )}
    </div>
  )
}
