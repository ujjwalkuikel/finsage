import { useState, useEffect, useRef } from 'react'
import { Bot, Terminal, Shield, TrendingUp, Newspaper, HelpCircle, XCircle, ArrowUpRight, ArrowDownRight, RefreshCw, LogOut } from 'lucide-react'
import { orchestrateTrade, getAgentPositions, closeAgentPosition } from '../lib/api'

export default function AgentTerminal() {
  const [ticker, setTicker] = useState('')
  const [loading, setLoading] = useState(false)
  const [consoleLogs, setConsoleLogs] = useState([])
  const [positions, setPositions] = useState([])
  const [closingId, setClosingId] = useState(null)
  const terminalEndRef = useRef(null)

  // Scroll terminal to bottom
  useEffect(() => {
    if (terminalEndRef.current) {
      terminalEndRef.current.scrollIntoView({ behavior: 'smooth' })
    }
  }, [consoleLogs])

  // Load active positions
  async function loadPositions() {
    try {
      const pos = await getAgentPositions()
      setPositions(pos)
    } catch (err) {
      console.error("Failed to load agent positions:", err)
    }
  }

  // Poll positions for live P&L updates
  useEffect(() => {
    loadPositions()
    const interval = setInterval(loadPositions, 5000)
    return () => clearInterval(interval)
  }, [])

  function addLog(text, type = 'info') {
    const time = new Date().toLocaleTimeString()
    setConsoleLogs((prev) => [...prev, { time, text, type }])
  }

  async function handleAudit() {
    if (!ticker.trim()) return
    const symbol = ticker.trim().toUpperCase()
    setLoading(true)
    setConsoleLogs([])

    addLog(`[SYSTEM] Initializing State Graph for symbol: ${symbol}...`, 'system')
    
    try {
      // 1. Kick off API call
      const res = await orchestrateTrade(symbol)
      
      if (res.status === 'error') {
        addLog(`[ERROR] Orchestrator failed: ${res.error}`, 'error')
        setLoading(false)
        return
      }

      // Simulate sequential node runs for premium UI typing effect
      const steps = [
        {
          delay: 800,
          text: `[MACRO] Regime detected: ${res.macro_analysis.market_regime.toUpperCase()} | Bias: ${res.macro_analysis.regime_bias.toUpperCase()}`,
          type: 'macro',
          extra: `Evidence: ${res.macro_analysis.evidence.join(' · ')}`
        },
        {
          delay: 1600,
          text: `[NEWS] News Sentiment: ${res.news_analysis.sentiment_score > 0 ? '+' : ''}${res.news_analysis.sentiment_score} | Headlines Analysed: ${res.news_analysis.inputs_used.news_count}`,
          type: 'news',
          extra: `Catalysts: ${res.news_analysis.catalysts.map(c => `${c.headline} (${c.impact.toUpperCase()})`).join(' · ')}`
        },
        {
          delay: 2400,
          text: `[TECH] Technical Outlook: ${res.technical_analysis.conclusion.toUpperCase()}`,
          type: 'tech',
          extra: `Evidence: ${res.technical_analysis.evidence.join(' · ')}`
        },
        {
          delay: 3200,
          text: `[THESIS] Verdict: ${res.thesis.verdict.toUpperCase()} | Duration: ${res.thesis.target_duration.toUpperCase()}`,
          type: 'thesis',
          extra: `Core Thesis: "${res.thesis.core_thesis}"`
        },
        {
          delay: 4000,
          text: `[RISK] Veto Decision: ${res.risk_analysis.veto ? 'VETOED ❌' : 'APPROVED ✅'}`,
          type: 'risk',
          extra: `Reasoning: ${res.risk_analysis.reason}`
        },
        {
          delay: 4800,
          text: `[EXECUTION] Status: ${res.trade_execution.status.toUpperCase()} | Details: ${res.trade_execution.message}`,
          type: res.trade_execution.status === 'executed' ? 'success' : 'system',
          extra: res.trade_execution.trade ? `Position Details: Qty ${res.trade_execution.trade.qty} @ $${res.trade_execution.trade.entry_price} | Stop: $${res.trade_execution.trade.stop_price} | Target: $${res.trade_execution.trade.target_price}` : null
        }
      ]

      steps.forEach((step) => {
        setTimeout(() => {
          addLog(step.text, step.type)
          if (step.extra) {
            addLog(`  -> ${step.extra}`, 'sub')
          }
          if (step.type === 'success' || step.delay === 4800) {
            setLoading(false)
            loadPositions()
          }
        }, step.delay)
      })

    } catch (err) {
      addLog(`[ERROR] Connection failed: ${err.message}`, 'error')
      setLoading(false)
    }
  }

  async function handleClosePosition(id, symbol) {
    setClosingId(id)
    try {
      const res = await closeAgentPosition(id)
      if (res.ok) {
        addLog(`[SYSTEM] Closed position for ${symbol} successfully.`, 'system')
        loadPositions()
      } else {
        addLog(`[ERROR] Failed to close position: ${res.error}`, 'error')
      }
    } catch (err) {
      addLog(`[ERROR] Connection failed: ${err.message}`, 'error')
    } finally {
      setClosingId(null)
    }
  }

  return (
    <div className="grid grid-cols-1 xl:grid-cols-2 gap-6 h-full items-start">
      {/* Left: Terminal Console */}
      <div className="bg-white rounded-2xl border border-neutral-200 shadow-sm p-6 space-y-5 flex flex-col h-[640px]">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Bot className="text-indigo-600" size={20} />
            <h2 className="text-sm font-bold text-neutral-900 uppercase tracking-wider">Agent Audit Terminal</h2>
          </div>
          <div className="flex items-center gap-2">
            <span className={`w-2 h-2 rounded-full ${loading ? 'bg-amber-500 animate-pulse' : 'bg-emerald-500'}`}></span>
            <span className="text-[10px] font-mono text-neutral-400 uppercase tracking-widest font-semibold">
              {loading ? 'Executing State Graph' : 'Graph Ready'}
            </span>
          </div>
        </div>

        {/* Console Controls */}
        <div className="flex gap-3">
          <div className="relative flex-1">
            <span className="absolute left-4 top-3 text-neutral-400 font-mono text-xs font-bold uppercase">$</span>
            <input
              type="text"
              value={ticker}
              onChange={(e) => setTicker(e.target.value)}
              disabled={loading}
              placeholder="ENTER TICKER (e.g. AAPL, NVDA)"
              className="w-full bg-neutral-50 text-xs font-mono border border-neutral-200 rounded-xl py-3 pl-8 pr-4 text-neutral-900 focus:outline-none focus:ring-1 focus:ring-indigo-600 disabled:opacity-50 transition"
            />
          </div>
          <button
            onClick={handleAudit}
            disabled={loading || !ticker.trim()}
            className="bg-neutral-950 text-white hover:bg-neutral-800 disabled:bg-neutral-200 text-xs font-mono font-bold uppercase tracking-wider px-5 py-3 rounded-xl transition flex items-center gap-2 disabled:text-neutral-400"
          >
            {loading ? <RefreshCw className="animate-spin" size={12} /> : <Terminal size={12} />}
            Audit & Execute
          </button>
        </div>

        {/* Terminal Screen */}
        <div className="flex-1 bg-[#090b10] border border-neutral-900 rounded-xl p-4 overflow-y-auto font-mono text-[11px] leading-relaxed shadow-inner space-y-2 select-text scrollbar-thin">
          {consoleLogs.length === 0 ? (
            <div className="text-neutral-600 h-full flex flex-col items-center justify-center space-y-2">
              <Terminal size={24} />
              <p>Copilot terminal idle. Enter a symbol to begin agent consensus flow.</p>
            </div>
          ) : (
            consoleLogs.map((log, idx) => {
              let color = 'text-neutral-400'
              if (log.type === 'system') color = 'text-amber-500 font-semibold'
              if (log.type === 'error') color = 'text-red-500 font-semibold'
              if (log.type === 'macro') color = 'text-blue-400'
              if (log.type === 'news') color = 'text-yellow-400'
              if (log.type === 'tech') color = 'text-cyan-400'
              if (log.type === 'thesis') color = 'text-indigo-400 font-bold'
              if (log.type === 'risk') color = 'text-purple-400 font-semibold'
              if (log.type === 'success') color = 'text-emerald-400 font-bold'
              if (log.type === 'sub') color = 'text-neutral-500 pl-4'
              
              return (
                <div key={idx} className={color}>
                  {log.type !== 'sub' && <span className="text-neutral-600 mr-2">[{log.time}]</span>}
                  {log.text}
                </div>
              )
            })
          )}
          <div ref={terminalEndRef} />
        </div>
      </div>

      {/* Right: Active Positions List */}
      <div className="bg-white rounded-2xl border border-neutral-200 shadow-sm p-6 space-y-5 flex flex-col h-[640px]">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Shield className="text-indigo-600" size={20} />
            <h2 className="text-sm font-bold text-neutral-900 uppercase tracking-wider">Active Copilot Positions</h2>
          </div>
          <button 
            onClick={loadPositions}
            className="p-2 hover:bg-neutral-100 rounded-xl transition text-neutral-400 hover:text-neutral-900"
          >
            <RefreshCw size={14} />
          </button>
        </div>

        {/* Positions Table */}
        <div className="flex-1 overflow-y-auto border border-neutral-100 rounded-xl">
          {positions.length === 0 ? (
            <div className="text-neutral-400 h-full flex flex-col items-center justify-center space-y-2 py-10">
              <Bot size={24} className="text-neutral-300" />
              <p className="text-xs">No active positions. Execute a buy thesis to start tracking.</p>
            </div>
          ) : (
            <div className="divide-y divide-neutral-100">
              {positions.map((pos) => {
                const isProfit = pos.pnl_pct >= 0
                return (
                  <div key={pos.id} className="p-4 hover:bg-neutral-50/50 transition flex items-center justify-between">
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <span className="text-sm font-bold text-neutral-900 font-mono">{pos.symbol}</span>
                        <span className={`text-[9px] font-mono px-2 py-0.5 rounded-full font-bold uppercase ${
                          pos.side === 'long' 
                            ? 'bg-emerald-50 text-emerald-700 border border-emerald-100' 
                            : 'bg-red-50 text-red-700 border border-red-100'
                        }`}>
                          {pos.side}
                        </span>
                      </div>
                      <div className="text-[10px] text-neutral-400 font-mono">
                        Entry: ${pos.entry_price} · Qty: {pos.qty}
                      </div>
                    </div>

                    <div className="flex items-center gap-4">
                      {/* P&L Display */}
                      <div className="text-right">
                        <div className={`flex items-center justify-end font-mono font-bold text-sm ${
                          isProfit ? 'text-emerald-600' : 'text-red-600'
                        }`}>
                          {isProfit ? <ArrowUpRight size={14} /> : <ArrowDownRight size={14} />}
                          {isProfit ? '+' : ''}{pos.pnl_pct.toFixed(2)}%
                        </div>
                        <div className="text-[9px] text-neutral-400 font-mono">
                          Live: ${pos.latest_price}
                        </div>
                      </div>

                      {/* Exit Action */}
                      <button
                        onClick={() => handleClosePosition(pos.id, pos.symbol)}
                        disabled={closingId === pos.id}
                        className="bg-neutral-50 hover:bg-red-50 text-neutral-500 hover:text-red-600 p-2.5 rounded-xl border border-neutral-200 hover:border-red-200 transition disabled:opacity-50"
                        title="Close Position"
                      >
                        {closingId === pos.id ? (
                          <RefreshCw className="animate-spin" size={14} />
                        ) : (
                          <LogOut size={14} />
                        )}
                      </button>
                    </div>
                  </div>
                )
              })}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
