import { useCallback, useEffect, useState, type FormEvent } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import { api, ApiError, isDemoMode } from '../api/client'
import { ConfirmDialog } from '../components/ConfirmDialog'
import { EmptyState } from '../components/EmptyState'
import { ErrorState } from '../components/ErrorState'
import { LoadingState } from '../components/LoadingState'
import type { ProjectSummary } from '../types'

export function Dashboard() {
  const navigate = useNavigate()
  const [searchParams, setSearchParams] = useSearchParams()
  const [projects, setProjects] = useState<ProjectSummary[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const [creating, setCreating] = useState(false)
  const [demoBusy, setDemoBusy] = useState(false)
  const [deleteTarget, setDeleteTarget] = useState<ProjectSummary | null>(null)
  const [deleting, setDeleting] = useState(false)

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const list = await api.listProjects()
      setProjects(list)
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err.message
          : err instanceof Error
            ? err.message
            : 'Failed to load projects',
      )
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    void load()
  }, [load])

  useEffect(() => {
    if (searchParams.get('demo') !== '1' || !isDemoMode()) return
    let cancelled = false
    ;(async () => {
      setDemoBusy(true)
      setError(null)
      try {
        const sample = await api.getDemoSample()
        const project = await api.createProject({
          name: 'Demo: Sample Web App',
          description: sample.disclaimer,
        })
        await api.putRequirements(project.id, sample.requirements)
        await api.confirmArchitecture(project.id, {
          architecture: sample.architecture,
          confirmed: false,
        })
        if (!cancelled) {
          setSearchParams({}, { replace: true })
          navigate(`/projects/${project.id}?step=architecture`)
        }
      } catch (err) {
        if (!cancelled) {
          setError(
            err instanceof ApiError
              ? err.message
              : err instanceof Error
                ? err.message
                : 'Demo setup failed',
          )
          setSearchParams({}, { replace: true })
        }
      } finally {
        if (!cancelled) setDemoBusy(false)
      }
    })()
    return () => {
      cancelled = true
    }
  }, [searchParams, setSearchParams, navigate])

  async function handleCreate(e: FormEvent) {
    e.preventDefault()
    if (!name.trim()) return
    setCreating(true)
    setError(null)
    try {
      const project = await api.createProject({
        name: name.trim(),
        description: description.trim() || null,
      })
      navigate(`/projects/${project.id}`)
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err.message
          : err instanceof Error
            ? err.message
            : 'Could not create project',
      )
    } finally {
      setCreating(false)
    }
  }

  async function confirmDelete() {
    if (!deleteTarget) return
    setDeleting(true)
    try {
      await api.deleteProject(deleteTarget.id)
      setDeleteTarget(null)
      await load()
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err.message
          : err instanceof Error
            ? err.message
            : 'Delete failed',
      )
      setDeleteTarget(null)
    } finally {
      setDeleting(false)
    }
  }

  const recentReports = projects.filter((p) => p.has_evaluation)

  return (
    <div>
      <div className="section-head anim-rise">
        <div>
          <h1>Dashboard</h1>
          <p>Create a project, continue a workflow, or open recent evaluation reports.</p>
        </div>
        {isDemoMode() ? (
          <button
            type="button"
            className="btn btn-secondary"
            disabled={demoBusy}
            onClick={() => setSearchParams({ demo: '1' })}
          >
            {demoBusy ? 'Opening demo…' : 'Open demo'}
          </button>
        ) : null}
      </div>

      <form className="create-bar panel anim-rise anim-delay-1" onSubmit={handleCreate}>
        <div className="field">
          <label htmlFor="project-name">Project name</label>
          <input
            id="project-name"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="e.g. Checkout API redesign"
            required
          />
        </div>
        <div className="field">
          <label htmlFor="project-desc">Description (optional)</label>
          <input
            id="project-desc"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="Short context"
          />
        </div>
        <button type="submit" className="btn" disabled={creating || !name.trim()}>
          {creating ? 'Creating…' : 'Create project'}
        </button>
      </form>

      {error ? <ErrorState message={error} onRetry={() => void load()} /> : null}
      {loading ? <LoadingState label="Loading projects…" /> : null}

      {!loading && !error && projects.length === 0 ? (
        <EmptyState
          title="No projects yet"
          description="Create your first project to capture requirements and generate an architecture."
        />
      ) : null}

      {!loading && projects.length > 0 ? (
        <section className="anim-rise anim-delay-2" aria-labelledby="projects-heading">
          <h2 id="projects-heading">Projects</h2>
          <div className="project-list">
            {projects.map((p) => (
              <div key={p.id} className="panel panel-interactive project-row">
                <Link to={`/projects/${p.id}`} className="project-row" style={{ flex: 1, padding: 0, border: 0, boxShadow: 'none', background: 'transparent' }}>
                  <div>
                    <strong>{p.name}</strong>
                    {p.description ? (
                      <p className="muted" style={{ margin: '0.2rem 0 0' }}>
                        {p.description}
                      </p>
                    ) : null}
                    <p className="muted" style={{ margin: '0.35rem 0 0', fontSize: '0.8rem' }}>
                      Updated {new Date(p.updated_at).toLocaleString()}
                    </p>
                  </div>
                  <div className="project-meta" aria-label="Progress">
                    <span className={`chip${p.has_requirements ? ' on' : ''}`}>Requirements</span>
                    <span className={`chip${p.has_architecture ? ' on' : ''}`}>Architecture</span>
                    <span className={`chip${p.has_evaluation ? ' on' : ''}`}>Evaluation</span>
                    <span className={`chip${p.has_optimization ? ' on' : ''}`}>Optimize</span>
                  </div>
                </Link>
                <button
                  type="button"
                  className="btn btn-ghost btn-sm"
                  aria-label={`Delete ${p.name}`}
                  onClick={() => setDeleteTarget(p)}
                >
                  Delete
                </button>
              </div>
            ))}
          </div>
        </section>
      ) : null}

      {!loading && recentReports.length > 0 ? (
        <section style={{ marginTop: '2rem' }} aria-labelledby="reports-heading">
          <h2 id="reports-heading">Recent reports</h2>
          <div className="project-list">
            {recentReports.map((p) => (
              <Link
                key={`report-${p.id}`}
                to={`/projects/${p.id}?step=report`}
                className="panel panel-interactive project-row"
              >
                <div>
                  <strong>{p.name}</strong>
                  <p className="muted" style={{ margin: '0.2rem 0 0' }}>
                    Open evaluation report
                  </p>
                </div>
              </Link>
            ))}
          </div>
        </section>
      ) : null}

      <ConfirmDialog
        open={deleteTarget !== null}
        title="Delete project?"
        message={
          deleteTarget
            ? `This permanently removes “${deleteTarget.name}” and its stored data from the backend.`
            : ''
        }
        confirmLabel={deleting ? 'Deleting…' : 'Delete'}
        danger
        onCancel={() => setDeleteTarget(null)}
        onConfirm={() => void confirmDelete()}
      />
    </div>
  )
}
