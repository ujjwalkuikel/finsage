import { LayoutDashboard, FlaskConical, LineChart } from 'lucide-react'

const items = [
  { id: 'dashboard', icon: LayoutDashboard, label: 'Dashboard' },
  { id: 'strategies', icon: LineChart, label: 'Strategies & Charts' },
  { id: 'trades', icon: FlaskConical, label: 'Trades Ledger' },
]

export default function Sidebar({ activeTab, setActiveTab }) {
  return (
    <aside className="w-60 shrink-0 bg-[#0b1020] text-white flex flex-col min-h-screen border-r border-white/5">
      <div className="px-6 py-5 flex items-center gap-2 border-b border-white/10">
        <div className="h-7 w-7 rounded-lg bg-indigo-600 grid place-items-center font-bold text-white">F</div>
        <span className="font-semibold tracking-tight text-white">FinSage</span>
      </div>
      <nav className="px-3 py-4 space-y-1 text-sm">
        {items.map(({ id, icon: Icon, label }) => (
          <button
            key={id}
            onClick={() => setActiveTab(id)}
            className={`w-full flex items-center gap-3 px-3 py-2 rounded-lg transition-colors ${
              activeTab === id
                ? 'bg-indigo-600 text-white font-medium shadow-sm'
                : 'text-gray-400 hover:text-white hover:bg-white/5'
            }`}
          >
            <Icon size={16} /> {label}
          </button>
        ))}
      </nav>
      <div className="mt-auto px-6 py-4 text-xs text-white/40 border-t border-white/10">
        Simulation mode · paper ledger
      </div>
    </aside>
  )
}
