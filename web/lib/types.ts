export interface TranscriptEntry {
  step: string
  details: any
  timestamp: string
}

export interface SwarmHunter {
  hunter: string
  alert_id: string
  investigation_id?: string
  recall_latency_ms?: number
  transcript?: TranscriptEntry[]
  success: boolean
  error?: string
}

export interface SwarmResult {
  mode: string
  num_hunters: number
  results: SwarmHunter[]
  total_recall_latency_ms: number
  avg_recall_latency_ms: number
  writes_completed: number
  wall_time_ms: number
  errors: string[]
  success: boolean
}

export interface Session {
  sessionId: string
  sessionStart: string
  isFreshSession: boolean
  previousSessionCount: number
}
