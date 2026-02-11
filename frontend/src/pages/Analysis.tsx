import { useState } from 'react'
import { Card, Button, Checkbox, Table, Row, Col } from 'antd'
import { useQuery } from '@tanstack/react-query'
import { useMarketStore } from '@/stores/market'
import { analysisApi } from '@/api/analysis'
import type { IndicatorResult, SupportResistanceResult, PatternResult } from '@/types/analysis'
import IntervalSelector from '@/components/business/IntervalSelector'
import LoadingSkeleton from '@/components/ui/LoadingSkeleton'
import EmptyState from '@/components/ui/EmptyState'

const indicatorOptions = [
  { label: 'MA (移动平均)', value: 'ma', group: '趋势' },
  { label: 'EMA (指数MA)', value: 'ema', group: '趋势' },
  { label: 'MACD', value: 'macd', group: '趋势' },
  { label: 'RSI (相对强弱)', value: 'rsi', group: '震荡' },
  { label: 'Bollinger (布林带)', value: 'bollinger', group: '波动率' },
]

export default function Analysis() {
  const { symbol, interval } = useMarketStore()
  const [selected, setSelected] = useState<string[]>(['ma', 'rsi'])
  const [enabled, setEnabled] = useState(false)

  const { data, isLoading } = useQuery({
    queryKey: ['indicators', symbol, interval, selected],
    queryFn: () =>
      analysisApi.getIndicators({
        symbol,
        interval,
        indicators: selected,
      }),
    enabled: enabled && selected.length > 0,
  })

  const { data: srData } = useQuery({
    queryKey: ['support-resistance', symbol, interval],
    queryFn: () =>
      analysisApi.getSupportResistance({ symbol, interval }),
    enabled,
  })

  const { data: patternData } = useQuery({
    queryKey: ['patterns', symbol, interval],
    queryFn: () => analysisApi.getPatterns({ symbol, interval }),
    enabled,
  })

  return (
    <div style={{ display: 'flex', gap: 12 }}>
      {/* 左侧：指标选择面板 */}
      <IndicatorPanel
        selected={selected}
        onChange={setSelected}
        onAnalyze={() => setEnabled(true)}
      />

      {/* 右侧：分析结果 */}
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: 12 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <span style={{ fontWeight: 600 }}>{symbol}</span>
          <IntervalSelector />
        </div>

        {!enabled ? (
          <EmptyState description="选择指标后点击「开始分析」" />
        ) : isLoading ? (
          <LoadingSkeleton rows={6} />
        ) : (
          <>
            <IndicatorResults data={data} />
            <SupportResistanceCard data={srData} />
            <PatternCard data={patternData} />
          </>
        )}
      </div>
    </div>
  )
}

function IndicatorPanel({
  selected,
  onChange,
  onAnalyze,
}: {
  selected: string[]
  onChange: (v: string[]) => void
  onAnalyze: () => void
}) {
  return (
    <Card
      title="指标选择"
      size="small"
      style={{
        width: 260,
        background: 'var(--bg-secondary)',
        border: '1px solid var(--border)',
        flexShrink: 0,
      }}
    >
      <Checkbox.Group
        value={selected}
        onChange={(v) => onChange(v as string[])}
        style={{ display: 'flex', flexDirection: 'column', gap: 8 }}
      >
        {indicatorOptions.map((opt) => (
          <Checkbox key={opt.value} value={opt.value}>
            {opt.label}
          </Checkbox>
        ))}
      </Checkbox.Group>
      <Button
        type="primary"
        block
        style={{ marginTop: 16 }}
        onClick={onAnalyze}
        disabled={selected.length === 0}
      >
        开始分析
      </Button>
    </Card>
  )
}

function IndicatorResults({
  data,
}: {
  data: IndicatorResult | undefined
}) {
  if (!data) return null
  const indicators = (data.indicators || {}) as Record<string, unknown>

  const rows = Object.entries(indicators).map(([key, val]) => ({
    key,
    indicator: key.toUpperCase(),
    value: typeof val === 'object' ? JSON.stringify(val) : String(val),
  }))

  return (
    <Card
      title="指标计算结果"
      size="small"
      style={{
        background: 'var(--bg-secondary)',
        border: '1px solid var(--border)',
      }}
    >
      <Table
        dataSource={rows}
        columns={[
          { title: '指标', dataIndex: 'indicator', key: 'indicator' },
          { title: '值', dataIndex: 'value', key: 'value' },
        ]}
        size="small"
        pagination={false}
      />
    </Card>
  )
}

function SupportResistanceCard({
  data,
}: {
  data: SupportResistanceResult | undefined
}) {
  if (!data) return null
  const supports = data.support_levels || []
  const resistances = data.resistance_levels || []

  return (
    <Card
      title="支撑阻力位"
      size="small"
      style={{
        background: 'var(--bg-secondary)',
        border: '1px solid var(--border)',
      }}
    >
      <Row gutter={16}>
        <Col span={12}>
          <div style={{ color: 'var(--success)', marginBottom: 8, fontWeight: 600 }}>
            支撑位
          </div>
          {supports.map((s, i) => (
            <div key={i} style={{ fontSize: 13, marginBottom: 4 }}>
              ${s.price.toLocaleString()} (触及 {s.touches} 次)
            </div>
          ))}
        </Col>
        <Col span={12}>
          <div style={{ color: 'var(--danger)', marginBottom: 8, fontWeight: 600 }}>
            阻力位
          </div>
          {resistances.map((r, i) => (
            <div key={i} style={{ fontSize: 13, marginBottom: 4 }}>
              ${r.price.toLocaleString()} (触及 {r.touches} 次)
            </div>
          ))}
        </Col>
      </Row>
    </Card>
  )
}

function PatternCard({
  data,
}: {
  data: PatternResult | undefined
}) {
  if (!data) return null

  return (
    <Card
      title="形态识别"
      size="small"
      style={{
        background: 'var(--bg-secondary)',
        border: '1px solid var(--border)',
      }}
    >
      <pre style={{ fontSize: 12, color: 'var(--text-secondary)', margin: 0 }}>
        {JSON.stringify(data.market_structure, null, 2)}
      </pre>
    </Card>
  )
}
