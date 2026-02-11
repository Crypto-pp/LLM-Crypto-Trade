import { Card, Row, Col, Table, Button, Tag } from 'antd'
import { useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { strategiesApi } from '@/api/strategies'
import { useSignals } from '@/hooks/useSignals'
import SignalBadge from '@/components/business/SignalBadge'
import LoadingSkeleton from '@/components/ui/LoadingSkeleton'
import { formatTime, formatPrice } from '@/utils/format'
import type { Strategy, Signal } from '@/types/strategy'

export default function Strategies() {
  const navigate = useNavigate()
  const { data, isLoading } = useQuery({
    queryKey: ['strategies'],
    queryFn: () => strategiesApi.list(),
  })
  const { data: signalData, isLoading: signalsLoading } = useSignals(
    undefined,
    20,
  )

  const strategies = data?.strategies || []
  const signals = signalData?.signals || []

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
      <h2 style={{ margin: 0, fontSize: 18 }}>策略管理</h2>

      {/* 策略卡片 */}
      {isLoading ? (
        <LoadingSkeleton rows={4} />
      ) : (
        <StrategyCards
          strategies={strategies}
          onDetail={(name: string) => navigate(`/strategies/${name}`)}
        />
      )}

      {/* 信号表格 */}
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
          <SignalTable signals={signals} />
        )}
      </Card>
    </div>
  )
}

/** 策略卡片网格 */
function StrategyCards({
  strategies,
  onDetail,
}: {
  strategies: Strategy[]
  onDetail: (name: string) => void
}) {
  return (
    <Row gutter={12}>
      {strategies.map((s) => (
        <Col key={s.name} span={8}>
          <Card
            size="small"
            style={{
              background: 'var(--bg-secondary)',
              border: '1px solid var(--border)',
            }}
          >
            <div style={{ fontWeight: 600, marginBottom: 8 }}>
              {s.name}
            </div>
            <div
              style={{
                color: 'var(--text-secondary)',
                fontSize: 13,
                marginBottom: 12,
              }}
            >
              {s.description}
            </div>
            <div style={{ marginBottom: 12 }}>
              {Object.entries(s.parameters || {}).map(([k, v]) => (
                <Tag key={k} style={{ marginBottom: 4 }}>
                  {k}: {v}
                </Tag>
              ))}
            </div>
            <Button
              type="primary"
              size="small"
              onClick={() => onDetail(s.name)}
            >
              详情
            </Button>
          </Card>
        </Col>
      ))}
    </Row>
  )
}

/** 信号表格 */
function SignalTable({
  signals,
}: {
  signals: Signal[]
}) {
  const columns = [
    { title: '交易对', dataIndex: 'symbol', key: 'symbol' },
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
      title: '入场价',
      dataIndex: 'entry_price',
      key: 'entry_price',
      render: (v: number) => formatPrice(v),
    },
    { title: '策略', dataIndex: 'strategy', key: 'strategy' },
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
      pagination={{ pageSize: 10 }}
    />
  )
}
