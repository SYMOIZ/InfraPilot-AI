import { memo, useCallback, useEffect, useState, type KeyboardEvent } from 'react'
import { Handle, Position, type Node, type NodeProps } from '@xyflow/react'
import { getService, getServiceColor } from '../../catalog/services'

export type AwsNodeData = {
  service_id: string
  label: string
  props?: Record<string, unknown>
  onLabelChange?: (nodeId: string, label: string) => void
}

export type AwsFlowNode = Node<AwsNodeData, 'aws'>

function AwsNodeComponent({ id, data, selected }: NodeProps<AwsFlowNode>) {
  const service = getService(data.service_id)
  const color = getServiceColor(data.service_id)
  const [editing, setEditing] = useState(false)
  const [draft, setDraft] = useState(data.label)

  useEffect(() => {
    if (!editing) setDraft(data.label)
  }, [data.label, editing])

  const commit = useCallback(() => {
    const next = draft.trim() || data.label
    setDraft(next)
    setEditing(false)
    if (next !== data.label) {
      data.onLabelChange?.(id, next)
    }
  }, [data, draft, id])

  function onKeyDown(e: KeyboardEvent<HTMLInputElement>) {
    if (e.key === 'Enter') {
      e.preventDefault()
      commit()
    } else if (e.key === 'Escape') {
      setDraft(data.label)
      setEditing(false)
    }
  }

  return (
    <div className={`aws-node${selected ? ' selected' : ''}`} style={{ borderLeftColor: color }}>
      <Handle type="target" position={Position.Left} className="aws-handle" />
      <div className="aws-node-body">
        <span className="aws-node-service" style={{ color }}>
          {service?.shortLabel ?? data.service_id}
        </span>
        {editing ? (
          <input
            className="aws-node-label-input nodrag nopan"
            value={draft}
            autoFocus
            onChange={(e) => setDraft(e.target.value)}
            onBlur={commit}
            onKeyDown={onKeyDown}
            aria-label="Node label"
          />
        ) : (
          <button
            type="button"
            className="aws-node-label nodrag"
            onDoubleClick={(e) => {
              e.stopPropagation()
              setEditing(true)
            }}
            title="Double-click to rename"
          >
            {data.label}
          </button>
        )}
      </div>
      <Handle type="source" position={Position.Right} className="aws-handle" />
    </div>
  )
}

export const AwsNode = memo(AwsNodeComponent)
