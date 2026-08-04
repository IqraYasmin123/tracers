import { useEffect, useState } from 'react'
import AppLayout from '../components/layout/AppLayout'
import { checkHealth, getCaseStats } from '../api/client'
import { formatConfidence } from '../utils/format'

export default function Dashboard() {
  const [health, setHealth] = useState(null)
  const [healthError, setHealthError] = useState(null)
  const [caseStats, setCaseStats] = useState(null)
  const [caseStatsError, setCaseStatsError] = useState(null)

  useEffect(() => {
    checkHealth()
      .then(setHealth)
      .catch((err) => setHealthError(err.message))
  }, [])

  useEffect(() => {
    getCaseStats()
      .then(setCaseStats)
      .catch((err) => setCaseStatsError(err.message))
  }, [])

  const stats = caseStats
    ? [
        { label: 'Total Cases', value: caseStats.total_cases, note: 'live' },
        { label: 'Attacks Detected', value: caseStats.adversarial_verdicts, note: 'live' },
        { label: 'Clean Images', value: caseStats.clean_verdicts, note: 'live' },
        {
          label: 'Avg. Confidence',
          value: caseStats.avg_confidence !== null ? formatConfidence(caseStats.avg_confidence) : '—',
          note: 'across all evidence',
        },
      ]
    : [
        { label: 'Total Cases', value: '—', note: caseStatsError || 'Loading…' },
        { label: 'Attacks Detected', value: '—', note: caseStatsError || 'Loading…' },
        { label: 'Clean Images', value: '—', note: caseStatsError || 'Loading…' },
        { label: 'Avg. Confidence', value: '—', note: caseStatsError || 'Loading…' },
      ]

  return (
    <AppLayout title="Dashboard">
      <div className="mb-6 rounded-lg border border-hairline bg-panel p-4">
        <div className="font-mono text-xs uppercase tracking-wide text-muted">
          System Status <span className="text-cyan">(live)</span>
        </div>
        <div className="mt-2 font-sans text-sm text-ink">
          {health && (
            <span className="text-verdict-clean">
              AI engine reachable — {health.status}
            </span>
          )}
          {healthError && (
            <span className="text-verdict-adversarial">
              AI engine unreachable — {healthError}
            </span>
          )}
          {!health && !healthError && <span className="text-muted">Checking…</span>}
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
        {stats.map((stat) => (
          <div key={stat.label} className="rounded-lg border border-hairline bg-panel p-4">
            <div className="font-mono text-2xl font-semibold text-ink">{stat.value}</div>
            <div className="mt-1 font-sans text-sm text-ink">{stat.label}</div>
            <div className="mt-1 font-mono text-[11px] text-muted">{stat.note}</div>
          </div>
        ))}
      </div>

      <div className="mt-6 rounded-lg border border-hairline bg-panel p-6 text-center">
        <p className="font-sans text-sm text-muted">
          Live detection-timeline charts, threat scoring, and attack-type breakdowns are on
          the Analytics page. Manage investigations and attach evidence on the Cases page.
        </p>
        <div className="mt-3 flex flex-wrap items-center justify-center gap-4">
          <a
            href="/investigation"
            className="font-mono text-sm text-cyan hover:underline"
          >
            Run a real analysis on the Investigation page →
          </a>
          <a
            href="/analytics"
            className="font-mono text-sm text-cyan hover:underline"
          >
            View Analytics →
          </a>
          <a
            href="/cases"
            className="font-mono text-sm text-cyan hover:underline"
          >
            View Cases →
          </a>
        </div>
      </div>
    </AppLayout>
  )
}
