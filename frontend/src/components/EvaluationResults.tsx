import type { EvaluationFinding, EvaluationReport } from '../types'
import { EmptyState } from './EmptyState'

interface EvaluationResultsProps {
  report: EvaluationReport | null
  loading?: boolean
  onEvaluate: () => void
}

export function EvaluationResults({
  report,
  loading = false,
  onEvaluate,
}: EvaluationResultsProps) {
  if (!report) {
    return (
      <EmptyState
        title="No evaluation yet"
        description="Run evaluation against the confirmed architecture. Results come from the backend rules engine and optional AI gap analysis — nothing is simulated in the UI."
        action={
          <button type="button" className="btn" onClick={onEvaluate} disabled={loading}>
            {loading ? 'Evaluating…' : 'Run evaluation'}
          </button>
        }
      />
    )
  }

  const rulesFindings = report.findings.filter((f) => f.source === 'rules')
  const aiFindings = report.findings.filter((f) => f.source === 'ai')

  return (
    <div className="anim-rise">
      <div className="section-head">
        <div>
          <h2>Evaluation results</h2>
          <p>{report.summary || 'Scores and findings from the latest evaluation run.'}</p>
        </div>
        <button type="button" className="btn btn-secondary" onClick={onEvaluate} disabled={loading}>
          {loading ? 'Re-running…' : 'Re-run evaluation'}
        </button>
      </div>

      <div className="score-grid" aria-label="Category scores">
        <ScoreCell label="Overall" value={report.scores.overall} />
        <ScoreCell label="Security" value={report.scores.categories.security} />
        <ScoreCell label="Cost" value={report.scores.categories.cost} />
        <ScoreCell label="Reliability" value={report.scores.categories.reliability} />
        <ScoreCell label="Scalability" value={report.scores.categories.scalability} />
        <ScoreCell label="Best practices" value={report.scores.categories.best_practices} />
      </div>

      {report.gaps.length > 0 ? (
        <div className="panel" style={{ marginBottom: '1.25rem' }}>
          <h3>Gaps</h3>
          <ul>
            {report.gaps.map((gap) => (
              <li key={gap}>{gap}</li>
            ))}
          </ul>
        </div>
      ) : null}

      <FindingsSection title="Deterministic rule findings" findings={rulesFindings} />
      <FindingsSection title="AI gap findings" findings={aiFindings} emptyHint="No AI findings in this report." />
    </div>
  )
}

function ScoreCell({ label, value }: { label: string; value: number }) {
  return (
    <div className="score-cell">
      <div className="value">{formatScore(value)}</div>
      <div className="label">{label}</div>
    </div>
  )
}

function FindingsSection({
  title,
  findings,
  emptyHint = 'No findings in this group.',
}: {
  title: string
  findings: EvaluationFinding[]
  emptyHint?: string
}) {
  return (
    <section style={{ marginBottom: '1.5rem' }}>
      <h3>{title}</h3>
      {findings.length === 0 ? (
        <p className="muted">{emptyHint}</p>
      ) : (
        <div className="findings-list">
          {findings.map((f) => (
            <article
              key={f.id}
              className={`finding status-${f.status.replace(/\s+/g, '')}`}
            >
              <div className="finding-head">
                <h4>{f.title}</h4>
                <span className={`sev ${f.severity.toLowerCase()}`}>{f.severity}</span>
                <span className={`source-tag ${f.source}`}>{f.source}</span>
                <span className="chip">{f.status}</span>
              </div>
              <p style={{ marginBottom: '0.35rem' }}>{f.message}</p>
              {f.evidence ? (
                <p className="muted" style={{ marginBottom: '0.25rem' }}>
                  <strong>Evidence:</strong> {f.evidence}
                </p>
              ) : null}
              {f.recommendation ? (
                <p className="muted" style={{ margin: 0 }}>
                  <strong>Recommendation:</strong> {f.recommendation}
                </p>
              ) : null}
            </article>
          ))}
        </div>
      )}
    </section>
  )
}

function formatScore(n: number): string {
  if (Number.isInteger(n)) return String(n)
  return n.toFixed(1)
}
