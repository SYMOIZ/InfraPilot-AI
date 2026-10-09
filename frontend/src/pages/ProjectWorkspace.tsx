import { useCallback, useEffect, useMemo, useState } from 'react'
import { Link, useParams, useSearchParams } from 'react-router-dom'
import { api, ApiError } from '../api/client'
import { ArchitectureCanvas } from '../components/ArchitectureCanvas'
import { ClarificationPanel } from '../components/ClarificationPanel'
import { ErrorState } from '../components/ErrorState'
import { EvaluationResults } from '../components/EvaluationResults'
import { LoadingState } from '../components/LoadingState'
import { OptimizationCompare } from '../components/OptimizationCompare'
import { ReportView } from '../components/ReportView'
import { RequirementsForm } from '../components/RequirementsForm'
import { UploadPanel } from '../components/UploadPanel'
import { WizardSteps } from '../components/WizardSteps'
import type {
  Architecture,
  ClarificationResponse,
  CompareResponse,
  Project,
  ReportResponse,
  Requirements,
  WorkflowStep,
} from '../types'

const STEP_ORDER: WorkflowStep[] = [
  'requirements',
  'clarify',
  'architecture',
  'upload',
  'evaluate',
  'optimize',
  'report',
]

function isStep(value: string | null): value is WorkflowStep {
  return STEP_ORDER.includes(value as WorkflowStep)
}

export function ProjectWorkspace() {
  const { projectId = '' } = useParams()
  const [searchParams, setSearchParams] = useSearchParams()

  const [project, setProject] = useState<Project | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)

  const [clarify, setClarify] = useState<ClarificationResponse | null>(null)
  const [draftArchitecture, setDraftArchitecture] = useState<Architecture | null>(null)
  const [compare, setCompare] = useState<CompareResponse | null>(null)
  const [report, setReport] = useState<ReportResponse | null>(null)

  const stepParam = searchParams.get('step')
  const step: WorkflowStep = isStep(stepParam) ? stepParam : 'requirements'

  const setStep = useCallback(
    (next: WorkflowStep) => {
      setSearchParams({ step: next }, { replace: true })
    },
    [setSearchParams],
  )

  const loadProject = useCallback(async () => {
    if (!projectId) return
    setLoading(true)
    setError(null)
    try {
      const p = await api.getProject(projectId)
      setProject(p)
      setDraftArchitecture(p.architecture ?? null)
      if (p.optimization) {
        try {
          const c = await api.compare(projectId)
          setCompare(c)
        } catch {
          setCompare(null)
        }
      }
    } catch (err) {
      setError(messageOf(err))
    } finally {
      setLoading(false)
    }
  }, [projectId])

  useEffect(() => {
    void loadProject()
  }, [loadProject])

  const unlocked = useMemo(() => {
    const set = new Set<WorkflowStep>(['requirements'])
    if (!project) return set
    if (project.requirements) {
      set.add('clarify')
      set.add('architecture')
      set.add('upload')
    }
    if (project.architecture) {
      set.add('evaluate')
    }
    if (project.evaluation || project.architecture?.confirmed) {
      set.add('optimize')
      set.add('report')
    }
    if (project.optimization) {
      set.add('optimize')
      set.add('report')
    }
    if (project.evaluation) {
      set.add('report')
    }
    // Always allow navigating to unlocked workflow stages once requirements exist
    if (project.architecture) {
      set.add('optimize')
      set.add('report')
    }
    return set
  }, [project])

  async function withBusy(fn: () => Promise<void>) {
    setBusy(true)
    setError(null)
    try {
      await fn()
    } catch (err) {
      setError(messageOf(err))
    } finally {
      setBusy(false)
    }
  }

  async function saveRequirements(requirements: Requirements) {
    await withBusy(async () => {
      const p = await api.putRequirements(projectId, requirements)
      setProject(p)
      const clarification = await api.clarify(projectId, { answers: {} })
      setClarify(clarification)
      if (clarification.questions.length > 0) {
        setStep('clarify')
      } else {
        setStep('architecture')
      }
    })
  }

  async function submitClarification(answers: Record<string, string>) {
    await withBusy(async () => {
      const clarification = await api.clarify(projectId, { answers })
      setClarify(clarification)
      const p = await api.getProject(projectId)
      setProject(p)
      if (clarification.questions.length === 0) {
        setStep('architecture')
      }
    })
  }

  async function generateArchitecture(regenerate = false) {
    await withBusy(async () => {
      const p = await api.generate(projectId, { regenerate })
      setProject(p)
      setDraftArchitecture(p.architecture ?? null)
      setStep('architecture')
    })
  }

  async function confirmArchitecture() {
    if (!draftArchitecture) return
    await withBusy(async () => {
      const p = await api.confirmArchitecture(projectId, {
        architecture: draftArchitecture,
        confirmed: true,
      })
      setProject(p)
      setDraftArchitecture(p.architecture ?? null)
    })
  }

  async function uploadFile(file: File) {
    await withBusy(async () => {
      const p = await api.upload(projectId, file)
      setProject(p)
      setDraftArchitecture(p.architecture ?? null)
      if (p.architecture) setStep('architecture')
    })
  }

  async function runEvaluate() {
    await withBusy(async () => {
      const evaluation = await api.evaluate(projectId)
      setProject((prev) => (prev ? { ...prev, evaluation } : prev))
      setStep('evaluate')
    })
  }

  async function runOptimize() {
    await withBusy(async () => {
      const optimization = await api.optimize(projectId)
      setProject((prev) =>
        prev
          ? {
              ...prev,
              optimization,
              optimized_architecture: optimization.optimized,
            }
          : prev,
      )
      const c = await api.compare(projectId)
      setCompare(c)
      setStep('optimize')
    })
  }

  async function runCompare() {
    await withBusy(async () => {
      const c = await api.compare(projectId)
      setCompare(c)
    })
  }

  async function loadReport() {
    await withBusy(async () => {
      const r = await api.getReport(projectId)
      setReport(r)
      setStep('report')
    })
  }

  if (loading) return <LoadingState label="Loading project…" />
  if (error && !project) {
    return <ErrorState message={error} onRetry={() => void loadProject()} />
  }
  if (!project) {
    return <ErrorState message="Project not found." />
  }

  return (
    <div>
      <div className="workspace-title anim-rise">
        <div>
          <p className="muted" style={{ margin: '0 0 0.25rem' }}>
            <Link to="/dashboard">Dashboard</Link> / Project
          </p>
          <h1>{project.name}</h1>
          {project.description ? <p className="muted">{project.description}</p> : null}
        </div>
      </div>

      <WizardSteps current={step} unlocked={unlocked} onSelect={setStep} />

      {error ? (
        <div style={{ marginBottom: '1rem' }}>
          <ErrorState message={error} />
        </div>
      ) : null}

      {busy ? (
        <div className="loading-inline" style={{ marginBottom: '1rem' }} role="status">
          <span className="spinner" aria-hidden="true" />
          Working…
        </div>
      ) : null}

      {step === 'requirements' ? (
        <section>
          <div className="section-head">
            <div>
              <h2>Business requirements</h2>
              <p>Capture workload intent before generating an architecture.</p>
            </div>
          </div>
          <RequirementsForm
            initial={project.requirements}
            submitting={busy}
            onSubmit={(r) => void saveRequirements(r)}
          />
        </section>
      ) : null}

      {step === 'clarify' ? (
        <section>
          <div className="section-head">
            <div>
              <h2>Clarification</h2>
              <p>Answer only when the API returns follow-up questions.</p>
            </div>
            <button
              type="button"
              className="btn btn-secondary btn-sm"
              disabled={busy}
              onClick={() =>
                void withBusy(async () => {
                  const clarification = await api.clarify(projectId, { answers: {} })
                  setClarify(clarification)
                })
              }
            >
              Refresh questions
            </button>
          </div>
          <ClarificationPanel
            questions={clarify?.questions ?? []}
            message={clarify?.message}
            submitting={busy}
            onSubmit={(answers) => void submitClarification(answers)}
            onSkip={() => setStep('architecture')}
          />
        </section>
      ) : null}

      {step === 'architecture' ? (
        <section>
          <div className="section-head">
            <div>
              <h2>Architecture</h2>
              <p>Generate, inspect, rearrange, and confirm the service graph.</p>
            </div>
            <div className="actions-row" style={{ marginTop: 0 }}>
              <button
                type="button"
                className="btn"
                disabled={busy || !project.requirements}
                onClick={() => void generateArchitecture(Boolean(project.architecture))}
              >
                {project.architecture ? 'Regenerate' : 'Generate architecture'}
              </button>
              <button
                type="button"
                className="btn btn-secondary"
                disabled={busy || !draftArchitecture}
                onClick={() => void confirmArchitecture()}
              >
                Confirm architecture
              </button>
            </div>
          </div>

          {!draftArchitecture ? (
            <div className="state-box">
              <h3>No architecture yet</h3>
              <p>
                Save requirements first, then generate from the API — or upload a draw.io
                diagram on the Upload step.
              </p>
            </div>
          ) : (
            <ArchitectureCanvas
              architecture={draftArchitecture}
              onChange={setDraftArchitecture}
            />
          )}
        </section>
      ) : null}

      {step === 'upload' ? (
        <section>
          <div className="section-head">
            <div>
              <h2>Upload diagram</h2>
              <p>Import an existing draw.io/XML architecture, then confirm services.</p>
            </div>
          </div>
          <UploadPanel uploading={busy} onUpload={(f) => void uploadFile(f)} />
          {project.uploaded_files.length > 0 ? (
            <p className="muted" style={{ marginTop: '1rem' }}>
              Uploaded: {project.uploaded_files.join(', ')}
            </p>
          ) : null}
          {draftArchitecture ? (
            <div style={{ marginTop: '1.25rem' }}>
              <h3>Confirm extracted services</h3>
              <ArchitectureCanvas
                architecture={draftArchitecture}
                onChange={setDraftArchitecture}
              />
              <div className="actions-row">
                <button
                  type="button"
                  className="btn"
                  disabled={busy}
                  onClick={() => void confirmArchitecture()}
                >
                  Confirm uploaded architecture
                </button>
              </div>
            </div>
          ) : null}
        </section>
      ) : null}

      {step === 'evaluate' ? (
        <EvaluationResults
          report={project.evaluation ?? null}
          loading={busy}
          onEvaluate={() => void runEvaluate()}
        />
      ) : null}

      {step === 'optimize' ? (
        <OptimizationCompare
          proposal={project.optimization ?? null}
          compare={compare}
          loadingOptimize={busy}
          loadingCompare={busy}
          onOptimize={() => void runOptimize()}
          onCompare={() => void runCompare()}
        />
      ) : null}

      {step === 'report' ? (
        <ReportView
          report={report}
          loading={busy}
          projectId={projectId}
          onLoad={() => void loadReport()}
        />
      ) : null}
    </div>
  )
}

function messageOf(err: unknown): string {
  if (err instanceof ApiError) return err.message
  if (err instanceof Error) return err.message
  return 'Request failed'
}
