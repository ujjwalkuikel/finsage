import { LayoutDashboard, FlaskConical, LineChart, Bot, Settings } from 'lucide-react'

const items = [
  { icon: LayoutDashboard, label: 'Dashboard', active: true },
  { icon: LineChart, label: 'Strategies' },
  { icon: FlaskConical, label: 'Backtests' },
  { icon: Bot, label: 'Agents' },
  { icon: Settings, label: 'Settings' },
]

export default function Sidebar() {
  return (
    <aside className="w-60 shrink-0 bg-ink text-white flex flex-col min-h-screen">
      <div className="px-6 py-5 flex items-center gap-2 border-b border-white/10">
        <div className="h-7 w-7 rounded-lg bg-brand grid place-items-center font-bold">A</div>
        <span className="font-semibold tracking-tight">AII Platform</span>
      </div>
      <nav className="px-3 py-4 space-y-1 text-sm">
        {items.map(({ icon: Icon, label, active }) => (
          <a key={label} href="#"
             className={`flex items-center gap-3 px-3 py-2 rounded-lg ${active ? 'bg-white/10 text-white font-medium' : 'text-white/60 hover:text-white'}`}>
            <Icon size={16} /> {label}
          </a>
        ))}
      </nav>
      <div className="mt-auto px-6 py-4 text-xs text-white/40 border-t border-white/10">
        Simulation mode · paper ledger
      </div>
    </aside>
  )
}
