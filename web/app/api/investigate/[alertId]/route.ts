import { proxyToBackend } from '@/lib/backend'

export const dynamic = 'force-dynamic'

export async function POST(
  _request: Request,
  { params }: { params: { alertId: string } }
) {
  return proxyToBackend(`/investigate/${encodeURIComponent(params.alertId)}`, {
    method: 'POST',
  })
}
