'use client'

interface Session {
  sessionId: string
  sessionStart: string
  isFreshSession: boolean
  previousSessionCount: number
}

interface Props {
  session: Session
  onRestart: () => void
}

export default function SessionHeader({ session, onRestart }: Props) {
  return (
    <div className="flex items-center gap-6">
      <div className="flex items-center gap-2 text-xs">
        <span className="text-text-secondary">Session:</span>
        <span className="font-mono text-accent-blue">{session.sessionId || 'N/A'}</span>
        <span className={`px-2 py-0.5 rounded ${session.isFreshSession ? 'bg-accent-green/20 text-accent-green' : 'bg-accent-orange/20 text-accent-orange'}`}>
          {session.isFreshSession ? 'FRESH' : 'RESUMED'}
        </span>
        {!session.isFreshSession && (
          <span className="text-text-secondary">
            Previous: {session.previousSessionCount}
          </span>
        )}
      </div>
      <button
        onClick={onRestart}
        className="px-4 py-1.5 bg-surface-border border border-accent-orange/50 text-accent-orange text-xs uppercase tracking-wider hover:bg-accent-orange/20 transition-colors"
      >
        Restart Agent
      </button>
    </div>
  )
}