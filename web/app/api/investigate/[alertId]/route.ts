import { NextRequest, NextResponse } from 'next/server'

export async function POST(request: NextRequest) {
  const { alertId } = await request.json()

  if (!alertId) {
    return NextResponse.json({ error: 'alertId is required' }, { status: 400 })
  }

  try {
    const response = await fetch(`http://localhost:8000/api/investigate/${alertId}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
    })
    const data = await response.json()
    return NextResponse.json(data)
  } catch (error) {
    return NextResponse.json({ error: 'Failed to investigate alert' }, { status: 500 })
  }
}