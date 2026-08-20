import { useState } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { ApiError } from '../api/client'

const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/

export default function Login() {
  const navigate = useNavigate()
  const location = useLocation()
  const { login } = useAuth()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [errors, setErrors] = useState({})
  const [submitting, setSubmitting] = useState(false)
  const [loginError, setLoginError] = useState(null)

  function validate() {
    const next = {}
    if (!email.trim()) next.email = 'Enter your email.'
    else if (!EMAIL_PATTERN.test(email)) next.email = 'Enter a valid email address.'
    if (!password) next.password = 'Enter your password.'
    else if (password.length < 8) next.password = 'Password must be at least 8 characters.'
    return next
  }

  async function handleSubmit(event) {
    event.preventDefault()
    const validationErrors = validate()
    setErrors(validationErrors)
    setLoginError(null)
    if (Object.keys(validationErrors).length > 0) return

    setSubmitting(true)
    try {
      // Real authentication (Module 16): a real backend call, a real JWT stored, and the
      // logged-in user's actual role — not the placeholder that used to just navigate
      // after a fake delay.
      await login(email.trim(), password)
      const redirectTo = location.state?.from?.pathname || '/dashboard'
      navigate(redirectTo, { replace: true })
    } catch (err) {
      setLoginError(err instanceof ApiError ? err.message : 'Could not sign in. Please try again.')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-void px-4">
      <div className="w-full max-w-sm">
        <div className="mb-8 text-center">
          <div className="font-mono text-2xl font-bold tracking-tight text-cyan">TRACER</div>
          <div className="mt-1 font-sans text-sm text-muted">
            Digital forensics for Vision-Language Models
          </div>
        </div>

        <form
          onSubmit={handleSubmit}
          noValidate
          className="space-y-4 rounded-lg border border-hairline bg-panel p-6"
        >
          <div>
            <label htmlFor="email" className="mb-1.5 block font-sans text-sm text-muted">
              Email
            </label>
            <input
              id="email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full rounded-md border border-hairline bg-void px-3 py-2 font-sans text-sm text-ink placeholder:text-muted/60"
              placeholder="you@agency.gov"
              aria-invalid={Boolean(errors.email)}
              aria-describedby={errors.email ? 'email-error' : undefined}
            />
            {errors.email && (
              <p id="email-error" className="mt-1 font-sans text-xs text-verdict-adversarial">
                {errors.email}
              </p>
            )}
          </div>

          <div>
            <label htmlFor="password" className="mb-1.5 block font-sans text-sm text-muted">
              Password
            </label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full rounded-md border border-hairline bg-void px-3 py-2 font-sans text-sm text-ink"
              aria-invalid={Boolean(errors.password)}
              aria-describedby={errors.password ? 'password-error' : undefined}
            />
            {errors.password && (
              <p id="password-error" className="mt-1 font-sans text-xs text-verdict-adversarial">
                {errors.password}
              </p>
            )}
          </div>

          {loginError && (
            <div className="rounded-md border border-verdict-adversarial/30 bg-verdict-adversarial/10 p-3 font-sans text-sm text-verdict-adversarial">
              {loginError}
            </div>
          )}

          <button
            type="submit"
            disabled={submitting}
            className="w-full rounded-md bg-cyan py-2 font-sans text-sm font-semibold text-void transition-opacity hover:opacity-90 disabled:opacity-50"
          >
            {submitting ? 'Signing in…' : 'Sign in'}
          </button>

          <p className="text-center font-mono text-[11px] text-muted">
            Accounts are provisioned by an administrator — no public sign-up.
          </p>
        </form>
      </div>
    </div>
  )
}
