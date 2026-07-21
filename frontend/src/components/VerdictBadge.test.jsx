import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import VerdictBadge from './VerdictBadge'

describe('VerdictBadge', () => {
  it('displays the verdict and formatted confidence', () => {
    render(<VerdictBadge verdict="adversarial" confidence={0.92} />)
    expect(screen.getByText('adversarial')).toBeInTheDocument()
    expect(screen.getByText('92.0% confidence')).toBeInTheDocument()
  })

  it('displays a clean verdict correctly', () => {
    render(<VerdictBadge verdict="clean" confidence={0.87} />)
    expect(screen.getByText('clean')).toBeInTheDocument()
    expect(screen.getByText('87.0% confidence')).toBeInTheDocument()
  })

  it('falls back gracefully when verdict is missing', () => {
    render(<VerdictBadge verdict={undefined} confidence={0.5} />)
    expect(screen.getByText('Unknown')).toBeInTheDocument()
  })
})
