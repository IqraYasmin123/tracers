/**
 * Thin wrapper around the TRACER backend (Module 9). Kept as plain functions (no React
 * dependency) so they're testable in isolation via a mocked fetch, same pattern as pure
 * logic elsewhere in this codebase.
 */

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000'

export class ApiError extends Error {
  constructor(message, status) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }
}

export async function checkHealth() {
  const response = await fetch(`${API_BASE_URL}/api/v1/health`)
  if (!response.ok) {
    throw new ApiError('Health check failed', response.status)
  }
  return response.json()
}

/**
 * Uploads an image (+ optional caption) for analysis. Mirrors exactly what
 * backend/app/api/routes/inference.py expects: multipart/form-data with a `file` field and
 * an optional `caption` field.
 */
export async function analyzeImage(file, caption) {
  const formData = new FormData()
  formData.append('file', file)
  if (caption) {
    formData.append('caption', caption)
  }

  let response
  try {
    response = await fetch(`${API_BASE_URL}/api/v1/analyze`, {
      method: 'POST',
      body: formData,
    })
  } catch (networkError) {
    throw new ApiError(
      'Could not reach the TRACER backend. Is it running at ' + API_BASE_URL + '?',
      0
    )
  }

  if (!response.ok) {
    const body = await response.json().catch(() => ({}))
    throw new ApiError(body.detail || `Request failed with status ${response.status}`, response.status)
  }

  return response.json()
}

/**
 * Case Management (Module 13). All mirror backend/app/api/routes/cases.py exactly.
 */

export async function listCases(status) {
  const url = new URL(`${API_BASE_URL}/api/v1/cases`)
  if (status) url.searchParams.set('status', status)

  const response = await fetch(url)
  if (!response.ok) {
    const body = await response.json().catch(() => ({}))
    throw new ApiError(body.detail || 'Failed to list cases', response.status)
  }
  return response.json()
}

export async function getCase(caseId) {
  const response = await fetch(`${API_BASE_URL}/api/v1/cases/${caseId}`)
  if (!response.ok) {
    const body = await response.json().catch(() => ({}))
    throw new ApiError(body.detail || 'Failed to load case', response.status)
  }
  return response.json()
}

export async function createCase({ title, description }) {
  const response = await fetch(`${API_BASE_URL}/api/v1/cases`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ title, description: description || null }),
  })
  if (!response.ok) {
    const body = await response.json().catch(() => ({}))
    throw new ApiError(body.detail || 'Failed to create case', response.status)
  }
  return response.json()
}

export async function updateCase(caseId, patch) {
  const response = await fetch(`${API_BASE_URL}/api/v1/cases/${caseId}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(patch),
  })
  if (!response.ok) {
    const body = await response.json().catch(() => ({}))
    throw new ApiError(body.detail || 'Failed to update case', response.status)
  }
  return response.json()
}

/** Uploads an image to a case: the backend re-runs the real AI pipeline server-side and
 * persists both the evidence file and its result — mirrors analyzeImage's shape. */
export async function attachEvidenceToCase(caseId, file, caption) {
  const formData = new FormData()
  formData.append('file', file)
  if (caption) {
    formData.append('caption', caption)
  }

  let response
  try {
    response = await fetch(`${API_BASE_URL}/api/v1/cases/${caseId}/evidence`, {
      method: 'POST',
      body: formData,
    })
  } catch (networkError) {
    throw new ApiError(
      'Could not reach the TRACER backend. Is it running at ' + API_BASE_URL + '?',
      0
    )
  }

  if (!response.ok) {
    const body = await response.json().catch(() => ({}))
    throw new ApiError(body.detail || `Request failed with status ${response.status}`, response.status)
  }
  return response.json()
}

export async function getCaseStats() {
  const response = await fetch(`${API_BASE_URL}/api/v1/cases/stats`)
  if (!response.ok) {
    const body = await response.json().catch(() => ({}))
    throw new ApiError(body.detail || 'Failed to load case statistics', response.status)
  }
  return response.json()
}

/**
 * Report generation (Module 14). Mirrors backend/app/api/routes/reports.py.
 */

export async function listReports(caseId) {
  const response = await fetch(`${API_BASE_URL}/api/v1/cases/${caseId}/reports`)
  if (!response.ok) {
    const body = await response.json().catch(() => ({}))
    throw new ApiError(body.detail || 'Failed to list reports', response.status)
  }
  return response.json()
}

export async function generateReport(caseId, format = 'pdf') {
  let response
  try {
    response = await fetch(`${API_BASE_URL}/api/v1/cases/${caseId}/reports`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ format }),
    })
  } catch (networkError) {
    throw new ApiError(
      'Could not reach the TRACER backend. Is it running at ' + API_BASE_URL + '?',
      0
    )
  }
  if (!response.ok) {
    const body = await response.json().catch(() => ({}))
    throw new ApiError(body.detail || `Request failed with status ${response.status}`, response.status)
  }
  return response.json()
}

/** Returns the direct download URL — used as an <a href> rather than fetched in JS, so the
 * browser handles the file download/save-as natively. */
export function getReportDownloadUrl(caseId, reportId) {
  return `${API_BASE_URL}/api/v1/cases/${caseId}/reports/${reportId}/download`
}
