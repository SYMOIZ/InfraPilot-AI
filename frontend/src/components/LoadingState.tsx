interface LoadingStateProps {
  label?: string
}

export function LoadingState({ label = 'Loading…' }: LoadingStateProps) {
  return (
    <div className="state-box anim-fade" role="status" aria-live="polite">
      <div className="loading-inline">
        <span className="spinner" aria-hidden="true" />
        <span>{label}</span>
      </div>
    </div>
  )
}
