import { describe, it, expect } from 'vitest'
import {
  computeVerdictCounts,
  computeAttackTypeDistribution,
  computeAvgConfidence,
  computeAvgProcessingTime,
  computeConfidenceTimeline,
  computeThreatLevel,
} from './analytics'

function session(overrides = {}) {
  return {
    id: 'x',
    timestamp: 0,
    verdict: 'clean',
    confidence: 0.5,
    attack_type: null,
    attack_type_confidence: null,
    processing_time_ms: 100,
    ...overrides,
  }
}

describe('computeVerdictCounts', () => {
  it('returns zeros for an empty session list', () => {
    expect(computeVerdictCounts([])).toEqual({ total: 0, clean: 0, adversarial: 0, other: 0 })
  })

  it('tallies clean vs adversarial vs other', () => {
    const sessions = [
      session({ verdict: 'clean' }),
      session({ verdict: 'clean' }),
      session({ verdict: 'adversarial' }),
      session({ verdict: null }),
    ]
    expect(computeVerdictCounts(sessions)).toEqual({ total: 4, clean: 2, adversarial: 1, other: 1 })
  })
})

describe('computeAttackTypeDistribution', () => {
  it('returns an empty array when nothing has an attack type', () => {
    expect(computeAttackTypeDistribution([session(), session()])).toEqual([])
  })

  it('excludes clean images and only counts entries with an attack_type', () => {
    const sessions = [
      session({ verdict: 'clean', attack_type: null }),
      session({ verdict: 'adversarial', attack_type: 'pgd' }),
      session({ verdict: 'adversarial', attack_type: 'pgd' }),
      session({ verdict: 'adversarial', attack_type: 'fgsm' }),
    ]
    const result = computeAttackTypeDistribution(sessions)
    expect(result).toEqual([
      { type: 'pgd', count: 2, pct: 2 / 3 },
      { type: 'fgsm', count: 1, pct: 1 / 3 },
    ])
  })

  it('sorts by count descending', () => {
    const sessions = [
      session({ attack_type: 'fgsm' }),
      session({ attack_type: 'pgd' }),
      session({ attack_type: 'pgd' }),
      session({ attack_type: 'pgd' }),
    ]
    const result = computeAttackTypeDistribution(sessions)
    expect(result[0].type).toBe('pgd')
    expect(result[0].count).toBe(3)
  })
})

describe('computeAvgConfidence', () => {
  it('returns null (not 0) when there is no data', () => {
    expect(computeAvgConfidence([])).toBeNull()
  })

  it('averages numeric confidence values', () => {
    const sessions = [session({ confidence: 0.8 }), session({ confidence: 0.4 })]
    expect(computeAvgConfidence(sessions)).toBeCloseTo(0.6)
  })

  it('ignores sessions with missing confidence', () => {
    const sessions = [session({ confidence: 0.8 }), session({ confidence: null })]
    expect(computeAvgConfidence(sessions)).toBeCloseTo(0.8)
  })
})

describe('computeAvgProcessingTime', () => {
  it('returns null when there is no data', () => {
    expect(computeAvgProcessingTime([])).toBeNull()
  })

  it('averages processing time in ms', () => {
    const sessions = [session({ processing_time_ms: 100 }), session({ processing_time_ms: 300 })]
    expect(computeAvgProcessingTime(sessions)).toBe(200)
  })
})

describe('computeConfidenceTimeline', () => {
  it('sorts chronologically oldest to newest regardless of input order', () => {
    const sessions = [
      session({ id: 'c', timestamp: 300, confidence: 0.3 }),
      session({ id: 'a', timestamp: 100, confidence: 0.1 }),
      session({ id: 'b', timestamp: 200, confidence: 0.2 }),
    ]
    const result = computeConfidenceTimeline(sessions)
    expect(result.map((r) => r.id)).toEqual(['a', 'b', 'c'])
    expect(result.map((r) => r.index)).toEqual([0, 1, 2])
  })

  it('skips sessions without a numeric confidence', () => {
    const sessions = [session({ confidence: 0.5 }), session({ confidence: undefined })]
    expect(computeConfidenceTimeline(sessions)).toHaveLength(1)
  })
})

describe('computeThreatLevel', () => {
  it('reports no-data when there are no scoreable sessions', () => {
    expect(computeThreatLevel([])).toEqual({ score: null, level: 'no-data', sampleSize: 0 })
  })

  it('classifies as low when adversarial detections are rare/low-confidence', () => {
    const sessions = [session({ verdict: 'clean', confidence: 0.9 }), session({ verdict: 'clean', confidence: 0.9 })]
    const result = computeThreatLevel(sessions)
    expect(result.level).toBe('low')
    expect(result.score).toBe(0)
  })

  it('classifies as high when recent adversarial confidence is high', () => {
    const sessions = [
      session({ verdict: 'adversarial', confidence: 0.95 }),
      session({ verdict: 'adversarial', confidence: 0.9 }),
    ]
    const result = computeThreatLevel(sessions)
    expect(result.level).toBe('high')
    expect(result.score).toBeCloseTo(0.925)
  })

  it('only considers the most recent windowSize sessions (list is newest-first)', () => {
    const recentClean = Array.from({ length: 10 }, () => session({ verdict: 'clean', confidence: 0.9 }))
    const oldAdversarial = Array.from({ length: 5 }, () =>
      session({ verdict: 'adversarial', confidence: 0.99 })
    )
    // newest-first: recent clean sessions come before the older adversarial ones
    const result = computeThreatLevel([...recentClean, ...oldAdversarial], 10)
    expect(result.sampleSize).toBe(10)
    expect(result.level).toBe('low')
  })
})
