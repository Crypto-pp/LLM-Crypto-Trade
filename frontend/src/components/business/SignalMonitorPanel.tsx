import { useState } from 'react'
import {
  Table, Button, Modal, Form, Select, Switch, Tag, Space,
  message, Popconfirm,
} from 'antd'
import {
  PlusOutlined, PlayCircleOutlined, EditOutlined,
  DeleteOutlined, LoadingOutlined,
} from '@ant-design/icons'
import {
  useSignalMonitors, useAddSignalMonitor, useUpdateSignalMonitor,
  useDeleteSignalMonitor, useRunSignalMonitor,
} from '@/hooks/useSettings'
import type { SignalMonitorTask, SignalMonitorCreate } from '@/types/settings'

/** 策略选项 */
const STRATEGY_OPTIONS = [
  { value: '趋势跟踪', label: '趋势跟踪' },
  { value: '均值回归', label: '均值回归' },
  { value: '动量策略', label: '动量策略' },
  { value: 'AI分析', label: 'AI分析' },
]

/** 周期选项 */
const INTERVAL_OPTIONS = [
  { value: '1m', label: '1分钟' },
  { value: '5m', label: '5分钟' },
  { value: '15m', label: '15分钟' },
  { value: '1h', label: '1小时' },
  { value: '4h', label: '4小时' },
  { value: '1d', label: '1天' },
]

/** 常用交易对 */
const SYMBOL_OPTIONS = [
  'BTC/USDT', 'ETH/USDT', 'BNB/USDT', 'SOL/USDT',
  'XRP/USDT', 'DOGE/USDT', 'ADA/USDT', 'AVAX/USDT',
  'DOT/USDT', 'MATIC/USDT', 'LINK/USDT', 'UNI/USDT',
]

/** 策略名称映射（key 已为中文，保留映射以兼容渲染逻辑） */
const STRATEGY_LABEL: Record<string, string> = {
  趋势跟踪: '趋势跟踪',
  均值回归: '均值回归',
  动量策略: '动量策略',
  AI分析: 'AI分析',
}

/** 信号类型颜色映射 */
const SIGNAL_COLOR: Record<string, string> = {
  BUY: 'green',
  SELL: 'red',
  HOLD: 'default',
}

export default function SignalMonitorPanel() {
  const { data, isLoading } = useSignalMonitors()
  const addMutation = useAddSignalMonitor()
  const updateMutation = useUpdateSignalMonitor()
  const deleteMutation = useDeleteSignalMonitor()
  const runMutation = useRunSignalMonitor()

  const [modalOpen, setModalOpen] = useState(false)
  const [editingTask, setEditingTask] = useState<SignalMonitorTask | null>(null)
  const [runningTaskId, setRunningTaskId] = useState<string | null>(null)
  const [form] = Form.useForm()

  const tasks = data?.tasks ?? []

  const openAddModal = () => {
    setEditingTask(null)
    form.resetFields()
    form.setFieldsValue({ enabled: true })
    setModalOpen(true)
  }

  const openEditModal = (task: SignalMonitorTask) => {
    setEditingTask(task)
    form.setFieldsValue({
      symbol: task.symbol,
      strategy: task.strategy,
      interval: task.interval,
      enabled: task.enabled,
    })
    setModalOpen(true)
  }

  const handleSubmit = async () => {
    const values = await form.validateFields()
    if (editingTask) {
      updateMutation.mutate(
        { id: editingTask.id, data: values },
        {
          onSuccess: () => {
            message.success('监控任务已更新')
            setModalOpen(false)
          },
          onError: () => message.error('更新失败'),
        },
      )
    } else {
      const createData: SignalMonitorCreate = {
        symbol: values.symbol,
        strategy: values.strategy,
        interval: values.interval,
        enabled: values.enabled ?? true,
      }
      addMutation.mutate(createData, {
        onSuccess: () => {
          message.success('监控任务已添加')
          setModalOpen(false)
        },
        onError: () => message.error('添加失败'),
      })
    }
  }

  const handleDelete = (id: string) => {
    deleteMutation.mutate(id, {
      onSuccess: () => message.success('监控任务已删除'),
      onError: () => message.error('删除失败'),
    })
  }

  const handleRun = (id: string) => {
    setRunningTaskId(id)
    runMutation.mutate(id, {
      onSuccess: () => {
        message.success('任务执行完成')
        setRunningTaskId(null)
      },
      onError: () => {
        message.error('执行失败')
        setRunningTaskId(null)
      },
    })
  }

  const handleToggle = (task: SignalMonitorTask, enabled: boolean) => {
    updateMutation.mutate(
      { id: task.id, data: { enabled } },
      {
        onSuccess: () => message.success(enabled ? '已启用' : '已禁用'),
        onError: () => message.error('操作失败'),
      },
    )
  }

  const columns = [
    {
      title: '交易对',
      dataIndex: 'symbol',
      key: 'symbol',
      width: 120,
    },
    {
      title: '策略',
      dataIndex: 'strategy',
      key: 'strategy',
      width: 100,
      render: (v: string) => STRATEGY_LABEL[v] || v,
    },
    {
      title: '周期',
      dataIndex: 'interval',
      key: 'interval',
      width: 80,
    },
    {
      title: '状态',
      dataIndex: 'enabled',
      key: 'enabled',
      width: 80,
      render: (enabled: boolean, record: SignalMonitorTask) => (
        <Switch
          size="small"
          checked={enabled}
          onChange={(v) => handleToggle(record, v)}
        />
      ),
    },
    {
      title: '最新信号',
      dataIndex: 'last_signal',
      key: 'last_signal',
      width: 90,
      render: (v: string | null) =>
        v ? <Tag color={SIGNAL_COLOR[v] || 'default'}>{v}</Tag> : '--',
    },
    {
      title: '操作',
      key: 'actions',
      width: 140,
      render: (_: unknown, record: SignalMonitorTask) => (
        <Space size={4}>
          <Button
            type="text"
            size="small"
            icon={<PlayCircleOutlined />}
            onClick={() => handleRun(record.id)}
            loading={runningTaskId === record.id}
            title="立即执行"
          />
          <Button
            type="text"
            size="small"
            icon={<EditOutlined />}
            onClick={() => openEditModal(record)}
            title="编辑"
          />
          <Popconfirm
            title="确定删除此监控任务？"
            onConfirm={() => handleDelete(record.id)}
            okText="确定"
            cancelText="取消"
          >
            <Button
              type="text"
              size="small"
              danger
              icon={<DeleteOutlined />}
              title="删除"
            />
          </Popconfirm>
        </Space>
      ),
    },
  ]

  if (isLoading) {
    return (
      <div style={{ textAlign: 'center', padding: 40 }}>
        <LoadingOutlined style={{ fontSize: 24 }} />
      </div>
    )
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <span style={{ fontSize: 14, color: 'var(--text-secondary)' }}>
          共 {tasks.length} 个监控任务
        </span>
        <Button
          type="primary"
          size="small"
          icon={<PlusOutlined />}
          onClick={openAddModal}
        >
          添加监控
        </Button>
      </div>

      <Table
        dataSource={tasks}
        columns={columns}
        rowKey="id"
        size="small"
        pagination={false}
        locale={{ emptyText: '暂无监控任务，点击上方按钮添加' }}
      />

      <Modal
        title={editingTask ? '编辑信号监控' : '添加信号监控'}
        open={modalOpen}
        onOk={handleSubmit}
        onCancel={() => setModalOpen(false)}
        confirmLoading={addMutation.isPending || updateMutation.isPending}
        okText="确定"
        cancelText="取消"
        destroyOnClose
      >
        <Form form={form} layout="vertical" style={{ marginTop: 16 }}>
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
            name="strategy"
            label="策略"
            rules={[{ required: true, message: '请选择策略' }]}
          >
            <Select placeholder="选择策略" options={STRATEGY_OPTIONS} />
          </Form.Item>
          <Form.Item
            name="interval"
            label="周期"
            rules={[{ required: true, message: '请选择周期' }]}
          >
            <Select placeholder="选择周期" options={INTERVAL_OPTIONS} />
          </Form.Item>
          <Form.Item name="enabled" label="启用" valuePropName="checked">
            <Switch />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}
