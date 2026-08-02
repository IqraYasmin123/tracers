/**
 * Horizontal bar chart of attack-type distribution. Hand-rolled SVG, same reasoning as
 * ConfidenceTimelineChart — one small chart doesn't justify a charting dependency.
 */
export default function AttackTypeBarChart({ distribution }) {
  if (!distribution || distribution.length === 0) {
    return (
      <div className="flex h-[120px] items-center justify-center font-sans text-sm text-muted">
        No adversarial attacks detected yet.
      </div>
    )
  }

  const maxCount = Math.max(...distribution.map((d) => d.count))

  return (
    <div className="space-y-2.5" role="img" aria-label="Attack type distribution">
      {distribution.map((d) => (
        <div key={d.type} className="flex items-center gap-3">
          <div className="w-20 shrink-0 truncate font-mono text-xs uppercase text-muted" title={d.type}>
            {d.type}
          </div>
          <div className="h-3 flex-1 overflow-hidden rounded-sm bg-hairline/40">
            <div
              className="h-full rounded-sm bg-verdict-warning"
              style={{ width: `${maxCount > 0 ? (d.count / maxCount) * 100 : 0}%` }}
            />
          </div>
          <div className="w-16 shrink-0 text-right font-mono text-xs text-ink">
            {d.count} ({Math.round(d.pct * 100)}%)
          </div>
        </div>
      ))}
    </div>
  )
}
