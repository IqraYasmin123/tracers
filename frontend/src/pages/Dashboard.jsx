import { useEffect, useState } from 'react'
import AppLayout from '../components/layout/AppLayout'
import { checkHealth } from '../api/client'

const PLACEHOLDER_STATS = [
  { label: 'Total Cases', value: '—', note: 'Arrives with Module 13' },
  { label: 'Attacks Detected', value: '—', note: 'Arrives with Module 13' },
  { label: 'Clean Images', value: '—', note: 'Arrives with Module 13' },
  { label: 'Avg. Confidence', value: '—', note: 'Arrives with Module 12' },
]

export default function Dashboard() {
  const [health, setHealth] = useState(null)
  const [healthError, setHealthError] = useState(null)

  useEffect(() => {
    checkHealth()
      .then(setHealth)
      .catch((err) => setHealthError(err.message))
  }, [])

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
        {PLACEHOLDER_STATS.map((stat) => (
          <div key={stat.label} className="rounded-lg border border-hairline bg-panel p-4">
            <div className="font-mono text-2xl font-semibold text-muted">{stat.value}</div>
            <div className="mt-1 font-sans text-sm text-ink">{stat.label}</div>
            <div className="mt-1 font-mono text-[11px] text-muted">{stat.note}</div>
          </div>
        ))}
      </div>

      <div className="mt-6 rounded-lg border border-hairline bg-panel p-6 text-center">
        <p className="font-sans text-sm text-muted">
          Live detection-timeline charts, threat scoring, and attack-type breakdowns are
          available now on the Analytics page. Case statistics arrive with Module 13
          (Case Management).
        </p>
        <div className="mt-3 flex items-center justify-center gap-4">
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
        </div>
      </div>
    </AppLayout>
  )
}
