import { Card, Tag, Space } from 'antd'
import { ClockCircleOutlined, RobotOutlined } from '@ant-design/icons'
import { formatTime } from '@/utils/format'
import type { AIAnalysisResult } from '@/types/ai'

/** AI分析结果卡片 */
export default function AIResultCard({ result }: { result: AIAnalysisResult }) {
  return (
    <Card
      size="small"
      style={{
        background: 'var(--bg-secondary)',
        border: '1px solid var(--border)',
      }}
      title={
        <Space>
          <RobotOutlined />
          <span>{result.symbol} - AI分析结果</span>
        </Space>
      }
      extra={
        <Space size={4}>
          <Tag color="blue">{result.provider}</Tag>
          <Tag>{result.model}</Tag>
        </Space>
      }
    >
      <div style={{ marginBottom: 8 }}>
        <Space size={12} style={{ fontSize: 12, color: 'var(--text-secondary)' }}>
          <span>
            <ClockCircleOutlined style={{ marginRight: 4 }} />
            {formatTime(result.timestamp)}
          </span>
          <span>周期: {result.interval}</span>
        </Space>
      </div>

      <div
        style={{
          whiteSpace: 'pre-wrap',
          lineHeight: 1.8,
          fontSize: 14,
        }}
      >
        {result.analysis}
      </div>
    </Card>
  )
}
