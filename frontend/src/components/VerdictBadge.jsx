import { formatConfidence, verdictToBgClass, verdictToColorClass } from '../utils/format'

export default function VerdictBadge({ verdict, confidence }) {
  return (
    <div
      className={`flex items-center justify-between rounded-lg border px-4 py-3 ${verdictToBgClass(
        verdict
      )}`}
    >
      <span className={`font-mono text-lg font-semibold uppercase tracking-wide ${verdictToColorClass(verdict)}`}>
        {verdict || 'Unknown'}
      </span>
      <span className="font-mono text-sm text-muted">{formatConfidence(confidence)} confidence</span>
    </div>
  )
}
