const money = (n) => n == null ? '—' : (n < 0 ? '-$' : '$') + Math.abs(n).toFixed(2)

export default function TradesTable({ trades }) {
  if (!trades.length) {
    return (
      <div className="bg-white border border-[#eceef4] rounded-2xl px-5 py-12 text-center text-mute text-sm">
        No trades yet. Click <span className="font-medium text-ink">Run simulation</span> to populate the ledger.
      </div>
    )
  }
  return (
    <div className="bg-white border border-[#eceef4] rounded-2xl overflow-hidden">
      <div className="px-5 py-4 border-b border-[#f0f1f6] font-semibold text-sm">Trades</div>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="text-mute text-xs uppercase tracking-wide">
            <tr className="text-left border-b border-[#f0f1f6]">
              <th className="px-5 py-3 font-medium">Strategy</th>
              <th className="px-5 py-3 font-medium">Symbol</th>
              <th className="px-5 py-3 font-medium">Side</th>
              <th className="px-5 py-3 font-medium text-right">Entry</th>
              <th className="px-5 py-3 font-medium text-right">Exit</th>
              <th className="px-5 py-3 font-medium text-right">P&amp;L</th>
              <th className="px-5 py-3 font-medium text-right">R</th>
              <th className="px-5 py-3 font-medium">Outcome</th>
            </tr>
          </thead>
          <tbody>
            {trades.map((t) => {
              const tone = (t.pnl ?? 0) > 0 ? 'text-up' : (t.pnl ?? 0) < 0 ? 'text-down' : 'text-mute'
              return (
                <tr key={t.id} className="border-b border-[#f5f6fa] hover:bg-[#fafbfd]">
                  <td className="px-5 py-3 text-mute">{t.strategy}</td>
                  <td className="px-5 py-3 font-medium">{t.symbol}</td>
                  <td className="px-5 py-3">{t.side}</td>
                  <td className="px-5 py-3 text-right num">{t.entry_price?.toFixed(2)}</td>
                  <td className="px-5 py-3 text-right num">{t.exit_price ? t.exit_price.toFixed(2) : '—'}</td>
                  <td className={`px-5 py-3 text-right num font-medium ${tone}`}>{money(t.pnl)}</td>
                  <td className={`px-5 py-3 text-right num ${tone}`}>{t.pnl_r != null ? t.pnl_r.toFixed(2) : '—'}</td>
                  <td className="px-5 py-3 text-mute capitalize">{t.status === 'open' ? 'open' : (t.exit_reason || 'closed')}</td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </div>
  )
}
