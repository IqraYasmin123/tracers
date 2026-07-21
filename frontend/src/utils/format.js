/**
 * Pure formatting/display-logic utilities — deliberately kept free of any React or API
 * dependency so they're trivially unit-testable, same testing philosophy used throughout
 * the AI engine and backend (Modules 2-9): separate pure logic from I/O.
 */

/** 0.923 -> "92.3%" */
export function formatConfidence(value) {
  if (typeof value !== 'number' || Number.isNaN(value)) return '—'
  return `${(value * 100).toFixed(1)}%`
}

/** "deadbeef...c0ffee" (64 chars) -> "deadbeef…c0ffee" */
export function truncateHash(hash, visibleChars = 8) {
  if (!hash || hash.length <= visibleChars * 2) return hash ?? ''
  return `${hash.slice(0, visibleChars)}…${hash.slice(-visibleChars)}`
}

/** Maps a detection verdict to its Tailwind color token — the single place this mapping
 * lives, so the "clean=green/adversarial=red" convention can't drift between components. */
export function verdictToColorClass(verdict) {
  switch (verdict) {
    case 'adversarial':
      return 'text-verdict-adversarial'
    case 'clean':
      return 'text-verdict-clean'
    default:
      return 'text-muted'
  }
}

export function verdictToBgClass(verdict) {
  switch (verdict) {
    case 'adversarial':
      return 'bg-verdict-adversarial/10 border-verdict-adversarial/30'
    case 'clean':
      return 'bg-verdict-clean/10 border-verdict-clean/30'
    default:
      return 'bg-panel border-hairline'
  }
}

/** 1234.5 -> "1.23s"; 823.1 -> "823ms" */
export function formatProcessingTime(ms) {
  if (typeof ms !== 'number' || Number.isNaN(ms)) return '—'
  if (ms >= 1000) return `${(ms / 1000).toFixed(2)}s`
  return `${Math.round(ms)}ms`
}
