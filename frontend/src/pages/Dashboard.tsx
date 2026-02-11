import { Row, Col, Card, Table, Alert } from 'antd'
import {
  MonitorOutlined,
  ThunderboltOutlined,
  NotificationOutlined,
  ClockCircleOutlined,
} from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'
import { useHealth } from '@/hooks/useHealth'
import { useSignals } from '@/hooks/useSignals'
import { useTicker } from '@/hooks/useTicker'
import { useMarketStore } from '@/stores/market'
import { useFavoriteStore } from '@/stores/favorites'
import StatusDot from '@/components/ui/StatusDot'
import SignalBadge from '@/components/business/SignalBadge'
import TickerCard from '@/components/business/TickerCard'
import LoadingSkeleton from '@/components/ui/LoadingSkeleton'
import { formatTime } from '@/utils/format'
import type { Signal } from '@/types/strategy'

export default function Dashboard() {
  const { exchange } = useMarketStore()
  const favoriteSymbols = useFavoriteStore((s) => s.symbols).slice(0, 8)
  const { data: health, isLoading: healthLoading } = useHealth()
  const { data: signalData, isLoading: signalsLoading } = useSignals(
    undefined,
    10,
  )
  const navigate = useNavigate()

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
      {/* 系统状态横幅 */}
      <HealthBanner health={health} loading={healthLoading} />

      {/* 统计卡片 */}
      <StatCards
        symbolCount={favoriteSymbols.length}
        signalCount={signalData?.signals?.length ?? 0}
      />

      {/* 收藏交易对行情 */}
      <div>
        <h3 style={{ marginBottom: 12, fontSize: 15 }}>收藏交易对</h3>
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fill, minmax(170px, 1fr))',
            gap: 12,
          }}
        >
          {favoriteSymbols.map((sym) => (
            <LiveTickerCard
              key={sym}
              exchange={exchange}
              symbol={sym}
              onClick={() =>
                navigate(`/market/${encodeURIComponent(sym)}`)
              }
            />
          ))}
        </div>
      </div>

      {/* 最新交易信号 */}
      <Card
        title="最新交易信号"
        size="small"
        style={{
          background: 'var(--bg-secondary)',
          border: '1px solid var(--border)',
        }}
      >
        {signalsLoading ? (
          <LoadingSkeleton rows={3} />
        ) : (
          <SignalTable signals={signalData?.signals || []} />
        )}
      </Card>
    </div>
  )
}

/** 系统健康状态横幅 */
function HealthBanner({
  health,
  loading,
}: {
  health: Record<string, unknown> | undefined
  loading: boolean
}) {
  if (loading) return <LoadingSkeleton rows={1} />

  const status = health?.status === 'healthy' ? 'healthy' : 'error'

  return (
    <Alert
      type={status === 'healthy' ? 'success' : 'error'}
      showIcon
      message={
        <span style={{ display: 'flex', gap: 24, alignItems: 'center' }}>
          <StatusDot
            status={status === 'healthy' ? 'healthy' : 'error'}
            label={`系统: ${status === 'healthy' ? '正常' : '异常'}`}
          />
        </span>
      }
      style={{
        background: 'var(--bg-secondary)',
        border: '1px solid var(--border)',
      }}
    />
  )
}

/** 统计卡片 */
function StatCards({
  symbolCount,
  signalCount,
}: {
  symbolCount: number
  signalCount: number
}) {
  const stats = [
    {
      icon: <MonitorOutlined />,
      label: '收藏交易对',
      value: String(symbolCount),
    },
    {
      icon: <ThunderboltOutlined />,
      label: '活跃策略',
      value: '3',
    },
    {
      icon: <NotificationOutlined />,
      label: '今日信号',
      value: String(signalCount),
    },
    {
      icon: <ClockCircleOutlined />,
      label: '数据来源',
      value: 'Binance',
    },
  ]

  return (
    <Row gutter={12}>
      {stats.map((s) => (
        <Col key={s.label} span={6}>
          <Card
            size="small"
            style={{
              background: 'var(--bg-secondary)',
              border: '1px solid var(--border)',
            }}
          >
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 8,
                color: 'var(--text-secondary)',
                fontSize: 13,
                marginBottom: 4,
              }}
            >
              {s.icon} {s.label}
            </div>
            <div style={{ fontSize: 22, fontWeight: 700 }}>{s.value}</div>
          </Card>
        </Col>
      ))}
    </Row>
  )
}

/** 实时行情卡片，自动获取真实价格 */
function LiveTickerCard({
  exchange,
  symbol,
  onClick,
}: {
  exchange: string
  symbol: string
  onClick: () => void
}) {
  const { data } = useTicker(exchange, symbol)
  const ticker = data?.ticker
  const price = ticker?.last_price ?? '--'
  const change = ticker?.price_change_24h ?? undefined

  return (
    <TickerCard
      symbol={symbol}
      price={price}
      change={change}
      onClick={onClick}
    />
  )
}

/** 信号表格 */
function SignalTable({
  signals,
}: {
  signals: Signal[]
}) {
  const columns = [
    {
      title: '交易对',
      dataIndex: 'symbol',
      key: 'symbol',
    },
    {
      title: '方向',
      dataIndex: 'signal_type',
      key: 'signal_type',
      render: (v: string, r: Signal) => (
        <SignalBadge
          type={v as 'BUY' | 'SELL' | 'HOLD'}
          confidence={r.confidence}
        />
      ),
    },
    {
      title: '策略',
      dataIndex: 'strategy',
      key: 'strategy',
    },
    {
      title: '时间',
      dataIndex: 'timestamp',
      key: 'timestamp',
      render: (v: string) => formatTime(v),
    },
  ]

  return (
    <Table
      dataSource={signals}
      columns={columns}
      rowKey="signal_id"
      size="small"
      pagination={false}
    />
  )
}
