import { Link } from 'react-router-dom'
import { isDemoMode } from '../api/client'

export function Landing() {
  const demo = isDemoMode()

  return (
    <section className="landing">
      <div className="landing-copy anim-rise">
        <h1 className="landing-brand">
          InfraPilot <em>AI</em>
        </h1>
        <p className="lede">
          Turn business requirements into evaluated AWS architectures — with
          gap analysis, optimization, and exportable reports.
        </p>
        <div className="cta-row anim-rise anim-delay-1">
          <Link to="/dashboard" className="btn">
            Start project
          </Link>
          {demo ? (
            <Link to="/dashboard?demo=1" className="btn btn-secondary">
              Open demo
            </Link>
          ) : null}
        </div>
      </div>

      <div className="landing-visual anim-fade anim-delay-2" aria-hidden="true">
        <svg className="hero-svg" viewBox="0 0 420 280" role="presentation">
          <line className="edge" x1="90" y1="70" x2="210" y2="140" pathLength={1} />
          <line className="edge" x1="210" y1="140" x2="330" y2="70" pathLength={1} />
          <line className="edge" x1="210" y1="140" x2="210" y2="220" pathLength={1} />
          <g className="pulse">
            <rect className="node-rect" x="30" y="45" width="120" height="50" rx="6" />
            <text className="node-label" x="48" y="75">
              Edge / CDN
            </text>
          </g>
          <g className="pulse" style={{ animationDelay: '0.15s' }}>
            <rect className="node-rect" x="150" y="115" width="120" height="50" rx="6" />
            <text className="node-label" x="168" y="145">
              Compute
            </text>
          </g>
          <g className="pulse" style={{ animationDelay: '0.3s' }}>
            <rect className="node-rect" x="270" y="45" width="120" height="50" rx="6" />
            <text className="node-label" x="292" y="75">
              Auth
            </text>
          </g>
          <g className="pulse" style={{ animationDelay: '0.45s' }}>
            <rect className="node-rect" x="150" y="195" width="120" height="50" rx="6" />
            <text className="node-label" x="178" y="225">
              Data
            </text>
          </g>
        </svg>
      </div>
    </section>
  )
}
