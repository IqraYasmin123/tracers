import { describe, it, expect, beforeEach, vi } from 'vitest'
import { render, screen, act } from '@testing-library/react'
import { SessionProvider, useSession } from './SessionContext'

function TestConsumer() {
  const { sessions, addAnalysis, clearSessions } = useSession()
  return (
    <div>
      <div data-testid="count">{sessions.length}</div>
      <button
        onClick={() =>
          addAnalysis(
            { verdict: 'adversarial', confidence: 0.9, processing_time_ms: 42, sha256_hash: 'abc' },
            { fileName: 'evidence.png' }
          )
        }
      >
        add
      </button>
      <button onClick={clearSessions}>clear</button>
    </div>
  )
}

function renderWithProvider() {
  return render(
    <SessionProvider>
      <TestConsumer />
    </SessionProvider>
  )
}

describe('SessionContext', () => {
  beforeEach(() => {
    window.localStorage.clear()
  })

  it('starts empty when localStorage has no prior data', () => {
    renderWithProvider()
    expect(screen.getByTestId('count')).toHaveTextContent('0')
  })

  it('records a new analysis and persists it to localStorage', async () => {
    renderWithProvider()
    await act(async () => {
      screen.getByText('add').click()
    })
    expect(screen.getByTestId('count')).toHaveTextContent('1')

    const stored = JSON.parse(window.localStorage.getItem('tracer.sessions.v1'))
    expect(stored).toHaveLength(1)
    expect(stored[0]).toMatchObject({
      verdict: 'adversarial',
      confidence: 0.9,
      fileName: 'evidence.png',
      sha256_hash: 'abc',
    })
    expect(stored[0].id).toBeTruthy()
    expect(stored[0].timestamp).toBeTypeOf('number')
  })

  it('loads existing sessions from localStorage on mount', () => {
    window.localStorage.setItem(
      'tracer.sessions.v1',
      JSON.stringify([{ id: '1', timestamp: 1, verdict: 'clean', confidence: 0.5 }])
    )
    renderWithProvider()
    expect(screen.getByTestId('count')).toHaveTextContent('1')
  })

  it('ignores corrupt localStorage data instead of crashing', () => {
    window.localStorage.setItem('tracer.sessions.v1', 'not valid json{{{')
    renderWithProvider()
    expect(screen.getByTestId('count')).toHaveTextContent('0')
  })

  it('clears all sessions', async () => {
    renderWithProvider()
    await act(async () => {
      screen.getByText('add').click()
    })
    expect(screen.getByTestId('count')).toHaveTextContent('1')

    await act(async () => {
      screen.getByText('clear').click()
    })
    expect(screen.getByTestId('count')).toHaveTextContent('0')
    expect(JSON.parse(window.localStorage.getItem('tracer.sessions.v1'))).toEqual([])
  })

  it('throws a clear error when useSession is used outside a provider', () => {
    // Suppress the expected React error boundary console noise for this one assertion.
    const spy = vi.spyOn(console, 'error').mockImplementation(() => {})
    expect(() => render(<TestConsumer />)).toThrow('useSession must be used within a SessionProvider')
    spy.mockRestore()
  })
})
