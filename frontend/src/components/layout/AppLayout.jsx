import Sidebar from './Sidebar'
import Topbar from './Topbar'

export default function AppLayout({ title, children }) {
  return (
    <div className="flex h-screen bg-void">
      <Sidebar />
      <div className="flex flex-1 flex-col overflow-hidden">
        <Topbar title={title} />
        <main className="flex-1 overflow-y-auto p-6">{children}</main>
      </div>
    </div>
  )
}
