import { formatConfidence, verdictToColorClass } from '../../utils/format'

/**
 * Grid of the most recent attribution heatmaps captured from real Investigation-page
 * analyses. Only a bounded number of recent sessions retain their heatmap image bytes
 * (see SessionContext's MAX_HEATMAPS) to stay well under localStorage's quota, so this
 * gallery is deliberately "recent", not "complete history".
 */
export default function HeatmapGallery({ sessions }) {
  const withHeatmaps = sessions.filter((s) => s.attribution_heatmap_png_base64)

  if (withHeatmaps.length === 0) {
    return (
      <div className="flex h-[120px] items-center justify-center font-sans text-sm text-muted">
        No attribution heatmaps captured yet — heatmaps appear here after you analyze an
        image on the Investigation page.
      </div>
    )
  }

  return (
    <div className="grid grid-cols-3 gap-3 sm:grid-cols-4 md:grid-cols-6">
      {withHeatmaps.map((s) => (
        <div key={s.id} className="overflow-hidden rounded-md border border-hairline bg-void">
          <img
            src={`data:image/png;base64,${s.attribution_heatmap_png_base64}`}
            alt={`Attribution heatmap — ${s.verdict ?? 'unknown'} verdict`}
            className="aspect-square w-full object-cover"
          />
          <div className="flex items-center justify-between px-1.5 py-1">
            <span className={`font-mono text-[10px] uppercase ${verdictToColorClass(s.verdict)}`}>
              {s.verdict ?? '—'}
            </span>
            <span className="font-mono text-[10px] text-muted">{formatConfidence(s.confidence)}</span>
          </div>
        </div>
      ))}
    </div>
  )
}
