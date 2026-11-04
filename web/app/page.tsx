'use client'

import AlertFeed from '@/app/components/AlertFeed'
import Transcript from '@/app/components/Transcript'
import MemoryGraph from '@/app/components/MemoryGraph'
import RecallInspector from '@/app/components/RecallInspector'
import MemoryStats from '@/app/components/MemoryStats'
import SessionHeader from '@/app/components/SessionHeader'
import SwarmPanel from '@/app/components/SwarmPanel'
import { useState, useCallback, useEffect } from 'react'
import type { Session, SwarmResult, TranscriptEntry } from '@/lib/types'

const errorMessage = (data: any, status: number) =>
  data?.detail || data?.error || `Request failed (${status})`

export default function Home() {
  const [session, setSession] = useState<Session>({
    sessionId: '',
    sessionStart: '',
    isFreshSession: true,
    previousSessionCount: 0,
  })
  const [selectedAlert, setSelectedAlert] = useState<string | null>(null)
  const [transcript, setTranscript] = useState<TranscriptEntry[]>([])
  const [investigating, setInvestigating] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [refreshKey, setRefreshKey] = useState(0)
  const [swarming, setSwarming] = useState(false)
  const [swarm, setSwarm] = useState<SwarmResult | null>(null)
  const [swarmError, setSwarmError] = useState<string | null>(null)
  const [showToast, setShowToast] = useState(false)
  const [toastMessage, setToastMessage] = useState('')

  // Show the real session in the header on load (not just after the first action)
  useEffect(() => {
    fetch('/api/session')
      .then(async (res) => {
        const data = await res.json()
        if (!res.ok) return
        setSession({
          sessionId: data.session_id,
          sessionStart: data.session_start,
          isFreshSession: data.is_fresh_session,
          previousSessionCount: data.previous_session_count,
        })
      })
      .catch(() => {})
  }, [])

  const flash = useCallback((message: string) => {
    setToastMessage(message)
    setShowToast(true)
    setTimeout(() => setShowToast(false), 3000)
  }, [])

  const handleInvestigate = useCallback(
    async (alertId: string) => {
      if (investigating) return
      setSelectedAlert(alertId)
      setInvestigating(true)
      setError(null)
      setTranscript([])
      try {
        const res = await fetch(`/api/investigate/${encodeURIComponent(alertId)}`, {
          method: 'POST',
        })
        const data = await res.json()
        if (!res.ok) throw new Error(errorMessage(data, res.status))
        setTranscript(data.transcript || [])
        setSession({
          sessionId: data.session_id,
          sessionStart: data.session_start,
          isFreshSession: data.is_fresh_session,
          previousSessionCount: data.previous_session_count,
        })
      } catch (e) {
        setError(e instanceof Error ? e.message : String(e))
      } finally {
        setInvestigating(false)
        setRefreshKey((k) => k + 1)
      }
    },
    [investigating]
  )

  const handleSwarm = useCallback(async () => {
    if (investigating || swarming) return
    setSwarming(true)
    setSwarmError(null)
    try {
      const res = await fetch('/api/swarm', { method: 'POST' })
      const data = await res.json()
      if (!res.ok) throw new Error(errorMessage(data, res.status))
      setSwarm(data)
    } catch (e) {
      setSwarmError(e instanceof Error ? e.message : String(e))
    } finally {
      setSwarming(false)
      setRefreshKey((k) => k + 1)
    }
  }, [investigating, swarming])

  const handleSelectHunter = useCallback((alertId: string, entries: TranscriptEntry[]) => {
    setSelectedAlert(alertId)
    setError(null)
    setTranscript(entries)
  }, [])

  const handleRestart = useCallback(async () => {
    try {
      const res = await fetch('/api/restart', { method: 'POST' })
      const data = await res.json()
      if (!res.ok) throw new Error(errorMessage(data, res.status))
      setSession({
        sessionId: data.session_id,
        sessionStart: data.session_start,
        isFreshSession: true,
        previousSessionCount: data.previous_session_count,
      })
      setTranscript([])
      setSelectedAlert(null)
      setError(null)
      setSwarm(null)
      setSwarmError(null)
      setRefreshKey((k) => k + 1)
      const decay = data.memory_decay
      flash(
        decay
          ? `Agent restarted — memory preserved (${decay.edges_decayed} edges decayed, ${decay.edges_pruned} pruned)`
          : 'Agent restarted — memory preserved'
      )
    } catch (e) {
      flash(`Restart failed: ${e instanceof Error ? e.message : String(e)}`)
    }
  }, [flash])

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b border-surface-border px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <h1 className="text-xl font-bold tracking-wider">MNEMOS</h1>
            <span className="text-xs text-text-secondary uppercase tracking-widest">
              Autonomous Threat Hunter
            </span>
          </div>
          <SessionHeader session={session} onRestart={handleRestart} />
        </div>
      </header>

      {/* Toast */}
      {showToast && (
        <div className="fixed top-20 right-6 z-50 bg-surface border border-accent-green px-4 py-2 rounded">
          <p className="text-accent-green text-sm">{toastMessage}</p>
        </div>
      )}

      {/* Main Content */}
      <main className="p-6">
        {/* Memory Stats Bar */}
        <MemoryStats refreshKey={refreshKey} />

        {/* 4-Panel Layout */}
        <div className="grid grid-cols-4 gap-4 mt-4">
          {/* Panel 1: Alert Feed */}
          <div className="bg-surface border border-surface-border rounded-lg p-4">
            <h2 className="text-sm font-semibold uppercase tracking-wider text-text-secondary mb-3">
              Alert Feed
            </h2>
            <AlertFeed
              onInvestigate={handleInvestigate}
              refreshKey={refreshKey}
              busy={investigating || swarming}
              activeAlert={selectedAlert}
            />
          </div>

          {/* Panel 2: Transcript */}
          <div className="bg-surface border border-surface-border rounded-lg p-4">
            <h2 className="text-sm font-semibold uppercase tracking-wider text-text-secondary mb-3">
              Transcript
            </h2>
            <Transcript
              alertId={selectedAlert}
              entries={transcript}
              loading={investigating}
              error={error}
            />
          </div>

          {/* Panel 3: Memory Graph */}
          <div className="bg-surface border border-surface-border rounded-lg p-4">
            <h2 className="text-sm font-semibold uppercase tracking-wider text-text-secondary mb-3">
              Memory Graph
            </h2>
            <MemoryGraph refreshKey={refreshKey} />
          </div>

          {/* Panel 4: Recall Inspector */}
          <div className="bg-surface border border-surface-border rounded-lg p-4">
            <h2 className="text-sm font-semibold uppercase tracking-wider text-text-secondary mb-3">
              Recall Inspector
            </h2>
            <RecallInspector entries={transcript} />
          </div>
        </div>

        {/* Swarm Mode */}
        <SwarmPanel
          running={swarming}
          disabled={swarming || investigating}
          result={swarm}
          error={swarmError}
          onRun={handleSwarm}
          onSelect={handleSelectHunter}
        />
      </main>
    </div>
  )
}
