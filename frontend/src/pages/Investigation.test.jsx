import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import Investigation from './Investigation'
import * as apiClient from '../api/client'

// Topbar independently calls checkHealth on mount — stub it so tests don't depend on it.
vi.spyOn(apiClient, 'checkHealth').mockResolvedValue({ status: 'ok' })

function renderInvestigation() {
  return render(
    <MemoryRouter>
      <Investigation />
    </MemoryRouter>
  )
}

function makeFile() {
  return new File(['fake image bytes'], 'evidence.png', { type: 'image/png' })
}

describe('Investigation page', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
    vi.spyOn(apiClient, 'checkHealth').mockResolvedValue({ status: 'ok' })
  })

  it('disables Analyze until a file is selected', () => {
    renderInvestigation()
    expect(screen.getByRole('button', { name: /analyze image/i })).toBeDisabled()
  })

  it('runs a full analysis and displays the real result fields', async () => {
    vi.spyOn(apiClient, 'analyzeImage').mockResolvedValue({
      verdict: 'adversarial',
      confidence: 0.92,
      attack_type: 'pgd',
      attack_type_confidence: 0.71,
      attribution_method: 'gradient_saliency',
      attribution_heatmap_png_base64: 'iVBORw0KGgo=',
      attribution_peak_fraction: 0.28,
      explanation_summary: 'This image was classified as ADVERSARIAL with 92.0% confidence.',
      explanation_details: ['A supporting detail.'],
      sha256_hash: 'deadbeef'.repeat(8),
      processing_time_ms: 1234.5,
    })

    renderInvestigation()
    const user = userEvent.setup()

    const fileInput = document.querySelector('input[type="file"]')
    await user.upload(fileInput, makeFile())

    const analyzeButton = screen.getByRole('button', { name: /analyze image/i })
    expect(analyzeButton).toBeEnabled()
    await user.click(analyzeButton)

    await waitFor(() => {
      expect(screen.getByText('adversarial')).toBeInTheDocument()
    })
    expect(screen.getByText('PGD')).toBeInTheDocument()
    expect(
      screen.getByText('This image was classified as ADVERSARIAL with 92.0% confidence.')
    ).toBeInTheDocument()
    expect(screen.getByText('A supporting detail.')).toBeInTheDocument()
    expect(screen.getByText('1.23s')).toBeInTheDocument()
  })

  it('displays a clear error message when the backend is unavailable', async () => {
    vi.spyOn(apiClient, 'analyzeImage').mockRejectedValue(
      new apiClient.ApiError('No trained detector available.', 503)
    )

    renderInvestigation()
    const user = userEvent.setup()

    const fileInput = document.querySelector('input[type="file"]')
    await user.upload(fileInput, makeFile())
    await user.click(screen.getByRole('button', { name: /analyze image/i }))

    await waitFor(() => {
      expect(screen.getByText('No trained detector available.')).toBeInTheDocument()
    })
  })
})
