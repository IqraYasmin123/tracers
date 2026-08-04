import { useEffect, useState } from 'react'
import AppLayout from '../components/layout/AppLayout'
import ConfidenceTimelineChart from '../components/charts/ConfidenceTimelineChart'
import AttackTypeBarChart from '../components/charts/AttackTypeBarChart'
import ThreatGauge from '../components/charts/ThreatGauge'
import HeatmapGallery from '../components/charts/HeatmapGallery'
import { useSession } from '../context/SessionContext'
import { getCaseStats } from '../api/client'
import { formatConfidence, formatProcessingTime } from '../utils/format'
import {
  computeVerdictCounts,
  computeAttackTypeDistribution,
  computeAvgConfidence,
  computeAvgProcessingTime,
  computeConfidenceTimeline,
  computeThreatLevel,
} from '../utils/analytics'

/**
 * Real, offline evaluation metrics from Module 5's Adversarial Detection Engine —
 * NOT computed live. Ground-truth accuracy/AUC/etc. require a labeled evaluation set,
 * which arbitrary uploads on the Investigation page don't have. Rather than fabricate a
 * live-looking metric, these are the actual numbers from that module's test run, clearly
 * labeled as historical. Only fields Module 5 actually reported are shown — precision/
 * recall/F1 aren't listed because they weren't part of that module's verified output.
 */
const HISTORICAL_DETECTOR_METRICS = [
  { label: 'Binary Accuracy', value: '86%', note: 'clean vs. adversarial' },
  { label: 'AUC', value: '0.95', note: 'binary classification' },
  { label: 'Attack-Type Accuracy', value: '74%', note: 'attack family classification' },
]

function StatCard({ label, value, note }) {
  return (
    <div className="rounded-lg border border-hairline bg-panel p-4">
      <div className="font-mono text-2xl font-semibold text-ink">{value}</div>
      <div className="mt-1 font-sans text-sm text-ink">{label}</div>
      {note && <div className="mt-1 font-mono text-[11px] text-muted">{note}</div>}
    </div>
  )
}

function Panel({ title, subtitle, children }) {
  return (
    <div className="rounded-lg border border-hairline bg-panel p-4">
      <div className="mb-3 flex items-baseline justify-between">
        <div className="font-mono text-xs uppercase tracking-wide text-muted">{title}</div>
        {subtitle && <div className="font-mono text-[11px] text-muted">{subtitle}</div>}
      </div>
      {children}
    </div>
  )
}

export default function Analytics() {
  const { sessions, clearSessions } = useSession()
  const [confirmingClear, setConfirmingClear] = useState(false)

  // Case Statistics (Module 13) — real, but scoped to every case/evidence in the database,
  // not this browser's session. Fetched independently from the live session data above so
  // a backend hiccup here doesn't block the (always-available) session-derived panels.
  const [caseStats, setCaseStats] = useState(null)
  const [caseStatsError, setCaseStatsError] = useState(null)

  useEffect(() => {
    getCaseStats()
      .then(setCaseStats)
      .catch((err) => setCaseStatsError(err.message))
  }, [])

  const verdictCounts = computeVerdictCounts(sessions)
  const attackDistribution = computeAttackTypeDistribution(sessions)
  const avgConfidence = computeAvgConfidence(sessions)
  const avgProcessingTime = computeAvgProcessingTime(sessions)
  const timeline = computeConfidenceTimeline(sessions)
  const threat = computeThreatLevel(sessions)

  function handleClearClick() {
    if (confirmingClear) {
      clearSessions()
      setConfirmingClear(false)
    } else {
      setConfirmingClear(true)
    }
  }

  return (
    <AppLayout title="Analytics">
      <div className="mb-4 flex items-start justify-between gap-4">
        <p className="font-sans text-sm text-muted">
          Computed live from the <span className="text-ink">{verdictCounts.total}</span> real
          analys{verdictCounts.total === 1 ? 'is' : 'es'} you've run on this browser via the
          Investigation page — nothing here is fabricated.
        </p>
        {sessions.length > 0 && (
          <button
            onClick={handleClearClick}
            onBlur={() => setConfirmingClear(false)}
            className="shrink-0 rounded-md border border-hairline px-3 py-1.5 font-mono text-xs text-muted transition-colors hover:border-verdict-adversarial/50 hover:text-verdict-adversarial"
          >
            {confirmingClear ? 'Click again to confirm' : 'Clear session history'}
          </button>
        )}
      </div>

      {sessions.length === 0 && (
        <div className="mb-6 rounded-lg border border-hairline bg-panel p-6 text-center">
          <p className="font-sans text-sm text-muted">
            No analyses yet. Live charts below will populate as soon as you run real
            analyses on the Investigation page.
          </p>
          <a
            href="/investigation"
            className="mt-3 inline-block font-mono text-sm text-cyan hover:underline"
          >
            Run a real analysis on the Investigation page →
          </a>
        </div>
      )}

      {/* Live session summary */}
      <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
        <StatCard label="Total Analyses" value={verdictCounts.total} note="this session" />
        <StatCard label="Clean" value={verdictCounts.clean} />
        <StatCard label="Adversarial" value={verdictCounts.adversarial} />
        <StatCard
          label="Avg. Confidence"
          value={avgConfidence !== null ? formatConfidence(avgConfidence) : '—'}
        />
      </div>

      <div className="mt-6 grid gap-6 lg:grid-cols-3">
        <Panel title="Threat Level" subtitle="last 10 analyses">
          <ThreatGauge score={threat.score} level={threat.level} sampleSize={threat.sampleSize} />
        </Panel>

        <div className="lg:col-span-2">
          <Panel title="Confidence Over Time" subtitle="live">
            <ConfidenceTimelineChart points={timeline} />
          </Panel>
        </div>
      </div>

      <div className="mt-6 grid gap-6 lg:grid-cols-2">
        <Panel title="Attack Type Distribution" subtitle="live">
          <AttackTypeBarChart distribution={attackDistribution} />
        </Panel>

        <Panel title="Processing Time" subtitle="live">
          <div className="flex h-[120px] flex-col items-center justify-center">
            <div className="font-mono text-3xl font-semibold text-ink">
              {avgProcessingTime !== null ? formatProcessingTime(avgProcessingTime) : '—'}
            </div>
            <div className="mt-1 font-sans text-sm text-muted">average per analysis</div>
          </div>
        </Panel>
      </div>

      <div className="mt-6">
        <Panel title="Attribution Heatmap Gallery" subtitle={`most recent, up to 12`}>
          <HeatmapGallery sessions={sessions} />
        </Panel>
      </div>

      {/* Historical model evaluation — clearly separated from live session data above */}
      <div className="mt-6">
        <Panel title="Detector Model Performance" subtitle="historical — Module 5 offline evaluation">
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
            {HISTORICAL_DETECTOR_METRICS.map((m) => (
              <div key={m.label}>
                <div className="font-mono text-2xl font-semibold text-cyan">{m.value}</div>
                <div className="mt-1 font-sans text-sm text-ink">{m.label}</div>
                <div className="mt-0.5 font-mono text-[11px] text-muted">{m.note}</div>
              </div>
            ))}
          </div>
        </Panel>
      </div>

      {/* Honest placeholders — same pattern as Module 11's Dashboard */}
      <div className="mt-6 grid gap-6 md:grid-cols-2">
        <div className="rounded-lg border border-hairline bg-panel p-4">
          <div className="mb-2 flex items-baseline justify-between">
            <div className="font-mono text-xs uppercase tracking-wide text-muted">
              Case Statistics
            </div>
            <div className="font-mono text-[11px] text-muted">
              live — every case in the database
            </div>
          </div>
          {caseStatsError && (
            <p className="font-sans text-sm text-verdict-adversarial">
              Could not load: {caseStatsError}
            </p>
          )}
          {!caseStats && !caseStatsError && (
            <p className="font-sans text-sm text-muted">Loading…</p>
          )}
          {caseStats && (
            <div className="grid grid-cols-2 gap-3">
              <div>
                <div className="font-mono text-xl font-semibold text-ink">{caseStats.total_cases}</div>
                <div className="font-sans text-xs text-muted">Total Cases</div>
              </div>
              <div>
                <div className="font-mono text-xl font-semibold text-ink">{caseStats.total_evidence}</div>
                <div className="font-sans text-xs text-muted">Evidence Files</div>
              </div>
              <div>
                <div className="font-mono text-xl font-semibold text-verdict-adversarial">
                  {caseStats.adversarial_verdicts}
                </div>
                <div className="font-sans text-xs text-muted">Adversarial</div>
              </div>
              <div>
                <div className="font-mono text-xl font-semibold text-verdict-clean">
                  {caseStats.clean_verdicts}
                </div>
                <div className="font-sans text-xs text-muted">Clean</div>
              </div>
            </div>
          )}
        </div>
        <div className="rounded-lg border border-hairline bg-panel p-4">
          <div className="font-mono text-xs uppercase tracking-wide text-muted">
            Live Reconstruction Comparison
          </div>
          <div className="mt-2 font-sans text-sm text-muted">
            Arrives with Module 9's deferred async job queue
          </div>
        </div>
      </div>
    </AppLayout>
  )
}
