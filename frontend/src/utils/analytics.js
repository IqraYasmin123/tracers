/**
 * Pure analytics computation over live session data (recorded by SessionContext from real
 * Investigation-page analyses). No React, no charting library, no I/O — same
 * separation-of-concerns used throughout the AI engine and backend (Modules 2-9) and in
 * utils/format.js: pure logic first, rendering second, so it's trivially unit-testable.
 *
 * `sessions` is expected newest-first, matching SessionContext's storage order.
 */

/** Total / clean / adversarial counts. */
export function computeVerdictCounts(sessions) {
  const counts = { total: sessions.length, clean: 0, adversarial: 0, other: 0 }
  for (const s of sessions) {
    if (s.verdict === 'clean') counts.clean += 1
    else if (s.verdict === 'adversarial') counts.adversarial += 1
    else counts.other += 1
  }
  return counts
}

/** [{ type, count, pct }] sorted by count desc. Only sessions with a non-null attack_type
 * are counted — clean images correctly have no attack type. */
export function computeAttackTypeDistribution(sessions) {
  const withAttackType = sessions.filter((s) => s.attack_type)
  const tally = new Map()
  for (const s of withAttackType) {
    tally.set(s.attack_type, (tally.get(s.attack_type) || 0) + 1)
  }
  const total = withAttackType.length
  return Array.from(tally.entries())
    .map(([type, count]) => ({ type, count, pct: total > 0 ? count / total : 0 }))
    .sort((a, b) => b.count - a.count)
}

/** Mean confidence across sessions that have a numeric confidence value. Returns null if
 * there's no data, rather than 0, so callers can distinguish "no data" from "0% confidence". */
export function computeAvgConfidence(sessions) {
  const values = sessions.map((s) => s.confidence).filter((v) => typeof v === 'number')
  if (values.length === 0) return null
  return values.reduce((sum, v) => sum + v, 0) / values.length
}

/** Mean processing time in ms across sessions that recorded one. Null if no data. */
export function computeAvgProcessingTime(sessions) {
  const values = sessions.map((s) => s.processing_time_ms).filter((v) => typeof v === 'number')
  if (values.length === 0) return null
  return values.reduce((sum, v) => sum + v, 0) / values.length
}

/**
 * Chronological (oldest -> newest) series for the confidence timeline chart. Each point
 * carries enough context (verdict, timestamp) for the chart to color and label it.
 */
export function computeConfidenceTimeline(sessions) {
  return [...sessions]
    .filter((s) => typeof s.confidence === 'number')
    .sort((a, b) => a.timestamp - b.timestamp)
    .map((s, index) => ({
      index,
      id: s.id,
      confidence: s.confidence,
      verdict: s.verdict,
      timestamp: s.timestamp,
    }))
}

/**
 * Threat level over the most recent `windowSize` sessions (default 10, or all if fewer).
 * Score is the mean confidence of adversarial verdicts within the window (0 for clean
 * verdicts, ignored if verdict/confidence missing) — i.e. "how strongly, on average, has
 * recent traffic been flagged as adversarial". Returns null score/level when there's no
 * data yet, rather than fabricating a 0 (which would visually read as "confirmed safe").
 */
export function computeThreatLevel(sessions, windowSize = 10) {
  const recent = sessions.slice(0, windowSize) // sessions is newest-first
  const scored = recent.filter(
    (s) => (s.verdict === 'clean' || s.verdict === 'adversarial') && typeof s.confidence === 'number'
  )
  if (scored.length === 0) {
    return { score: null, level: 'no-data', sampleSize: 0 }
  }
  const sum = scored.reduce((acc, s) => acc + (s.verdict === 'adversarial' ? s.confidence : 0), 0)
  const score = sum / scored.length

  let level
  if (score < 0.2) level = 'low'
  else if (score < 0.5) level = 'moderate'
  else level = 'high'

  return { score, level, sampleSize: scored.length }
}
