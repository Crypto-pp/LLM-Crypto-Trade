import { useState } from 'react'
import { Card, Tabs, Form, InputNumber, Select, Button, Table, Tag, DatePicker, message } from 'antd'
import dayjs from 'dayjs'
import { useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { strategiesApi } from '@/api/strategies'
import { useBacktestList, useRunBacktest } from '@/hooks/useBacktest'
import type { BacktestTask } from '@/types/backtest'
import LoadingSkeleton from '@/components/ui/LoadingSkeleton'
import EmptyState from '@/components/ui/EmptyState'
import { formatTime } from '@/utils/format'

export default function Backtest() {
  const [activeTab, setActiveTab] = useState('create')

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
      <h2 style={{ margin: 0, fontSize: 18 }}>回测中心</h2>
      <Tabs
        activeKey={activeTab}
        onChange={setActiveTab}
        items={[
          { key: 'create', label: '创建回测', children: <CreateBacktest /> },
          { key: 'history', label: '历史记录', children: <BacktestHistory /> },
        ]}
      />
    </div>
  )
}

/** 创建回测表单 */
function CreateBacktest() {

  const SYMBOL_OPTIONS = [
    'BTC/USDT', 'ETH/USDT', 'BNB/USDT', 'SOL/USDT',
    'XRP/USDT', 'DOGE/USDT', 'ADA/USDT', 'AVAX/USDT',
    'DOT/USDT', 'MATIC/USDT', 'LINK/USDT', 'UNI/USDT',
  ]

  const [form] = Form.useForm()
  const navigate = useNavigate()
  const runBacktest = useRunBacktest()

  const { data: strategyData, isLoading: strategiesLoading } = useQuery({
    queryKey: ['strategies'],
    queryFn: () => strategiesApi.list(),
  })

  const strategies = strategyData?.strategies || []

  const handleSubmit = async (values: Record<string, unknown>) => {
    try {
      const startDate = dayjs.isDayjs(values.start_date)
        ? (values.start_date as dayjs.Dayjs).format('YYYY-MM-DD')
        : (values.start_date as string)
      const endDate = dayjs.isDayjs(values.end_date)
        ? (values.end_date as dayjs.Dayjs).format('YYYY-MM-DD')
        : (values.end_date as string)
      const res = await runBacktest.mutateAsync({
        strategy: values.strategy as string,
        symbol: values.symbol as string,
        start_date: startDate,
        end_date: endDate,
        initial_capital: values.initial_capital as number,
      })
      message.success(`回测已提交: ${res.backtest_id}`)
      navigate(`/backtest/${res.backtest_id}`)
    } catch {
      message.error('回测提交失败')
    }
  }

  return (
    <Card
      size="small"
      style={{
        background: 'var(--bg-secondary)',
        border: '1px solid var(--border)',
      }}
    >
      {strategiesLoading ? (
        <LoadingSkeleton rows={4} />
      ) : (
        <Form
          form={form}
          layout="vertical"
          onFinish={handleSubmit}
          initialValues={{ symbol: 'BTC/USDT', initial_capital: 10000 }}
          style={{ maxWidth: 480 }}
        >
          <Form.Item
            name="strategy"
            label="策略"
            rules={[{ required: true, message: '请选择策略' }]}
          >
            <Select placeholder="选择策略">
              {strategies.map((s) => (
                <Select.Option key={s.name} value={s.name}>
                  {s.name}
                </Select.Option>
              ))}
            </Select>
          </Form.Item>

          <Form.Item
            name="symbol"
            label="交易对"
            rules={[{ required: true, message: '请选择交易对' }]}
          >
            <Select
              showSearch
              placeholder="选择交易对"
              options={SYMBOL_OPTIONS.map((s) => ({ value: s, label: s }))}
            />
          </Form.Item>

          <Form.Item
            name="start_date"
            label="开始日期"
            rules={[{ required: true, message: '请选择开始日期' }]}
          >
            <DatePicker style={{ width: '100%' }} placeholder="选择开始日期" />
          </Form.Item>

          <Form.Item
            name="end_date"
            label="结束日期"
            rules={[{ required: true, message: '请选择结束日期' }]}
          >
            <DatePicker style={{ width: '100%' }} placeholder="选择结束日期" />
          </Form.Item>

          <Form.Item name="initial_capital" label="初始资金 (USDT)">
            <InputNumber
              min={100}
              step={1000}
              style={{ width: '100%' }}
            />
          </Form.Item>

          <Form.Item>
            <Button
              type="primary"
              htmlType="submit"
              loading={runBacktest.isPending}
            >
              开始回测
            </Button>
          </Form.Item>
        </Form>
      )}
    </Card>
  )
}

/** 回测历史列表 */
function BacktestHistory() {
  const navigate = useNavigate()
  const { data, isLoading } = useBacktestList(20)

  const items = data?.items || []

  const statusColor: Record<string, string> = {
    completed: 'green',
    running: 'blue',
    failed: 'red',
    pending: 'default',
  }

  const columns = [
    {
      title: '策略',
      dataIndex: ['request', 'strategy'],
      key: 'strategy',
    },
    {
      title: '交易对',
      dataIndex: ['request', 'symbol'],
      key: 'symbol',
    },
    {
      title: '时间范围',
      key: 'range',
      render: (_: unknown, r: BacktestTask) => {
        return `${r.request.start_date} ~ ${r.request.end_date}`
      },
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (v: string) => (
        <Tag color={statusColor[v] || 'default'}>{v}</Tag>
      ),
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (v: string) => formatTime(v),
    },
    {
      title: '操作',
      key: 'action',
      render: (_: unknown, r: BacktestTask, index: number) => (
        <Button
          type="link"
          size="small"
          disabled={r.status !== 'completed'}
          onClick={() => navigate(`/backtest/${index}`)}
        >
          查看报告
        </Button>
      ),
    },
  ]

  if (isLoading) return <LoadingSkeleton rows={4} />

  if (items.length === 0) {
    return <EmptyState description="暂无回测记录" />
  }

  return (
    <Table
      dataSource={items}
      columns={columns}
      rowKey={(_, i) => String(i)}
      size="small"
      pagination={{ pageSize: 10 }}
    />
  )
}
