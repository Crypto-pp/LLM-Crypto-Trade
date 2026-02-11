import { useParams, useNavigate } from 'react-router-dom'
import { useState } from 'react'
import { Card, Button, Tag, message } from 'antd'
import { ArrowLeftOutlined } from '@ant-design/icons'
import { useQuery } from '@tanstack/react-query'
import { strategiesApi } from '@/api/strategies'
import { useMarketStore } from '@/stores/market'
import IntervalSelector from '@/components/business/IntervalSelector'
import SignalBadge from '@/components/business/SignalBadge'
import LoadingSkeleton from '@/components/ui/LoadingSkeleton'
import EmptyState from '@/components/ui/EmptyState'
import { formatPrice, formatTime } from '@/utils/format'
import type { Signal } from '@/types/strategy'

export default function StrategyDetail() {
  const { name } = useParams<{ name: string }>()
  const navigate = useNavigate()
  const { symbol, interval } = useMarketStore()
  const [analyzing, setAnalyzing] = useState(false)
  const [result, setResult] = useState<Record<string, unknown> | null>(null)

  const { data, isLoading } = useQuery({
    queryKey: ['strategies'],
    queryFn: () => strategiesApi.list(),
  })

  const { data: signalData } = useQuery({
    queryKey: ['signals', name],
    queryFn: () => strategiesApi.getSignals({ strategy: name, limit: 20 }),
    enabled: !!name,
  })

  const strategies = data?.strategies || []
  const strategy = strategies.find((s) => s.name === name)
  const signals = signalData?.signals || []

  const handleAnalyze = async () => {
    if (!name) return
    setAnalyzing(true)
    try {
      const res = await strategiesApi.analyze(name, { symbol, interval })
      setResult(res)
      message.success('分析完成')
    } catch {
      message.error('分析失败')
    } finally {
      setAnalyzing(false)
    }
  }

  if (isLoading) return <LoadingSkeleton rows={6} />

  if (!strategy) {
    return <EmptyState description={`未找到策略: ${name}`} />
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
      <Header name={strategy.name} onBack={() => navigate('/strategies')} />
      <StrategyInfo strategy={strategy} />
      <AnalyzePanel
        symbol={symbol}
        analyzing={analyzing}
        onAnalyze={handleAnalyze}
      />
      {result && <AnalyzeResult data={result} />}
      <SignalHistory signals={signals} />
    </div>
  )
}

function Header({ name, onBack }: { name: string; onBack: () => void }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
      <Button
        type="text"
        icon={<ArrowLeftOutlined />}
        onClick={onBack}
      />
      <h2 style={{ margin: 0, fontSize: 18 }}>{name}</h2>
    </div>
  )
}

function StrategyInfo({
  strategy,
}: {
  strategy: { name: string; description: string; parameters: Record<string, number> }
}) {
  return (
    <Card
      title="策略信息"
      size="small"
      style={{
        background: 'var(--bg-secondary)',
        border: '1px solid var(--border)',
      }}
    >
      <div style={{ marginBottom: 12, color: 'var(--text-secondary)', fontSize: 13 }}>
        {strategy.description}
      </div>
      <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
        {Object.entries(strategy.parameters).map(([k, v]) => (
          <Tag key={k}>
            {k}: {v}
          </Tag>
        ))}
      </div>
    </Card>
  )
}

function AnalyzePanel({
  symbol,
  analyzing,
  onAnalyze,
}: {
  symbol: string
  analyzing: boolean
  onAnalyze: () => void
}) {
  return (
    <Card
      title="执行分析"
      size="small"
      style={{
        background: 'var(--bg-secondary)',
        border: '1px solid var(--border)',
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
        <span style={{ fontSize: 13, color: 'var(--text-secondary)' }}>
          交易对: <strong style={{ color: 'var(--text-primary)' }}>{symbol}</strong>
        </span>
        <IntervalSelector />
        <Button
          type="primary"
          loading={analyzing}
          onClick={onAnalyze}
        >
          开始分析
        </Button>
      </div>
    </Card>
  )
}

function AnalyzeResult({ data }: { data: Record<string, unknown> }) {
  return (
    <Card
      title="分析结果"
      size="small"
      style={{
        background: 'var(--bg-secondary)',
        border: '1px solid var(--border)',
      }}
    >
      <pre style={{ fontSize: 12, color: 'var(--text-secondary)', margin: 0 }}>
        {JSON.stringify(data, null, 2)}
      </pre>
    </Card>
  )
}

function SignalHistory({
  signals,
}: {
  signals: Signal[]
}) {
  if (signals.length === 0) {
    return (
      <Card
        title="历史信号"
        size="small"
        style={{
          background: 'var(--bg-secondary)',
          border: '1px solid var(--border)',
        }}
      >
        <EmptyState description="暂无历史信号" />
      </Card>
    )
  }

  return (
    <Card
      title="历史信号"
      size="small"
      style={{
        background: 'var(--bg-secondary)',
        border: '1px solid var(--border)',
      }}
    >
      <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
        {signals.map((s, i) => (
          <div
            key={i}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 12,
              fontSize: 13,
              padding: '6px 0',
              borderBottom: '1px solid var(--border)',
            }}
          >
            <span style={{ width: 90 }}>{s.symbol}</span>
            <SignalBadge
              type={s.signal_type}
              confidence={s.confidence}
            />
            <span style={{ color: 'var(--text-secondary)' }}>
              入场: {formatPrice(s.entry_price)}
            </span>
            <span style={{ marginLeft: 'auto', fontSize: 11, color: 'var(--text-secondary)' }}>
              {formatTime(s.timestamp)}
            </span>
          </div>
        ))}
      </div>
    </Card>
  )
}
