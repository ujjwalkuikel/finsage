export default function StatCard({ label, value, sub, tone }) {
  const color = tone === 'up' ? 'text-up' : tone === 'down' ? 'text-down' : 'text-ink'
  return (
    <div className="bg-white border border-[#eceef4] rounded-2xl p-5">
      <div className="text-xs text-mute font-medium">{label}</div>
      <div className={`num text-2xl font-semibold mt-1 ${color}`}>{value}</div>
      <div className="text-xs text-mute mt-1">{sub}</div>
    </div>
  )
}
