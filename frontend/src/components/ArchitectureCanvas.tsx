import {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
  type PointerEvent as ReactPointerEvent,
  type WheelEvent as ReactWheelEvent,
} from 'react'
import type { Architecture, ArchitectureNode } from '../types'

const NODE_W = 140
const NODE_H = 48

interface ArchitectureCanvasProps {
  architecture: Architecture
  onChange?: (architecture: Architecture) => void
  readOnly?: boolean
}

function layoutNodes(nodes: ArchitectureNode[]): ArchitectureNode[] {
  return nodes.map((node, i) => {
    if (node.x != null && node.y != null) return node
    const col = i % 3
    const row = Math.floor(i / 3)
    return {
      ...node,
      x: 40 + col * 200,
      y: 40 + row * 100,
    }
  })
}

export function ArchitectureCanvas({
  architecture,
  onChange,
  readOnly = false,
}: ArchitectureCanvasProps) {
  const [nodes, setNodes] = useState(() => layoutNodes(architecture.nodes))
  const nodesRef = useRef(nodes)
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [scale, setScale] = useState(1)
  const [pan, setPan] = useState({ x: 0, y: 0 })
  const dragRef = useRef<{
    mode: 'node' | 'pan'
    id?: string
    startX: number
    startY: number
    origX: number
    origY: number
    origPanX: number
    origPanY: number
  } | null>(null)
  const [dragging, setDragging] = useState(false)

  useEffect(() => {
    nodesRef.current = nodes
  }, [nodes])

  useEffect(() => {
    setNodes(layoutNodes(architecture.nodes))
  }, [architecture.id, architecture.nodes])

  const selected = useMemo(
    () => nodes.find((n) => n.id === selectedId) ?? null,
    [nodes, selectedId],
  )

  const emitChange = useCallback(
    (nextNodes: ArchitectureNode[]) => {
      if (!onChange) return
      onChange({ ...architecture, nodes: nextNodes })
    },
    [architecture, onChange],
  )

  function onPointerDown(e: ReactPointerEvent, mode: 'node' | 'pan', id?: string) {
    if (readOnly && mode === 'node') {
      if (id) setSelectedId(id)
      return
    }
    const target = e.currentTarget as Element
    target.setPointerCapture?.(e.pointerId)
    const node = id ? nodes.find((n) => n.id === id) : null
    dragRef.current = {
      mode,
      id,
      startX: e.clientX,
      startY: e.clientY,
      origX: node?.x ?? 0,
      origY: node?.y ?? 0,
      origPanX: pan.x,
      origPanY: pan.y,
    }
    setDragging(true)
    if (id) setSelectedId(id)
  }

  function onPointerMove(e: ReactPointerEvent) {
    const drag = dragRef.current
    if (!drag) return
    const dx = (e.clientX - drag.startX) / scale
    const dy = (e.clientY - drag.startY) / scale

    if (drag.mode === 'pan') {
      setPan({
        x: drag.origPanX + (e.clientX - drag.startX),
        y: drag.origPanY + (e.clientY - drag.startY),
      })
      return
    }

    if (!drag.id || readOnly) return
    setNodes((prev) =>
      prev.map((n) =>
        n.id === drag.id
          ? { ...n, x: drag.origX + dx, y: drag.origY + dy }
          : n,
      ),
    )
  }

  function onPointerUp() {
    if (dragRef.current?.mode === 'node' && !readOnly) {
      emitChange(nodesRef.current)
    }
    dragRef.current = null
    setDragging(false)
  }

  function onWheel(e: ReactWheelEvent) {
    e.preventDefault()
    const delta = e.deltaY > 0 ? -0.08 : 0.08
    setScale((s) => Math.min(2.2, Math.max(0.4, s + delta)))
  }

  function zoom(delta: number) {
    setScale((s) => Math.min(2.2, Math.max(0.4, s + delta)))
  }

  function resetView() {
    setScale(1)
    setPan({ x: 0, y: 0 })
  }

  const nodePos = useMemo(() => {
    const map = new Map<string, { x: number; y: number }>()
    for (const n of nodes) {
      map.set(n.id, { x: n.x ?? 0, y: n.y ?? 0 })
    }
    return map
  }, [nodes])

  return (
    <div>
      <div className="canvas-toolbar">
        <button type="button" className="btn btn-secondary btn-sm" onClick={() => zoom(0.1)}>
          Zoom in
        </button>
        <button type="button" className="btn btn-secondary btn-sm" onClick={() => zoom(-0.1)}>
          Zoom out
        </button>
        <button type="button" className="btn btn-ghost btn-sm" onClick={resetView}>
          Reset view
        </button>
        <span className="muted" aria-live="polite">
          {Math.round(scale * 100)}%
          {architecture.confirmed ? ' · Confirmed' : ''}
          {architecture.source ? ` · ${architecture.source}` : ''}
        </span>
      </div>

      <div
        className="canvas-wrap"
        role="application"
        aria-label={`Architecture canvas: ${architecture.name}`}
        onPointerMove={onPointerMove}
        onPointerUp={onPointerUp}
        onPointerLeave={onPointerUp}
        onWheel={onWheel}
      >
        <svg
          className={`canvas-svg${dragging ? ' dragging' : ''}`}
          onPointerDown={(e) => {
            if ((e.target as Element).closest?.('.arch-node')) return
            onPointerDown(e, 'pan')
          }}
        >
          <defs>
            <marker
              id="arrowhead"
              markerWidth="8"
              markerHeight="8"
              refX="6"
              refY="3"
              orient="auto"
            >
              <path d="M0,0 L6,3 L0,6 Z" fill="#7a8d98" />
            </marker>
          </defs>
          <g transform={`translate(${pan.x},${pan.y}) scale(${scale})`}>
            {architecture.edges.map((edge, i) => {
              const from = nodePos.get(edge.from)
              const to = nodePos.get(edge.to)
              if (!from || !to) return null
              const x1 = from.x + NODE_W / 2
              const y1 = from.y + NODE_H / 2
              const x2 = to.x + NODE_W / 2
              const y2 = to.y + NODE_H / 2
              return (
                <line
                  key={edge.id ?? `${edge.from}-${edge.to}-${i}`}
                  className="arch-edge"
                  x1={x1}
                  y1={y1}
                  x2={x2}
                  y2={y2}
                />
              )
            })}
            {nodes.map((node) => {
              const x = node.x ?? 0
              const y = node.y ?? 0
              const isSelected = node.id === selectedId
              return (
                <g
                  key={node.id}
                  className={`arch-node${isSelected ? ' selected' : ''}`}
                  transform={`translate(${x},${y})`}
                  onPointerDown={(e) => {
                    e.stopPropagation()
                    onPointerDown(e, 'node', node.id)
                  }}
                  role="button"
                  tabIndex={0}
                  aria-pressed={isSelected}
                  aria-label={node.label}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' || e.key === ' ') {
                      e.preventDefault()
                      setSelectedId(node.id)
                    }
                  }}
                >
                  <rect width={NODE_W} height={NODE_H} rx={6} ry={6} />
                  <text x={10} y={22} fontWeight={600}>
                    {truncate(node.label, 18)}
                  </text>
                  <text x={10} y={38} fill="#7a8d98" fontSize={10}>
                    {truncate(node.service_id, 20)}
                  </text>
                </g>
              )
            })}
          </g>
        </svg>
      </div>

      {selected ? (
        <div className="node-detail panel" style={{ marginTop: '0.75rem' }}>
          <h3>{selected.label}</h3>
          <p className="muted" style={{ margin: 0 }}>
            Service: {selected.service_id} · Position: ({Math.round(selected.x ?? 0)},{' '}
            {Math.round(selected.y ?? 0)})
          </p>
        </div>
      ) : (
        <p className="muted" style={{ marginTop: '0.75rem' }}>
          Select a node to inspect. Drag nodes to rearrange
          {readOnly ? ' (read-only view)' : ''}. Scroll or use zoom controls.
        </p>
      )}
    </div>
  )
}

function truncate(text: string, max: number): string {
  return text.length > max ? `${text.slice(0, max - 1)}…` : text
}
