import { Link, useNavigate } from 'react-router-dom'
import { useState } from 'react'
import { api, ApiError, isDemoMode } from '../api/client'
import { AiSupportBadge } from '../components/studio/AiSupportBadge'

export function Landing() {
  const navigate = useNavigate()
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function openBlank() {
    setBusy(true)
    setError(null)
    try {
      const project = await api.createProject({
        name: 'Blank architecture',
        description: 'Hand-drawn diagram',
      })
      navigate(`/studio/${project.id}`)
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err.message
          : err instanceof Error
            ? err.message
            : 'Could not create project',
      )
    } finally {
      setBusy(false)
    }
  }

  return (
    <section className="landing">
      <div className="landing-copy anim-rise">
        <h1 className="landing-brand">
          InfraPilot <em>AI</em>
        </h1>
        <AiSupportBadge variant="full" className="landing-ai-badge" />
        <p className="lede">
          Draw AWS architectures by hand with official service icons. Turn on{' '}
          <strong>AI Support</strong> anytime for Bedrock-powered proposals, evaluation, and
          optimization — never required.
        </p>
        <div className="cta-row anim-rise anim-delay-1">
          <Link to="/dashboard" className="btn">
            Open studio
          </Link>
          <button
            type="button"
            className="btn btn-secondary"
            disabled={busy}
            onClick={() => void openBlank()}
          >
            {busy ? 'Creating…' : 'New blank diagram'}
          </button>
          {isDemoMode() ? (
            <Link to="/dashboard?demo=1" className="btn btn-ghost">
              Load demo
            </Link>
          ) : null}
        </div>
        {error ? (
          <p role="alert" style={{ color: 'var(--fail)', marginTop: '1rem' }}>
            {error}
          </p>
        ) : null}
      </div>
    </section>
  )
}
