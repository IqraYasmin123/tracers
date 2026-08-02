import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import App from './App'
import { SessionProvider } from './context/SessionContext'
import * as apiClient from './api/client'

// Every page under AppLayout renders Topbar, which independently calls checkHealth on mount.
vi.spyOn(apiClient, 'checkHealth').mockResolvedValue({ status: 'ok' })

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
})
