import {
  useCallback,
  useEffect,
  useRef,
  type DragEvent,
} from 'react'
import {
  Background,
  BackgroundVariant,
  Controls,
  MiniMap,
  ReactFlow,
  ReactFlowProvider,
  addEdge,
  useEdgesState,
  useNodesState,
  useReactFlow,
  type Connection,
  type Edge,
  type NodeTypes,
} from '@xyflow/react'
import '@xyflow/react/dist/style.css'

import { getService, type CatalogService } from '../../catalog/services'
import type { Architecture } from '../../types'
import { architectureToFlow, flowToArchitecture } from './architectureConvert'
import { AwsNode, type AwsFlowNode, type AwsNodeData } from './AwsNode'
import { PALETTE_MIME } from './ServicePalette'

const nodeTypes: NodeTypes = { aws: AwsNode }

function newId(prefix: string): string {
  return `${prefix}_${crypto.randomUUID().slice(0, 8)}`
}

interface ArchitectureFlowProps {
  architecture: Architecture | null | undefined
  /** Bump only when loading external architecture (agent/optimize/initial). */
  syncKey: number
  onArchitectureChange: (architecture: Architecture) => void
  addRequest: CatalogService | null
  onAddRequestHandled: () => void
}

function FlowInner({
  architecture,
  syncKey,
  onArchitectureChange,
  addRequest,
  onAddRequestHandled,
}: ArchitectureFlowProps) {
  const { screenToFlowPosition, getViewport } = useReactFlow()
  const skipEmit = useRef(false)
  const baseRef = useRef(architecture)
  baseRef.current = architecture
  const syncArchRef = useRef(architecture)
  syncArchRef.current = architecture

  const labelChangeRef = useRef<(nodeId: string, label: string) => void>(() => undefined)

  const [nodes, setNodes, onNodesChange] = useNodesState<AwsFlowNode>([])
  const [edges, setEdges, onEdgesChange] = useEdgesState<Edge>([])

  labelChangeRef.current = (nodeId, label) => {
    setNodes((nds) =>
      nds.map((n) => (n.id === nodeId ? { ...n, data: { ...n.data, label } } : n)),
    )
  }

  const onLabelChange = useCallback((nodeId: string, label: string) => {
    labelChangeRef.current(nodeId, label)
  }, [])

  useEffect(() => {
    skipEmit.current = true
    const next = architectureToFlow(syncArchRef.current, onLabelChange)
    setNodes(next.nodes)
    setEdges(next.edges)
    const t = window.setTimeout(() => {
      skipEmit.current = false
    }, 0)
    return () => window.clearTimeout(t)
  }, [syncKey, onLabelChange, setNodes, setEdges])

  useEffect(() => {
    if (skipEmit.current) return
    onArchitectureChange(flowToArchitecture(nodes, edges, baseRef.current))
  }, [nodes, edges, onArchitectureChange])

  const onConnect = useCallback(
    (connection: Connection) => {
      setEdges((eds) => addEdge({ ...connection, id: newId('edge') }, eds))
    },
    [setEdges],
  )

  const addServiceAt = useCallback(
    (service: CatalogService, position?: { x: number; y: number }) => {
      const pos =
        position ??
        (() => {
          const vp = getViewport()
          return {
            x: (-vp.x + 420) / vp.zoom,
            y: (-vp.y + 260) / vp.zoom,
          }
        })()

      const id = newId(service.id)
      const data: AwsNodeData = {
        service_id: service.id,
        label: service.shortLabel,
        props: {},
        onLabelChange,
      }
      const node: AwsFlowNode = {
        id,
        type: 'aws',
        position: pos,
        data,
      }
      setNodes((nds) => [...nds, node])
    },
    [getViewport, onLabelChange, setNodes],
  )

  useEffect(() => {
    if (!addRequest) return
    addServiceAt(addRequest)
    onAddRequestHandled()
  }, [addRequest, addServiceAt, onAddRequestHandled])

  const onDragOver = useCallback((e: DragEvent) => {
    e.preventDefault()
    e.dataTransfer.dropEffect = 'copy'
  }, [])

  const onDrop = useCallback(
    (e: DragEvent) => {
      e.preventDefault()
      const serviceId = e.dataTransfer.getData(PALETTE_MIME)
      const service = getService(serviceId)
      if (!service) return
      const position = screenToFlowPosition({ x: e.clientX, y: e.clientY })
      addServiceAt(service, position)
    },
    [addServiceAt, screenToFlowPosition],
  )

  const empty = nodes.length === 0

  return (
    <div className="studio-canvas-host">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onConnect={onConnect}
        onDragOver={onDragOver}
        onDrop={onDrop}
        nodeTypes={nodeTypes}
        fitView={syncKey > 0 && nodes.length > 0}
        fitViewOptions={{ padding: 0.2 }}
        deleteKeyCode={['Backspace', 'Delete']}
        multiSelectionKeyCode="Shift"
        proOptions={{ hideAttribution: true }}
      >
        <Background variant={BackgroundVariant.Dots} gap={18} size={1} color="#c5d4db" />
        <Controls showInteractive={false} />
        <MiniMap
          nodeColor={(n) =>
            getService(String((n.data as AwsNodeData)?.service_id))?.color ?? '#94a3b8'
          }
          maskColor="rgba(15, 28, 36, 0.08)"
        />
      </ReactFlow>
      {empty ? (
        <div className="studio-empty" aria-hidden="true">
          Drag AWS services here to design by hand
        </div>
      ) : null}
    </div>
  )
}

export function ArchitectureFlow(props: ArchitectureFlowProps) {
  return (
    <ReactFlowProvider>
      <FlowInner {...props} />
    </ReactFlowProvider>
  )
}
