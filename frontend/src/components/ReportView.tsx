import type { ReportResponse } from '../types'
import { EmptyState } from './EmptyState'
import { ExportActions } from './ExportActions'

interface ReportViewProps {
  report: ReportResponse | null
  loading?: boolean
  projectId: string
  onLoad: () => void
}

export function ReportView({ report, loading = false, projectId, onLoad }: ReportViewProps) {
  if (!report) {
    return (
      <EmptyState
        title="Report not loaded"
        description="Fetch the generated report from the API when architecture and evaluation data are ready."
        action={
          <button type="button" className="btn" onClick={onLoad} disabled={loading}>
            {loading ? 'Loading…' : 'Load report'}
          </button>
        }
      />
    )
  }

  return (
    <div className="anim-rise">
      <div className="section-head">
        <div>
          <h2>{report.title}</h2>
          <p className="muted" style={{ margin: 0 }}>
            Generated {new Date(report.generated_at).toLocaleString()}
          </p>
        </div>
        <button type="button" className="btn btn-secondary" onClick={onLoad} disabled={loading}>
          Refresh
        </button>
      </div>

      <div className="panel report-block">
        <h3>Executive summary</h3>
        <p style={{ margin: 0 }}>{report.executive_summary || 'No summary provided.'}</p>
      </div>

      {report.requirements ? (
        <div className="panel report-block">
          <h3>Requirements</h3>
          <p>
            <strong>Purpose:</strong> {report.requirements.purpose}
          </p>
          <p className="muted" style={{ margin: 0 }}>
            {report.requirements.workload} · {report.requirements.region} ·{' '}
            {report.requirements.availability} availability · budget {report.requirements.budget}
          </p>
        </div>
      ) : null}

      {report.architecture ? (
        <div className="panel report-block">
          <h3>Architecture</h3>
          <p style={{ margin: 0 }}>
            {report.architecture.name} — {report.architecture.nodes.length} services,{' '}
            {report.architecture.edges.length} connections
            {report.architecture.confirmed ? ' (confirmed)' : ''}
          </p>
        </div>
      ) : null}

      {report.evaluation ? (
        <div className="panel report-block">
          <h3>Evaluation</h3>
          <p>
            Overall score: <strong>{report.evaluation.scores.overall}</strong>
          </p>
          <p style={{ margin: 0 }}>{report.evaluation.summary}</p>
        </div>
      ) : null}

      {report.optimization ? (
        <div className="panel report-block">
          <h3>Optimization</h3>
          <p style={{ margin: 0 }}>{report.optimization.summary}</p>
        </div>
      ) : null}

      <div className="panel">
        <h3>Export</h3>
        <p className="muted">Download artifacts produced by the backend exporters.</p>
        <ExportActions projectId={projectId} />
      </div>
    </div>
  )
}
