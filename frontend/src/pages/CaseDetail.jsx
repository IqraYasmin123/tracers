import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import AppLayout from '../components/layout/AppLayout'
import CaseStatusBadge from '../components/CaseStatusBadge'
import VerdictBadge from '../components/VerdictBadge'
import HashTag from '../components/HashTag'
import { getCase, updateCase } from '../api/client'
import { formatProcessingTime } from '../utils/format'

const STATUS_OPTIONS = ['open', 'in_progress', 'closed', 'archived']

export default function CaseDetail() {
  const { caseId } = useParams()
  const [caseData, setCaseData] = useState(null)
  const [status, setStatus] = useState('loading') // 'loading' | 'ready' | 'error'
  const [error, setError] = useState(null)
  const [updatingStatus, setUpdatingStatus] = useState(false)

  function load() {
    setStatus('loading')
    getCase(caseId)
      .then((data) => {
        setCaseData(data)
        setStatus('ready')
      })
      .catch((err) => {
        setError(err.message)
        setStatus('error')
      })
  }

  useEffect(() => {
    load()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [caseId])

  async function handleStatusChange(newStatus) {
    setUpdatingStatus(true)
    try {
      const updated = await updateCase(caseId, { status: newStatus })
      setCaseData((prev) => ({ ...prev, ...updated }))
    } catch (err) {
      setError(err.message)
    } finally {
      setUpdatingStatus(false)
    }
  }

  if (status === 'loading') {
    return (
      <AppLayout title="Case Detail">
        <p className="font-sans text-sm text-muted">Loading case…</p>
      </AppLayout>
    )
  }

  if (status === 'error') {
    return (
      <AppLayout title="Case Detail">
        <div className="rounded-lg border border-verdict-adversarial/30 bg-verdict-adversarial/10 p-4">
          <p className="font-sans text-sm text-verdict-adversarial">
            Could not load this case: {error}
          </p>
        </div>
        <Link to="/cases" className="mt-3 inline-block font-mono text-sm text-cyan hover:underline">
          ← Back to Cases
        </Link>
      </AppLayout>
    )
  }

  return (
    <AppLayout title={caseData.title}>
      <Link to="/cases" className="mb-4 inline-block font-mono text-sm text-cyan hover:underline">
        ← Back to Cases
      </Link>

      <div className="rounded-lg border border-hairline bg-panel p-4">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <div className="font-mono text-xs text-muted">{caseData.case_number}</div>
            <h2 className="mt-1 font-sans text-lg font-semibold text-ink">{caseData.title}</h2>
            {caseData.description && (
              <p className="mt-1 font-sans text-sm text-muted">{caseData.description}</p>
            )}
          </div>
          <div className="flex items-center gap-2">
            <CaseStatusBadge status={caseData.status} />
            <select
              value={caseData.status}
              disabled={updatingStatus}
              onChange={(e) => handleStatusChange(e.target.value)}
              className="rounded-md border border-hairline bg-void px-2 py-1 font-mono text-xs text-ink disabled:opacity-50"
              aria-label="Change case status"
            >
              {STATUS_OPTIONS.map((s) => (
                <option key={s} value={s}>
                  {s.replace('_', ' ')}
                </option>
              ))}
            </select>
          </div>
        </div>
        <div className="mt-3 font-mono text-[11px] text-muted">
          Created {new Date(caseData.created_at).toLocaleString()} · Updated{' '}
          {new Date(caseData.updated_at).toLocaleString()}
        </div>
      </div>

      <div className="mt-6">
        <div className="mb-3 flex items-center justify-between">
          <h3 className="font-mono text-xs uppercase tracking-wide text-muted">
            Evidence ({caseData.evidence_count})
          </h3>
          <Link
            to="/investigation"
            className="font-mono text-xs text-cyan hover:underline"
          >
            + Attach evidence via Investigation →
          </Link>
        </div>

        {caseData.evidence.length === 0 ? (
          <div className="rounded-lg border border-hairline bg-panel p-6 text-center">
            <p className="font-sans text-sm text-muted">
              No evidence attached to this case yet.
            </p>
          </div>
        ) : (
          <div className="space-y-3">
            {caseData.evidence.map((ev) => (
              <div key={ev.id} className="rounded-lg border border-hairline bg-panel p-4">
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <div>
                    <div className="font-sans text-sm text-ink">{ev.original_filename}</div>
                    <div className="mt-1 flex items-center gap-2 font-mono text-[11px] text-muted">
                      <HashTag hash={ev.sha256_hash} />
                      <span>{new Date(ev.uploaded_at).toLocaleString()}</span>
                    </div>
                  </div>
                  {ev.ai_result ? (
                    <div className="w-full sm:w-auto sm:min-w-[280px]">
                      <VerdictBadge verdict={ev.ai_result.verdict} confidence={ev.ai_result.confidence} />
                      {ev.ai_result.attack_type && (
                        <div className="mt-1 text-right font-mono text-[11px] text-muted">
                          {ev.ai_result.attack_type} ·{' '}
                          {formatProcessingTime(ev.ai_result.processing_time_ms)}
                        </div>
                      )}
                    </div>
                  ) : (
                    <span className="font-mono text-xs text-muted">No AI result</span>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </AppLayout>
  )
}
