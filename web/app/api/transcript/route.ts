import { NextRequest, NextResponse } from 'next/server'
import { proxyToBackend } from '@/lib/backend'

export const dynamic = 'force-dynamic'

export async function GET(request: NextRequest) {
  const alertId = new URL(request.url).searchParams.get('alertId')

  if (!alertId) {
    return NextResponse.json({ error: 'alertId is required' }, { status: 400 })
  }

  return proxyToBackend(`/investigate/${encodeURIComponent(alertId)}/transcript`)
}
