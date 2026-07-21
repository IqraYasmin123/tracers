import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { checkHealth, analyzeImage, ApiError } from './client'

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
