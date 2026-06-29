import { useEffect, useState } from 'react'
import Sidebar from './components/Sidebar'
import StatCard from './components/StatCard'
import TradesTable from './components/TradesTable'
import StrategiesTable from './components/StrategiesTable'
import ValidationModal from './components/ValidationModal'
import { getStats, getTrades, getStrategies, runSim } from './lib/api'

export default function App() {
  const [activeTab, setActiveTab] = useState('dashboard')
  const [stats, setStats] = useState(null)
  const [trades, setTrades] = useState([])
  const [strategies, setStrategies] = useState({})
  const [selectedStrategy, setSelectedStrategy] = useState(null)
  const [busy, setBusy] = useState(false)

  async function load() {
    try {
      const [s, t, strats] = await Promise.all([
        getStats(),
        getTrades(),
        getStrategies()
      ])
      setStats(s)
      setTrades(t)
      setStrategies(strats)
    } catch (err) {
      console.error("Failed to load dashboard data:", err)
    }
  }

  useEffect(() => {
    load()
  }, [])

  async function onRun() {
    setBusy(true)
    try {
      await runSim()
      await load()
    } catch (err) {
      console.error("Simulation run failed:", err)
    } finally {
      setBusy(false)
    }
  }

  const money = (n) => n == null ? '—' : (n < 0 ? '-$' : '$') + Math.abs(n).toFixed(2)

  return (
    <div className="flex bg-[#f6f7fb] min-h-screen text-slate-800">
      <Sidebar activeTab={activeTab} setActiveTab={setActiveTab} />
      
      <main className="flex-1 min-w-0">
        {/* Header */}
        <header className="flex items-center justify-between px-8 py-5 border-b border-[#eceef4] bg-white">
          <div>
            <h1 className="text-lg font-bold tracking-tight text-gray-900 capitalize">
              {activeTab === 'dashboard' ? 'Overview' : activeTab === 'strategies' ? 'Strategies Comparison' : 'Trades Ledger'}
            </h1>
            <p className="text-xs text-gray-400 font-mono mt-0.5">
              {activeTab === 'dashboard' 
                ? 'Consolidated simulated account performance metrics' 
                : activeTab === 'strategies' 
                ? 'Compare expectancies and run validation gauntlets' 
                : 'Raw trade logs from SQLite db'}
            </p>
          </div>
          <button 
            onClick={onRun} 
            disabled={busy}
            className="text-xs font-semibold bg-[#0b1020] text-white px-4 py-2.5 rounded-xl hover:bg-slate-800 disabled:opacity-50 transition shadow-sm"
          >
            {busy ? 'Running Simulation…' : 'Run Simulation'}
          </button>
        </header>

        {/* Tab Views */}
        <section className="px-8 py-6 space-y-6">
          
          {/* Global statistics row (always visible on Dashboard, hidden on detail tabs to focus content) */}
          {activeTab === 'dashboard' && (
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
              <StatCard label="Total P&L" value={stats ? money(stats.total_pnl) : '—'}
                sub={stats ? `${stats.total_trades} closed trades` : ''}
                tone={stats && stats.total_pnl > 0 ? 'up' : stats && stats.total_pnl < 0 ? 'down' : ''} />
              <StatCard label="Win Rate" value={stats ? stats.win_rate + '%' : '—'}
                sub={stats ? `${stats.wins}W / ${stats.losses}L` : ''} />
              <StatCard label="Expectancy" value={stats ? stats.expectancy_r + ' R' : '—'} sub="per trade"
                tone={stats && stats.expectancy_r > 0 ? 'up' : stats && stats.expectancy_r < 0 ? 'down' : ''} />
              <StatCard label="Profit Factor" value={stats ? stats.profit_factor : '—'} sub="gross win / gross loss" />
            </div>
          )}

          {/* Tab Render Switch */}
          {activeTab === 'dashboard' && (
            <div className="space-y-6">
              {/* Overview shows strategies list first as the core hunter portfolio */}
              <StrategiesTable 
                strategies={strategies} 
                onValidate={(name) => setSelectedStrategy(name)} 
              />
              
              <div className="border-t border-gray-100 pt-6">
                <TradesTable trades={trades.slice(0, 10)} />
                {trades.length > 10 && (
                  <div className="mt-3 text-center">
                    <button 
                      onClick={() => setActiveTab('trades')}
                      className="text-xs font-semibold text-indigo-600 hover:text-indigo-700 font-mono"
                    >
                      View all {trades.length} trades →
                    </button>
                  </div>
                )}
              </div>
            </div>
          )}

          {activeTab === 'strategies' && (
            <StrategiesTable 
              strategies={strategies} 
              onValidate={(name) => setSelectedStrategy(name)} 
            />
          )}

          {activeTab === 'trades' && (
            <TradesTable trades={trades} />
          )}

        </section>
      </main>

      {/* Validation Gauntlet Modal Overlay */}
      {selectedStrategy && (
        <ValidationModal 
          strategyName={selectedStrategy} 
          onClose={() => setSelectedStrategy(null)} 
        />
      )}
    </div>
  )
}
