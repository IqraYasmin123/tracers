import { verdictToColorClass } from '../../utils/format'

const WIDTH = 640
const HEIGHT = 180
const PAD = { top: 16, right: 16, bottom: 24, left: 32 }

/**
 * Confidence-over-time line chart. Deliberately hand-rolled SVG (no charting library) —
 * the app has no chart dependency yet, and this keeps the bundle and dependency surface
 * small for a single line series. Points are colored by verdict; hovering isn't wired up
 * yet (no tooltip lib), so each point instead gets a native <title> for accessible
 * on-hover detail.
 */
export default function ConfidenceTimelineChart({ points }) {
  if (!points || points.length === 0) {
    return (
      <div className="flex h-[180px] items-center justify-center font-sans text-sm text-muted">
        No analyses yet — results will appear here as you run them.
      </div>
    )
  }

  const innerW = WIDTH - PAD.left - PAD.right
  const innerH = HEIGHT - PAD.top - PAD.bottom
  const n = points.length

  const x = (i) => PAD.left + (n === 1 ? innerW / 2 : (i / (n - 1)) * innerW)
  const y = (conf) => PAD.top + (1 - conf) * innerH

  const linePath = points.map((p, i) => `${i === 0 ? 'M' : 'L'} ${x(i).toFixed(1)} ${y(p.confidence).toFixed(1)}`).join(' ')

  return (
    <svg viewBox={`0 0 ${WIDTH} ${HEIGHT}`} className="w-full" role="img" aria-label="Confidence over time">
      {/* Gridlines at 0%, 50%, 100% confidence */}
      {[0, 0.5, 1].map((frac) => (
        <g key={frac}>
          <line
            x1={PAD.left}
            x2={WIDTH - PAD.right}
            y1={y(frac)}
            y2={y(frac)}
            stroke="#232733"
            strokeWidth="1"
          />
          <text x={4} y={y(frac) + 3} className="fill-muted" fontSize="9" fontFamily="monospace">
            {Math.round(frac * 100)}%
          </text>
        </g>
      ))}

      <path d={linePath} fill="none" stroke="#3DD6C4" strokeWidth="1.5" opacity="0.5" />

      {points.map((p, i) => (
        <circle
          key={p.id ?? i}
          cx={x(i)}
          cy={y(p.confidence)}
          r={3.5}
          fill="currentColor"
          className={verdictToColorClass(p.verdict)}
        >
          <title>
            {`${p.verdict ?? 'unknown'} — ${(p.confidence * 100).toFixed(1)}% confidence`}
          </title>
        </circle>
      ))}
    </svg>
  )
}
