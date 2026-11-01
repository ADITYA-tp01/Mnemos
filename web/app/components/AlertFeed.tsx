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
}

const severityColors = {
  critical: 'bg-accent-red',
  high: 'bg-accent-orange',
  medium: 'bg-accent-blue',
  low: 'bg-accent-green',
}

export default function AlertFeed({ onInvestigate }: Props) {
  const [alerts, setAlerts] = useState<Alert[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetch('/api/alerts')
      .then((res) => res.json())
      .then((data) => {
        setAlerts(data.alerts || [])
        setLoading(false)
      })
      .catch(() => setLoading(false))
  }, [])

  if (loading) {
    return <p className="text-text-secondary text-xs">Loading alerts...</p>
  }

  return (
    <div className="space-y-2">
      {alerts.map((alert) => (
        <button
          key={alert.id}
          onClick={() => onInvestigate(alert.id)}
          className="w-full text-left p-3 bg-background border border-surface-border rounded hover:border-accent-blue transition-colors"
        >
          <div className="flex items-center justify-between mb-1">
            <span className="text-xs font-mono">{alert.id}</span>
            <span className={`w-2 h-2 rounded-full ${severityColors[alert.severity as keyof typeof severityColors] || 'bg-accent-blue'}`} />
          </div>
          <p className="text-xs text-text-secondary truncate">{alert.type}</p>
          <div className="flex items-center justify-between mt-1">
            <span className="text-xs uppercase text-text-secondary">{alert.severity}</span>
            <span className={`text-xs ${alert.status === 'investigating' ? 'text-accent-orange' : alert.status === 'investigated' ? 'text-accent-green' : 'text-text-secondary'}`}>
              {alert.status}
            </span>
          </div>
        </button>
      ))}
      {alerts.length === 0 && (
        <p className="text-text-secondary text-xs">No alerts found</p>
      )}
    </div>
  )
}