import { proxyToBackend } from '@/lib/backend'

export const dynamic = 'force-dynamic'

export async function POST(request: Request) {
  const body = await request.text()
  return proxyToBackend('/swarm/hunt', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: body || undefined,
  })
}
