import { Card, Row, Col, Tabs } from 'antd'
import { useHealth } from '@/hooks/useHealth'
import StatusDot from '@/components/ui/StatusDot'
import LoadingSkeleton from '@/components/ui/LoadingSkeleton'
import { formatUptime } from '@/utils/format'
import AIConfigPanel from '@/components/business/AIConfigPanel'
import ExchangeConfigPanel from '@/components/business/ExchangeConfigPanel'
import SignalMonitorPanel from '@/components/business/SignalMonitorPanel'
import NotificationPanel from '@/components/business/NotificationPanel'

export default function System() {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
      <h2 style={{ margin: 0, fontSize: 18 }}>系统设置</h2>
      <Tabs
        defaultActiveKey="monitor"
        items={[
          { key: 'monitor', label: '系统监控', children: <MonitorTab /> },
          { key: 'ai', label: 'AI模型', children: <AIConfigPanel /> },
          { key: 'exchange', label: '交易所配置', children: <ExchangeConfigPanel /> },
          { key: 'signals', label: '信号监控', children: <SignalMonitorPanel /> },
          { key: 'notifications', label: '消息通知', children: <NotificationPanel /> },
        ]}
      />
    </div>
  )
}

/** 系统监控标签页 */
function MonitorTab() {
  const { data: health, isLoading } = useHealth()

  if (isLoading) return <LoadingSkeleton rows={8} />

  const status = health?.status === 'healthy' ? 'healthy' : 'error'
  const services = (health?.services || {}) as Record<string, string>
  const uptime = health?.uptime as number | undefined

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
      <OverviewCard status={status} uptime={uptime} />
      <ServiceStatusCard services={services} />
      <SystemInfoCard health={health} />
    </div>
  )
}

function OverviewCard({
  status,
  uptime,
}: {
  status: 'healthy' | 'error'
  uptime: number | undefined
}) {
  return (
    <Card
      title="系统概览"
      size="small"
      style={{
        background: 'var(--bg-secondary)',
        border: '1px solid var(--border)',
      }}
    >
      <Row gutter={24}>
        <Col span={8}>
          <div style={{ color: 'var(--text-secondary)', fontSize: 12, marginBottom: 4 }}>
            系统状态
          </div>
          <StatusDot
            status={status}
            label={status === 'healthy' ? '正常运行' : '异常'}
          />
        </Col>
        <Col span={8}>
          <div style={{ color: 'var(--text-secondary)', fontSize: 12, marginBottom: 4 }}>
            运行时间
          </div>
          <span style={{ fontSize: 16, fontWeight: 600 }}>
            {uptime ? formatUptime(uptime) : '--'}
          </span>
        </Col>
        <Col span={8}>
          <div style={{ color: 'var(--text-secondary)', fontSize: 12, marginBottom: 4 }}>
            API 版本
          </div>
          <span style={{ fontSize: 16, fontWeight: 600 }}>v1</span>
        </Col>
      </Row>
    </Card>
  )
}

function ServiceStatusCard({
  services,
}: {
  services: Record<string, string>
}) {
  const entries = Object.entries(services)

  return (
    <Card
      title="服务状态"
      size="small"
      style={{
        background: 'var(--bg-secondary)',
        border: '1px solid var(--border)',
      }}
    >
      {entries.length === 0 ? (
        <div style={{ color: 'var(--text-secondary)', fontSize: 13 }}>
          暂无服务信息
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          {entries.map(([name, st]) => (
            <div
              key={name}
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                padding: '6px 0',
                borderBottom: '1px solid var(--border)',
              }}
            >
              <span style={{ fontSize: 13 }}>{name}</span>
              <StatusDot
                status={st === 'healthy' ? 'healthy' : 'error'}
                label={st === 'healthy' ? '正常' : st}
              />
            </div>
          ))}
        </div>
      )}
    </Card>
  )
}

function SystemInfoCard({
  health,
}: {
  health: Record<string, unknown> | undefined
}) {
  if (!health) return null

  const infoKeys = Object.keys(health).filter(
    (k) => !['status', 'services', 'uptime'].includes(k),
  )

  if (infoKeys.length === 0) return null

  return (
    <Card
      title="其他信息"
      size="small"
      style={{
        background: 'var(--bg-secondary)',
        border: '1px solid var(--border)',
      }}
    >
      <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
        {infoKeys.map((key) => (
          <div
            key={key}
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              fontSize: 13,
            }}
          >
            <span style={{ color: 'var(--text-secondary)' }}>{key}</span>
            <span>{String(health[key])}</span>
          </div>
        ))}
      </div>
    </Card>
  )
}