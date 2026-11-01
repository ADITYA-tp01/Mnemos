import { NextRequest, NextResponse } from 'next/server'

export async function POST() {
  try {
    const response = await fetch('http://localhost:8000/api/agent/restart', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
    })
    const data = await response.json()
    return NextResponse.json(data)
  } catch (error) {
    return NextResponse.json({ error: 'Failed to restart agent' }, { status: 500 })
  }
}