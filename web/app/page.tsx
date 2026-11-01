'use client'

import dynamic from 'next/dynamic'
import AlertFeed from '@/app/components/AlertFeed'
import Transcript from '@/app/components/Transcript'
import MemoryGraph from '@/app/components/MemoryGraph'
import RecallInspector from '@/app/components/RecallInspector'
import MemoryStats from '@/app/components/MemoryStats'
import SessionHeader from '@/app/components/SessionHeader'
import { useState, useCallback } from 'react'

export default function Home() {
  const [session, setSession] = useState({
    sessionId: '',
    sessionStart: '',
    isFreshSession: true,
    previousSessionCount: 0,
  })
  const [selectedAlert, setSelectedAlert] = useState<string | null>(null)
  const [showToast, setShowToast] = useState(false)
  const [toastMessage, setToastMessage] = useState('')

  const handleInvestigate = useCallback((alertId: string) => {
    setSelectedAlert(alertId)
  }, [])

  const handleRestart = useCallback(() => {
    fetch('/api/restart', { method: 'POST' })
      .then((res) => res.json())
      .then((data) => {
        setSession({
          sessionId: data.session_id,
          sessionStart: data.session_start,
          isFreshSession: true,
          previousSessionCount: data.previous_session_count,
        })
        setToastMessage('Agent restarted — memory preserved')
        setShowToast(true)
        setTimeout(() => setShowToast(false), 3000)
      })
  }, [])

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
        <MemoryStats />

        {/* 4-Panel Layout */}
        <div className="grid grid-cols-4 gap-4 mt-4">
          {/* Panel 1: Alert Feed */}
          <div className="bg-surface border border-surface-border rounded-lg p-4">
            <h2 className="text-sm font-semibold uppercase tracking-wider text-text-secondary mb-3">
              Alert Feed
            </h2>
            <AlertFeed onInvestigate={handleInvestigate} />
          </div>

          {/* Panel 2: Transcript */}
          <div className="bg-surface border border-surface-border rounded-lg p-4">
            <h2 className="text-sm font-semibold uppercase tracking-wider text-text-secondary mb-3">
              Transcript
            </h2>
            <Transcript alertId={selectedAlert} />
          </div>

          {/* Panel 3: Memory Graph */}
          <div className="bg-surface border border-surface-border rounded-lg p-4">
            <h2 className="text-sm font-semibold uppercase tracking-wider text-text-secondary mb-3">
              Memory Graph
            </h2>
            <MemoryGraph />
          </div>

          {/* Panel 4: Recall Inspector */}
          <div className="bg-surface border border-surface-border rounded-lg p-4">
            <h2 className="text-sm font-semibold uppercase tracking-wider text-text-secondary mb-3">
              Recall Inspector
            </h2>
            <RecallInspector />
          </div>
        </div>
      </main>
    </div>
  )
}