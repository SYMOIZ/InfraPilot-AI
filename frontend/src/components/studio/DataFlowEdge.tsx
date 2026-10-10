import { BaseEdge, EdgeLabelRenderer, getBezierPath, type EdgeProps } from '@xyflow/react'

/** Animated “data travel” edge — packet moves along the connection. */
export function DataFlowEdge({
  id,
  sourceX,
  sourceY,
  targetX,
  targetY,
  sourcePosition,
  targetPosition,
  style,
  markerEnd,
  label,
  selected,
}: EdgeProps) {
  const [edgePath, labelX, labelY] = getBezierPath({
    sourceX,
    sourceY,
    targetX,
    targetY,
    sourcePosition,
    targetPosition,
  })

  return (
    <>
      <BaseEdge
        id={id}
        path={edgePath}
        markerEnd={markerEnd}
        style={{
          ...style,
          stroke: selected ? '#0d9488' : '#64748b',
          strokeWidth: selected ? 2.5 : 2,
        }}
      />
      <circle r={4.5} fill="#0891b2" className="data-flow-packet">
        <animateMotion dur="1.6s" repeatCount="indefinite" path={edgePath} />
      </circle>
      <circle r={3} fill="#ccfbf1" opacity={0.9} className="data-flow-packet">
        <animateMotion dur="1.6s" begin="0.8s" repeatCount="indefinite" path={edgePath} />
      </circle>
      {label ? (
        <EdgeLabelRenderer>
          <div
            className="data-flow-label"
            style={{
              transform: `translate(-50%, -50%) translate(${labelX}px,${labelY}px)`,
            }}
          >
            {String(label)}
          </div>
        </EdgeLabelRenderer>
      ) : null}
    </>
  )
}
