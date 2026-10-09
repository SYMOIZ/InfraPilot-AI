import type {
  ClarificationRequest,
  ClarificationResponse,
  CompareResponse,
  ConfirmArchitectureRequest,
  DemoSample,
  EvaluationReport,
  GenerateRequest,
  HealthResponse,
  OptimizationProposal,
  Project,
  ProjectCreate,
  ProjectSummary,
  ReportResponse,
  Requirements,
} from '../types'

const API_BASE = (import.meta.env.VITE_API_BASE_URL ?? '').replace(/\/$/, '')

export class ApiError extends Error {
  status: number
  detail: unknown

  constructor(message: string, status: number, detail?: unknown) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.detail = detail
  }
}

function detailToMessage(detail: unknown, fallback: string): string {
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail)) {
    return detail
      .map((item) => {
        if (typeof item === 'string') return item
        if (item && typeof item === 'object' && 'msg' in item) {
          return String((item as { msg: unknown }).msg)
        }
        return JSON.stringify(item)
      })
      .join('; ')
  }
  if (detail && typeof detail === 'object' && 'message' in detail) {
    return String((detail as { message: unknown }).message)
  }
  if (detail != null) return JSON.stringify(detail)
  return fallback
}

async function request<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const url = `${API_BASE}${path}`
  const headers = new Headers(options.headers)
  if (options.body && !(options.body instanceof FormData) && !headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json')
  }

  let response: Response
  try {
    response = await fetch(url, { ...options, headers })
  } catch (err) {
    throw new ApiError(
      err instanceof Error ? err.message : 'Network request failed',
      0,
    )
  }

  if (response.status === 204) {
    return undefined as T
  }

  const contentType = response.headers.get('content-type') ?? ''
  const isJson = contentType.includes('application/json')

  if (!response.ok) {
    let detail: unknown
    if (isJson) {
      try {
        const body = await response.json()
        detail = body.detail ?? body
      } catch {
        detail = undefined
      }
    } else {
      detail = await response.text()
    }
    throw new ApiError(
      detailToMessage(detail, `Request failed (${response.status})`),
      response.status,
      detail,
    )
  }

  if (isJson) {
    return (await response.json()) as T
  }

  return (await response.text()) as T
}

async function downloadBlob(path: string, filename: string): Promise<void> {
  const url = `${API_BASE}${path}`
  let response: Response
  try {
    response = await fetch(url)
  } catch (err) {
    throw new ApiError(
      err instanceof Error ? err.message : 'Network request failed',
      0,
    )
  }

  if (!response.ok) {
    let detail: unknown
    const contentType = response.headers.get('content-type') ?? ''
    if (contentType.includes('application/json')) {
      try {
        const body = await response.json()
        detail = body.detail ?? body
      } catch {
        detail = undefined
      }
    } else {
      detail = await response.text()
    }
    throw new ApiError(
      detailToMessage(detail, `Export failed (${response.status})`),
      response.status,
      detail,
    )
  }

  const blob = await response.blob()
  const objectUrl = URL.createObjectURL(blob)
  const anchor = document.createElement('a')
  anchor.href = objectUrl
  anchor.download = filename
  document.body.appendChild(anchor)
  anchor.click()
  anchor.remove()
  URL.revokeObjectURL(objectUrl)
}

export const api = {
  health: () => request<HealthResponse>('/health'),

  getDemoSample: () => request<DemoSample>('/api/v1/demo/sample'),

  listProjects: () => request<ProjectSummary[]>('/api/v1/projects'),

  createProject: (body: ProjectCreate) =>
    request<Project>('/api/v1/projects', {
      method: 'POST',
      body: JSON.stringify(body),
    }),

  getProject: (id: string) => request<Project>(`/api/v1/projects/${id}`),

  deleteProject: (id: string) =>
    request<void>(`/api/v1/projects/${id}`, { method: 'DELETE' }),

  putRequirements: (id: string, body: Requirements) =>
    request<Project>(`/api/v1/projects/${id}/requirements`, {
      method: 'PUT',
      body: JSON.stringify(body),
    }),

  clarify: (id: string, body?: ClarificationRequest) =>
    request<ClarificationResponse>(`/api/v1/projects/${id}/clarify`, {
      method: 'POST',
      body: JSON.stringify(body ?? { answers: {} }),
    }),

  generate: (id: string, body?: GenerateRequest) =>
    request<Project>(`/api/v1/projects/${id}/generate`, {
      method: 'POST',
      body: JSON.stringify(body ?? { regenerate: false }),
    }),

  upload: (id: string, file: File) => {
    const form = new FormData()
    form.append('file', file)
    return request<Project>(`/api/v1/projects/${id}/upload`, {
      method: 'POST',
      body: form,
    })
  },

  confirmArchitecture: (id: string, body: ConfirmArchitectureRequest) =>
    request<Project>(`/api/v1/projects/${id}/confirm-architecture`, {
      method: 'POST',
      body: JSON.stringify(body),
    }),

  evaluate: (id: string) =>
    request<EvaluationReport>(`/api/v1/projects/${id}/evaluate`, {
      method: 'POST',
    }),

  optimize: (id: string) =>
    request<OptimizationProposal>(`/api/v1/projects/${id}/optimize`, {
      method: 'POST',
    }),

  compare: (id: string) =>
    request<CompareResponse>(`/api/v1/projects/${id}/compare`),

  getReport: (id: string) =>
    request<ReportResponse>(`/api/v1/projects/${id}/report`),

  exportDrawio: (id: string) =>
    downloadBlob(`/api/v1/projects/${id}/export/drawio`, `${id}.drawio`),

  exportPng: (id: string) =>
    downloadBlob(`/api/v1/projects/${id}/export/png`, `${id}.png`),

  exportExcel: (id: string) =>
    downloadBlob(`/api/v1/projects/${id}/export/excel`, `${id}.xlsx`),
}

export function isDemoMode(): boolean {
  return String(import.meta.env.VITE_DEMO_MODE ?? 'true').toLowerCase() === 'true'
}
