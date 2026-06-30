import { LayoutDashboard, FlaskConical, LineChart, Bot } from 'lucide-react'

const items = [
  { id: 'dashboard', icon: LayoutDashboard, label: 'Overview' },
  { id: 'strategies', icon: LineChart, label: 'Strategies comparison' },
  { id: 'agent_terminal', icon: Bot, label: 'Agent Terminal' },
  { id: 'trades', icon: FlaskConical, label: 'Trades ledger' },
]

export default function Sidebar({ activeTab, setActiveTab }) {
  return (
    <aside className="w-60 shrink-0 bg-white text-neutral-800 flex flex-col min-h-screen border-r border-neutral-200">
      {/* Brand logo header */}
      <div className="px-6 py-5 border-b border-neutral-200 flex items-center justify-start">
        <img src="/logo.png" className="h-9 w-auto max-w-[140px] object-contain" alt="FinSage" />
      </div>
      
      {/* Navigation */}
      <nav className="px-3 py-4 space-y-1 text-sm flex-1">
        {items.map(({ id, icon: Icon, label }) => (
          <button
            key={id}
            onClick={() => setActiveTab(id)}
            className={`w-full flex items-center gap-3 px-3.5 py-2.5 rounded-xl transition-all ${
              activeTab === id
                ? 'bg-neutral-900 text-white font-semibold shadow-sm'
                : 'text-neutral-500 hover:text-neutral-900 hover:bg-neutral-100/70'
            }`}
          >
            <Icon size={16} /> {label}
          </button>
        ))}
      </nav>
      
      {/* Footer details */}
      <div className="px-6 py-4 text-[10px] text-neutral-400 font-semibold uppercase tracking-wider border-t border-neutral-200 bg-neutral-50">
        Simulation mode · paper ledger
      </div>
    </aside>
  )
}
