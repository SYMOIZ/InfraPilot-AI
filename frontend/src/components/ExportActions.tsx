import { useState } from 'react'
import { api, ApiError } from '../api/client'

interface ExportActionsProps {
  projectId: string
}

type ExportKind = 'drawio' | 'png' | 'excel'

export function ExportActions({ projectId }: ExportActionsProps) {
  const [busy, setBusy] = useState<ExportKind | null>(null)
  const [error, setError] = useState<string | null>(null)

  async function run(kind: ExportKind) {
    setBusy(kind)
    setError(null)
    try {
      if (kind === 'drawio') await api.exportDrawio(projectId)
      else if (kind === 'png') await api.exportPng(projectId)
      else await api.exportExcel(projectId)
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err.message
          : err instanceof Error
            ? err.message
            : 'Export failed',
      )
    } finally {
      setBusy(null)
    }
  }

  return (
    <div>
      <div className="actions-row" style={{ marginTop: 0 }}>
        <button
          type="button"
          className="btn btn-secondary"
          disabled={busy !== null}
          onClick={() => void run('drawio')}
        >
          {busy === 'drawio' ? 'Exporting…' : 'Export draw.io'}
        </button>
        <button
          type="button"
          className="btn btn-secondary"
          disabled={busy !== null}
          onClick={() => void run('png')}
        >
          {busy === 'png' ? 'Exporting…' : 'Export PNG'}
        </button>
        <button
          type="button"
          className="btn btn-secondary"
          disabled={busy !== null}
          onClick={() => void run('excel')}
        >
          {busy === 'excel' ? 'Exporting…' : 'Export Excel'}
        </button>
      </div>
      {error ? (
        <p className="hint" role="alert" style={{ color: 'var(--fail)', marginTop: '0.75rem' }}>
          {error}
        </p>
      ) : null}
    </div>
  )
}
