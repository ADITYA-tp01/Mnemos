'use client'

import { useEffect, useState } from 'react'

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

export default function MemoryStats() {
  const [stats, setStats] = useState<Stats | null>(null)
  const [previousStats, setPreviousStats] = useState<Stats | null>(null)
  const [growth, setGrowth] = useState(0)

  const fetchStats = () => {
    fetch('/api/memory/stats')
      .then((res) => res.json())
      .then((data) => {
        setPreviousStats(stats)
        setStats(data)
        if (previousStats) {
          const currentTotal = Object.values(data as any).reduce((a: number, b: any) => a + (b || 0), 0)
          const previousTotal = Object.values(previousStats).reduce((a: number, b: any) => a + (b || 0), 0)
          setGrowth(currentTotal - previousTotal)
        }
      })
  }

  useEffect(() => {
    fetchStats()
    const interval = setInterval(fetchStats, 5000) // Auto-refresh every 5s
    return () => clearInterval(interval)
  }, [])

  if (!stats) {
    return <p className="text-xs text-text-secondary">Loading stats...</p>
  }

  return (
    <div className="bg-surface border border-surface-border rounded-lg p-4">
      <div className="flex items-center justify-between mb-3">
        <h2 className="text-sm font-semibold uppercase tracking-wider text-text-secondary">
          Memory Stats
        </h2>
        {growth > 0 && (
          <span className="text-xs text-accent-green">
            +{growth} nodes
          </span>
        )}
      </div>
      <div className="grid grid-cols-4 gap-4">
        <div className="text-center">
          <p className="text-2xl font-bold text-accent-blue">{stats.ThreatActor + stats.TTP + stats.IoC + stats.Asset}</p>
          <p className="text-xs text-text-secondary uppercase">Semantic</p>
        </div>
        <div className="text-center">
          <p className="text-2xl font-bold text-accent-orange">{stats.Investigation + stats.Alert + stats.Action}</p>
          <p className="text-xs text-text-secondary uppercase">Episodic</p>
        </div>
        <div className="text-center">
          <p className="text-2xl font-bold text-accent-purple">{stats.Playbook}</p>
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