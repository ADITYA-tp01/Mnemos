'use client'

import type { SwarmResult, TranscriptEntry } from '@/lib/types'

interface Props {
  running: boolean
  disabled: boolean
  result: SwarmResult | null
  error: string | null
  onRun: () => void
  onSelect: (alertId: string, transcript: TranscriptEntry[]) => void
}

export default function SwarmPanel({ running, disabled, result, error, onRun, onSelect }: Props) {
  return (
    <div className="bg-surface border border-surface-border rounded-lg p-4 mt-4">
      <div className="flex items-center justify-between mb-3">
        <div>
          <h2 className="text-sm font-semibold uppercase tracking-wider text-text-secondary">
            Swarm Mode
          </h2>
          <p className="text-xs text-text-secondary mt-1">
            Parallel hunters, one per alert, reading and writing the same graph.
          </p>
        </div>
        <button
          onClick={onRun}
          disabled={disabled}
          className="px-4 py-1.5 bg-surface-border border border-accent-purple/50 text-accent-purple text-xs uppercase tracking-wider hover:bg-accent-purple/20 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {running ? 'Hunting...' : 'Run swarm (3 hunters)'}
        </button>
      </div>

      {running && (
        <p className="text-accent-purple text-xs animate-pulse">
          Hunters are investigating in parallel...
        </p>
      )}
      {error && <p className="text-accent-red text-xs">{`Swarm failed: ${error}`}</p>}

      {result && !running && (
        <div className="space-y-3">
          <div className="grid grid-cols-4 gap-4">
            <div className="text-center">
              <p className="text-2xl font-bold text-accent-purple">{result.num_hunters}</p>
              <p className="text-xs text-text-secondary uppercase">Hunters</p>
            </div>
            <div className="text-center">
              <p className="text-2xl font-bold text-accent-blue">{`${result.avg_recall_latency_ms}ms`}</p>
              <p className="text-xs text-text-secondary uppercase">Avg recall latency</p>
            </div>
            <div className="text-center">
              <p className="text-2xl font-bold text-accent-green">{result.writes_completed}</p>
              <p className="text-xs text-text-secondary uppercase">Concurrent writes</p>
            </div>
            <div className="text-center">
              <p className="text-2xl font-bold text-text-primary">{`${(result.wall_time_ms / 1000).toFixed(1)}s`}</p>
              <p className="text-xs text-text-secondary uppercase">Wall time</p>
            </div>
          </div>

          <div className="grid grid-cols-3 gap-3">
            {result.results.map((h) => (
              <button
                key={`${h.hunter}-${h.alert_id}`}
                onClick={() => h.success && onSelect(h.alert_id, h.transcript || [])}
                disabled={!h.success}
                className="text-left p-3 bg-background border border-surface-border rounded hover:border-accent-purple transition-colors disabled:cursor-default"
              >
                <div className="flex items-center justify-between mb-1">
                  <span className="text-xs font-mono">{h.alert_id}</span>
                  <span className={`text-xs ${h.success ? 'text-accent-green' : 'text-accent-red'}`}>
                    {h.success ? 'done' : 'failed'}
                  </span>
                </div>
                <p className="text-xs text-text-secondary font-mono">{h.hunter}</p>
                {h.success ? (
                  <>
                    <p className="text-xs text-text-secondary font-mono">{h.investigation_id}</p>
                    <p className="text-xs text-accent-blue mt-1">{`Recall latency: ${h.recall_latency_ms}ms`}</p>
                    <p className="text-xs text-text-secondary mt-1">Click to view transcript</p>
                  </>
                ) : (
                  <p className="text-xs text-accent-red mt-1 break-words">{h.error}</p>
                )}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
