'use client'

import { useEffect, useState } from 'react'

interface Alert {
  id: string
  type: string
  severity: string
  status: string
}

interface Props {
  onInvestigate: (alertId: string) => void
  refreshKey: number
  busy: boolean
  activeAlert: string | null
}

const severityColors = {
  critical: 'bg-accent-red',
  high: 'bg-accent-orange',
  medium: 'bg-accent-blue',
  low: 'bg-accent-green',
}

export default function AlertFeed({ onInvestigate, refreshKey, busy, activeAlert }: Props) {
  const [alerts, setAlerts] = useState<Alert[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false
    fetch('/api/alerts')
      .then(async (res) => {
        const data = await res.json()
        if (!res.ok) throw new Error(data.detail || data.error || `Request failed (${res.status})`)
        if (!cancelled) {
          setAlerts(data.alerts || [])
          setError(null)
        }
      })
      .catch((err) => {
        if (!cancelled) setError(err.message)
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [refreshKey])

  if (loading) {
    return <p className="text-text-secondary text-xs">Loading alerts...</p>
  }

  return (
    <div className="space-y-2">
      {error && <p className="text-accent-red text-xs">Error loading alerts: {error}</p>}
      {alerts.map((alert) => {
        const status = busy && alert.id === activeAlert ? 'investigating' : alert.status
        return (
          <button
            key={alert.id}
            onClick={() => onInvestigate(alert.id)}
            disabled={busy}
            className="w-full text-left p-3 bg-background border border-surface-border rounded hover:border-accent-blue transition-colors disabled:opacity-60 disabled:cursor-not-allowed"
          >
            <div className="flex items-center justify-between mb-1">
              <span className="text-xs font-mono">{alert.id}</span>
              <span className={`w-2 h-2 rounded-full ${severityColors[alert.severity as keyof typeof severityColors] || 'bg-accent-blue'}`} />
            </div>
            <p className="text-xs text-text-secondary truncate">{alert.type}</p>
            <div className="flex items-center justify-between mt-1">
              <span className="text-xs uppercase text-text-secondary">{alert.severity}</span>
              <span className={`text-xs ${status === 'investigating' ? 'text-accent-orange animate-pulse' : status === 'investigated' ? 'text-accent-green' : 'text-text-secondary'}`}>
                {status}
              </span>
            </div>
          </button>
        )
      })}
      {!error && alerts.length === 0 && (
        <p className="text-text-secondary text-xs">No alerts found — run scripts/seed_scenario.py</p>
      )}
    </div>
  )
}
