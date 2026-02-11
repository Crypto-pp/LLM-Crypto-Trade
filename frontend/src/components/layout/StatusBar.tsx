import StatusDot from '@/components/ui/StatusDot'
import { useWebSocketStore } from '@/stores/websocket'

/** 底部状态栏 */
export default function StatusBar() {
  const connected = useWebSocketStore((s) => s.connected)
  const latency = useWebSocketStore((s) => s.latency)

  return (
    <div
      style={{
        height: 28,
        display: 'flex',
        alignItems: 'center',
        gap: 24,
        padding: '0 16px',
        background: 'var(--bg-secondary)',
        borderTop: '1px solid var(--border)',
        fontSize: 12,
        color: 'var(--text-secondary)',
      }}
    >
      <StatusDot
        status={connected ? 'healthy' : 'error'}
        label={connected ? 'WS 已连接' : 'WS 断开'}
      />
      <span>延迟: {latency}ms</span>
      <span style={{ marginLeft: 'auto' }}>v1.0.0</span>
    </div>
  )
}
