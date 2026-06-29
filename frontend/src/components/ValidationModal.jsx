import { useEffect, useState } from 'react'
import { X, CheckCircle, AlertTriangle, Play, RefreshCw } from 'lucide-react'
import { validateStrategy } from '../lib/api'

export default function ValidationModal({ strategyName, onClose }) {
  const [loading, setLoading] = useState(true)
  const [report, setReport] = useState(null)
  const [error, setError] = useState(null)
  const [loadingStep, setLoadingStep] = useState(0)

  const steps = [
    "Running overfit smell-test...",
    "Permuting returns via block bootstrap...",
    "Simulating 100 randomized Monte Carlo walks...",
    "Executing walk-forward roll optimizer...",
    "Computing out-of-sample significance p-values..."
  ]

  async function run() {
    setLoading(true)
    setError(null)
    setReport(null)
    setLoadingStep(0)
    
    // Simulate loading steps for visual polish
    const interval = setInterval(() => {
      setLoadingStep(s => (s < steps.length - 1 ? s + 1 : s))
    }, 600)

    try {
      const res = await validateStrategy(strategyName)
      clearInterval(interval)
      if (res.ok) {
        setReport(res.report)
      } else {
        setError(res.error || "Failed to validate strategy")
      }
    } catch (err) {
      clearInterval(interval)
      setError("Failed to query validation endpoint: " + err.message)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (strategyName) {
      run()
    }
  }, [strategyName])

  if (!strategyName) return null

  const prettyName = strategyName.replace(/_/g, ' ')

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
      <div className="bg-white w-full max-w-2xl rounded-2xl shadow-xl overflow-hidden flex flex-col border border-gray-100 max-h-[90vh]">
        
        {/* Header */}
        <div className="px-6 py-4 border-b border-gray-100 flex items-center justify-between">
          <div>
            <h3 className="font-semibold text-gray-900 capitalize text-base">Validation Gauntlet</h3>
            <p className="text-xs text-gray-400 font-mono mt-0.5">{prettyName}</p>
          </div>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600 transition-colors">
            <X size={18} />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 overflow-y-auto flex-1">
          
          {loading && (
            <div className="flex flex-col items-center justify-center py-16">
              <RefreshCw className="animate-spin text-indigo-600 mb-4" size={32} />
              <p className="text-sm font-medium text-gray-800">{steps[loadingStep]}</p>
              <p className="text-xs text-gray-400 mt-1 font-mono">Running statistical simulations strictly in RAM...</p>
            </div>
          )}

          {error && (
            <div className="bg-red-50 text-red-700 p-4 rounded-xl flex items-start gap-3 text-sm">
              <AlertTriangle className="shrink-0 mt-0.5" size={16} />
              <div>
                <p className="font-semibold">Validation failed</p>
                <p className="mt-1 font-mono text-xs opacity-90">{error}</p>
                <button onClick={run} className="mt-3 flex items-center gap-1.5 px-3 py-1 bg-red-100 rounded-lg hover:bg-red-200 transition font-medium">
                  <Play size={12} /> Retry Gauntlet
                </button>
              </div>
            </div>
          )}

          {report && (
            <div className="space-y-6">
              
              {/* Verdict Banner */}
              <div className={`p-5 rounded-2xl flex items-center justify-between border ${
                report.verdict === 'PASS' 
                  ? 'bg-green-50/50 border-green-100 text-green-800' 
                  : 'bg-red-50/50 border-red-100 text-red-800'
              }`}>
                <div>
                  <div className="text-xs font-semibold uppercase tracking-wider opacity-60">Validation Verdict</div>
                  <div className="text-2xl font-bold mt-1 flex items-center gap-2">
                    {report.verdict === 'PASS' ? (
                      <>
                        <CheckCircle size={24} className="text-green-600" />
                        <span className="text-green-600">PASS</span>
                      </>
                    ) : (
                      <>
                        <AlertTriangle size={24} className="text-red-600" />
                        <span className="text-red-600">FAIL</span>
                      </>
                    )}
                  </div>
                </div>
                <div className="text-right text-xs max-w-xs opacity-80">
                  {report.verdict === 'PASS' 
                    ? "Strategy displays statistically significant edge with low overfitting signs." 
                    : "Strategy failed one or more gauntlet significance levels or has too few trades."}
                </div>
              </div>

              {/* Grid Metrics */}
              <div className="grid grid-cols-3 gap-4">
                <div className="bg-gray-50 border border-gray-100 p-4 rounded-xl">
                  <div className="text-xs text-gray-400 font-medium">Win Rate</div>
                  <div className="text-lg font-bold text-gray-800 font-mono mt-1">{report.smells.win_rate}%</div>
                </div>
                <div className="bg-gray-50 border border-gray-100 p-4 rounded-xl">
                  <div className="text-xs text-gray-400 font-medium">Profit Factor</div>
                  <div className="text-lg font-bold text-gray-800 font-mono mt-1">
                    {report.smells.profit_factor === Infinity ? '∞' : report.smells.profit_factor}
                  </div>
                </div>
                <div className="bg-gray-50 border border-gray-100 p-4 rounded-xl">
                  <div className="text-xs text-gray-400 font-medium">Overfit Warning Count</div>
                  <div className={`text-lg font-bold mt-1 ${report.smells.warnings.length > 0 ? 'text-amber-500' : 'text-gray-800'}`}>
                    {report.smells.warnings.length}
                  </div>
                </div>
              </div>

              {/* Permutation Tests */}
              <div className="border border-gray-100 rounded-xl overflow-hidden text-sm">
                <div className="bg-gray-50 px-4 py-2.5 font-semibold text-gray-700 border-b border-gray-100">
                  Permutation Significance Tests
                </div>
                <div className="p-4 space-y-4">
                  
                  {/* Monte Carlo */}
                  <div className="flex items-center justify-between border-b border-gray-100 pb-3">
                    <div>
                      <div className="font-semibold text-gray-800">In-Sample Monte Carlo</div>
                      <div className="text-xs text-gray-400">Compares strategy to block bootstrap random walks</div>
                    </div>
                    <div className="text-right">
                      <div className="font-mono font-bold text-gray-800">p = {(report.mc_p_value * 100).toFixed(1)}%</div>
                      <div className={`text-xs mt-0.5 ${report.mc_p_value < 0.01 ? 'text-green-600' : 'text-red-500'}`}>
                        {report.mc_p_value < 0.01 ? 'Signficant (target < 1%)' : 'Not Significant'}
                      </div>
                    </div>
                  </div>

                  {/* Walk Forward */}
                  <div className="flex items-center justify-between">
                    <div>
                      <div className="font-semibold text-gray-800">Walk-Forward Out-Of-Sample</div>
                      <div className="text-xs text-gray-400">Verifies rolling out-of-sample forward slices</div>
                    </div>
                    <div className="text-right">
                      <div className="font-mono font-bold text-gray-800">p = {(report.wf_p_value * 100).toFixed(1)}%</div>
                      <div className={`text-xs mt-0.5 ${report.wf_p_value < 0.05 ? 'text-green-600' : 'text-red-500'}`}>
                        {report.wf_p_value < 0.05 ? 'Significant (target < 5%)' : 'Not Significant'}
                      </div>
                    </div>
                  </div>

                </div>
              </div>

              {/* Overfit Warning List */}
              {report.smells.warnings.length > 0 ? (
                <div className="bg-amber-50 text-amber-800 p-4 rounded-xl border border-amber-100">
                  <div className="flex items-center gap-1.5 font-semibold text-sm mb-2">
                    <AlertTriangle size={16} /> Smell-Test Warnings
                  </div>
                  <ul className="list-disc list-inside text-xs space-y-1 opacity-90 pl-1 font-mono">
                    {report.smells.warnings.map((w, idx) => (
                      <li key={idx}>{w}</li>
                    ))}
                  </ul>
                </div>
              ) : (
                <div className="bg-green-50/50 text-green-800 p-4 rounded-xl border border-green-100 flex items-center gap-2 text-xs">
                  <CheckCircle size={14} className="text-green-600" />
                  <span>No overfitting smells detected (reasonable win-rates, trade counts, and parameters count).</span>
                </div>
              )}

            </div>
          )}

        </div>

        {/* Footer */}
        <div className="px-6 py-4 bg-gray-50 border-t border-gray-100 flex justify-end gap-3">
          <button onClick={onClose} className="px-4 py-2 border border-gray-200 text-gray-700 bg-white text-sm font-semibold rounded-xl hover:bg-gray-50 transition">
            Close
          </button>
          {report && (
            <button onClick={run} className="px-4 py-2 bg-indigo-600 text-white text-sm font-semibold rounded-xl hover:bg-indigo-700 transition flex items-center gap-2">
              <RefreshCw size={14} /> Run Again
            </button>
          )}
        </div>

      </div>
    </div>
  )
}
