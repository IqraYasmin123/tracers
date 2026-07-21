import { describe, it, expect } from 'vitest'
import {
  formatConfidence,
  truncateHash,
  verdictToColorClass,
  verdictToBgClass,
  formatProcessingTime,
} from './format'

describe('formatConfidence', () => {
  it('formats a fraction as a percentage with one decimal', () => {
    expect(formatConfidence(0.923)).toBe('92.3%')
  })

  it('handles 0 and 1 correctly', () => {
    expect(formatConfidence(0)).toBe('0.0%')
    expect(formatConfidence(1)).toBe('100.0%')
  })

  it('returns an em-dash for non-numeric input', () => {
    expect(formatConfidence(null)).toBe('—')
    expect(formatConfidence(undefined)).toBe('—')
    expect(formatConfidence(NaN)).toBe('—')
  })
})

describe('truncateHash', () => {
  it('truncates a long hash to first/last N characters', () => {
    // A realistic-looking 64-char SHA-256 hex string, deliberately non-repeating so the
    // first-8/last-8 truncation is visibly distinct (unlike a repeated pattern, which
    // would make first-8 and last-8 identical and the test misleadingly pass either way).
    const hash = 'a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2'
    expect(truncateHash(hash)).toBe('a1b2c3d4…e9f0a1b2')
  })

  it('leaves short strings untouched', () => {
    expect(truncateHash('short')).toBe('short')
  })

  it('handles empty/null input without throwing', () => {
    expect(truncateHash(null)).toBe('')
    expect(truncateHash(undefined)).toBe('')
    expect(truncateHash('')).toBe('')
  })
})

describe('verdictToColorClass', () => {
  it('maps adversarial to the danger color', () => {
    expect(verdictToColorClass('adversarial')).toBe('text-verdict-adversarial')
  })

  it('maps clean to the safe color', () => {
    expect(verdictToColorClass('clean')).toBe('text-verdict-clean')
  })

  it('falls back to muted for unknown verdicts', () => {
    expect(verdictToColorClass('unknown')).toBe('text-muted')
    expect(verdictToColorClass(undefined)).toBe('text-muted')
  })
})

describe('verdictToBgClass', () => {
  it('returns a background class containing the matching verdict color', () => {
    expect(verdictToBgClass('adversarial')).toContain('verdict-adversarial')
    expect(verdictToBgClass('clean')).toContain('verdict-clean')
  })
})

describe('formatProcessingTime', () => {
  it('formats sub-second times in milliseconds', () => {
    expect(formatProcessingTime(823.1)).toBe('823ms')
  })

  it('formats times at or above 1000ms in seconds', () => {
    expect(formatProcessingTime(1234.5)).toBe('1.23s')
  })

  it('returns an em-dash for non-numeric input', () => {
    expect(formatProcessingTime('not a number')).toBe('—')
  })
})
