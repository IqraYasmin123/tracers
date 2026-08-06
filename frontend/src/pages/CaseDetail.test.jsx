import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import CaseDetail from './CaseDetail'
import * as apiClient from '../api/client'

vi.spyOn(apiClient, 'checkHealth').mockResolvedValue({ status: 'ok' })

function renderCaseDetail(caseId = 'case-1') {
  return render(
    <MemoryRouter initialEntries={[`/cases/${caseId}`]}>
      <Routes>
        <Route path="/cases/:caseId" element={<CaseDetail />} />
      </Routes>
    </MemoryRouter>
  )
}

const SAMPLE_CASE = {
  id: 'case-1',
  case_number: 'CASE-AAAA1111',
  title: 'Suspicious upload investigation',
  description: 'Some notes about this case.',
  status: 'open',
  created_at: '2026-01-01T00:00:00Z',
  updated_at: '2026-01-01T00:00:00Z',
  evidence_count: 1,
  evidence: [
    {
      id: 'evidence-1',
      original_filename: 'photo.png',
      sha256_hash: 'a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2',
      mime_type: 'image/png',
      file_size_bytes: 2048,
      uploaded_at: '2026-01-01T01:00:00Z',
      ai_result: {
        verdict: 'adversarial',
        confidence: 0.92,
        attack_type: 'pgd',
        attack_type_confidence: 0.71,
        attribution_method: 'gradient_saliency',
        attribution_peak_fraction: 0.28,
        explanation_summary: 'Adversarial.',
        explanation_details: [],
        processing_time_ms: 500,
        created_at: '2026-01-01T01:00:00Z',
      },
    },
  ],
}

describe('CaseDetail page', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
    vi.spyOn(apiClient, 'checkHealth').mockResolvedValue({ status: 'ok' })
    vi.spyOn(apiClient, 'listReports').mockResolvedValue([])
  })

  it('renders case info and its evidence', async () => {
    vi.spyOn(apiClient, 'getCase').mockResolvedValue(SAMPLE_CASE)
    renderCaseDetail()

    expect((await screen.findAllByText('Suspicious upload investigation')).length).toBeGreaterThan(0)
    expect(screen.getByText('Some notes about this case.')).toBeInTheDocument()
    expect(screen.getByText('photo.png')).toBeInTheDocument()
    expect(screen.getByText('adversarial')).toBeInTheDocument()
  })

  it('shows the empty-evidence state when a case has no evidence', async () => {
    vi.spyOn(apiClient, 'getCase').mockResolvedValue({
      ...SAMPLE_CASE,
      evidence_count: 0,
      evidence: [],
    })
    renderCaseDetail()
    expect(await screen.findByText('No evidence attached to this case yet.')).toBeInTheDocument()
  })

  it('shows an error message when the case fails to load', async () => {
    vi.spyOn(apiClient, 'getCase').mockRejectedValue(new Error("Case 'case-1' not found."))
    renderCaseDetail()
    expect(
      await screen.findByText(/Could not load this case: Case 'case-1' not found\./)
    ).toBeInTheDocument()
  })

  it('updates the case status via the status dropdown', async () => {
    vi.spyOn(apiClient, 'getCase').mockResolvedValue(SAMPLE_CASE)
    const updateCaseSpy = vi
      .spyOn(apiClient, 'updateCase')
      .mockResolvedValue({ ...SAMPLE_CASE, status: 'closed' })
    renderCaseDetail()
    const user = userEvent.setup()

    await screen.findAllByText('Suspicious upload investigation')
    await user.selectOptions(screen.getByLabelText('Change case status'), 'closed')

    await waitFor(() =>
      expect(updateCaseSpy).toHaveBeenCalledWith('case-1', { status: 'closed' })
    )
  })

  describe('Reports (Module 14)', () => {
    it('shows the empty-reports state when no reports exist yet', async () => {
      vi.spyOn(apiClient, 'getCase').mockResolvedValue(SAMPLE_CASE)
      renderCaseDetail()
      expect(
        await screen.findByText(/No reports generated yet/)
      ).toBeInTheDocument()
    })

    it('renders previously generated reports with a download link', async () => {
      vi.spyOn(apiClient, 'getCase').mockResolvedValue(SAMPLE_CASE)
      vi.spyOn(apiClient, 'listReports').mockResolvedValue([
        {
          id: 'report-1',
          case_id: 'case-1',
          format: 'pdf',
          file_size_bytes: 51200,
          created_at: '2026-01-02T00:00:00Z',
        },
      ])
      renderCaseDetail()

      expect(await screen.findByText('pdf')).toBeInTheDocument()
      expect(screen.getByText(/50\.0 KB/)).toBeInTheDocument()
      expect(screen.getByRole('link', { name: 'Download →' })).toHaveAttribute(
        'href',
        expect.stringContaining('/api/v1/cases/case-1/reports/report-1/download')
      )
    })

    it('generates a PDF report and refreshes the report list', async () => {
      vi.spyOn(apiClient, 'getCase').mockResolvedValue(SAMPLE_CASE)
      const generateReportSpy = vi.spyOn(apiClient, 'generateReport').mockResolvedValue({
        id: 'report-1',
        case_id: 'case-1',
        format: 'pdf',
        file_size_bytes: 51200,
        created_at: '2026-01-02T00:00:00Z',
      })
      renderCaseDetail()
      const user = userEvent.setup()

      await screen.findByText(/No reports generated yet/)
      await user.click(screen.getByRole('button', { name: '+ Generate PDF' }))

      await waitFor(() => expect(generateReportSpy).toHaveBeenCalledWith('case-1', 'pdf'))
    })

    it('shows an error message when report generation fails', async () => {
      vi.spyOn(apiClient, 'getCase').mockResolvedValue(SAMPLE_CASE)
      vi.spyOn(apiClient, 'generateReport').mockRejectedValue(new Error('Backend unreachable'))
      renderCaseDetail()
      const user = userEvent.setup()

      await screen.findByText(/No reports generated yet/)
      await user.click(screen.getByRole('button', { name: '+ Generate DOCX' }))

      expect(await screen.findByText('Backend unreachable')).toBeInTheDocument()
    })
  })
})
