import { formatPrice } from '@/utils/format'

interface PriceTextProps {
  value: number | string
  precision?: number
  prevValue?: number
  size?: 'sm' | 'md' | 'lg'
}

const sizeMap = {
  sm: '14px',
  md: '16px',
  lg: '24px',
}

/** 价格显示组件，自动涨跌着色 */
export default function PriceText({
  value,
  precision,
  prevValue,
  size = 'md',
}: PriceTextProps) {
  const num = typeof value === 'string' ? parseFloat(value) : value
  const prev = prevValue ?? num

  let color = 'var(--text-primary)'
  if (num > prev) color = 'var(--success)'
  else if (num < prev) color = 'var(--danger)'

  return (
    <span
      style={{
        color,
        fontSize: sizeMap[size],
        fontWeight: 600,
        fontVariantNumeric: 'tabular-nums',
      }}
    >
      {formatPrice(num, precision)}
    </span>
  )
}
