import { Card, Select, Space } from 'antd'
import { useMarketStore } from '@/stores/market'
import { useKlines } from '@/hooks/useKlines'
import { useTicker } from '@/hooks/useTicker'
import KlineChart from '@/components/business/KlineChart'
import IntervalSelector from '@/components/business/IntervalSelector'
import PriceText from '@/components/ui/PriceText'
import PercentBadge from '@/components/ui/PercentBadge'
import LoadingSkeleton from '@/components/ui/LoadingSkeleton'
import { formatVolume } from '@/utils/format'

export default function Market() {
  const { exchange, symbol, interval } = useMarketStore()
  const { data: klineData, isLoading: klineLoading } = useKlines(
    exchange,
    symbol,
    interval,
  )
  const { data: tickerData } = useTicker(exchange, symbol)

  const ticker = tickerData?.ticker

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
      {/* 工具栏 */}
      <Toolbar />

      {/* K线图 */}
      <Card
        size="small"
        style={{
          background: 'var(--bg-secondary)',
          border: '1px solid var(--border)',
        }}
        styles={{ body: { padding: 0 } }}
      >
        {klineLoading ? (
          <LoadingSkeleton rows={8} />
        ) : (
          <KlineChart
            data={klineData?.klines || []}
            height={480}
          />
        )}
      </Card>

      {/* 实时行情面板 */}
      {ticker && <TickerPanel ticker={ticker} />}
    </div>
  )
}

function Toolbar() {
  const { exchange, setExchange } = useMarketStore()

  return (
    <div
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: 12,
        flexWrap: 'wrap',
      }}
    >
      <Select
        value={exchange}
        onChange={setExchange}
        size="small"
        style={{ width: 120 }}
        options={[
          { label: 'Binance', value: 'binance' },
          { label: 'OKX', value: 'okx' },
        ]}
      />
      <IntervalSelector />
    </div>
  )
}

function TickerPanel({
  ticker,
}: {
  ticker: {
    last_price: string
    price_change_24h: string | null
    volume_24h: string | null
  }
}) {
  return (
    <Card
      size="small"
      style={{
        background: 'var(--bg-secondary)',
        border: '1px solid var(--border)',
      }}
    >
      <Space size={32}>
        <div>
          <div style={{ color: 'var(--text-secondary)', fontSize: 12 }}>
            最新价
          </div>
          <PriceText value={ticker.last_price} size="lg" />
        </div>
        {ticker.price_change_24h && (
          <div>
            <div style={{ color: 'var(--text-secondary)', fontSize: 12 }}>
              24h涨跌
            </div>
            <PercentBadge value={ticker.price_change_24h} />
          </div>
        )}
        {ticker.volume_24h && (
          <div>
            <div style={{ color: 'var(--text-secondary)', fontSize: 12 }}>
              24h成交量
            </div>
            <span>{formatVolume(ticker.volume_24h)}</span>
          </div>
        )}
      </Space>
    </Card>
  )
}
