const money = (n) => n == null ? '—' : (n < 0 ? '-$' : '$') + Math.abs(n).toFixed(2)

export default function TradesTable({ trades }) {
  if (!trades.length) {
    return (
      <div className="bg-white border border-neutral-200 rounded-2xl px-5 py-12 text-center text-neutral-400 text-sm">
        No trades yet. Click <span className="font-semibold text-neutral-800">Run Simulation</span> to populate the ledger.
      </div>
    )
  }
  return (
    <div className="bg-white border border-neutral-200 rounded-2xl overflow-hidden shadow-sm">
      <div className="px-6 py-4 border-b border-neutral-200 font-semibold text-gray-900 text-sm">Trades Ledger</div>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-gray-50/50 text-neutral-400 text-xs font-semibold uppercase tracking-wider border-b border-neutral-200">
            <tr className="text-left">
              <th className="px-6 py-3 font-medium">Strategy</th>
              <th className="px-6 py-3 font-medium">Symbol</th>
              <th className="px-6 py-3 font-medium">Side</th>
              <th className="px-6 py-3 font-medium text-right">Entry</th>
              <th className="px-6 py-3 font-medium text-right">Exit</th>
              <th className="px-6 py-3 font-medium text-right">P&amp;L</th>
              <th className="px-6 py-3 font-medium text-right">R</th>
              <th className="px-6 py-3 font-medium">Outcome</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {trades.map((t) => {
              const isProfit = (t.pnl ?? 0) > 0
              const isLoss = (t.pnl ?? 0) < 0
              const pnlColor = isProfit ? 'text-green-600' : isLoss ? 'text-red-600' : 'text-neutral-500'
              
              const sideBadge = t.side === 'long'
                ? '<span class="text-xs font-medium px-2 py-0.5 rounded bg-green-50 text-green-700">long</span>'
                : '<span class="text-xs font-medium px-2 py-0.5 rounded bg-red-50 text-red-700">short</span>'

              return (
                <tr key={t.id} className="hover:bg-gray-50/30 transition-colors">
                  <td className="px-6 py-4 text-neutral-500 capitalize">{t.strategy.replace(/_/g, ' ')}</td>
                  <td className="px-6 py-4 font-semibold text-neutral-900">{t.symbol}</td>
                  <td className="px-6 py-4">
                    <span 
                      className={`text-xs font-semibold px-2.5 py-1 rounded-full uppercase tracking-wider ${
                        t.side === 'long' 
                          ? 'bg-green-50 text-green-700' 
                          : 'bg-red-50 text-red-700'
                      }`}
                    >
                      {t.side}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-right font-mono text-neutral-600">{t.entry_price?.toFixed(2)}</td>
                  <td className="px-6 py-4 text-right font-mono text-neutral-600">{t.exit_price ? t.exit_price.toFixed(2) : '—'}</td>
                  <td className={`px-6 py-4 text-right font-mono font-bold ${pnlColor}`}>{money(t.pnl)}</td>
                  <td className={`px-6 py-4 text-right font-mono font-semibold ${pnlColor}`}>
                    {t.pnl_r != null ? `${t.pnl_r.toFixed(2)} R` : '—'}
                  </td>
                  <td className="px-6 py-4 text-neutral-500 capitalize">
                    {t.status === 'open' ? (
                      <span className="text-xs font-semibold px-2 py-0.5 rounded bg-blue-50 text-blue-700 uppercase tracking-wide">open</span>
                    ) : (
                      t.exit_reason || 'closed'
                    )}
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
