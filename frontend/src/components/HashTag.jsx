import { useState } from 'react'
import { truncateHash } from '../utils/format'

/**
 * The recurring "chain of custody" signature element — a monospace hash pill shown
 * wherever a piece of evidence appears. Ties the real SHA-256 hashing feature from the
 * backend (Module 9) directly into the visual identity of the whole app, rather than
 * burying it in a details panel.
 */
export default function HashTag({ hash }) {
  const [copied, setCopied] = useState(false)

  async function handleCopy() {
    try {
      await navigator.clipboard.writeText(hash)
      setCopied(true)
      setTimeout(() => setCopied(false), 1500)
    } catch {
      // Clipboard API can fail in some contexts (e.g. insecure origin) — fail silently,
      // the hash is still visible and selectable by hand.
    }
  }

  if (!hash) return null

  return (
    <button
      onClick={handleCopy}
      className="inline-flex items-center gap-1.5 rounded-full border border-hairline bg-panel px-2.5 py-1 font-mono text-[11px] text-muted transition-colors hover:border-cyan/50 hover:text-ink"
      title={hash}
    >
      <span className="uppercase tracking-wide text-cyan/70">SHA256</span>
      <span>{truncateHash(hash)}</span>
      <span className="text-cyan">{copied ? '✓' : '⧉'}</span>
    </button>
  )
}
