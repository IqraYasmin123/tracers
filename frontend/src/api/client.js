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
