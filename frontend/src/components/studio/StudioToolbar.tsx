interface StudioToolbarProps {
  projectName: string
  saving: boolean
  dirty: boolean
  evaluating: boolean
  agentOpen: boolean
  onSave: () => void
  onEvaluate: () => void
  onExport: (kind: 'drawio' | 'png' | 'excel') => void
  onToggleAgent: () => void
}

export function StudioToolbar({
  projectName,
  saving,
  dirty,
  evaluating,
  agentOpen,
  onSave,
  onEvaluate,
  onExport,
  onToggleAgent,
}: StudioToolbarProps) {
  return (
    <header className="studio-toolbar">
      <div className="studio-toolbar-brand">
        <span className="studio-logo">
          InfraPilot <em>AI</em>
        </span>
        <span className="studio-project-name" title={projectName}>
          {projectName}
        </span>
        <span className={`studio-save-status${dirty ? ' dirty' : ''}`}>
          {saving ? 'Saving…' : dirty ? 'Unsaved' : 'Saved'}
        </span>
      </div>
      <div className="studio-toolbar-actions">
        <button type="button" className="btn btn-sm btn-secondary" onClick={onSave} disabled={saving}>
          {saving ? 'Saving…' : 'Save'}
        </button>
        <button
          type="button"
          className="btn btn-sm"
          onClick={onEvaluate}
          disabled={evaluating}
        >
          {evaluating ? 'Evaluating…' : 'Evaluate'}
        </button>
        <div className="studio-export-menu">
          <button type="button" className="btn btn-sm btn-ghost" onClick={() => onExport('drawio')}>
            Export
          </button>
          <div className="studio-export-dropdown">
            <button type="button" onClick={() => onExport('drawio')}>
              draw.io
            </button>
            <button type="button" onClick={() => onExport('png')}>
              PNG
            </button>
            <button type="button" onClick={() => onExport('excel')}>
              Excel
            </button>
          </div>
        </div>
        <button
          type="button"
          className={`btn btn-sm${agentOpen ? '' : ' btn-secondary'}`}
          onClick={onToggleAgent}
          aria-pressed={agentOpen}
        >
          AI Agent
        </button>
      </div>
    </header>
  )
}
