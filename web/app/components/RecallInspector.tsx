'use client'

import type { TranscriptEntry } from '@/lib/types'

interface Props {
  entries: TranscriptEntry[]
}

export default function RecallInspector({ entries }: Props) {
  // Show the most recent recall step of the current investigation.
  const recall = [...entries].reverse().find((e) => e.step === 'recall')
  const results: Record<string, any> = recall?.details?.results || {}
  const queryNames: Record<string, string> = recall?.details?.query_names || {}
  const rows = Object.entries(results)

  return (
    <div className="space-y-4 max-h-96 overflow-y-auto">
      {rows.length === 0 ? (
        <p className="text-text-secondary text-xs">
          No recall data yet — investigate an alert
        </p>
      ) : (
        rows.map(([key, entry]) => (
          <div key={key} className="bg-background border border-surface-border rounded p-3">
            <div className="flex items-center justify-between mb-2 gap-2">
              <span className="text-accent-blue text-xs font-mono truncate">
                {`${queryNames[key] ? queryNames[key] + ' · ' : ''}${key}`}
              </span>
              <span className="text-xs text-text-secondary whitespace-nowrap">{`Latency: ${entry.latency_ms}ms`}</span>
            </div>
            <pre className="text-xs text-accent-purple font-mono whitespace-pre-wrap">
              {entry.cypher}
            </pre>
            <div className="mt-2">
              <p className="text-text-secondary text-xs mb-1">Result:</p>
              <pre className="text-xs text-accent-green font-mono whitespace-pre-wrap break-words">
                {JSON.stringify(entry.result, null, 2)}
              </pre>
            </div>
          </div>
        ))
      )}
    </div>
  )
}
