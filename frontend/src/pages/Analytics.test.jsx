import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import Analytics from './Analytics'
import { SessionProvider } from '../context/SessionContext'
import * as apiClient from '../api/client'

vi.spyOn(apiClient, 'checkHealth').mockResolvedValue({ status: 'ok' })

function renderAnalytics() {
  return render(
    <MemoryRouter>
      <SessionProvider>
        <Analytics />
      </SessionProvider>
    </MemoryRouter>
  )
}

function seedSessions(sessions) {
  window.localStorage.setItem('tracer.sessions.v1', JSON.stringify(sessions))
}

describe('Analytics page', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
    vi.spyOn(apiClient, 'checkHealth').mockResolvedValue({ status: 'ok' })
    window.localStorage.clear()
  })

  it('shows the empty state and a CTA when there are no analyses yet', () => {
    renderAnalytics()
    expect(screen.getByText(/live charts below will populate/i)).toBeInTheDocument()
    expect(screen.getByText(/run a real analysis on the investigation page/i)).toBeInTheDocument()
    expect(screen.getByText('Total Analyses').parentElement).toHaveTextContent('0')
  })

  it('always shows the historical detector metrics, even with no live data', () => {
    renderAnalytics()
    expect(screen.getByText('Binary Accuracy')).toBeInTheDocument()
    expect(screen.getByText('86%')).toBeInTheDocument()
    expect(screen.getByText('0.95')).toBeInTheDocument()
  })

  it('always shows the honest placeholders for Modules 13 and 9', () => {
    renderAnalytics()
    expect(screen.getByText('Arrives with Module 13 (Case Management)')).toBeInTheDocument()
    expect(screen.getByText(/module 9's deferred async job queue/i)).toBeInTheDocument()
  })

  it('renders real computed stats from seeded live session data', () => {
    seedSessions([
      {
        id: '1',
        timestamp: 1000,
        verdict: 'adversarial',
        confidence: 0.9,
        attack_type: 'pgd',
        attack_type_confidence: 0.7,
        processing_time_ms: 1200,
      },
      {
        id: '2',
        timestamp: 2000,
        verdict: 'clean',
        confidence: 0.6,
        attack_type: null,
        processing_time_ms: 800,
      },
    ])

    renderAnalytics()

    expect(screen.queryByText(/live charts below will populate/i)).not.toBeInTheDocument()
    expect(screen.getByText('Total Analyses').parentElement).toHaveTextContent('2')
    expect(screen.getByText('75.0%')).toBeInTheDocument() // avg confidence (0.9+0.6)/2
    // AttackTypeBarChart renders the raw type string; uppercase styling is CSS-only.
    expect(screen.getByText('pgd')).toBeInTheDocument()
  })

  it('clears session history after a confirm click', async () => {
    seedSessions([{ id: '1', timestamp: 1000, verdict: 'clean', confidence: 0.5 }])
    renderAnalytics()
    const user = userEvent.setup()

    const clearButton = screen.getByText('Clear session history')
    await user.click(clearButton)
    expect(screen.getByText('Click again to confirm')).toBeInTheDocument()

    await user.click(screen.getByText('Click again to confirm'))
    expect(screen.getByText(/live charts below will populate/i)).toBeInTheDocument()
  })
})
