import { useState } from 'react'
import {
  Card, Table, Button, Modal, Form, Input, Select, Switch, Space,
  message, Popconfirm, Tag, Divider,
} from 'antd'
import {
  PlusOutlined, EditOutlined, DeleteOutlined,
  SendOutlined, LoadingOutlined,
} from '@ant-design/icons'
import {
  useNotificationConfig,
  useUpdateNotificationSettings,
  useAddNotificationChannel,
  useUpdateNotificationChannel,
  useDeleteNotificationChannel,
  useTestNotificationChannel,
} from '@/hooks/useSettings'
import type {
  NotificationChannel,
  NotificationChannelCreate,
} from '@/types/settings'

/** 渠道类型选项 */
const CHANNEL_TYPE_OPTIONS = [
  { value: 'telegram', label: 'Telegram' },
  { value: 'feishu', label: '飞书' },
]

/** 渠道类型标签颜色 */
const TYPE_COLOR: Record<string, string> = {
  telegram: 'blue',
  feishu: 'cyan',
}

export default function NotificationPanel() {
  const { data, isLoading } = useNotificationConfig()
  const updateSettings = useUpdateNotificationSettings()
  const addChannel = useAddNotificationChannel()
  const updateChannel = useUpdateNotificationChannel()
  const deleteChannel = useDeleteNotificationChannel()
  const testChannel = useTestNotificationChannel()

  const [modalOpen, setModalOpen] = useState(false)
  const [editing, setEditing] = useState<NotificationChannel | null>(null)
  const [testingId, setTestingId] = useState<string | null>(null)
  const [channelType, setChannelType] = useState<string>('telegram')
  const [form] = Form.useForm()

  const channels = data?.channels ?? []
  const settings = data?.settings ?? {
    notify_on_buy: true,
    notify_on_sell: true,
    notify_on_hold: false,
  }

  // ========== 事件处理 ==========

  const openAddModal = () => {
    setEditing(null)
    setChannelType('telegram')
    form.resetFields()
    form.setFieldsValue({ type: 'telegram', enabled: true })
    setModalOpen(true)
  }

  const openEditModal = (ch: NotificationChannel) => {
    setEditing(ch)
    setChannelType(ch.type)
    form.setFieldsValue({
      type: ch.type,
      name: ch.name,
      enabled: ch.enabled,
      ...ch.config,
    })
    setModalOpen(true)
  }

  const handleSubmit = async () => {
    const values = await form.validateFields()
    const { type, name, enabled, ...configFields } = values

    if (editing) {
      updateChannel.mutate(
        { id: editing.id, data: { name, enabled, config: configFields } },
        {
          onSuccess: () => { message.success('渠道已更新'); setModalOpen(false) },
          onError: () => message.error('更新失败'),
        },
      )
    } else {
      const createData: NotificationChannelCreate = {
        type, name, enabled: enabled ?? true, config: configFields,
      }
      addChannel.mutate(createData, {
        onSuccess: () => { message.success('渠道已添加'); setModalOpen(false) },
        onError: () => message.error('添加失败'),
      })
    }
  }

  const handleDelete = (id: string) => {
    deleteChannel.mutate(id, {
      onSuccess: () => message.success('渠道已删除'),
      onError: () => message.error('删除失败'),
    })
  }

  const handleTest = (id: string) => {
    setTestingId(id)
    testChannel.mutate(id, {
      onSuccess: () => { message.success('测试消息发送成功'); setTestingId(null) },
      onError: () => { message.error('测试发送失败，请检查配置'); setTestingId(null) },
    })
  }

  const handleToggle = (ch: NotificationChannel, enabled: boolean) => {
    updateChannel.mutate(
      { id: ch.id, data: { enabled } },
      {
        onSuccess: () => message.success(enabled ? '已启用' : '已禁用'),
        onError: () => message.error('操作失败'),
      },
    )
  }

  const handleSettingChange = (key: string, value: boolean) => {
    updateSettings.mutate({ [key]: value })
  }

  // ========== 表格列定义 ==========

  const columns = [
    {
      title: '名称',
      dataIndex: 'name',
      key: 'name',
      width: 150,
    },
    {
      title: '类型',
      dataIndex: 'type',
      key: 'type',
      width: 100,
      render: (v: string) => (
        <Tag color={TYPE_COLOR[v] || 'default'}>
          {v === 'telegram' ? 'Telegram' : '飞书'}
        </Tag>
      ),
    },
    {
      title: '状态',
      dataIndex: 'enabled',
      key: 'enabled',
      width: 80,
      render: (enabled: boolean, record: NotificationChannel) => (
        <Switch
          size="small"
          checked={enabled}
          onChange={(v) => handleToggle(record, v)}
        />
      ),
    },
    {
      title: '操作',
      key: 'actions',
      width: 140,
      render: (_: unknown, record: NotificationChannel) => (
        <Space size={4}>
          <Button
            type="text"
            size="small"
            icon={<SendOutlined />}
            onClick={() => handleTest(record.id)}
            loading={testingId === record.id}
            title="发送测试"
          />
          <Button
            type="text"
            size="small"
            icon={<EditOutlined />}
            onClick={() => openEditModal(record)}
            title="编辑"
          />
          <Popconfirm
            title="确定删除此通知渠道？"
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

  // ========== 渲染 ==========

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
      {/* 全局设置 */}
      <Card
        title="通知触发条件"
        size="small"
        style={{ background: 'var(--bg-secondary)', border: '1px solid var(--border)' }}
      >
        <div style={{ display: 'flex', gap: 24, flexWrap: 'wrap' }}>
          <label style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 13 }}>
            <Switch
              size="small"
              checked={settings.notify_on_buy}
              onChange={(v) => handleSettingChange('notify_on_buy', v)}
            />
            买入信号
          </label>
          <label style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 13 }}>
            <Switch
              size="small"
              checked={settings.notify_on_sell}
              onChange={(v) => handleSettingChange('notify_on_sell', v)}
            />
            卖出信号
          </label>
          <label style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 13 }}>
            <Switch
              size="small"
              checked={settings.notify_on_hold}
              onChange={(v) => handleSettingChange('notify_on_hold', v)}
            />
            持有信号
          </label>
        </div>
      </Card>

      {/* 渠道列表 */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <span style={{ fontSize: 14, color: 'var(--text-secondary)' }}>
          共 {channels.length} 个通知渠道
        </span>
        <Button type="primary" size="small" icon={<PlusOutlined />} onClick={openAddModal}>
          添加渠道
        </Button>
      </div>

      <Table
        dataSource={channels}
        columns={columns}
        rowKey="id"
        size="small"
        pagination={false}
        locale={{ emptyText: '暂无通知渠道，点击上方按钮添加' }}
      />

      {/* 添加/编辑弹窗 */}
      <Modal
        title={editing ? '编辑通知渠道' : '添加通知渠道'}
        open={modalOpen}
        onOk={handleSubmit}
        onCancel={() => setModalOpen(false)}
        confirmLoading={addChannel.isPending || updateChannel.isPending}
        okText="确定"
        cancelText="取消"
        destroyOnClose
      >
        <Form form={form} layout="vertical" style={{ marginTop: 16 }}>
          <Form.Item
            name="type"
            label="渠道类型"
            rules={[{ required: true, message: '请选择渠道类型' }]}
          >
            <Select
              placeholder="选择渠道类型"
              options={CHANNEL_TYPE_OPTIONS}
              disabled={!!editing}
              onChange={(v) => setChannelType(v)}
            />
          </Form.Item>
          <Form.Item
            name="name"
            label="渠道名称"
            rules={[{ required: true, message: '请输入渠道名称' }]}
          >
            <Input placeholder="例如：交易信号群" />
          </Form.Item>

          <Divider style={{ margin: '12px 0' }} />

          {/* Telegram 配置字段 */}
          {channelType === 'telegram' && (
            <>
              <Form.Item
                name="bot_token"
                label="Bot Token"
                rules={[{ required: !editing, message: '请输入 Bot Token' }]}
              >
                <Input.Password placeholder="从 @BotFather 获取" />
              </Form.Item>
              <Form.Item
                name="chat_id"
                label="Chat ID"
                rules={[{ required: !editing, message: '请输入 Chat ID' }]}
              >
                <Input placeholder="群组或用户的 Chat ID" />
              </Form.Item>
            </>
          )}

          {/* 飞书配置字段 */}
          {channelType === 'feishu' && (
            <>
              <Form.Item
                name="webhook_url"
                label="Webhook URL"
                rules={[{ required: !editing, message: '请输入 Webhook URL' }]}
              >
                <Input placeholder="https://open.feishu.cn/open-apis/bot/v2/hook/xxx" />
              </Form.Item>
              <Form.Item name="secret" label="签名密钥（可选）">
                <Input.Password placeholder="安全设置中的签名校验密钥" />
              </Form.Item>
            </>
          )}

          <Form.Item name="enabled" label="启用" valuePropName="checked">
            <Switch />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}
