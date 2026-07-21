/**
 * A horizontal scanline sweep, shown over an image while analysis is running — evokes a
 * forensic scanner rather than a generic spinner. Respects prefers-reduced-motion via the
 * global CSS rule in index.css (animation-duration forced to near-zero).
 */
export default function ScanlineLoader({ label = 'Analyzing…' }) {
  return (
    <div className="relative flex h-full w-full items-center justify-center overflow-hidden rounded-lg border border-hairline bg-panel">
      <div className="pointer-events-none absolute inset-0">
        <div className="absolute left-0 right-0 h-px animate-scanline bg-gradient-to-r from-transparent via-cyan to-transparent shadow-[0_0_12px_2px_rgba(61,214,196,0.6)]" />
      </div>
      <div className="z-10 flex flex-col items-center gap-2">
        <div className="font-mono text-sm tracking-wide text-cyan">{label}</div>
        <div className="font-mono text-xs text-muted">Extracting attention entropy…</div>
      </div>
    </div>
  )
}
