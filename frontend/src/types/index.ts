/** Types mirroring backend/app/models/schemas.py */

export type RuleStatus = 'Pass' | 'Fail' | 'Warning' | 'Unknown' | 'Not Applicable'

export type WorkloadType = 'web' | 'api' | 'batch' | 'streaming' | 'data' | 'other'

export type DataSensitivity = 'public' | 'internal' | 'confidential' | 'regulated'

export type AvailabilityTarget = 'standard' | 'high' | 'critical'

export interface Requirements {
  purpose: string
  workload: WorkloadType
  traffic: string
  data_sensitivity: DataSensitivity
  availability: AvailabilityTarget
  recovery: string
  budget: string
  region: string
  scalability: string
  constraints: string[]
  notes?: string | null
}

export interface ArchitectureNode {
  id: string
  service_id: string
  label: string
  props: Record<string, unknown>
  x?: number | null
  y?: number | null
}

export interface ArchitectureEdge {
  id?: string | null
  from: string
  to: string
  label?: string | null
}

export interface Architecture {
  id: string
  name: string
  nodes: ArchitectureNode[]
  edges: ArchitectureEdge[]
  confirmed: boolean
  source: string
  metadata: Record<string, unknown>
}

export interface EvaluationFinding {
  id: string
  rule_id: string
  category: string
  title: string
  status: RuleStatus
  severity: string
  message: string
  evidence?: string | null
  recommendation?: string | null
  source: string
}

export interface CategoryScores {
  security: number
  cost: number
  reliability: number
  scalability: number
  best_practices: number
}

export interface ScoreReport {
  categories: CategoryScores
  overall: number
  weights: Record<string, number>
}

export interface EvaluationReport {
  project_id: string
  findings: EvaluationFinding[]
  scores: ScoreReport
  summary: string
  gaps: string[]
  evaluated_at: string
}

export interface OptimizationChange {
  change_type: string
  service_id?: string | null
  description: string
  rationale: string
  impact_categories: string[]
}

export interface OptimizationProposal {
  project_id: string
  original: Architecture
  optimized: Architecture
  changes: OptimizationChange[]
  summary: string
  cost_notes: string
  created_at: string
}

export interface CompareResponse {
  project_id: string
  original?: Architecture | null
  optimized?: Architecture | null
  changes: OptimizationChange[]
  original_scores?: ScoreReport | null
  optimized_scores?: ScoreReport | null
}

export interface ProjectCreate {
  name: string
  description?: string | null
}

export interface ProjectSummary {
  id: string
  name: string
  description?: string | null
  created_at: string
  updated_at: string
  has_requirements: boolean
  has_architecture: boolean
  has_evaluation: boolean
  has_optimization: boolean
}

export interface Project {
  id: string
  name: string
  description?: string | null
  created_at: string
  updated_at: string
  requirements?: Requirements | null
  architecture?: Architecture | null
  optimized_architecture?: Architecture | null
  evaluation?: EvaluationReport | null
  optimization?: OptimizationProposal | null
  uploaded_files: string[]
  clarification_answers: Record<string, string>
}

export interface ClarificationRequest {
  answers: Record<string, string>
}

export interface ClarificationQuestion {
  id: string
  question: string
  reason: string
}

export interface ClarificationResponse {
  project_id: string
  questions: ClarificationQuestion[]
  message: string
}

export interface ConfirmArchitectureRequest {
  architecture: Architecture
  confirmed: boolean
}

export interface GenerateRequest {
  regenerate?: boolean
  prompt?: string | null
}

export interface ReportResponse {
  project_id: string
  title: string
  executive_summary: string
  requirements?: Requirements | null
  architecture?: Architecture | null
  evaluation?: EvaluationReport | null
  optimization?: OptimizationProposal | null
  generated_at: string
}

export interface DemoSample {
  label: string
  disclaimer: string
  requirements: Requirements
  architecture: Architecture
}

export interface HealthResponse {
  status: string
  service: string
  demo_mode: boolean
  version: string
}

export type WorkflowStep =
  | 'requirements'
  | 'clarify'
  | 'architecture'
  | 'upload'
  | 'evaluate'
  | 'optimize'
  | 'report'
