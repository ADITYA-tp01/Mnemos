'use client'

import { useEffect, useRef, useState } from 'react'
import cytoscape from 'cytoscape'

interface GraphData {
  nodes: Array<{
    id: string
    label: string
    properties: Record<string, any>
  }>
  edges: Array<{
    id: string
    source: string
    target: string
    type: string
  }>
}

// Color by memory type: semantic = blue, episodic = green, procedural = purple
const SEMANTIC = ['ThreatActor', 'TTP', 'IoC', 'Asset']
const EPISODIC = ['Alert', 'Investigation']
const PROCEDURAL = ['Playbook', 'Action']

const nodeColor = (label: string) => {
  if (SEMANTIC.includes(label)) return '#3b82f6'
  if (EPISODIC.includes(label)) return '#10b981'
  if (PROCEDURAL.includes(label)) return '#a855f7'
  return '#6b7280'
}

export default function MemoryGraph({ refreshKey }: { refreshKey: number }) {
  const containerRef = useRef<HTMLDivElement>(null)
  const [data, setData] = useState<GraphData | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false
    fetch('/api/memory/graph')
      .then(async (res) => {
        const json = await res.json()
        if (!res.ok) throw new Error(json.detail || json.error || `Request failed (${res.status})`)
        if (!cancelled) {
          setData(json)
          setError(null)
        }
      })
      .catch((err) => {
        if (!cancelled) setError(err.message)
      })
    return () => {
      cancelled = true
    }
  }, [refreshKey])

  useEffect(() => {
    if (!data || !containerRef.current) return

    const cy = cytoscape({
      container: containerRef.current,
      elements: {
        nodes: data.nodes.map((node) => ({
          data: { id: node.id, label: node.label, properties: node.properties },
          classes: node.label.toLowerCase(),
        })),
        edges: data.edges.map((edge) => ({
          data: { id: edge.id, source: edge.source, target: edge.target, type: edge.type },
        })),
      },
      style: [
        {
          selector: 'node',
          style: {
            'background-color': (ele: any) => nodeColor(ele.data('label')),
            label: (ele: any) => {
              const p = ele.data('properties') || {}
              return String(p.name || p.value || p.mitre_id || p.id || ele.data('label'))
            },
            'text-wrap': 'wrap',
            'text-max-width': '120px',
            'text-valign': 'top',
            'text-halign': 'center',
            'font-size': '10px',
            'color': '#f3f4f6',
            shape: 'ellipse',
            width: '40px',
            height: '40px',
          },
        },
        {
          selector: 'edge',
          style: {
            'curve-style': 'bezier',
            'line-color': '#374151',
            'target-arrow-color': '#374151',
            'target-arrow-shape': 'triangle',
            width: '1',
          },
        },
        {
          selector: ':selected',
          style: {
            'border-width': '2px',
            'border-color': '#3b82f6',
          },
        },
      ],
      layout: {
        name: 'cose',
        padding: 20,
        animate: false,
      },
      userZoomingEnabled: true,
      userPanningEnabled: true,
      boxSelectionEnabled: false,
    })

    return () => {
      cy.destroy()
    }
  }, [data])

  if (!data) {
    return error ? (
      <p className="text-accent-red text-xs">Error loading graph: {error}</p>
    ) : (
      <p className="text-text-secondary text-xs">Loading graph...</p>
    )
  }

  return (
    <div>
      <div className="flex gap-3 mb-2 text-xs text-text-secondary">
        <span><span className="inline-block w-2 h-2 rounded-full bg-accent-blue mr-1" />Semantic</span>
        <span><span className="inline-block w-2 h-2 rounded-full bg-accent-green mr-1" />Episodic</span>
        <span><span className="inline-block w-2 h-2 rounded-full bg-accent-purple mr-1" />Procedural</span>
        {error && <span className="text-accent-red ml-auto">Stale: {error}</span>}
      </div>
      <div className="h-96 bg-background rounded border border-surface-border overflow-hidden">
        <div ref={containerRef} className="w-full h-full" />
      </div>
    </div>
  )
}
