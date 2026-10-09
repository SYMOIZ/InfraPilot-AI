import { useState, type FormEvent } from 'react'
import type { ClarificationQuestion } from '../types'
import { EmptyState } from './EmptyState'

interface ClarificationPanelProps {
  questions: ClarificationQuestion[]
  message?: string
  submitting?: boolean
  onSubmit: (answers: Record<string, string>) => void
  onSkip: () => void
}

export function ClarificationPanel({
  questions,
  message,
  submitting = false,
  onSubmit,
  onSkip,
}: ClarificationPanelProps) {
  const [answers, setAnswers] = useState<Record<string, string>>({})

  if (questions.length === 0) {
    return (
      <EmptyState
        title="No clarification needed"
        description={message || 'Requirements look complete enough to generate an architecture.'}
        action={
          <button type="button" className="btn" onClick={onSkip}>
            Continue to architecture
          </button>
        }
      />
    )
  }

  function handleSubmit(e: FormEvent) {
    e.preventDefault()
    onSubmit(answers)
  }

  return (
    <form className="panel anim-rise" onSubmit={handleSubmit}>
      {message ? <p className="muted">{message}</p> : null}
      {questions.map((q) => (
        <div className="field" key={q.id}>
          <label htmlFor={`q-${q.id}`}>{q.question}</label>
          <p className="hint">{q.reason}</p>
          <textarea
            id={`q-${q.id}`}
            value={answers[q.id] ?? ''}
            onChange={(e) =>
              setAnswers((prev) => ({ ...prev, [q.id]: e.target.value }))
            }
            required
          />
        </div>
      ))}
      <div className="actions-row">
        <button type="submit" className="btn" disabled={submitting}>
          {submitting ? 'Submitting…' : 'Submit answers'}
        </button>
        <button type="button" className="btn btn-secondary" onClick={onSkip} disabled={submitting}>
          Skip for now
        </button>
      </div>
    </form>
  )
}
