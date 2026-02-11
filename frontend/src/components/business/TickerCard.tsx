import { Card } from 'antd'
import PriceText from '@/components/ui/PriceText'
import PercentBadge from '@/components/ui/PercentBadge'

interface TickerCardProps {
  symbol: string
  price: number | string
  change?: number | string
  onClick?: () => void
}

/** 行情卡片：价格 + 涨跌幅 */
export default function TickerCard({
  symbol,
  price,
  change,
  onClick,
}: TickerCardProps) {
  return (
    <Card
      hoverable
      size="small"
      onClick={onClick}
      style={{
        minWidth: 160,
        background: 'var(--bg-secondary)',
        border: '1px solid var(--border)',
      }}
      styles={{ body: { padding: '12px 16px' } }}
    >
      <div style={{ fontWeight: 600, marginBottom: 4 }}>{symbol}</div>
      <PriceText value={price} size="lg" />
      {change != null && (
        <div style={{ marginTop: 4 }}>
          <PercentBadge value={change} />
        </div>
      )}
    </Card>
  )
}
