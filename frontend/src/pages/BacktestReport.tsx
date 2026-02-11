import { useParams, useNavigate } from 'react-router-dom'
import { Card, Row, Col, Button, Tag } from 'antd'
import { ArrowLeftOutlined } from '@ant-design/icons'
import { useBacktestResults } from '@/hooks/useBacktest'
import EquityCurve from '@/components/charts/EquityCurve'
import LoadingSkeleton from '@/components/ui/LoadingSkeleton'
import EmptyState from '@/components/ui/EmptyState'
import { formatPercent } from '@/utils/format'

export default function BacktestReport() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const { data, isLoading } = useBacktestResults(id || '')

  if (isLoading) return <LoadingSkeleton rows={8} />
  if (!data) return <EmptyState description="未找到回测结果" />

  const { metrics, summary, rating } = data

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
      <Header id={id || ''} onBack={() => navigate('/backtest')} />
      <MetricsCards metrics={metrics} />
      <EquityCurveCard summary={summary} />
      <SummaryCard summary={summary} />
      {rating && <RatingCard rating={rating} />}
    </div>
  )
}

function Header({ id, onBack }: { id: string; onBack: () => void }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
      <Button type="text" icon={<ArrowLeftOutlined />} onClick={onBack} />
      <h2 style={{ margin: 0, fontSize: 18 }}>回测报告</h2>
      <Tag color="blue">{id}</Tag>
    </div>
  )
}

function MetricsCards({
  metrics,
}: {
  metrics: {
    total_return: number
    sharpe_ratio: number
    max_drawdown: number
    win_rate: number
    total_trades: number
  }
}) {
  const items = [
    {
      label: '总收益率',
      value: formatPercent(metrics.total_return),
      color: metrics.total_return >= 0 ? 'var(--success)' : 'var(--danger)',
    },
    {
      label: '夏普比率',
      value: metrics.sharpe_ratio.toFixed(2),
      color: metrics.sharpe_ratio >= 1 ? 'var(--success)' : 'var(--warning)',
    },
    {
      label: '最大回撤',
      value: formatPercent(metrics.max_drawdown),
      color: 'var(--danger)',
    },
    {
      label: '胜率',
      value: formatPercent(metrics.win_rate),
      color: metrics.win_rate >= 50 ? 'var(--success)' : 'var(--warning)',
    },
    {
      label: '总交易次数',
      value: String(metrics.total_trades),
      color: 'var(--text-primary)',
    },
  ]

  return (
    <Row gutter={12}>
      {items.map((item) => (
        <Col key={item.label} flex="1">
          <Card
            size="small"
            style={{
              background: 'var(--bg-secondary)',
              border: '1px solid var(--border)',
            }}
          >
            <div style={{ color: 'var(--text-secondary)', fontSize: 12, marginBottom: 4 }}>
              {item.label}
            </div>
            <div style={{ fontSize: 20, fontWeight: 700, color: item.color }}>
              {item.value}
            </div>
          </Card>
        </Col>
      ))}
    </Row>
  )
}

function EquityCurveCard({
  summary,
}: {
  summary: Record<string, unknown>
}) {
  const equity = (summary.equity_curve || []) as Array<{
    time: string
    value: number
  }>

  if (equity.length === 0) return null

  return (
    <Card
      title="资金曲线"
      size="small"
      style={{
        background: 'var(--bg-secondary)',
        border: '1px solid var(--border)',
      }}
    >
      <EquityCurve data={equity} height={360} />
    </Card>
  )
}

function SummaryCard({
  summary,
}: {
  summary: Record<string, unknown>
}) {
  const labelMap: Record<string, string> = {
    initial_capital: '初始资金',
    final_capital: '最终资金',
    total_return: '总收益率',
    annualized_return: '年化收益率',
    max_drawdown: '最大回撤',
    sharpe_ratio: '夏普比率',
    win_rate: '胜率',
    total_trades: '总交易次数',
    total_pnl: '总盈亏',
    avg_daily_return: '日均收益率',
  }

  const displayKeys = Object.keys(summary).filter(
    (k) => k !== 'equity_curve',
  )

  if (displayKeys.length === 0) return null

  return (
    <Card
      title="回测摘要"
      size="small"
      style={{
        background: 'var(--bg-secondary)',
        border: '1px solid var(--border)',
      }}
    >
      <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
        {displayKeys.map((key) => (
          <div
            key={key}
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              fontSize: 13,
            }}
          >
            <span style={{ color: 'var(--text-secondary)' }}>{labelMap[key] || key}</span>
            <span>
              {typeof summary[key] === 'object'
                ? JSON.stringify(summary[key])
                : String(summary[key])}
            </span>
          </div>
        ))}
      </div>
    </Card>
  )
}

function RatingCard({
  rating,
}: {
  rating: Record<string, unknown>
}) {
  const labelMap: Record<string, string> = {
    rating: '综合评级',
    total_score: '总分',
    return_score: '收益得分',
    risk_score: '风险得分',
    stability_score: '稳定性得分',
    trading_score: '交易得分',
  }

  return (
    <Card
      title="策略评级"
      size="small"
      style={{
        background: 'var(--bg-secondary)',
        border: '1px solid var(--border)',
      }}
    >
      <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
        {Object.entries(rating).map(([key, val]) => (
          <div
            key={key}
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              fontSize: 13,
            }}
          >
            <span style={{ color: 'var(--text-secondary)' }}>{labelMap[key] || key}</span>
            <span>{String(val)}</span>
          </div>
        ))}
      </div>
    </Card>
  )
}
