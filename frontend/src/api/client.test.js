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
