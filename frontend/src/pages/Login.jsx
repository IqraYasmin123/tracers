import { useState } from 'react'
import { useNavigate } from 'react-router-dom'

const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/

export default function Login() {
  const navigate = useNavigate()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [errors, setErrors] = useState({})
  const [submitting, setSubmitting] = useState(false)

  function validate() {
    const next = {}
    if (!email.trim()) next.email = 'Enter your email.'
    else if (!EMAIL_PATTERN.test(email)) next.email = 'Enter a valid email address.'
    if (!password) next.password = 'Enter your password.'
    else if (password.length < 8) next.password = 'Password must be at least 8 characters.'
    return next
  }

  function handleSubmit(event) {
    event.preventDefault()
    const validationErrors = validate()
    setErrors(validationErrors)
    if (Object.keys(validationErrors).length > 0) return

    // Real authentication (JWT issued by the backend) arrives in Module 16. For now, this
    // validates real input honestly and then proceeds — not wired to a fake "always
    // succeeds" backend call, since that would be more misleading than just being direct
    // about what's implemented yet.
    setSubmitting(true)
    setTimeout(() => {
      navigate('/dashboard')
    }, 400)
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

          <button
            type="submit"
            disabled={submitting}
            className="w-full rounded-md bg-cyan py-2 font-sans text-sm font-semibold text-void transition-opacity hover:opacity-90 disabled:opacity-50"
          >
            {submitting ? 'Signing in…' : 'Sign in'}
          </button>

          <p className="text-center font-mono text-[11px] text-muted">
            Full authentication arrives in Module 16
          </p>
        </form>
      </div>
    </div>
  )
}
