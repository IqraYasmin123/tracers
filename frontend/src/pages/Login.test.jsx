import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import Login from './Login'

function renderLogin() {
  return render(
    <MemoryRouter>
      <Login />
    </MemoryRouter>
  )
}

describe('Login', () => {
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

  it('shows no validation errors for valid input', async () => {
    renderLogin()
    const user = userEvent.setup()

    await user.type(screen.getByLabelText(/email/i), 'user@example.com')
    await user.type(screen.getByLabelText(/password/i), 'validpassword123')
    await user.click(screen.getByRole('button', { name: /sign in/i }))

    expect(screen.queryByText('Enter your email.')).not.toBeInTheDocument()
    expect(screen.queryByText('Enter your password.')).not.toBeInTheDocument()
  })
})
