import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import Cases from './Cases'
import * as apiClient from '../api/client'

vi.spyOn(apiClient, 'checkHealth').mockResolvedValue({ status: 'ok' })

function renderCases() {
  return render(
    <MemoryRouter>
      <Cases />
    </MemoryRouter>
  )
}

const SAMPLE_CASES = [
  {
    id: 'case-1',
    case_number: 'CASE-AAAA1111',
    title: 'First investigation',
    description: null,
    status: 'open',
    created_at: '2026-01-01T00:00:00Z',
    updated_at: '2026-01-01T00:00:00Z',
    evidence_count: 2,
  },
  {
    id: 'case-2',
    case_number: 'CASE-BBBB2222',
    title: 'Second investigation',
    description: null,
    status: 'closed',
    created_at: '2026-01-02T00:00:00Z',
    updated_at: '2026-01-02T00:00:00Z',
    evidence_count: 0,
  },
]

describe('Cases page', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
    vi.spyOn(apiClient, 'checkHealth').mockResolvedValue({ status: 'ok' })
  })

  it('shows the empty state when there are no cases', async () => {
    vi.spyOn(apiClient, 'listCases').mockResolvedValue([])
    renderCases()
    expect(await screen.findByText('No cases yet.')).toBeInTheDocument()
  })

  it('renders real cases returned by the API', async () => {
    vi.spyOn(apiClient, 'listCases').mockResolvedValue(SAMPLE_CASES)
    renderCases()

    expect(await screen.findByText('First investigation')).toBeInTheDocument()
    expect(screen.getByText('Second investigation')).toBeInTheDocument()
    expect(screen.getByText('CASE-AAAA1111')).toBeInTheDocument()
  })

  it('shows an error message when the case list fails to load', async () => {
    vi.spyOn(apiClient, 'listCases').mockRejectedValue(new Error('Backend unreachable'))
    renderCases()
    expect(await screen.findByText(/Could not load cases: Backend unreachable/)).toBeInTheDocument()
  })

  it('re-fetches with a status filter when a filter button is clicked', async () => {
    const listCasesSpy = vi.spyOn(apiClient, 'listCases').mockResolvedValue([])
    renderCases()
    await waitFor(() => expect(listCasesSpy).toHaveBeenCalledWith(undefined))

    const user = userEvent.setup()
    await user.click(screen.getByRole('button', { name: 'Open' }))

    await waitFor(() => expect(listCasesSpy).toHaveBeenLastCalledWith('open'))
  })

  it('creates a new case through the inline form', async () => {
    vi.spyOn(apiClient, 'listCases').mockResolvedValue([])
    const createCaseSpy = vi.spyOn(apiClient, 'createCase').mockResolvedValue({
      ...SAMPLE_CASES[0],
      id: 'new-case',
    })
    renderCases()
    const user = userEvent.setup()

    await user.click(screen.getByRole('button', { name: '+ New Case' }))
    await user.type(screen.getByLabelText('Title'), 'A brand new case')
    await user.click(screen.getByRole('button', { name: 'Create Case' }))

    await waitFor(() =>
      expect(createCaseSpy).toHaveBeenCalledWith({ title: 'A brand new case', description: null })
    )
  })

  it('shows a validation message when creating a case without a title', async () => {
    vi.spyOn(apiClient, 'listCases').mockResolvedValue([])
    const createCaseSpy = vi.spyOn(apiClient, 'createCase')
    renderCases()
    const user = userEvent.setup()

    await user.click(screen.getByRole('button', { name: '+ New Case' }))
    await user.click(screen.getByRole('button', { name: 'Create Case' }))

    expect(await screen.findByText('Title is required.')).toBeInTheDocument()
    expect(createCaseSpy).not.toHaveBeenCalled()
  })
})
