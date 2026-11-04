import { NextResponse } from 'next/server'

// Read at request time (routes use `dynamic = 'force-dynamic'`), so docker-compose's
// BACKEND_URL applies at runtime. Defaults to a locally running backend.
export const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8000'

export async function proxyToBackend(path: string, init: RequestInit = {}) {
  try {
    const res = await fetch(`${BACKEND_URL}${path}`, { ...init, cache: 'no-store' })
    const data = await res.json().catch(() => ({ error: `Backend returned ${res.status}` }))
    return NextResponse.json(data, { status: res.status })
  } catch {
    return NextResponse.json(
      { error: `Backend unreachable at ${BACKEND_URL}` },
      { status: 502 }
    )
  }
}
