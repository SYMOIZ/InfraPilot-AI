import type { Edge } from '@xyflow/react'
import type { Architecture, ArchitectureEdge, ArchitectureNode } from '../../types'
import type { AwsFlowNode, AwsNodeData } from './AwsNode'

export function architectureToFlow(
  architecture: Architecture | null | undefined,
  onLabelChange: (nodeId: string, label: string) => void,
): { nodes: AwsFlowNode[]; edges: Edge[] } {
  const nodes: AwsFlowNode[] = (architecture?.nodes ?? []).map((n, i) => ({
    id: n.id,
    type: 'aws' as const,
    position: {
      x: n.x ?? 80 + (i % 4) * 200,
      y: n.y ?? 80 + Math.floor(i / 4) * 120,
    },
    data: {
      service_id: n.service_id,
      label: n.label,
      props: n.props ?? {},
      onLabelChange,
    } satisfies AwsNodeData,
  }))

  const edges: Edge[] = (architecture?.edges ?? []).map((e, i) => ({
    id: e.id ?? `e_${e.from}_${e.to}_${i}`,
    source: e.from,
    target: e.to,
    label: e.label ?? undefined,
  }))

  return { nodes, edges }
}

export function flowToArchitecture(
  nodes: AwsFlowNode[],
  edges: Edge[],
  base: Architecture | null | undefined,
): Architecture {
  const archNodes: ArchitectureNode[] = nodes.map((n) => ({
    id: n.id,
    service_id: n.data.service_id,
    label: n.data.label,
    props: n.data.props ?? {},
    x: Math.round(n.position.x),
    y: Math.round(n.position.y),
  }))

  const archEdges: ArchitectureEdge[] = edges.map((e) => ({
    id: e.id,
    from: e.source,
    to: e.target,
    label: typeof e.label === 'string' ? e.label : null,
  }))

  return {
    id: base?.id ?? crypto.randomUUID(),
    name: base?.name ?? 'Untitled Architecture',
    nodes: archNodes,
    edges: archEdges,
    confirmed: base?.confirmed ?? false,
    source: base?.source && base.source !== 'generated' ? base.source : 'hand',
    metadata: base?.metadata ?? {},
  }
}

export function mergeArchitectures(
  current: Architecture | null,
  incoming: Architecture,
): Architecture {
  const existingIds = new Set((current?.nodes ?? []).map((n) => n.id))
  const offset = (current?.nodes.length ?? 0) > 0 ? 40 : 0
  const mergedNodes: ArchitectureNode[] = [
    ...(current?.nodes ?? []),
    ...incoming.nodes
      .filter((n) => !existingIds.has(n.id))
      .map((n, i) => ({
        ...n,
        x: (n.x ?? 100) + 220 + offset,
        y: (n.y ?? 80) + i * 24,
      })),
  ]
  const nodeIdSet = new Set(mergedNodes.map((n) => n.id))
  const existingEdgeKeys = new Set(
    (current?.edges ?? []).map((e) => `${e.from}->${e.to}`),
  )
  const mergedEdges: ArchitectureEdge[] = [
    ...(current?.edges ?? []),
    ...incoming.edges.filter((e) => {
      const key = `${e.from}->${e.to}`
      if (existingEdgeKeys.has(key)) return false
      return nodeIdSet.has(e.from) && nodeIdSet.has(e.to)
    }),
  ]
  return {
    id: current?.id ?? incoming.id,
    name: current?.name ?? incoming.name,
    nodes: mergedNodes,
    edges: mergedEdges,
    confirmed: false,
    source: 'hand',
    metadata: { ...(current?.metadata ?? {}), ...(incoming.metadata ?? {}) },
  }
}
