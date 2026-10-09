import { Link, Outlet } from 'react-router-dom'

export function Layout() {
  return (
    <div className="app-shell">
      <header className="app-header">
        <Link to="/" className="brand-link" aria-label="InfraPilot AI home">
          <span>InfraPilot</span>
          <span>AI</span>
        </Link>
        <nav aria-label="Primary">
          <Link to="/dashboard" className="btn btn-ghost btn-sm">
            Dashboard
          </Link>
        </nav>
      </header>
      <main className="app-main">
        <Outlet />
      </main>
      <footer className="app-footer">
        InfraPilot AI designs and evaluates architectures — it does not deploy infrastructure.
      </footer>
    </div>
  )
}
