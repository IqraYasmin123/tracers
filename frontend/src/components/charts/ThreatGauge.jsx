const LEVEL_CONFIG = {
  low: { color: '#5FD98A', label: 'LOW' },
  moderate: { color: '#E8A83D', label: 'MODERATE' },
  high: { color: '#E85C4A', label: 'HIGH' },
  'no-data': { color: '#8B93A3', label: 'NO DATA' },
}

const WIDTH = 220
const HEIGHT = 130
const CX = WIDTH / 2
const CY = 110
const R = 90

/** Point on the gauge's semicircle for a given 0..1 fraction (0 = far left/score 0,
 * 1 = far right/score 1), sweeping through the top. */
function pointOnArc(fraction) {
  const angle = Math.PI - fraction * Math.PI // PI (left) -> 0 (right)
  return {
    x: CX + R * Math.cos(angle),
    y: CY - R * Math.sin(angle),
  }
}

function arcPath(fromFraction, toFraction) {
  const start = pointOnArc(fromFraction)
  const end = pointOnArc(toFraction)
  const largeArc = toFraction - fromFraction > 0.5 ? 1 : 0
  return `M ${start.x} ${start.y} A ${R} ${R} 0 ${largeArc} 1 ${end.x} ${end.y}`
}

/**
 * Semi-circle threat gauge. score is a 0..1 float from computeThreatLevel (recent-window
 * mean adversarial confidence); level drives the label and needle color. A null score
 * (no data yet) renders a flat, dim arc with a "NO DATA" label instead of pretending the
 * threat level is known to be zero.
 */
export default function ThreatGauge({ score, level, sampleSize }) {
  const config = LEVEL_CONFIG[level] ?? LEVEL_CONFIG['no-data']
  const clampedScore = typeof score === 'number' ? Math.min(Math.max(score, 0), 1) : 0
  const needleAngle = Math.PI - clampedScore * Math.PI
  const needleTip = {
    x: CX + (R - 14) * Math.cos(needleAngle),
    y: CY - (R - 14) * Math.sin(needleAngle),
  }

  return (
    <div className="flex flex-col items-center">
      <svg viewBox={`0 0 ${WIDTH} ${HEIGHT}`} className="w-full max-w-[240px]" role="img" aria-label="Threat level gauge">
        {/* Background track */}
        <path d={arcPath(0, 1)} fill="none" stroke="#232733" strokeWidth="14" strokeLinecap="round" />
        {/* Colored zones */}
        <path d={arcPath(0, 0.2)} fill="none" stroke="#5FD98A" strokeWidth="14" strokeLinecap="round" opacity="0.35" />
        <path d={arcPath(0.2, 0.5)} fill="none" stroke="#E8A83D" strokeWidth="14" opacity="0.35" />
        <path d={arcPath(0.5, 1)} fill="none" stroke="#E85C4A" strokeWidth="14" strokeLinecap="round" opacity="0.35" />

        {level !== 'no-data' && (
          <line
            x1={CX}
            y1={CY}
            x2={needleTip.x}
            y2={needleTip.y}
            stroke={config.color}
            strokeWidth="3"
            strokeLinecap="round"
          />
        )}
        <circle cx={CX} cy={CY} r="6" fill={config.color} />
      </svg>
      <div className="-mt-2 text-center">
        <div className="font-mono text-xl font-semibold" style={{ color: config.color }}>
          {config.label}
        </div>
        <div className="font-mono text-[11px] text-muted">
          {level === 'no-data'
            ? 'Run an analysis to populate'
            : `score ${score.toFixed(2)} · last ${sampleSize} analys${sampleSize === 1 ? 'is' : 'es'}`}
        </div>
      </div>
    </div>
  )
}
