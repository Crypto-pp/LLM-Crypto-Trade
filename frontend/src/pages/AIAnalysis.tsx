import { useState } from 'react'
import { Card, Select, Button, Alert, Row, Col } from 'antd'
import {
  RobotOutlined,
  ThunderboltOutlined,
  SendOutlined,
  SettingOutlined,
} from '@ant-design/icons'
import { useAIProviders, useAIPrompts, useAIAnalyze } from '@/hooks/useAIAnalysis'
import { useSymbols } from '@/hooks/useSymbols'
import { useMarketStore } from '@/stores/market'
import AIResultCard from '@/components/business/AIResultCard'
import AIConfigDrawer from '@/components/business/AIConfigDrawer'
import LoadingSkeleton from '@/components/ui/LoadingSkeleton'
import type { AIAnalysisResult } from '@/types/ai'

const intervals = [
  { value: '5m', label: '5分钟' },
  { value: '15m', label: '15分钟' },
  { value: '1h', label: '1小时' },
  { value: '4h', label: '4小时' },
  { value: '1d', label: '1天' },
]

export default function AIAnalysis() {
  const { data: providerData, isLoading: providersLoading } = useAIProviders()
  const { data: promptData, isLoading: promptsLoading } = useAIPrompts()
  const analyzeMutation = useAIAnalyze()
  const exchange = useMarketStore((s) => s.exchange)
  const { data: symbolData, isLoading: symbolsLoading } = useSymbols(exchange)

  const [symbol, setSymbol] = useState('BTC/USDT')
  const [interval, setInterval] = useState('1h')
  const [promptId, setPromptId] = useState('comprehensive')
  const [provider, setProvider] = useState<string | undefined>(undefined)
  const [result, setResult] = useState<AIAnalysisResult | null>(null)
  const [configOpen, setConfigOpen] = useState(false)

  const providers = providerData?.providers ?? []
  const prompts = promptData?.prompts ?? []

  const handleAnalyze = () => {
    analyzeMutation.mutate(
      { symbol, interval, prompt_id: promptId, provider },
      { onSuccess: (data) => setResult(data) },
    )
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <h2 style={{ margin: 0, fontSize: 18 }}>
          <RobotOutlined style={{ marginRight: 8 }} />
          AI 辅助分析
        </h2>
        <Button
          icon={<SettingOutlined />}
          onClick={() => setConfigOpen(true)}
          size="small"
        >
          配置
        </Button>
      </div>

      {providers.length === 0 && !providersLoading && (
        <Alert
          type="warning"
          showIcon
          message="未配置AI模型API Key，请点击右上角「配置」按钮设置"
          style={{ background: 'var(--bg-secondary)', border: '1px solid var(--border)' }}
        />
      )}

      <Row gutter={16}>
        <Col xs={24} lg={7}>
          <ControlPanel
            symbol={symbol}
            interval={interval}
            promptId={promptId}
            provider={provider}
            providers={providers}
            prompts={prompts}
            symbols={symbolData?.symbols ?? []}
            symbolsLoading={symbolsLoading}
            providersLoading={providersLoading}
            promptsLoading={promptsLoading}
            analyzing={analyzeMutation.isPending}
            onSymbolChange={setSymbol}
            onIntervalChange={setInterval}
            onPromptChange={setPromptId}
            onProviderChange={setProvider}
            onAnalyze={handleAnalyze}
          />
        </Col>
        <Col xs={24} lg={17}>
          <ResultPanel
            result={result}
            analyzing={analyzeMutation.isPending}
            error={analyzeMutation.error}
          />
        </Col>
      </Row>

      <AIConfigDrawer open={configOpen} onClose={() => setConfigOpen(false)} />
    </div>
  )
}

/** 左侧控制面板 */
function ControlPanel({
  symbol,
  interval,
  promptId,
  provider,
  providers,
  prompts,
  symbols,
  symbolsLoading,
  providersLoading,
  promptsLoading,
  analyzing,
  onSymbolChange,
  onIntervalChange,
  onPromptChange,
  onProviderChange,
  onAnalyze,
}: {
  symbol: string
  interval: string
  promptId: string
  provider: string | undefined
  providers: { id: string; name: string; model: string }[]
  prompts: { id: string; name: string; description: string; category: string }[]
  symbols: string[]
  symbolsLoading: boolean
  providersLoading: boolean
  promptsLoading: boolean
  analyzing: boolean
  onSymbolChange: (v: string) => void
  onIntervalChange: (v: string) => void
  onPromptChange: (v: string) => void
  onProviderChange: (v: string | undefined) => void
  onAnalyze: () => void
}) {
  return (
    <Card
      size="small"
      title={<><ThunderboltOutlined /> 分析配置</>}
      style={{
        background: 'var(--bg-secondary)',
        border: '1px solid var(--border)',
      }}
    >
      <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
        {/* 交易对 */}
        <div>
          <div style={{ fontSize: 12, color: 'var(--text-secondary)', marginBottom: 4 }}>
            交易对
          </div>
          <Select
            value={symbol}
            onChange={onSymbolChange}
            style={{ width: '100%' }}
            showSearch
            loading={symbolsLoading}
            filterOption={(input, option) =>
              (option?.label ?? '').toLowerCase().includes(input.toLowerCase())
            }
            options={symbols.map((s) => ({ value: s, label: s }))}
          />
        </div>

        {/* 时间周期 */}
        <div>
          <div style={{ fontSize: 12, color: 'var(--text-secondary)', marginBottom: 4 }}>
            时间周期
          </div>
          <Select
            value={interval}
            onChange={onIntervalChange}
            style={{ width: '100%' }}
            options={intervals}
          />
        </div>

        {/* AI模型 */}
        <div>
          <div style={{ fontSize: 12, color: 'var(--text-secondary)', marginBottom: 4 }}>
            AI模型
          </div>
          <Select
            value={provider}
            onChange={onProviderChange}
            style={{ width: '100%' }}
            placeholder="使用默认模型"
            allowClear
            loading={providersLoading}
            options={providers.map((p) => ({
              value: p.id,
              label: `${p.name} (${p.model})`,
            }))}
          />
        </div>

        {/* 分析类型 */}
        <div>
          <div style={{ fontSize: 12, color: 'var(--text-secondary)', marginBottom: 4 }}>
            分析类型
          </div>
          <Select
            value={promptId}
            onChange={onPromptChange}
            style={{ width: '100%' }}
            loading={promptsLoading}
            options={prompts.map((p) => ({
              value: p.id,
              label: p.name,
            }))}
          />
          {prompts.find((p) => p.id === promptId)?.description && (
            <div style={{ fontSize: 11, color: 'var(--text-secondary)', marginTop: 4 }}>
              {prompts.find((p) => p.id === promptId)?.description}
            </div>
          )}
        </div>

        {/* 开始分析按钮 */}
        <Button
          type="primary"
          icon={<SendOutlined />}
          onClick={onAnalyze}
          loading={analyzing}
          disabled={providers.length === 0 && !providersLoading}
          block
          style={{ marginTop: 4 }}
        >
          {analyzing ? '分析中...' : '开始分析'}
        </Button>
      </div>
    </Card>
  )
}

/** 右侧结果面板 */
function ResultPanel({
  result,
  analyzing,
  error,
}: {
  result: AIAnalysisResult | null
  analyzing: boolean
  error: Error | null
}) {
  if (analyzing) {
    return (
      <Card
        size="small"
        style={{
          background: 'var(--bg-secondary)',
          border: '1px solid var(--border)',
        }}
      >
        <LoadingSkeleton rows={8} />
      </Card>
    )
  }

  if (error) {
    return (
      <Alert
        type="error"
        showIcon
        message="分析失败"
        description={String(error)}
        style={{
          background: 'var(--bg-secondary)',
          border: '1px solid var(--border)',
        }}
      />
    )
  }

  if (!result) {
    return (
      <Card
        size="small"
        style={{
          background: 'var(--bg-secondary)',
          border: '1px solid var(--border)',
          minHeight: 300,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
        }}
      >
        <div style={{ textAlign: 'center', color: 'var(--text-secondary)' }}>
          <RobotOutlined style={{ fontSize: 48, marginBottom: 12 }} />
          <div>选择交易对和分析类型，点击"开始分析"</div>
        </div>
      </Card>
    )
  }

  return <AIResultCard result={result} />
}