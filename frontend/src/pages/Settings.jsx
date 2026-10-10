import { useState } from 'react'
import AppLayout from '../components/layout/AppLayout'
import { changePassword, ApiError } from '../api/client'

const NOTIFICATION_SECTION = {
  title: 'Notifications',
  items: [
    { label: 'Email me when an investigation completes', note: 'Not yet implemented' },
    { label: 'Notify on high-confidence adversarial detections', note: 'Not yet implemented' },
  ],
}

// Two-factor authentication was never built as part of Module 16 — only login, password
// change, and role-based access exist. This is tracked honestly rather than left as a
// stale "arrives with Module 16" claim now that Module 16 has actually shipped without it.
const TWO_FACTOR_NOTE = 'Not yet implemented'

export default function Settings() {
  return (
    <AppLayout title="Settings">
      <div className="max-w-2xl space-y-6">
        <div className="rounded-lg border border-hairline bg-panel p-5">
          <h2 className="mb-3 font-sans text-sm font-semibold text-ink">
            {NOTIFICATION_SECTION.title}
          </h2>
          <div className="space-y-3">
            {NOTIFICATION_SECTION.items.map((item) => (
              <div key={item.label} className="flex items-center justify-between">
                <span className="font-sans text-sm text-ink">{item.label}</span>
                <span className="font-mono text-[11px] text-muted">{item.note}</span>
              </div>
            ))}
          </div>
        </div>

        <div className="rounded-lg border border-hairline bg-panel p-5">
          <h2 className="mb-3 font-sans text-sm font-semibold text-ink">Account</h2>
          <ChangePasswordForm />
          <div className="mt-4 flex items-center justify-between border-t border-hairline pt-3">
            <span className="font-sans text-sm text-ink">Two-factor authentication</span>
            <span className="font-mono text-[11px] text-muted">{TWO_FACTOR_NOTE}</span>
          </div>
        </div>
      </div>
    </AppLayout>
  )
}

function ChangePasswordForm() {
  const [currentPassword, setCurrentPassword] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState(null)
  const [success, setSuccess] = useState(false)

  async function handleSubmit(e) {
    e.preventDefault()
    setError(null)
    setSuccess(false)

    if (newPassword !== confirmPassword) {
      setError('New password and confirmation do not match.')
      return
    }
    if (newPassword.length < 8) {
      setError('New password must be at least 8 characters.')
      return
    }

    setSubmitting(true)
    try {
      await changePassword(currentPassword, newPassword)
      setSuccess(true)
      setCurrentPassword('')
      setNewPassword('')
      setConfirmPassword('')
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Failed to change password.')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-3">
      <div className="flex items-center justify-between">
        <span className="font-sans text-sm text-ink">Change password</span>
      </div>
      <div className="grid gap-3 sm:grid-cols-3">
        <div>
          <label htmlFor="current-password" className="font-mono text-xs uppercase text-muted">
            Current password
          </label>
          <input
            id="current-password"
            type="password"
            value={currentPassword}
            onChange={(e) => setCurrentPassword(e.target.value)}
            className="mt-1 w-full rounded-md border border-hairline bg-void px-3 py-2 font-sans text-sm text-ink"
            autoComplete="current-password"
            required
          />
        </div>
        <div>
          <label htmlFor="new-password" className="font-mono text-xs uppercase text-muted">
            New password
          </label>
          <input
            id="new-password"
            type="password"
            value={newPassword}
            onChange={(e) => setNewPassword(e.target.value)}
            className="mt-1 w-full rounded-md border border-hairline bg-void px-3 py-2 font-sans text-sm text-ink"
            autoComplete="new-password"
            required
          />
        </div>
        <div>
          <label htmlFor="confirm-password" className="font-mono text-xs uppercase text-muted">
            Confirm new password
          </label>
          <input
            id="confirm-password"
            type="password"
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            className="mt-1 w-full rounded-md border border-hairline bg-void px-3 py-2 font-sans text-sm text-ink"
            autoComplete="new-password"
            required
          />
        </div>
      </div>

      {error && <p className="font-sans text-sm text-verdict-adversarial">{error}</p>}
      {success && (
        <p className="font-sans text-sm text-verdict-clean">Password changed successfully.</p>
      )}

      <button
        type="submit"
        disabled={submitting}
        className="rounded-md border border-cyan/50 bg-cyan/10 px-4 py-1.5 font-mono text-xs text-cyan transition-colors hover:bg-cyan/20 disabled:opacity-50"
      >
        {submitting ? 'Changing…' : 'Change Password'}
      </button>
    </form>
  )
}
