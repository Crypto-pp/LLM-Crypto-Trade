interface StatusDotProps {
  status: 'healthy' | 'warning' | 'error' | 'unknown'
  label?: string
}

const colorMap = {
  healthy: 'var(--success)',
  warning: 'var(--warning)',
  error: 'var(--danger)',
  unknown: 'var(--text-secondary)',
}

/** 状态圆点指示器 */
export default function StatusDot({ status, label }: StatusDotProps) {
  return (
    <span style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}>
      <span
        style={{
          width: 8,
          height: 8,
          borderRadius: '50%',
          backgroundColor: colorMap[status],
          display: 'inline-block',
        }}
      />
      {label && (
        <span style={{ color: 'var(--text-secondary)', fontSize: 13 }}>
          {label}
        </span>
      )}
    </span>
  )
}
