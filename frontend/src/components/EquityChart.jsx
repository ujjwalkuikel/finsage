import { useId } from 'react'

export default function EquityChart({ data = [], width = 360, height = 120 }) {
  const gradientId = useId()
  
  if (!data || data.length < 2) {
    return (
      <div className="flex items-center justify-center bg-gray-50 border border-gray-100 rounded-lg text-xs text-gray-400 font-mono" style={{ width, height }}>
        Not enough trades to plot equity curve
      </div>
    )
  }

  // Find bounds
  const pnls = data.map(d => d.pnl)
  const minPnl = Math.min(0, ...pnls)
  const maxPnl = Math.max(10, ...pnls)
  const pnlRange = maxPnl - minPnl

  const padding = 10
  const chartWidth = width - 2 * padding
  const chartHeight = height - 2 * padding

  // Convert points to SVG coordinates
  const points = data.map((d, i) => {
    const x = padding + (i / (data.length - 1)) * chartWidth
    // Invert Y coordinate so higher P&L sits at the top of the SVG viewport
    const y = padding + chartHeight - ((d.pnl - minPnl) / pnlRange) * chartHeight
    return { x, y }
  })

  // Create path strings
  const linePath = points.map((p, i) => `${i === 0 ? 'M' : 'L'} ${p.x.toFixed(1)} ${p.y.toFixed(1)}`).join(' ')
  
  // Close the path at the baseline to fill the area under the curve
  const zeroY = padding + chartHeight - ((0 - minPnl) / pnlRange) * chartHeight
  const areaPath = `${linePath} L ${points[points.length - 1].x.toFixed(1)} ${zeroY.toFixed(1)} L ${points[0].x.toFixed(1)} ${zeroY.toFixed(1)} Z`

  const isProfitable = data[data.length - 1].pnl >= 0
  const strokeColor = isProfitable ? '#16a34a' : '#dc2626'
  const stopColor = isProfitable ? 'rgba(22, 163, 74, 0.15)' : 'rgba(220, 38, 38, 0.15)'

  return (
    <div className="relative" style={{ width, height }}>
      <svg width={width} height={height} className="overflow-visible">
        <defs>
          <linearGradient id={gradientId} x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={stopColor} />
            <stop offset="100%" stopColor="rgba(255, 255, 255, 0)" />
          </linearGradient>
        </defs>

        {/* Zero baseline guide */}
        <line
          x1={padding}
          y1={zeroY}
          x2={width - padding}
          y2={zeroY}
          stroke="#eceef4"
          strokeWidth="1"
          strokeDasharray="2 3"
        />

        {/* Filled gradient area */}
        <path d={areaPath} fill={`url(#${gradientId})`} />

        {/* Curve stroke */}
        <path d={linePath} fill="none" stroke={strokeColor} strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round" />

        {/* Endpoint marker dot */}
        <circle
          cx={points[points.length - 1].x}
          cy={points[points.length - 1].y}
          r="3"
          fill={strokeColor}
          stroke="#fff"
          strokeWidth="1.5"
        />
      </svg>
    </div>
  )
}
