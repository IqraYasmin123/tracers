import { caseStatusToBgClass, caseStatusToColorClass, formatCaseStatus } from '../utils/format'

export default function CaseStatusBadge({ status }) {
  return (
    <span
      className={`inline-block rounded-full border px-3 py-1 font-mono text-xs font-semibold uppercase tracking-wide ${caseStatusToBgClass(
        status
      )} ${caseStatusToColorClass(status)}`}
    >
      {formatCaseStatus(status)}
    </span>
  )
}
