import { formatPercent } from '@/utils/format'

interface PercentBadgeProps {
  value: number | string
  precision?: number
}

/** 百分比徽章组件，涨绿跌红 + 箭头 */
export default function PercentBadge({
  value,
  precision = 2,
}: PercentBadgeProps) {
  const num = typeof value === 'string' ? parseFloat(value) : value
  const isUp = num > 0
  const isDown = num < 0
  const color = isUp
    ? 'var(--success)'
    : isDown
      ? 'var(--danger)'
      : 'var(--text-secondary)'
  const arrow = isUp ? '▲' : isDown ? '▼' : ''

  return (
    <span
      style={{
        color,
        fontWeight: 500,
        fontVariantNumeric: 'tabular-nums',
      }}
    >
      {arrow} {formatPercent(num, precision)}
    </span>
  )
}
