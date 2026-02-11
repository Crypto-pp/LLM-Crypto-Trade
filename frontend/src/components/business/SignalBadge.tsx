import { Tag } from 'antd'
import { SIGNAL_COLORS, SIGNAL_LABELS } from '@/utils/constants'

interface SignalBadgeProps {
  type: 'BUY' | 'SELL' | 'HOLD'
  confidence?: number
}

/** 交易信号标签 */
export default function SignalBadge({ type, confidence }: SignalBadgeProps) {
  return (
    <Tag
      color={SIGNAL_COLORS[type]}
      style={{ fontWeight: 600, fontSize: 12 }}
    >
      {SIGNAL_LABELS[type]}
      {confidence != null && ` ${(confidence * 100).toFixed(0)}%`}
    </Tag>
  )
}
