'use client'

import { useCallback, useEffect, useRef, useState } from 'react'

interface Stats {
  ThreatActor: number
  TTP: number
  IoC: number
  Asset: number
  Alert: number
  Investigation: number
  Playbook: number
  Action: number
  edges: number
}

const nodeTotal = (s: Stats) =>
  s.ThreatActor + s.TTP + s.IoC + s.Asset + s.Alert + s.Investigation + s.Playbook + s.Action

export default function MemoryStats({ refreshKey }: { refreshKey: number }) {
  const [stats, setStats] = useState<Stats | null>(null)
  const [growth, setGrowth] = useState(0)
  const [error, setError] = useState<string | null>(null)
  const previousTotal = useRef<number | null>(null)

  const fetchStats = useCallback(() => {
    fetch('/api/memory/stats')
      .then(async (res) => {
        const data = await res.json()
        if (!res.ok) throw new Error(data.detail || data.error || `Request failed (${res.status})`)
        const total = nodeTotal(data as Stats)
        if (previousTotal.current !== null && total > previousTotal.current) {
          setGrowth(total - previousTotal.current)
        }
        previousTotal.current = total
        setStats(data)
        setError(null)
      })
      .catch((err) => setError(err.message))
  }, [])

  useEffect(() => {
    fetchStats()
    const interval = setInterval(fetchStats, 5000) // Auto-refresh every 5s
    return () => clearInterval(interval)
  }, [fetchStats])

  // Refresh immediately after an investigation / restart
  useEffect(() => {
    if (refreshKey > 0) fetchStats()
  }, [refreshKey, fetchStats])

  if (!stats) {
    return error ? (
      <p className="text-xs text-accent-red">{`Error loading stats: ${error}`}</p>
    ) : (
      <p className="text-xs text-text-secondary">Loading stats...</p>
    )
  }

  return (
    <div className="bg-surface border border-surface-border rounded-lg p-4">
      <div className="flex items-center justify-between mb-3">
        <h2 className="text-sm font-semibold uppercase tracking-wider text-text-secondary">
          Memory Stats
        </h2>
        <div className="flex items-center gap-3">
          {error && <span className="text-xs text-accent-red">{`Stale: ${error}`}</span>}
          {growth > 0 && (
            <span className="text-xs text-accent-green">
              {`Memory grew by ${growth} nodes`}
            </span>
          )}
        </div>
      </div>
      <div className="grid grid-cols-4 gap-4">
        <div className="text-center">
          <p className="text-2xl font-bold text-accent-blue">{stats.ThreatActor + stats.TTP + stats.IoC + stats.Asset}</p>
          <p className="text-xs text-text-secondary uppercase">Semantic</p>
        </div>
        <div className="text-center">
          <p className="text-2xl font-bold text-accent-green">{stats.Investigation + stats.Alert}</p>
          <p className="text-xs text-text-secondary uppercase">Episodic</p>
        </div>
        <div className="text-center">
          <p className="text-2xl font-bold text-accent-purple">{stats.Playbook + stats.Action}</p>
          <p className="text-xs text-text-secondary uppercase">Procedural</p>
        </div>
        <div className="text-center">
          <p className="text-2xl font-bold text-text-primary">{stats.edges}</p>
          <p className="text-xs text-text-secondary uppercase">Edges</p>
        </div>
      </div>
    </div>
  )
}
