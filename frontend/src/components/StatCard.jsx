export default function StatCard({ label, value, sub, tone }) {
  const color = tone === 'up' ? 'text-green-600' : tone === 'down' ? 'text-red-600' : 'text-neutral-950'
  return (
    <div className="bg-white border border-neutral-200 rounded-2xl p-5 shadow-sm">
      <div className="text-xs text-neutral-400 font-semibold uppercase tracking-wider">{label}</div>
      <div className={`num text-2xl font-bold mt-1.5 ${color}`}>{value}</div>
      <div className="text-xs text-neutral-400 mt-1">{sub}</div>
    </div>
  )
}
