import type { WorkflowStep } from '../types'

const STEPS: { id: WorkflowStep; label: string }[] = [
  { id: 'requirements', label: 'Requirements' },
  { id: 'clarify', label: 'Clarify' },
  { id: 'architecture', label: 'Architecture' },
  { id: 'upload', label: 'Upload' },
  { id: 'evaluate', label: 'Evaluate' },
  { id: 'optimize', label: 'Optimize' },
  { id: 'report', label: 'Report' },
]

interface WizardStepsProps {
  current: WorkflowStep
  unlocked: Set<WorkflowStep>
  onSelect: (step: WorkflowStep) => void
}

export function WizardSteps({ current, unlocked, onSelect }: WizardStepsProps) {
  return (
    <nav className="wizard-nav" aria-label="Workflow steps">
      {STEPS.map((step) => {
        const isActive = step.id === current
        const isUnlocked = unlocked.has(step.id)
        const className = [
          'wizard-step-btn',
          isActive ? 'active' : '',
          !isActive && isUnlocked ? 'done' : '',
        ]
          .filter(Boolean)
          .join(' ')

        return (
          <button
            key={step.id}
            type="button"
            className={className}
            disabled={!isUnlocked}
            aria-current={isActive ? 'step' : undefined}
            onClick={() => onSelect(step.id)}
          >
            {step.label}
          </button>
        )
      })}
    </nav>
  )
}

export { STEPS }
