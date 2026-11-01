import { NextRequest, NextResponse } from 'next/server'

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url)
  const alertId = searchParams.get('alertId')

  if (!alertId) {
    return NextResponse.json({ error: 'alertId is required' }, { status: 400 })
  }

  try {
    const response = await fetch(`http://localhost:8000/api/investigate/${alertId}/transcript`)
    const data = await response.json()
    return NextResponse.json(data)
  } catch (error) {
    return NextResponse.json({ error: 'Failed to fetch transcript' }, { status: 500 })
  }
}