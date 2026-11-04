import { proxyToBackend } from '@/lib/backend'

export const dynamic = 'force-dynamic'

export async function POST() {
  return proxyToBackend('/agent/restart', { method: 'POST' })
}
