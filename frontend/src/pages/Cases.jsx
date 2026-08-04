import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import AppLayout from '../components/layout/AppLayout'
import CaseStatusBadge from '../components/CaseStatusBadge'
import { createCase, listCases } from '../api/client'

const STATUS_FILTERS = [
  { value: '', label: 'All' },
  { value: 'open', label: 'Open' },
  { value: 'in_progress', label: 'In Progress' },
  { value: 'closed', label: 'Closed' },
  { value: 'archived', label: 'Archived' },
]

export default function Cases() {
  const [cases, setCases] = useState([])
  const [status, setStatus] = useState('loading') // 'loading' | 'ready' | 'error'
  const [error, setError] = useState(null)
  const [statusFilter, setStatusFilter] = useState('')

  const [showNewCaseForm, setShowNewCaseForm] = useState(false)
  const [newTitle, setNewTitle] = useState('')
  const [newDescription, setNewDescription] = useState('')
  const [creating, setCreating] = useState(false)
  const [createError, setCreateError] = useState(null)

  function loadCases(filter) {
    setStatus('loading')
    listCases(filter || undefined)
      .then((data) => {
        setCases(data)
        setStatus('ready')
      })
      .catch((err) => {
        setError(err.message)
        setStatus('error')
      })
  }

  useEffect(() => {
    loadCases(statusFilter)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [statusFilter])

  async function handleCreateCase(e) {
    e.preventDefault()
    if (!newTitle.trim()) {
      setCreateError('Title is required.')
      return
    }
    setCreating(true)
    setCreateError(null)
    try {
      await createCase({ title: newTitle.trim(), description: newDescription.trim() || null })
      setNewTitle('')
      setNewDescription('')
      setShowNewCaseForm(false)
      loadCases(statusFilter)
    } catch (err) {
      setCreateError(err.message)
    } finally {
      setCreating(false)
    }
  }

  return (
    <AppLayout title="Cases">
      <div className="mb-4 flex flex-wrap items-center justify-between gap-4">
        <div className="flex gap-2">
          {STATUS_FILTERS.map((f) => (
            <button
              key={f.value}
              onClick={() => setStatusFilter(f.value)}
              className={`rounded-md border px-3 py-1.5 font-mono text-xs transition-colors ${
                statusFilter === f.value
                  ? 'border-cyan text-cyan'
                  : 'border-hairline text-muted hover:text-ink'
              }`}
            >
              {f.label}
            </button>
          ))}
        </div>
        <button
          onClick={() => setShowNewCaseForm((v) => !v)}
          className="rounded-md border border-cyan/50 bg-cyan/10 px-4 py-1.5 font-mono text-xs text-cyan transition-colors hover:bg-cyan/20"
        >
          {showNewCaseForm ? 'Cancel' : '+ New Case'}
        </button>
      </div>

      {showNewCaseForm && (
        <form
          onSubmit={handleCreateCase}
          className="mb-6 rounded-lg border border-hairline bg-panel p-4"
        >
          <div className="grid gap-3 sm:grid-cols-2">
            <div>
              <label htmlFor="case-title" className="font-mono text-xs uppercase text-muted">
                Title
              </label>
              <input
                id="case-title"
                type="text"
                value={newTitle}
                onChange={(e) => setNewTitle(e.target.value)}
                className="mt-1 w-full rounded-md border border-hairline bg-void px-3 py-2 font-sans text-sm text-ink"
                placeholder="Suspicious upload investigation"
              />
            </div>
            <div>
              <label htmlFor="case-description" className="font-mono text-xs uppercase text-muted">
                Description (optional)
              </label>
              <input
                id="case-description"
                type="text"
                value={newDescription}
                onChange={(e) => setNewDescription(e.target.value)}
                className="mt-1 w-full rounded-md border border-hairline bg-void px-3 py-2 font-sans text-sm text-ink"
                placeholder="Brief notes about this case"
              />
            </div>
          </div>
          {createError && (
            <p className="mt-2 font-sans text-sm text-verdict-adversarial">{createError}</p>
          )}
          <button
            type="submit"
            disabled={creating}
            className="mt-3 rounded-md border border-cyan/50 bg-cyan/10 px-4 py-1.5 font-mono text-xs text-cyan transition-colors hover:bg-cyan/20 disabled:opacity-50"
          >
            {creating ? 'Creating…' : 'Create Case'}
          </button>
        </form>
      )}

      {status === 'loading' && <p className="font-sans text-sm text-muted">Loading cases…</p>}

      {status === 'error' && (
        <div className="rounded-lg border border-verdict-adversarial/30 bg-verdict-adversarial/10 p-4">
          <p className="font-sans text-sm text-verdict-adversarial">
            Could not load cases: {error}
          </p>
        </div>
      )}

      {status === 'ready' && cases.length === 0 && (
        <div className="rounded-lg border border-hairline bg-panel p-6 text-center">
          <p className="font-sans text-sm text-muted">
            {statusFilter ? `No ${statusFilter.replace('_', ' ')} cases yet.` : 'No cases yet.'}
          </p>
        </div>
      )}

      {status === 'ready' && cases.length > 0 && (
        <div className="overflow-hidden rounded-lg border border-hairline bg-panel">
          <table className="w-full text-left">
            <thead>
              <tr className="border-b border-hairline font-mono text-xs uppercase tracking-wide text-muted">
                <th className="px-4 py-3">Case</th>
                <th className="px-4 py-3">Title</th>
                <th className="px-4 py-3">Status</th>
                <th className="px-4 py-3">Evidence</th>
                <th className="px-4 py-3">Created</th>
              </tr>
            </thead>
            <tbody>
              {cases.map((c) => (
                <tr key={c.id} className="border-b border-hairline last:border-0 hover:bg-void/50">
                  <td className="px-4 py-3 font-mono text-xs text-muted">{c.case_number}</td>
                  <td className="px-4 py-3">
                    <Link to={`/cases/${c.id}`} className="font-sans text-sm text-ink hover:text-cyan">
                      {c.title}
                    </Link>
                  </td>
                  <td className="px-4 py-3">
                    <CaseStatusBadge status={c.status} />
                  </td>
                  <td className="px-4 py-3 font-mono text-sm text-muted">{c.evidence_count}</td>
                  <td className="px-4 py-3 font-mono text-xs text-muted">
                    {new Date(c.created_at).toLocaleDateString()}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </AppLayout>
  )
}
