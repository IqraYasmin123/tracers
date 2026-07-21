import { useEffect, useState } from 'react'
import { checkHealth } from '../../api/client'

export default function Topbar({ title }) {
  const [backendStatus, setBackendStatus] = useState('checking')

  useEffect(() => {
    let cancelled = false
    checkHealth()
      .then(() => {
        if (!cancelled) setBackendStatus('online')
      })
      .catch(() => {
        if (!cancelled) setBackendStatus('offline')
      })
    return () => {
      cancelled = true
    }
  }, [])

  const statusConfig = {
    checking: { color: 'bg-muted', label: 'Checking…' },
    online: { color: 'bg-verdict-clean', label: 'AI engine online' },
    offline: { color: 'bg-verdict-adversarial', label: 'AI engine offline' },
  }[backendStatus]

  return (
    <header className="flex h-16 items-center justify-between border-b border-hairline bg-void px-6">
      <h1 className="font-sans text-lg font-semibold text-ink">{title}</h1>
      <div className="flex items-center gap-2 font-mono text-xs text-muted">
        <span className={`h-2 w-2 rounded-full ${statusConfig.color}`} aria-hidden="true" />
        {statusConfig.label}
      </div>
    </header>
  )
}
