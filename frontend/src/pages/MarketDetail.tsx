import { useParams } from 'react-router-dom'
import { Card } from 'antd'
import { useMarketStore } from '@/stores/market'
import { useKlines } from '@/hooks/useKlines'
import { useTicker } from '@/hooks/useTicker'
import { useSignals } from '@/hooks/useSignals'
import KlineChart from '@/components/business/KlineChart'
import IntervalSelector from '@/components/business/IntervalSelector'
import PriceText from '@/components/ui/PriceText'
import PercentBadge from '@/components/ui/PercentBadge'
import SignalBadge from '@/components/business/SignalBadge'
import LoadingSkeleton from '@/components/ui/LoadingSkeleton'
import EmptyState from '@/components/ui/EmptyState'
import { formatPrice, formatVolume, formatTime } from '@/utils/format'
import type { Ticker } from '@/types/market'
import type { Signal } from '@/types/strategy'
import { useEffect } from 'react'

export default function MarketDetail() {
  const { symbol: urlSymbol } = useParams<{ symbol: string }>()
  const { exchange, interval, setSymbol } = useMarketStore()
  const symbol = urlSymbol ? decodeURIComponent(urlSymbol) : 'BTC/USDT'

  useEffect(() => {
    if (urlSymbol) setSymbol(decodeURIComponent(urlSymbol))
  }, [urlSymbol, setSymbol])

  const { data: klineData, isLoading: klineLoading } = useKlines(
    exchange,
    symbol,
    interval,
  )
  const { data: tickerData } = useTicker(exchange, symbol)
  const { data: signalData } = useSignals(symbol, 5)

  const ticker = tickerData?.ticker
  const signals = signalData?.signals || []

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
      {/* 标题栏 */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
        <h2 style={{ margin: 0, fontSize: 18 }}>{symbol}</h2>
        {ticker && <PriceText value={ticker.last_price} size="lg" />}
        {ticker?.price_change_24h && (
          <PercentBadge value={ticker.price_change_24h} />
        )}
        <div style={{ marginLeft: 'auto' }}>
          <IntervalSelector />
        </div>
      </div>

      {/* K线图 */}
      {klineLoading ? (
        <LoadingSkeleton rows={8} />
      ) : (
        <KlineChart data={klineData?.klines || []} height={500} />
      )}

      {/* 下方面板 */}
      <div style={{ display: 'flex', gap: 12 }}>
        {/* 行情详情 */}
        <Card
          title="行情详情"
          size="small"
          style={{
            flex: 1,
            background: 'var(--bg-secondary)',
            border: '1px solid var(--border)',
          }}
        >
          {ticker ? (
            <TickerDetail ticker={ticker} />
          ) : (
            <EmptyState description="暂无行情数据" />
          )}
        </Card>

        {/* 交易信号 */}
        <Card
          title="交易信号"
          size="small"
          style={{
            flex: 1,
            background: 'var(--bg-secondary)',
            border: '1px solid var(--border)',
          }}
        >
          {signals.length > 0 ? (
            <SignalList signals={signals} />
          ) : (
            <EmptyState description="暂无信号" />
          )}
        </Card>
      </div>
    </div>
  )
}

function TickerDetail({
  ticker,
}: {
  ticker: Ticker
}) {
  const rows = [
    { label: '最新价', value: formatPrice(ticker.last_price || 0) },
    { label: '买一价', value: ticker.bid_price ? formatPrice(ticker.bid_price) : '--' },
    { label: '卖一价', value: ticker.ask_price ? formatPrice(ticker.ask_price) : '--' },
    { label: '24h成交量', value: ticker.volume_24h ? formatVolume(ticker.volume_24h) : '--' },
  ]

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
      {rows.map((r) => (
        <div
          key={r.label}
          style={{
            display: 'flex',
            justifyContent: 'space-between',
            fontSize: 13,
          }}
        >
          <span style={{ color: 'var(--text-secondary)' }}>{r.label}</span>
          <span>{r.value}</span>
        </div>
      ))}
    </div>
  )
}

function SignalList({
  signals,
}: {
  signals: Signal[]
}) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
      {signals.map((s, i) => (
        <div
          key={i}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 8,
            fontSize: 13,
          }}
        >
          <SignalBadge
            type={s.signal_type}
            confidence={s.confidence}
          />
          <span style={{ color: 'var(--text-secondary)' }}>
            {s.strategy}
          </span>
          <span style={{ marginLeft: 'auto', fontSize: 11, color: 'var(--text-secondary)' }}>
            {formatTime(s.timestamp)}
          </span>
        </div>
      ))}
    </div>
  )
}
