import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import Login from './Login'
import { AuthProvider } from '../context/AuthContext'
import * as apiClient from '../api/client'

function renderLogin() {
  return render(
    <MemoryRouter initialEntries={['/login']}>
      <AuthProvider>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/dashboard" element={<div>Dashboard page</div>} />
        </Routes>
      </AuthProvider>
    </MemoryRouter>
  )
}

describe('Login', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
    // No stored token by default — AuthProvider resolves to 'unauthenticated' immediately
    // without a network call, so Login renders right away in every test below.
    vi.spyOn(apiClient, 'getStoredToken').mockReturnValue(null)
  })

  it('shows validation errors when submitting an empty form', async () => {
    renderLogin()
    const user = userEvent.setup()

    await user.click(screen.getByRole('button', { name: /sign in/i }))

    expect(await screen.findByText('Enter your email.')).toBeInTheDocument()
    expect(await screen.findByText('Enter your password.')).toBeInTheDocument()
  })

  it('shows an error for an invalid email format', async () => {
    renderLogin()
    const user = userEvent.setup()

    await user.type(screen.getByLabelText(/email/i), 'not-an-email')
    await user.type(screen.getByLabelText(/password/i), 'validpassword123')
    await user.click(screen.getByRole('button', { name: /sign in/i }))

    expect(await screen.findByText('Enter a valid email address.')).toBeInTheDocument()
  })

  it('shows an error for a too-short password', async () => {
    renderLogin()
    const user = userEvent.setup()

    await user.type(screen.getByLabelText(/email/i), 'user@example.com')
    await user.type(screen.getByLabelText(/password/i), 'short')
    await user.click(screen.getByRole('button', { name: /sign in/i }))

    expect(await screen.findByText('Password must be at least 8 characters.')).toBeInTheDocument()
  })

  it('calls the real login API and redirects to the dashboard on success', async () => {
    vi.spyOn(apiClient, 'login').mockResolvedValue({ access_token: 'real-token' })
    vi.spyOn(apiClient, 'getCurrentUser').mockResolvedValue({
      id: '1',
      username: 'alice',
      email: 'user@example.com',
      role: 'investigator',
    })
    renderLogin()
    const user = userEvent.setup()

    await user.type(screen.getByLabelText(/email/i), 'user@example.com')
    await user.type(screen.getByLabelText(/password/i), 'validpassword123')
    await user.click(screen.getByRole('button', { name: /sign in/i }))

    expect(screen.queryByText('Enter your email.')).not.toBeInTheDocument()
    expect(screen.queryByText('Enter your password.')).not.toBeInTheDocument()
    await waitFor(() => expect(apiClient.login).toHaveBeenCalledWith('user@example.com', 'validpassword123'))
    expect(await screen.findByText('Dashboard page')).toBeInTheDocument()
  })

  it('shows the real backend error message on invalid credentials, and does not navigate', async () => {
    vi.spyOn(apiClient, 'login').mockRejectedValue(
      new apiClient.ApiError('Incorrect username or password.', 401)
    )
    renderLogin()
    const user = userEvent.setup()

    await user.type(screen.getByLabelText(/email/i), 'user@example.com')
    await user.type(screen.getByLabelText(/password/i), 'wrongpassword')
    await user.click(screen.getByRole('button', { name: /sign in/i }))

    expect(await screen.findByText('Incorrect username or password.')).toBeInTheDocument()
    expect(screen.queryByText('Dashboard page')).not.toBeInTheDocument()
  })
})
