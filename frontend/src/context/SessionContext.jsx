import { createContext, useContext, useEffect, useMemo, useState } from 'react'

/**
 * SessionContext — client-side record of every real analysis run on the Investigation
 * page this browser has performed, persisted to localStorage so it survives refreshes.
 *
 * This is NOT a substitute for Module 13 (Case Management). It has no server-side
 * persistence, no multi-device sync, and no auth scoping — it's a single-browser
 * activity log that Module 12's Analytics page reads from. Real "cases" arrive with
 * Module 13; this just means Analytics has honest live data to chart in the meantime,
 * instead of fabricated numbers.
 */

const STORAGE_KEY = 'tracer.sessions.v1'
const MAX_SESSIONS = 100
// Heatmap PNGs are the only large field on a session record. Keeping all of them for
// 100 sessions risks blowing the ~5MB localStorage quota, so only the most recent
// MAX_HEATMAPS get their image persisted across reloads; older entries keep every other
// field (verdict, confidence, timing, hash) but drop the image bytes on save.
const MAX_HEATMAPS = 12

const SessionContext = createContext(undefined)

function loadFromStorage() {
  if (typeof window === 'undefined') return []
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY)
    if (!raw) return []
    const parsed = JSON.parse(raw)
    if (!Array.isArray(parsed)) return []
    return parsed
  } catch {
    // Corrupt or inaccessible localStorage (e.g. private browsing quirks) — start fresh
    // rather than crashing the app over a client-side cache.
    return []
  }
}

function saveToStorage(sessions) {
  if (typeof window === 'undefined') return
  try {
    const trimmed = sessions.map((session, index) => {
      const isRecent = index < MAX_HEATMAPS
      return isRecent ? session : { ...session, attribution_heatmap_png_base64: null }
    })
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(trimmed))
  } catch {
    // Quota exceeded or storage unavailable — the in-memory list still works for this
    // page load, it just won't persist. Not worth surfacing as a user-facing error.
  }
}

function makeId() {
  if (typeof crypto !== 'undefined' && crypto.randomUUID) return crypto.randomUUID()
  return `${Date.now()}-${Math.random().toString(36).slice(2)}`
}

export function SessionProvider({ children }) {
  const [sessions, setSessions] = useState(() => loadFromStorage())

  useEffect(() => {
    saveToStorage(sessions)
  }, [sessions])

  const addAnalysis = (result, meta = {}) => {
    const record = {
      id: makeId(),
      timestamp: Date.now(),
      fileName: meta.fileName ?? null,
      verdict: result.verdict ?? null,
      confidence: typeof result.confidence === 'number' ? result.confidence : null,
      attack_type: result.attack_type ?? null,
      attack_type_confidence:
        typeof result.attack_type_confidence === 'number' ? result.attack_type_confidence : null,
      processing_time_ms:
        typeof result.processing_time_ms === 'number' ? result.processing_time_ms : null,
      sha256_hash: result.sha256_hash ?? null,
      attribution_method: result.attribution_method ?? null,
      attribution_heatmap_png_base64: result.attribution_heatmap_png_base64 ?? null,
    }
    // Newest first, capped at MAX_SESSIONS.
    setSessions((prev) => [record, ...prev].slice(0, MAX_SESSIONS))
    return record
  }

  const clearSessions = () => setSessions([])

  const value = useMemo(() => ({ sessions, addAnalysis, clearSessions }), [sessions])

  return <SessionContext.Provider value={value}>{children}</SessionContext.Provider>
}

export function useSession() {
  const context = useContext(SessionContext)
  if (context === undefined) {
    throw new Error('useSession must be used within a SessionProvider')
  }
  return context
}
