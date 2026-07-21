import AppLayout from '../components/layout/AppLayout'

const SETTINGS_SECTIONS = [
  {
    title: 'Notifications',
    items: [
      { label: 'Email me when an investigation completes', note: 'Wired up in Module 16' },
      { label: 'Notify on high-confidence adversarial detections', note: 'Wired up in Module 16' },
    ],
  },
  {
    title: 'Account',
    items: [
      { label: 'Change password', note: 'Arrives with Module 16 (Authentication)' },
      { label: 'Two-factor authentication', note: 'Arrives with Module 16 (Authentication)' },
    ],
  },
]

export default function Settings() {
  return (
    <AppLayout title="Settings">
      <div className="max-w-2xl space-y-6">
        {SETTINGS_SECTIONS.map((section) => (
          <div key={section.title} className="rounded-lg border border-hairline bg-panel p-5">
            <h2 className="mb-3 font-sans text-sm font-semibold text-ink">{section.title}</h2>
            <div className="space-y-3">
              {section.items.map((item) => (
                <div key={item.label} className="flex items-center justify-between">
                  <span className="font-sans text-sm text-ink">{item.label}</span>
                  <span className="font-mono text-[11px] text-muted">{item.note}</span>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </AppLayout>
  )
}
