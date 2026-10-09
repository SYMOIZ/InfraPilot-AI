import { useState, type FormEvent } from 'react'
import type {
  AvailabilityTarget,
  DataSensitivity,
  Requirements,
  WorkloadType,
} from '../types'

const DEFAULT_REQUIREMENTS: Requirements = {
  purpose: '',
  workload: 'web',
  traffic: 'low',
  data_sensitivity: 'internal',
  availability: 'standard',
  recovery: 'best-effort',
  budget: 'moderate',
  region: 'us-east-1',
  scalability: 'moderate',
  constraints: [],
  notes: '',
}

interface RequirementsFormProps {
  initial?: Requirements | null
  submitting?: boolean
  onSubmit: (requirements: Requirements) => void
}

export function RequirementsForm({
  initial,
  submitting = false,
  onSubmit,
}: RequirementsFormProps) {
  const [form, setForm] = useState<Requirements>(() => ({
    ...DEFAULT_REQUIREMENTS,
    ...initial,
    constraints: initial?.constraints ?? [],
    notes: initial?.notes ?? '',
  }))
  const [constraintsText, setConstraintsText] = useState(
    (initial?.constraints ?? []).join('\n'),
  )

  function update<K extends keyof Requirements>(key: K, value: Requirements[K]) {
    setForm((prev) => ({ ...prev, [key]: value }))
  }

  function handleSubmit(e: FormEvent) {
    e.preventDefault()
    const constraints = constraintsText
      .split('\n')
      .map((s) => s.trim())
      .filter(Boolean)
    onSubmit({
      ...form,
      constraints,
      notes: form.notes?.trim() ? form.notes : null,
    })
  }

  return (
    <form className="panel anim-rise" onSubmit={handleSubmit} noValidate>
      <div className="form-grid">
        <div className="field span-2">
          <label htmlFor="purpose">Purpose</label>
          <textarea
            id="purpose"
            required
            value={form.purpose}
            onChange={(e) => update('purpose', e.target.value)}
            placeholder="What should the system accomplish?"
            aria-describedby="purpose-hint"
          />
          <p id="purpose-hint" className="hint">
            Describe the business outcome, not the AWS services.
          </p>
        </div>

        <div className="field">
          <label htmlFor="workload">Workload</label>
          <select
            id="workload"
            value={form.workload}
            onChange={(e) => update('workload', e.target.value as WorkloadType)}
          >
            <option value="web">Web</option>
            <option value="api">API</option>
            <option value="batch">Batch</option>
            <option value="streaming">Streaming</option>
            <option value="data">Data</option>
            <option value="other">Other</option>
          </select>
        </div>

        <div className="field">
          <label htmlFor="traffic">Traffic</label>
          <input
            id="traffic"
            value={form.traffic}
            onChange={(e) => update('traffic', e.target.value)}
            placeholder="low / medium / high or RPS"
          />
        </div>

        <div className="field">
          <label htmlFor="data_sensitivity">Data sensitivity</label>
          <select
            id="data_sensitivity"
            value={form.data_sensitivity}
            onChange={(e) =>
              update('data_sensitivity', e.target.value as DataSensitivity)
            }
          >
            <option value="public">Public</option>
            <option value="internal">Internal</option>
            <option value="confidential">Confidential</option>
            <option value="regulated">Regulated</option>
          </select>
        </div>

        <div className="field">
          <label htmlFor="availability">Availability</label>
          <select
            id="availability"
            value={form.availability}
            onChange={(e) =>
              update('availability', e.target.value as AvailabilityTarget)
            }
          >
            <option value="standard">Standard</option>
            <option value="high">High</option>
            <option value="critical">Critical</option>
          </select>
        </div>

        <div className="field">
          <label htmlFor="recovery">Recovery</label>
          <input
            id="recovery"
            value={form.recovery}
            onChange={(e) => update('recovery', e.target.value)}
            placeholder="e.g. RPO &lt; 1h, best-effort"
          />
        </div>

        <div className="field">
          <label htmlFor="budget">Budget</label>
          <input
            id="budget"
            value={form.budget}
            onChange={(e) => update('budget', e.target.value)}
            placeholder="low / moderate / high"
          />
        </div>

        <div className="field">
          <label htmlFor="region">Region</label>
          <input
            id="region"
            value={form.region}
            onChange={(e) => update('region', e.target.value)}
            placeholder="us-east-1"
          />
        </div>

        <div className="field">
          <label htmlFor="scalability">Scalability</label>
          <input
            id="scalability"
            value={form.scalability}
            onChange={(e) => update('scalability', e.target.value)}
            placeholder="moderate"
          />
        </div>

        <div className="field span-2">
          <label htmlFor="constraints">Constraints</label>
          <textarea
            id="constraints"
            value={constraintsText}
            onChange={(e) => setConstraintsText(e.target.value)}
            placeholder="One constraint per line"
            aria-describedby="constraints-hint"
          />
          <p id="constraints-hint" className="hint">
            One constraint per line (e.g. Prefer serverless).
          </p>
        </div>

        <div className="field span-2">
          <label htmlFor="notes">Notes (optional)</label>
          <textarea
            id="notes"
            value={form.notes ?? ''}
            onChange={(e) => update('notes', e.target.value)}
          />
        </div>
      </div>

      <div className="actions-row">
        <button type="submit" className="btn" disabled={submitting || !form.purpose.trim()}>
          {submitting ? (
            <span className="loading-inline">
              <span className="spinner" aria-hidden="true" />
              Saving…
            </span>
          ) : (
            'Save & continue'
          )}
        </button>
      </div>
    </form>
  )
}
