import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import Settings from './Settings'
import { AuthProvider } from '../context/AuthContext'
import * as apiClient from '../api/client'

function renderSettings() {
  return render(
    <MemoryRouter>
      <AuthProvider>
        <Settings />
      </AuthProvider>
    </MemoryRouter>
  )
}

describe('Settings', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
    // AppLayout renders Sidebar, which calls useAuth() — same no-token setup Login.test.jsx
    // uses, so AuthProvider resolves to 'unauthenticated' immediately without a network call.
    vi.spyOn(apiClient, 'getStoredToken').mockReturnValue(null)
  })

  it('does not claim notifications or two-factor auth are wired up (both are honestly unimplemented)', () => {
    renderSettings()
    const notImplementedNotes = screen.getAllByText('Not yet implemented')
    // 2 notification toggles + two-factor auth = 3 honest "not yet implemented" labels
    expect(notImplementedNotes).toHaveLength(3)
    expect(screen.queryByText(/Module 16/)).not.toBeInTheDocument()
  })

  it('submits current and new password to the real API on valid input', async () => {
    vi.spyOn(apiClient, 'changePassword').mockResolvedValue(undefined)
    renderSettings()
    const user = userEvent.setup()

    await user.type(screen.getByLabelText(/current password/i), 'oldpass123')
    await user.type(screen.getByLabelText(/^new password/i), 'newpass456')
    await user.type(screen.getByLabelText(/confirm new password/i), 'newpass456')
    await user.click(screen.getByRole('button', { name: /change password/i }))

    expect(apiClient.changePassword).toHaveBeenCalledWith('oldpass123', 'newpass456')
    expect(await screen.findByText('Password changed successfully.')).toBeInTheDocument()
  })

  it('shows an error and does not call the API when new password and confirmation do not match', async () => {
    vi.spyOn(apiClient, 'changePassword').mockResolvedValue(undefined)
    renderSettings()
    const user = userEvent.setup()

    await user.type(screen.getByLabelText(/current password/i), 'oldpass123')
    await user.type(screen.getByLabelText(/^new password/i), 'newpass456')
    await user.type(screen.getByLabelText(/confirm new password/i), 'somethingelse')
    await user.click(screen.getByRole('button', { name: /change password/i }))

    expect(await screen.findByText('New password and confirmation do not match.')).toBeInTheDocument()
    expect(apiClient.changePassword).not.toHaveBeenCalled()
  })

  it('shows an error and does not call the API when the new password is too short', async () => {
    vi.spyOn(apiClient, 'changePassword').mockResolvedValue(undefined)
    renderSettings()
    const user = userEvent.setup()

    await user.type(screen.getByLabelText(/current password/i), 'oldpass123')
    await user.type(screen.getByLabelText(/^new password/i), 'short')
    await user.type(screen.getByLabelText(/confirm new password/i), 'short')
    await user.click(screen.getByRole('button', { name: /change password/i }))

    expect(
      await screen.findByText('New password must be at least 8 characters.')
    ).toBeInTheDocument()
    expect(apiClient.changePassword).not.toHaveBeenCalled()
  })

  it('shows the backend error message when the current password is wrong', async () => {
    vi.spyOn(apiClient, 'changePassword').mockRejectedValue(
      new apiClient.ApiError('Current password is incorrect.', 400)
    )
    renderSettings()
    const user = userEvent.setup()

    await user.type(screen.getByLabelText(/current password/i), 'wrongold')
    await user.type(screen.getByLabelText(/^new password/i), 'newpass456')
    await user.type(screen.getByLabelText(/confirm new password/i), 'newpass456')
    await user.click(screen.getByRole('button', { name: /change password/i }))

    expect(await screen.findByText('Current password is incorrect.')).toBeInTheDocument()
  })

  it('clears the form fields after a successful password change', async () => {
    vi.spyOn(apiClient, 'changePassword').mockResolvedValue(undefined)
    renderSettings()
    const user = userEvent.setup()

    await user.type(screen.getByLabelText(/current password/i), 'oldpass123')
    await user.type(screen.getByLabelText(/^new password/i), 'newpass456')
    await user.type(screen.getByLabelText(/confirm new password/i), 'newpass456')
    await user.click(screen.getByRole('button', { name: /change password/i }))

    await screen.findByText('Password changed successfully.')
    expect(screen.getByLabelText(/current password/i)).toHaveValue('')
    expect(screen.getByLabelText(/^new password/i)).toHaveValue('')
    expect(screen.getByLabelText(/confirm new password/i)).toHaveValue('')
  })
})
