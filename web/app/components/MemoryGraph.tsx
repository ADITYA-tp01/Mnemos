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

export default function MemoryGraph() {
  const containerRef = useRef<HTMLDivElement>(null)
  const [data, setData] = useState<GraphData | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetch('/api/memory/graph')
      .then((res) => res.json())
      .then((json) => setData(json))
      .catch((err) => setError(err.message))
  }, [])

  useEffect(() => {
    if (!data || !containerRef.current) return

    // Clean up previous instance
    if (containerRef.current) {
      const prevInstance = containerRef.current.dataset.cyref
      if (prevInstance) {
        // Remove old instance (stored globally)
        const oldCy = (window as any).__mnemos_cytoscape_instances?.[prevInstance]
        oldCy?.destroy()
      }
    }

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
            'background-color': (ele: any) => {
              const label = ele.data('label')
              switch (label) {
                case 'ThreatActor': return '#3b82f6'
                case 'TTP': return '#8b5cf6'
                case 'IoC': return '#f59e0b'
                case 'Asset': return '#10b981'
                case 'Alert': return '#ef4444'
                case 'Investigation': return '#06b6d4'
                case 'Playbook': return '#a855f7'
                default: return '#6b7280'
              }
            },
            label: 'data(label)',
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

    // Store for cleanup
    if (containerRef.current) {
      containerRef.current.dataset.cyref = 'main-graph'
      ;(window as any).__mnemos_cytoscape_instances = {
        ...(window as any).__mnemos_cytoscape_instances,
        'main-graph': cy,
      }
    }

    return () => {
      cy.destroy()
    }
  }, [data])

  if (error) {
    return <p className="text-accent-red text-xs">Error loading graph: {error}</p>
  }

  if (!data) {
    return <p className="text-text-secondary text-xs">Loading graph...</p>
  }

  return (
    <div className="h-96 bg-background rounded border border-surface-border overflow-hidden">
      <div ref={containerRef} className="w-full h-full" />
    </div>
  )
}