import { useEffect, useState } from 'react'
import Sidebar from './components/Sidebar'
import StatCard from './components/StatCard'
import TradesTable from './components/TradesTable'
import StrategiesTable from './components/StrategiesTable'
import ValidationModal from './components/ValidationModal'
import AgentTerminal from './components/AgentTerminal'
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
    <div className="flex bg-[#fafafa] min-h-screen text-neutral-800 antialiased">
      <Sidebar activeTab={activeTab} setActiveTab={setActiveTab} />
      
      <main className="flex-1 min-w-0 flex flex-col">
        {/* Header */}
        <header className="flex items-center justify-between px-8 py-5 border-b border-neutral-200 bg-white">
          <div>
            <h1 className="text-xl font-bold tracking-tight text-neutral-900 capitalize">
              {activeTab === 'dashboard' ? 'Overview' : activeTab === 'strategies' ? 'Strategies Comparison' : activeTab === 'agent_terminal' ? 'Agent Terminal' : 'Trades Ledger'}
            </h1>
            <p className="text-xs text-neutral-400 font-mono mt-1 uppercase tracking-wider font-semibold">
              {activeTab === 'dashboard' 
                ? 'Consolidated simulated account performance metrics' 
                : activeTab === 'strategies' 
                ? 'Compare expectancies and run validation gauntlets' 
                : activeTab === 'agent_terminal'
                ? 'Interactive multi-agent decision log and position monitor'
                : 'Raw trade logs from SQLite db'}
            </p>
          </div>
          <button 
            onClick={onRun} 
            disabled={busy}
            className="text-xs font-bold bg-neutral-950 text-white hover:bg-neutral-800 active:bg-black px-5 py-3 rounded-xl disabled:opacity-50 transition shadow-sm uppercase tracking-wider"
          >
            {busy ? 'Running Simulation…' : 'Run Simulation'}
          </button>
        </header>

        {/* Tab Views */}
        <section className="px-8 py-6 space-y-6 flex-1">
          
          {/* Global statistics row */}
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
              <StrategiesTable 
                strategies={strategies} 
                onValidate={(name) => setSelectedStrategy(name)} 
              />
              
              <div className="border-t border-neutral-200 pt-6">
                <TradesTable trades={trades.slice(0, 10)} />
                {trades.length > 10 && (
                  <div className="mt-3 text-center">
                    <button 
                      onClick={() => setActiveTab('trades')}
                      className="text-xs font-bold text-neutral-900 hover:text-neutral-600 font-mono uppercase tracking-wider"
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

          {activeTab === 'agent_terminal' && (
            <AgentTerminal />
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
