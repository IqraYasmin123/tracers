import { NavLink } from 'react-router-dom'

const NAV_ITEMS = [
  { to: '/dashboard', label: 'Dashboard', icon: '▦' },
  { to: '/investigation', label: 'Investigation', icon: '⌕' },
  { to: '/settings', label: 'Settings', icon: '⚙' },
]

export default function Sidebar() {
  return (
    <aside className="flex h-screen w-60 shrink-0 flex-col border-r border-hairline bg-panel">
      <div className="flex items-center gap-2 border-b border-hairline px-5 py-5">
        <span className="font-mono text-lg font-bold tracking-tight text-cyan">TRACER</span>
      </div>

      <nav className="flex-1 space-y-1 px-3 py-4" aria-label="Primary">
        {NAV_ITEMS.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            className={({ isActive }) =>
              `flex items-center gap-3 rounded-md px-3 py-2 font-sans text-sm transition-colors ${
                isActive
                  ? 'bg-cyan/10 text-cyan'
                  : 'text-muted hover:bg-hairline/50 hover:text-ink'
              }`
            }
          >
            <span className="text-base" aria-hidden="true">
              {item.icon}
            </span>
            {item.label}
          </NavLink>
        ))}
      </nav>

      <div className="border-t border-hairline px-5 py-4">
        <div className="font-mono text-[11px] text-muted">TRACER v0.1.0</div>
        <div className="font-mono text-[11px] text-muted">AI-VLM Forensics</div>
      </div>
    </aside>
  )
}
