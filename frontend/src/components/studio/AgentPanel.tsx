import { useState } from 'react'
import { api, ApiError } from '../../api/client'
import type {
  Architecture,
  EvaluationFinding,
  EvaluationReport,
  OptimizationChange,
  OptimizationProposal,
} from '../../types'
import { AiSupportBadge } from './AiSupportBadge'

type AgentTab = 'assist' | 'evaluate' | 'optimize'

interface AgentPanelProps {
  projectId: string
  open: boolean
  onClose: () => void
  currentArchitecture: Architecture | null
  onApplyArchitecture: (architecture: Architecture, mode: 'replace' | 'merge') => void
  onEvaluateDone: (report: EvaluationReport) => void
}

export function AgentPanel({
  projectId,
  open,
  onClose,
  currentArchitecture,
  onApplyArchitecture,
  onEvaluateDone,
}: AgentPanelProps) {
  const [tab, setTab] = useState<AgentTab>('assist')
  const [prompt, setPrompt] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [findings, setFindings] = useState<EvaluationFinding[]>([])
  const [evalSummary, setEvalSummary] = useState<string | null>(null)
  const [proposal, setProposal] = useState<OptimizationProposal | null>(null)
  const [pendingArch, setPendingArch] = useState<Architecture | null>(null)

  async function askAgent() {
    if (!prompt.trim()) return
    setBusy(true)
    setError(null)
    setPendingArch(null)
    try {
      const project = await api.generate(projectId, {
        regenerate: true,
        prompt: prompt.trim(),
      })
      if (project.architecture) {
        setPendingArch(project.architecture)
        setTab('assist')
      }
    } catch (err) {
      setError(errMessage(err))
    } finally {
      setBusy(false)
    }
  }

  async function runEvaluate() {
    setBusy(true)
    setError(null)
    try {
      if (currentArchitecture) {
        await api.confirmArchitecture(projectId, {
          architecture: currentArchitecture,
          confirmed: true,
        })
      }
      const report = await api.evaluate(projectId)
      setFindings(report.findings)
      setEvalSummary(report.summary)
      onEvaluateDone(report)
      setTab('evaluate')
    } catch (err) {
      setError(errMessage(err))
    } finally {
      setBusy(false)
    }
  }

  async function runOptimize() {
    setBusy(true)
    setError(null)
    try {
      if (currentArchitecture) {
        await api.confirmArchitecture(projectId, {
          architecture: currentArchitecture,
          confirmed: true,
        })
      }
      const result = await api.optimize(projectId)
      setProposal(result)
      setTab('optimize')
    } catch (err) {
      setError(errMessage(err))
    } finally {
      setBusy(false)
    }
  }

  if (!open) return null

  return (
    <aside className="studio-agent" aria-label="Official AI Support">
      <div className="studio-agent-head">
        <div>
          <h2>AI Support</h2>
          <p className="studio-agent-note">Official · optional — design by hand anytime</p>
        </div>
        <button type="button" className="btn btn-ghost btn-sm" onClick={onClose} aria-label="Close AI Support">
          ✕
        </button>
      </div>

      <AiSupportBadge variant="full" />

      <div className="studio-agent-tabs" role="tablist">
        {(['assist', 'evaluate', 'optimize'] as AgentTab[]).map((t) => (
          <button
            key={t}
            type="button"
            role="tab"
            aria-selected={tab === t}
            className={`studio-agent-tab${tab === t ? ' active' : ''}`}
            onClick={() => setTab(t)}
          >
            {t === 'assist' ? 'Propose' : t === 'evaluate' ? 'Evaluate' : 'Optimize'}
          </button>
        ))}
      </div>

      <div className="studio-agent-body">
        {error ? (
          <p className="studio-agent-error" role="alert">
            {error}
          </p>
        ) : null}

        {tab === 'assist' ? (
          <div className="studio-agent-section">
            <label htmlFor="agent-prompt">Describe what you need</label>
            <textarea
              id="agent-prompt"
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              placeholder="e.g. Serverless API with DynamoDB and Cognito auth"
              rows={4}
            />
            <button
              type="button"
              className="btn btn-sm"
              disabled={busy || !prompt.trim()}
              onClick={() => void askAgent()}
            >
              {busy ? 'Working…' : 'Ask AI Support to propose'}
            </button>

            {pendingArch ? (
              <div className="studio-agent-propose">
                <p>
                  AI Support proposed <strong>{pendingArch.nodes.length}</strong> services and{' '}
                  <strong>{pendingArch.edges.length}</strong> connections.
                </p>
                <div className="studio-agent-propose-actions">
                  <button
                    type="button"
                    className="btn btn-sm"
                    onClick={() => {
                      onApplyArchitecture(pendingArch, 'replace')
                      setPendingArch(null)
                    }}
                  >
                    Replace canvas
                  </button>
                  <button
                    type="button"
                    className="btn btn-sm btn-secondary"
                    onClick={() => {
                      onApplyArchitecture(pendingArch, 'merge')
                      setPendingArch(null)
                    }}
                  >
                    Merge onto canvas
                  </button>
                </div>
              </div>
            ) : null}
          </div>
        ) : null}

        {tab === 'evaluate' ? (
          <div className="studio-agent-section">
            <button type="button" className="btn btn-sm" disabled={busy} onClick={() => void runEvaluate()}>
              {busy ? 'Running…' : 'Run evaluation'}
            </button>
            {evalSummary ? <p className="muted">{evalSummary}</p> : null}
            <ul className="studio-findings">
              {findings.map((f) => (
                <li key={f.id} className={`studio-finding status-${f.status.replace(/\s+/g, '')}`}>
                  <span className="studio-finding-title">{f.title}</span>
                  <span className="studio-finding-meta">
                    {f.status} · {f.severity}
                  </span>
                  <span className="studio-finding-msg">{f.message}</span>
                </li>
              ))}
            </ul>
            {!busy && findings.length === 0 && !evalSummary ? (
              <p className="muted">Save a diagram, then run evaluation for findings.</p>
            ) : null}
          </div>
        ) : null}

        {tab === 'optimize' ? (
          <div className="studio-agent-section">
            <button type="button" className="btn btn-sm" disabled={busy} onClick={() => void runOptimize()}>
              {busy ? 'Running…' : 'Run optimize'}
            </button>
            {proposal ? (
              <>
                <p className="muted">{proposal.summary}</p>
                <ul className="studio-changes">
                  {proposal.changes.map((c: OptimizationChange, i: number) => (
                    <li key={`${c.change_type}-${i}`}>
                      <strong>{c.change_type}</strong>: {c.description}
                    </li>
                  ))}
                </ul>
                <button
                  type="button"
                  className="btn btn-sm"
                  onClick={() => onApplyArchitecture(proposal.optimized, 'replace')}
                >
                  Apply optimized
                </button>
              </>
            ) : (
              <p className="muted">Optimize suggests improvements after you have an architecture.</p>
            )}
          </div>
        ) : null}
      </div>
    </aside>
  )
}

function errMessage(err: unknown): string {
  if (err instanceof ApiError) return err.message
  if (err instanceof Error) return err.message
  return 'Request failed'
}
