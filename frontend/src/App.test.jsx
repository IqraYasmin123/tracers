import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import App from './App'
import { SessionProvider } from './context/SessionContext'
import * as apiClient from './api/client'

// Every page under AppLayout renders Topbar, which independently calls checkHealth on mount.
vi.spyOn(apiClient, 'checkHealth').mockResolvedValue({ status: 'ok' })
vi.spyOn(apiClient, 'getCaseStats').mockResolvedValue({
  total_cases: 0,
  open_cases: 0,
  in_progress_cases: 0,
  closed_cases: 0,
  archived_cases: 0,
  total_evidence: 0,
  clean_verdicts: 0,
  adversarial_verdicts: 0,
  avg_confidence: null,
})
vi.spyOn(apiClient, 'listCases').mockResolvedValue([])

function renderAt(path) {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <SessionProvider>
        <App />
      </SessionProvider>
    </MemoryRouter>
  )
}

describe('App routing', () => {
  beforeEach(() => {
    window.localStorage.clear()
  })

  // Regression test: Analytics reads live data via useSession(), which throws if rendered
  // outside a SessionProvider. main.jsx must mount SessionProvider above <App /> for every
  // route — including /analytics — to work at all in the real app, not just in isolated
  // component tests that wrap themselves in their own SessionProvider.
  it('renders the Analytics route without crashing', () => {
    renderAt('/analytics')
    expect(screen.getAllByText('Analytics').length).toBeGreaterThan(0)
    expect(screen.getByText(/nothing here is fabricated/i)).toBeInTheDocument()
  })

  it('renders the Dashboard route without crashing', () => {
    renderAt('/dashboard')
    expect(screen.getAllByText('Dashboard').length).toBeGreaterThan(0)
  })

  it('renders the Investigation route without crashing', () => {
    renderAt('/investigation')
    expect(screen.getAllByText('Investigation').length).toBeGreaterThan(0)
  })

  it('renders the Cases route without crashing', () => {
    renderAt('/cases')
    expect(screen.getAllByText('Cases').length).toBeGreaterThan(0)
  })

  it('renders the CaseDetail route without crashing', async () => {
    vi.spyOn(apiClient, 'getCase').mockResolvedValue({
      id: 'case-1',
      case_number: 'CASE-ABCD1234',
      title: 'Test case',
      description: null,
      status: 'open',
      created_at: '2026-01-01T00:00:00Z',
      updated_at: '2026-01-01T00:00:00Z',
      evidence_count: 0,
      evidence: [],
    })
    renderAt('/cases/case-1')
    expect((await screen.findAllByText('Test case')).length).toBeGreaterThan(0)
  })
})
