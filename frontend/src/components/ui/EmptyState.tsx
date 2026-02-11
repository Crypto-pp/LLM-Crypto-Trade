import { Empty } from 'antd'

interface EmptyStateProps {
  description?: string
}

/** 空数据占位组件 */
export default function EmptyState({
  description = '暂无数据',
}: EmptyStateProps) {
  return (
    <div
      style={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        padding: 48,
      }}
    >
      <Empty
        description={
          <span style={{ color: 'var(--text-secondary)' }}>
            {description}
          </span>
        }
      />
    </div>
  )
}
