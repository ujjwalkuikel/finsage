import { ShieldCheck, Play } from 'lucide-react'
import EquityChart from './EquityChart'

export default function StrategiesTable({ strategies = {}, onValidate }) {
  const list = Object.values(strategies)

  if (!list.length) {
    return (
      <div className="bg-white border border-gray-100 rounded-2xl p-12 text-center text-gray-400 text-sm">
        No strategy backtests run yet. Click <span className="font-semibold text-gray-800">Run simulation</span> to populate metrics.
      </div>
    )
  }

  const money = (n) => n == null ? '—' : (n < 0 ? '-$' : '$') + Math.abs(n).toFixed(2)

  return (
    <div className="bg-white border border-gray-100 rounded-2xl overflow-hidden">
      <div className="px-6 py-4 border-b border-gray-100 flex items-center justify-between">
        <h2 className="font-semibold text-gray-900 text-sm">Strategies Library</h2>
        <span className="text-xs text-gray-400 font-mono">{list.length} strategies active</span>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-gray-50/50 text-gray-400 text-xs font-semibold uppercase tracking-wider border-b border-gray-100">
            <tr className="text-left">
              <th className="px-6 py-3 font-medium">Strategy</th>
              <th className="px-6 py-3 font-medium text-center">Trades</th>
              <th className="px-6 py-3 font-medium text-right">Win Rate</th>
              <th className="px-6 py-3 font-medium text-right">Expectancy</th>
              <th className="px-6 py-3 font-medium text-right">Profit Factor</th>
              <th className="px-6 py-3 font-medium text-right">P&L</th>
              <th className="px-6 py-3 font-medium text-center">Equity Curve</th>
              <th className="px-6 py-3 font-medium text-center">Gauntlet</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {list.map(s => {
              const pnlTone = s.total_pnl > 0 ? 'text-green-600' : s.total_pnl < 0 ? 'text-red-600' : 'text-gray-500'
              const expTone = s.expectancy_r > 0 ? 'text-green-600' : s.expectancy_r < 0 ? 'text-red-600' : 'text-gray-500'

              return (
                <tr key={s.strategy} className="hover:bg-gray-50/30 transition-colors">
                  <td className="px-6 py-4">
                    <span className="font-semibold text-gray-800 capitalize tracking-tight">
                      {s.strategy.replace(/_/g, ' ')}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-center font-mono font-medium text-gray-600">
                    {s.total_trades}
                  </td>
                  <td className="px-6 py-4 text-right font-mono font-medium text-gray-700">
                    {s.win_rate}%
                  </td>
                  <td className={`px-6 py-4 text-right font-mono font-bold ${expTone}`}>
                    {s.expectancy_r.toFixed(3)} R
                  </td>
                  <td className="px-6 py-4 text-right font-mono font-medium text-gray-700">
                    {s.profit_factor === Infinity ? '∞' : s.profit_factor.toFixed(2)}
                  </td>
                  <td className={`px-6 py-4 text-right font-mono font-bold ${pnlTone}`}>
                    {money(s.total_pnl)}
                  </td>
                  <td className="px-6 py-3 flex justify-center">
                    {/* Small visual thumbnail curve */}
                    <EquityChart data={s.equity_curve} width={130} height={40} />
                  </td>
                  <td className="px-6 py-4 text-center">
                    <button
                      onClick={() => onValidate(s.strategy)}
                      className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold text-indigo-600 bg-indigo-50 rounded-xl hover:bg-indigo-100 hover:text-indigo-700 transition"
                    >
                      <ShieldCheck size={13} /> Validate
                    </button>
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </div>
  )
}
