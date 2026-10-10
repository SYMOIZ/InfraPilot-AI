interface AiSupportBadgeProps {
  /** compact = toolbar chip; full = panel/landing */
  variant?: 'compact' | 'full'
  className?: string
}

/** Visible “official AI Support” mark — Amazon Bedrock–backed assist. */
export function AiSupportBadge({ variant = 'compact', className = '' }: AiSupportBadgeProps) {
  if (variant === 'full') {
    return (
      <div className={`ai-support-badge ai-support-badge-full ${className}`.trim()} role="status">
        <span className="ai-support-mark" aria-hidden="true">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
            <path
              d="M12 3l1.8 5.4L19 10.2l-5.2 1.8L12 17.4l-1.8-5.4L5 10.2l5.2-1.8L12 3z"
              fill="currentColor"
            />
            <path
              d="M18.5 14.5l.7 2.1 2.1.7-2.1.7-.7 2.1-.7-2.1-2.1-.7 2.1-.7.7-2.1z"
              fill="currentColor"
              opacity="0.7"
            />
          </svg>
        </span>
        <div className="ai-support-text">
          <strong>AI Support</strong>
          <span>Official assist powered by Amazon Bedrock</span>
        </div>
      </div>
    )
  }

  return (
    <span className={`ai-support-badge ai-support-badge-compact ${className}`.trim()} title="Official AI Support · Amazon Bedrock">
      <span className="ai-support-mark" aria-hidden="true">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none">
          <path
            d="M12 3l1.8 5.4L19 10.2l-5.2 1.8L12 17.4l-1.8-5.4L5 10.2l5.2-1.8L12 3z"
            fill="currentColor"
          />
        </svg>
      </span>
      <span className="ai-support-label">AI Support</span>
      <span className="ai-support-sub">Bedrock</span>
    </span>
  )
}
