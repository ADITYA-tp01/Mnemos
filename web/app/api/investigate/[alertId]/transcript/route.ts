import { proxyToBackend } from '@/lib/backend'

export const dynamic = 'force-dynamic'

export async function GET(
  _request: Request,
  { params }: { params: { alertId: string } }
) {
  return proxyToBackend(`/investigate/${encodeURIComponent(params.alertId)}/transcript`)
}
