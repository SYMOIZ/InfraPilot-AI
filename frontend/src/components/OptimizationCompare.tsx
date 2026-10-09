import type { CompareResponse, OptimizationProposal } from '../types'
import { ArchitectureCanvas } from './ArchitectureCanvas'
import { EmptyState } from './EmptyState'

interface OptimizationCompareProps {
  proposal: OptimizationProposal | null
  compare: CompareResponse | null
  loadingOptimize?: boolean
  loadingCompare?: boolean
  onOptimize: () => void
  onCompare: () => void
}

export function OptimizationCompare({
  proposal,
  compare,
  loadingOptimize = false,
  loadingCompare = false,
  onOptimize,
  onCompare,
}: OptimizationCompareProps) {
  if (!proposal) {
    return (
      <EmptyState
        title="No optimization yet"
        description="Run optimization to produce an improved architecture proposal from the backend. The UI does not invent changes."
        action={
          <button type="button" className="btn" onClick={onOptimize} disabled={loadingOptimize}>
            {loadingOptimize ? 'Optimizing…' : 'Run optimization'}
          </button>
        }
      />
    )
  }

  const original = compare?.original ?? proposal.original
  const optimized = compare?.optimized ?? proposal.optimized
  const changes = compare?.changes?.length ? compare.changes : proposal.changes

  return (
    <div className="anim-rise">
      <div className="section-head">
        <div>
          <h2>Optimization & comparison</h2>
          <p>{proposal.summary || 'Original vs optimized architecture from the API.'}</p>
        </div>
        <div className="actions-row" style={{ marginTop: 0 }}>
          <button
            type="button"
            className="btn btn-secondary"
            onClick={onOptimize}
            disabled={loadingOptimize}
          >
            {loadingOptimize ? 'Re-running…' : 'Re-run optimize'}
          </button>
          <button
            type="button"
            className="btn"
            onClick={onCompare}
            disabled={loadingCompare}
          >
            {loadingCompare ? 'Comparing…' : 'Refresh compare'}
          </button>
        </div>
      </div>

      <p className="muted">{proposal.cost_notes}</p>

      {(compare?.original_scores || compare?.optimized_scores) && (
        <div className="compare-grid" style={{ marginBottom: '1.25rem' }}>
          <div className="panel">
            <h3>Original scores</h3>
            {compare.original_scores ? (
              <ScoreSummary scores={compare.original_scores} />
            ) : (
              <p className="muted">Not available</p>
            )}
          </div>
          <div className="panel">
            <h3>Optimized scores</h3>
            {compare.optimized_scores ? (
              <ScoreSummary scores={compare.optimized_scores} />
            ) : (
              <p className="muted">Not available</p>
            )}
          </div>
        </div>
      )}

      <div className="compare-grid">
        <div>
          <h3>Original</h3>
          <ArchitectureCanvas architecture={original} readOnly />
        </div>
        <div>
          <h3>Optimized</h3>
          <ArchitectureCanvas architecture={optimized} readOnly />
        </div>
      </div>

      <div className="panel" style={{ marginTop: '1.25rem' }}>
        <h3>Changes</h3>
        {changes.length === 0 ? (
          <p className="muted">No change list returned.</p>
        ) : (
          <ul className="changes-list">
            {changes.map((c, i) => (
              <li key={`${c.change_type}-${i}`}>
                <strong>{c.change_type}</strong>
                {c.service_id ? ` · ${c.service_id}` : ''}: {c.description}
                <br />
                <span className="muted">{c.rationale}</span>
                {c.impact_categories.length > 0 ? (
                  <>
                    <br />
                    <span className="muted">
                      Impact: {c.impact_categories.join(', ')}
                    </span>
                  </>
                ) : null}
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  )
}

function ScoreSummary({
  scores,
}: {
  scores: NonNullable<CompareResponse['original_scores']>
}) {
  return (
    <div className="score-grid" style={{ margin: 0 }}>
      <div className="score-cell">
        <div className="value">{scores.overall.toFixed(1)}</div>
        <div className="label">Overall</div>
      </div>
      <div className="score-cell">
        <div className="value">{scores.categories.security.toFixed(1)}</div>
        <div className="label">Security</div>
      </div>
      <div className="score-cell">
        <div className="value">{scores.categories.reliability.toFixed(1)}</div>
        <div className="label">Reliability</div>
      </div>
    </div>
  )
}
