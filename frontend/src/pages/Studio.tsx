import { useCallback, useEffect, useRef, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { api, ApiError } from '../api/client'
import type { CatalogService } from '../catalog/services'
import { AgentPanel } from '../components/studio/AgentPanel'
import { ArchitectureFlow } from '../components/studio/ArchitectureFlow'
import { mergeArchitectures } from '../components/studio/architectureConvert'
import { ServicePalette } from '../components/studio/ServicePalette'
import { StudioToolbar } from '../components/studio/StudioToolbar'
import { ErrorState } from '../components/ErrorState'
import { LoadingState } from '../components/LoadingState'
import type { Architecture, EvaluationReport, Project } from '../types'

function emptyArchitecture(name: string): Architecture {
  return {
    id: crypto.randomUUID(),
    name,
    nodes: [],
    edges: [],
    confirmed: false,
    source: 'hand',
    metadata: {},
  }
}

export function Studio() {
  const { projectId = '' } = useParams()
  const [project, setProject] = useState<Project | null>(null)
  const [architecture, setArchitecture] = useState<Architecture | null>(null)
  const [syncKey, setSyncKey] = useState(0)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [saving, setSaving] = useState(false)
  const [dirty, setDirty] = useState(false)
  const [evaluating, setEvaluating] = useState(false)
  const [exportingGif, setExportingGif] = useState(false)
  const [agentOpen, setAgentOpen] = useState(() =>
    typeof window !== 'undefined' ? window.innerWidth >= 960 : true,
  )
  const [addRequest, setAddRequest] = useState<CatalogService | null>(null)
  const [toast, setToast] = useState<string | null>(null)

  const architectureRef = useRef(architecture)
  architectureRef.current = architecture
  const dirtyRef = useRef(false)
  const saveTimer = useRef<number | null>(null)

  const load = useCallback(async () => {
    if (!projectId) return
    setLoading(true)
    setError(null)
    try {
      const p = await api.getProject(projectId)
      setProject(p)
      const arch = p.architecture ?? emptyArchitecture(p.name)
      setArchitecture(arch)
      setSyncKey((k) => k + 1)
      setDirty(false)
      dirtyRef.current = false
    } catch (err) {
      setError(errMessage(err))
    } finally {
      setLoading(false)
    }
  }, [projectId])

  useEffect(() => {
    void load()
  }, [load])

  const persist = useCallback(
    async (arch: Architecture, confirmed = true) => {
      if (!projectId) return
      setSaving(true)
      try {
        const toSave = { ...arch, confirmed, source: arch.source || 'hand' }
        await api.confirmArchitecture(projectId, {
          architecture: toSave,
          confirmed,
        })
        setDirty(false)
        dirtyRef.current = false
      } catch (err) {
        setToast(errMessage(err))
      } finally {
        setSaving(false)
      }
    },
    [projectId],
  )

  const scheduleSave = useCallback(
    (arch: Architecture) => {
      if (saveTimer.current) window.clearTimeout(saveTimer.current)
      saveTimer.current = window.setTimeout(() => {
        void persist(arch)
      }, 2000)
    },
    [persist],
  )

  useEffect(() => {
    return () => {
      if (saveTimer.current) window.clearTimeout(saveTimer.current)
    }
  }, [])

  const onArchitectureChange = useCallback(
    (next: Architecture) => {
      setArchitecture(next)
      setDirty(true)
      dirtyRef.current = true
      scheduleSave(next)
    },
    [scheduleSave],
  )

  const applyArchitecture = useCallback(
    (incoming: Architecture, mode: 'replace' | 'merge') => {
      const next =
        mode === 'merge' ? mergeArchitectures(architectureRef.current, incoming) : incoming
      setArchitecture(next)
      setSyncKey((k) => k + 1)
      setDirty(true)
      dirtyRef.current = true
      scheduleSave(next)
    },
    [scheduleSave],
  )

  async function handleSave() {
    if (!architecture) return
    if (saveTimer.current) window.clearTimeout(saveTimer.current)
    await persist(architecture)
    setToast('Saved')
  }

  async function handleEvaluate() {
    if (!projectId || !architecture) return
    setEvaluating(true)
    setAgentOpen(true)
    try {
      await persist(architecture)
      const report = await api.evaluate(projectId)
      setProject((p) => (p ? { ...p, evaluation: report } : p))
      setToast(`Evaluation complete — overall ${Math.round(report.scores.overall)}`)
    } catch (err) {
      setToast(errMessage(err))
    } finally {
      setEvaluating(false)
    }
  }

  async function handleExport(kind: 'drawio' | 'png' | 'excel' | 'gif') {
    if (!projectId || !architecture) return
    try {
      await persist(architecture)
      if (kind === 'gif') {
        setExportingGif(true)
        setToast('Recording data-travel GIF…')
        const el = document.querySelector('.studio-canvas-host .react-flow') as HTMLElement | null
        if (!el) throw new Error('Canvas not ready')
        const { downloadBlob, exportCanvasGif } = await import('../utils/exportGif')
        const blob = await exportCanvasGif(el, { frames: 10, delayMs: 140 })
        const safeName = (project?.name || projectId).replace(/[^\w.-]+/g, '_')
        downloadBlob(blob, `${safeName}-architecture.gif`)
        setToast('GIF downloaded')
      } else if (kind === 'drawio') await api.exportDrawio(projectId)
      else if (kind === 'png') await api.exportPng(projectId)
      else await api.exportExcel(projectId)
    } catch (err) {
      setToast(errMessage(err))
    } finally {
      setExportingGif(false)
    }
  }

  useEffect(() => {
    if (!toast) return
    const t = window.setTimeout(() => setToast(null), 3200)
    return () => window.clearTimeout(t)
  }, [toast])

  if (loading) {
    return (
      <div className="studio-boot">
        <LoadingState label="Opening studio…" />
      </div>
    )
  }

  if (error || !project) {
    return (
      <div className="studio-boot">
        <ErrorState message={error ?? 'Project not found'} onRetry={() => void load()} />
        <Link to="/dashboard" className="btn btn-secondary" style={{ marginTop: '1rem' }}>
          Back to dashboard
        </Link>
      </div>
    )
  }

  return (
    <div className={`studio-shell${agentOpen ? ' agent-open' : ''}`}>
      <StudioToolbar
        projectName={project.name}
        saving={saving}
        dirty={dirty}
        evaluating={evaluating}
        exportingGif={exportingGif}
        agentOpen={agentOpen}
        onSave={() => void handleSave()}
        onEvaluate={() => void handleEvaluate()}
        onExport={(k) => void handleExport(k)}
        onToggleAgent={() => setAgentOpen((o) => !o)}
      />

      <div className="studio-body">
        <ServicePalette onAddService={(s) => setAddRequest(s)} />

        <ArchitectureFlow
          architecture={architecture}
          syncKey={syncKey}
          onArchitectureChange={onArchitectureChange}
          addRequest={addRequest}
          onAddRequestHandled={() => setAddRequest(null)}
        />

        <AgentPanel
          projectId={project.id}
          open={agentOpen}
          onClose={() => setAgentOpen(false)}
          currentArchitecture={architecture}
          onApplyArchitecture={applyArchitecture}
          onEvaluateDone={(report: EvaluationReport) => {
            setProject((p) => (p ? { ...p, evaluation: report } : p))
          }}
        />
      </div>

      {toast ? (
        <div className="studio-toast" role="status">
          {toast}
        </div>
      ) : null}
    </div>
  )
}

function errMessage(err: unknown): string {
  if (err instanceof ApiError) return err.message
  if (err instanceof Error) return err.message
  return 'Something went wrong'
}
