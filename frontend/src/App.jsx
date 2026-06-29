import { useEffect, useState } from 'react'
import Sidebar from './components/Sidebar'
import StatCard from './components/StatCard'
import TradesTable from './components/TradesTable'
import { getStats, getTrades, runSim } from './lib/api'

export default function App() {
  const [stats, setStats] = useState(null)
  const [trades, setTrades] = useState([])
  const [busy, setBusy] = useState(false)

  async function load() {
    const [s, t] = await Promise.all([getStats(), getTrades()])
    setStats(s); setTrades(t)
  }
  useEffect(() => { load() }, [])

  async function onRun() {
    setBusy(true); await runSim(); await load(); setBusy(false)
  }

  const money = (n) => n == null ? '—' : (n < 0 ? '-$' : '$') + Math.abs(n).toFixed(2)

  return (
    <div className="flex">
      <Sidebar />
      <main className="flex-1 min-w-0">
        <header className="flex items-center justify-between px-8 py-5 border-b border-[#eceef4] bg-white">
          <div>
            <h1 className="text-lg font-semibold tracking-tight">Dashboard</h1>
            <p className="text-sm text-mute">Strategy performance, simulated ledger</p>
          </div>
          <button onClick={onRun} disabled={busy}
            className="text-sm font-medium bg-ink text-white px-4 py-2 rounded-lg hover:opacity-90 disabled:opacity-50">
            {busy ? 'Running…' : 'Run simulation'}
          </button>
        </header>

        <section className="px-8 py-6">
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            <StatCard label="Total P&L" value={stats ? money(stats.total_pnl) : '—'}
              sub={stats ? `${stats.total_trades} closed trades` : ''}
              tone={stats && stats.total_pnl > 0 ? 'up' : stats && stats.total_pnl < 0 ? 'down' : ''} />
            <StatCard label="Win rate" value={stats ? stats.win_rate + '%' : '—'}
              sub={stats ? `${stats.wins}W / ${stats.losses}L` : ''} />
            <StatCard label="Expectancy" value={stats ? stats.expectancy_r + ' R' : '—'} sub="per trade"
              tone={stats && stats.expectancy_r > 0 ? 'up' : stats && stats.expectancy_r < 0 ? 'down' : ''} />
            <StatCard label="Profit factor" value={stats ? stats.profit_factor : '—'} sub="gross win / gross loss" />
          </div>
          <div className="mt-6">
            <TradesTable trades={trades} />
          </div>
        </section>
      </main>
    </div>
  )
}
