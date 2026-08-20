import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import {
  checkHealth,
  analyzeImage,
  ApiError,
  listCases,
  getCase,
  createCase,
  updateCase,
  attachEvidenceToCase,
  getCaseStats,
  listReports,
  generateReport,
  downloadReport,
  login,
  logout,
  getCurrentUser,
  getStoredToken,
  setStoredToken,
  clearStoredToken,
} from './client'

describe('checkHealth', () => {
  beforeEach(() => {
    global.fetch = vi.fn()
  })
  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('returns the parsed JSON on success', async () => {
    global.fetch.mockResolvedValue({
      ok: true,
      json: async () => ({ status: 'ok' }),
    })
    const result = await checkHealth()
    expect(result).toEqual({ status: 'ok' })
  })

  it('throws ApiError when the response is not ok', async () => {
    global.fetch.mockResolvedValue({ ok: false, status: 503 })
    await expect(checkHealth()).rejects.toThrow(ApiError)
  })
})

describe('analyzeImage', () => {
  beforeEach(() => {
    global.fetch = vi.fn()
  })
  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('sends a multipart request with the file and caption', async () => {
    global.fetch.mockResolvedValue({
      ok: true,
      json: async () => ({ verdict: 'adversarial', confidence: 0.92 }),
    })

    const file = new File(['fake image bytes'], 'test.png', { type: 'image/png' })
    const result = await analyzeImage(file, 'a test caption')

    expect(global.fetch).toHaveBeenCalledTimes(1)
    const [url, options] = global.fetch.mock.calls[0]
    expect(url).toContain('/api/v1/analyze')
    expect(options.method).toBe('POST')
    expect(options.body).toBeInstanceOf(FormData)
    expect(result.verdict).toBe('adversarial')
  })

  it('omits the caption field when none is given', async () => {
    global.fetch.mockResolvedValue({
      ok: true,
      json: async () => ({ verdict: 'clean', confidence: 0.95 }),
    })
    const file = new File(['x'], 'test.png', { type: 'image/png' })
    await analyzeImage(file)

    const [, options] = global.fetch.mock.calls[0]
    expect(options.body.has('caption')).toBe(false)
  })

  it('throws ApiError with the backend detail message on failure', async () => {
    global.fetch.mockResolvedValue({
      ok: false,
      status: 503,
      json: async () => ({ detail: 'No trained detector available.' }),
    })
    const file = new File(['x'], 'test.png', { type: 'image/png' })

    await expect(analyzeImage(file)).rejects.toThrow('No trained detector available.')
  })

  it('throws a clear ApiError when the network request itself fails', async () => {
    global.fetch.mockRejectedValue(new TypeError('Failed to fetch'))
    const file = new File(['x'], 'test.png', { type: 'image/png' })

    await expect(analyzeImage(file)).rejects.toThrow(/Could not reach the TRACER backend/)
  })
})

describe('Case Management API (Module 13)', () => {
  beforeEach(() => {
    global.fetch = vi.fn()
  })
  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('listCases fetches /cases without a status filter by default', async () => {
    global.fetch.mockResolvedValue({ ok: true, json: async () => [] })
    await listCases()
    const [url] = global.fetch.mock.calls[0]
    expect(String(url)).toContain('/api/v1/cases')
    expect(String(url)).not.toContain('status=')
  })

  it('listCases includes the status filter when given', async () => {
    global.fetch.mockResolvedValue({ ok: true, json: async () => [] })
    await listCases('open')
    const [url] = global.fetch.mock.calls[0]
    expect(String(url)).toContain('status=open')
  })

  it('getCase fetches the specific case by id', async () => {
    global.fetch.mockResolvedValue({ ok: true, json: async () => ({ id: 'abc' }) })
    const result = await getCase('abc')
    const [url] = global.fetch.mock.calls[0]
    expect(String(url)).toContain('/api/v1/cases/abc')
    expect(result).toEqual({ id: 'abc' })
  })

  it('getCase throws ApiError with the backend detail on 404', async () => {
    global.fetch.mockResolvedValue({
      ok: false,
      status: 404,
      json: async () => ({ detail: "Case 'abc' not found." }),
    })
    await expect(getCase('abc')).rejects.toThrow("Case 'abc' not found.")
  })

  it('createCase POSTs title and description as JSON', async () => {
    global.fetch.mockResolvedValue({ ok: true, json: async () => ({ id: 'new-case' }) })
    await createCase({ title: 'New case', description: 'notes' })

    const [url, options] = global.fetch.mock.calls[0]
    expect(String(url)).toContain('/api/v1/cases')
    expect(options.method).toBe('POST')
    expect(JSON.parse(options.body)).toEqual({ title: 'New case', description: 'notes' })
  })

  it('updateCase PATCHes only the given fields', async () => {
    global.fetch.mockResolvedValue({ ok: true, json: async () => ({ status: 'closed' }) })
    await updateCase('case-1', { status: 'closed' })

    const [url, options] = global.fetch.mock.calls[0]
    expect(String(url)).toContain('/api/v1/cases/case-1')
    expect(options.method).toBe('PATCH')
    expect(JSON.parse(options.body)).toEqual({ status: 'closed' })
  })

  it('attachEvidenceToCase sends a multipart request to the case-specific endpoint', async () => {
    global.fetch.mockResolvedValue({
      ok: true,
      json: async () => ({ id: 'evidence-1', ai_result: { verdict: 'clean' } }),
    })
    const file = new File(['x'], 'evidence.png', { type: 'image/png' })
    const result = await attachEvidenceToCase('case-1', file, 'a caption')

    const [url, options] = global.fetch.mock.calls[0]
    expect(String(url)).toContain('/api/v1/cases/case-1/evidence')
    expect(options.method).toBe('POST')
    expect(options.body).toBeInstanceOf(FormData)
    expect(result.ai_result.verdict).toBe('clean')
  })

  it('attachEvidenceToCase throws a clear ApiError when the network request fails', async () => {
    global.fetch.mockRejectedValue(new TypeError('Failed to fetch'))
    const file = new File(['x'], 'evidence.png', { type: 'image/png' })
    await expect(attachEvidenceToCase('case-1', file)).rejects.toThrow(
      /Could not reach the TRACER backend/
    )
  })

  it('getCaseStats fetches the stats endpoint', async () => {
    global.fetch.mockResolvedValue({
      ok: true,
      json: async () => ({ total_cases: 3 }),
    })
    const result = await getCaseStats()
    const [url] = global.fetch.mock.calls[0]
    expect(String(url)).toContain('/api/v1/cases/stats')
    expect(result.total_cases).toBe(3)
  })
})

describe('Report generation API (Module 14)', () => {
  beforeEach(() => {
    global.fetch = vi.fn()
  })
  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('listReports fetches the reports list for a case', async () => {
    global.fetch.mockResolvedValue({ ok: true, json: async () => [] })
    await listReports('case-1')
    const [url] = global.fetch.mock.calls[0]
    expect(String(url)).toContain('/api/v1/cases/case-1/reports')
  })

  it('generateReport POSTs the requested format', async () => {
    global.fetch.mockResolvedValue({
      ok: true,
      json: async () => ({ id: 'report-1', format: 'docx' }),
    })
    const result = await generateReport('case-1', 'docx')

    const [url, options] = global.fetch.mock.calls[0]
    expect(String(url)).toContain('/api/v1/cases/case-1/reports')
    expect(options.method).toBe('POST')
    expect(JSON.parse(options.body)).toEqual({ format: 'docx' })
    expect(result.format).toBe('docx')
  })

  it('generateReport defaults to pdf when no format is given', async () => {
    global.fetch.mockResolvedValue({ ok: true, json: async () => ({ format: 'pdf' }) })
    await generateReport('case-1')
    const [, options] = global.fetch.mock.calls[0]
    expect(JSON.parse(options.body)).toEqual({ format: 'pdf' })
  })

  it('generateReport throws a clear ApiError when the network request fails', async () => {
    global.fetch.mockRejectedValue(new TypeError('Failed to fetch'))
    await expect(generateReport('case-1', 'pdf')).rejects.toThrow(
      /Could not reach the TRACER backend/
    )
  })

  it('downloadReport fetches with the auth header and triggers a save, not a bare href', async () => {
    setStoredToken('test-token')
    const mockBlob = new Blob(['pdf bytes'], { type: 'application/pdf' })
    global.fetch.mockResolvedValue({ ok: true, blob: async () => mockBlob })

    const clickSpy = vi.fn()
    const originalCreateElement = document.createElement.bind(document)
    vi.spyOn(document, 'createElement').mockImplementation((tag) => {
      const el = originalCreateElement(tag)
      if (tag === 'a') el.click = clickSpy
      return el
    })

    await downloadReport('case-1', 'report-1', 'my_report.pdf')

    const [url, options] = global.fetch.mock.calls[0]
    expect(String(url)).toContain('/api/v1/cases/case-1/reports/report-1/download')
    expect(options.headers.Authorization).toBe('Bearer test-token')
    expect(clickSpy).toHaveBeenCalled()
    clearStoredToken()
  })

  it('downloadReport throws a clear ApiError on failure', async () => {
    global.fetch.mockResolvedValue({
      ok: false,
      status: 404,
      json: async () => ({ detail: "Report 'report-1' not found." }),
    })
    await expect(downloadReport('case-1', 'report-1')).rejects.toThrow(
      "Report 'report-1' not found."
    )
  })
})

describe('Auth API (Module 16)', () => {
  beforeEach(() => {
    global.fetch = vi.fn()
    clearStoredToken()
  })
  afterEach(() => {
    vi.restoreAllMocks()
    clearStoredToken()
  })

  it('login sends form-urlencoded credentials, not JSON (matches OAuth2PasswordRequestForm)', async () => {
    global.fetch.mockResolvedValue({
      ok: true,
      json: async () => ({ access_token: 'abc123', token_type: 'bearer', expires_in_minutes: 480 }),
    })
    await login('someone@example.com', 'hunter2pass')

    const [url, options] = global.fetch.mock.calls[0]
    expect(String(url)).toContain('/api/v1/auth/login')
    expect(options.headers['Content-Type']).toBe('application/x-www-form-urlencoded')
    expect(options.body.toString()).toContain('username=someone%40example.com')
    expect(options.body.toString()).toContain('password=hunter2pass')
  })

  it('login stores the returned token', async () => {
    global.fetch.mockResolvedValue({
      ok: true,
      json: async () => ({ access_token: 'stored-token-value', token_type: 'bearer', expires_in_minutes: 480 }),
    })
    await login('someone@example.com', 'hunter2pass')
    expect(getStoredToken()).toBe('stored-token-value')
  })

  it('login throws a clear ApiError with the backend detail on invalid credentials', async () => {
    global.fetch.mockResolvedValue({
      ok: false,
      status: 401,
      json: async () => ({ detail: 'Incorrect username or password.' }),
    })
    await expect(login('someone@example.com', 'wrong')).rejects.toThrow(
      'Incorrect username or password.'
    )
  })

  it('logout clears the stored token', async () => {
    setStoredToken('some-token')
    logout()
    expect(getStoredToken()).toBeNull()
  })

  it('getCurrentUser sends the stored token as a bearer header', async () => {
    setStoredToken('my-token')
    global.fetch.mockResolvedValue({
      ok: true,
      json: async () => ({ id: '1', username: 'alice', email: 'a@example.com', role: 'admin' }),
    })
    await getCurrentUser()
    const [, options] = global.fetch.mock.calls[0]
    expect(options.headers.Authorization).toBe('Bearer my-token')
  })

  it('getCurrentUser throws a clear ApiError on a 401', async () => {
    global.fetch.mockResolvedValue({
      ok: false,
      status: 401,
      json: async () => ({ detail: 'Not authenticated.' }),
    })
    await expect(getCurrentUser()).rejects.toThrow('Not authenticated.')
  })
})
