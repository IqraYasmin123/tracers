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

/**
 * Auth (Module 16). Token is kept in localStorage — a plain string under one fixed key,
 * read directly by every authenticated call below. Kept out of React state/context here
 * so this file stays framework-agnostic and independently testable, same as everything
 * else in it; AuthContext.jsx is the React-facing layer that wraps these functions.
 */
const TOKEN_STORAGE_KEY = 'tracer.auth_token.v1'

export function getStoredToken() {
  return localStorage.getItem(TOKEN_STORAGE_KEY)
}

export function setStoredToken(token) {
  localStorage.setItem(TOKEN_STORAGE_KEY, token)
}

export function clearStoredToken() {
  localStorage.removeItem(TOKEN_STORAGE_KEY)
}

function authHeaders() {
  const token = getStoredToken()
  return token ? { Authorization: `Bearer ${token}` } : {}
}

/** Accepts either a username or an email in the same field — see
 * backend/app/auth/routes.py's login() for why. FastAPI's OAuth2PasswordRequestForm
 * expects application/x-www-form-urlencoded, not JSON. */
export async function login(usernameOrEmail, password) {
  let response
  try {
    response = await fetch(`${API_BASE_URL}/api/v1/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: new URLSearchParams({ username: usernameOrEmail, password }),
    })
  } catch (networkError) {
    throw new ApiError(
      'Could not reach the TRACER backend. Is it running at ' + API_BASE_URL + '?',
      0
    )
  }
  if (!response.ok) {
    const body = await response.json().catch(() => ({}))
    throw new ApiError(body.detail || 'Login failed', response.status)
  }
  const body = await response.json()
  setStoredToken(body.access_token)
  return body
}

export function logout() {
  clearStoredToken()
}

export async function getCurrentUser() {
  const response = await fetch(`${API_BASE_URL}/api/v1/auth/me`, { headers: authHeaders() })
  if (!response.ok) {
    const body = await response.json().catch(() => ({}))
    throw new ApiError(body.detail || 'Failed to load current user', response.status)
  }
  return response.json()
}

/** Backend returns 204 No Content on success — no JSON body to parse, unlike most other
 * endpoints here. See backend/app/auth/routes.py's change_my_password(). */
export async function changePassword(currentPassword, newPassword) {
  const response = await fetch(`${API_BASE_URL}/api/v1/auth/me/password`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json', ...authHeaders() },
    body: JSON.stringify({ current_password: currentPassword, new_password: newPassword }),
  })
  if (!response.ok) {
    const body = await response.json().catch(() => ({}))
    throw new ApiError(body.detail || 'Failed to change password', response.status)
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
 * an optional `caption` field. Note: /analyze itself doesn't require auth (Module 9 predates
 * Module 16 and is a stateless, unsaved analysis) — only the case/evidence/report endpoints
 * below, which persist real records, require a logged-in user.
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
 * Case Management (Module 13). All mirror backend/app/api/routes/cases.py exactly. Every
 * one of these now requires auth (Module 16) — a 401 propagates as an ApiError the same
 * way any other failure does; AuthContext listens for that to redirect to /login.
 */

export async function listCases(status) {
  const url = new URL(`${API_BASE_URL}/api/v1/cases`)
  if (status) url.searchParams.set('status', status)

  const response = await fetch(url, { headers: authHeaders() })
  if (!response.ok) {
    const body = await response.json().catch(() => ({}))
    throw new ApiError(body.detail || 'Failed to list cases', response.status)
  }
  return response.json()
}

export async function getCase(caseId) {
  const response = await fetch(`${API_BASE_URL}/api/v1/cases/${caseId}`, { headers: authHeaders() })
  if (!response.ok) {
    const body = await response.json().catch(() => ({}))
    throw new ApiError(body.detail || 'Failed to load case', response.status)
  }
  return response.json()
}

export async function createCase({ title, description }) {
  const response = await fetch(`${API_BASE_URL}/api/v1/cases`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...authHeaders() },
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
    headers: { 'Content-Type': 'application/json', ...authHeaders() },
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
      headers: authHeaders(),
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
  const response = await fetch(`${API_BASE_URL}/api/v1/cases/stats`, { headers: authHeaders() })
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
  const response = await fetch(`${API_BASE_URL}/api/v1/cases/${caseId}/reports`, {
    headers: authHeaders(),
  })
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
      headers: { 'Content-Type': 'application/json', ...authHeaders() },
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

/** The download endpoint now requires auth (Module 16), and a plain <a href> navigation
 * can't carry a custom Authorization header — so this fetches the file with the header,
 * then triggers a save via a temporary object URL, instead of exposing a raw href like
 * before Module 16. Returns nothing; the browser's save dialog (or default download
 * behavior) takes over once triggered. */
export async function downloadReport(caseId, reportId, suggestedFilename) {
  let response
  try {
    response = await fetch(
      `${API_BASE_URL}/api/v1/cases/${caseId}/reports/${reportId}/download`,
      { headers: authHeaders() }
    )
  } catch (networkError) {
    throw new ApiError(
      'Could not reach the TRACER backend. Is it running at ' + API_BASE_URL + '?',
      0
    )
  }
  if (!response.ok) {
    const body = await response.json().catch(() => ({}))
    throw new ApiError(body.detail || 'Failed to download report', response.status)
  }
  const blob = await response.blob()
  const objectUrl = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = objectUrl
  link.download = suggestedFilename || 'report'
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(objectUrl)
}
