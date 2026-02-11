import { useState, useEffect } from 'react'
import {
  Form, Input, Select, Slider, InputNumber,
  Button, Collapse, Space, message, Tag,
} from 'antd'
import {
  ApiOutlined, CheckCircleOutlined, CloseCircleOutlined,
  LoadingOutlined,
} from '@ant-design/icons'
import { useAIConfig, useAIConfigUpdate, useAITestProvider } from '@/hooks/useAIAnalysis'
import type { AIConfigResponse } from '@/types/ai'

/** 提供商显示名称映射 */
const PROVIDER_NAMES: Record<string, string> = {
  deepseek: 'DeepSeek',
  gemini: 'Google Gemini',
  openai: 'OpenAI',
}

/** 有 base_url 字段的提供商 */
const PROVIDERS_WITH_BASE_URL = ['deepseek', 'openai']

/** AI配置面板（可内联到页面或嵌入Drawer） */
export default function AIConfigPanel() {
  const { data: config, isLoading } = useAIConfig()
  const updateMutation = useAIConfigUpdate()
  const testMutation = useAITestProvider()
  const [form] = Form.useForm()
  const [testResults, setTestResults] = useState<Record<string, { success: boolean; message: string }>>({})

  useEffect(() => {
    if (config) {
      fillForm(config)
    }
  }, [config])

  const fillForm = (cfg: AIConfigResponse) => {
    const values: Record<string, unknown> = {
      default_provider: cfg.default_provider,
      max_tokens: cfg.general.max_tokens,
      temperature: cfg.general.temperature,
      timeout: cfg.general.timeout,
    }
    for (const [pid, pCfg] of Object.entries(cfg.providers)) {
      values[`${pid}_api_key`] = pCfg.api_key
      values[`${pid}_model`] = pCfg.model
      if (pCfg.base_url !== undefined) {
        values[`${pid}_base_url`] = pCfg.base_url
      }
    }
    form.setFieldsValue(values)
  }

  const handleSave = async () => {
    const values = await form.validateFields()
    updateMutation.mutate(values, {
      onSuccess: () => message.success('配置已保存'),
      onError: () => message.error('保存失败'),
    })
  }

  const handleTest = (provider: string) => {
    testMutation.mutate(provider, {
      onSuccess: (result) => {
        setTestResults((prev) => ({ ...prev, [provider]: result }))
        if (result.success) {
          message.success(`${PROVIDER_NAMES[provider]}: ${result.message}`)
        } else {
          message.warning(`${PROVIDER_NAMES[provider]}: ${result.message}`)
        }
      },
      onError: () => {
        message.error(`测试 ${PROVIDER_NAMES[provider]} 连接失败`)
      },
    })
  }

  if (isLoading) {
    return (
      <div style={{ textAlign: 'center', padding: 40 }}>
        <LoadingOutlined style={{ fontSize: 24 }} />
      </div>
    )
  }

  return (
    <Form form={form} layout="vertical" size="small">
      <DefaultProviderSection />
      <Collapse
        defaultActiveKey={['deepseek']}
        ghost
        items={Object.keys(PROVIDER_NAMES).map((pid) => ({
          key: pid,
          label: <ProviderLabel pid={pid} config={config} testResult={testResults[pid]} />,
          children: (
            <ProviderFields
              pid={pid}
              onTest={() => handleTest(pid)}
              testing={testMutation.isPending}
            />
          ),
        }))}
      />
      <GeneralSection />
      <Button
        type="primary"
        onClick={handleSave}
        loading={updateMutation.isPending}
        block
        style={{ marginTop: 16 }}
      >
        保存配置
      </Button>
    </Form>
  )
}

/** 默认提供商选择区域 */
function DefaultProviderSection() {
  return (
    <Form.Item
      name="default_provider"
      label="默认提供商"
      style={{ marginBottom: 16 }}
    >
      <Select
        options={Object.entries(PROVIDER_NAMES).map(([id, name]) => ({
          value: id,
          label: name,
        }))}
      />
    </Form.Item>
  )
}

/** 提供商折叠面板标题 */
function ProviderLabel({
  pid,
  config,
  testResult,
}: {
  pid: string
  config?: AIConfigResponse
  testResult?: { success: boolean; message: string }
}) {
  const hasKey = config?.providers[pid]?.has_key ?? false
  return (
    <Space>
      <span>{PROVIDER_NAMES[pid]}</span>
      {hasKey ? (
        <Tag color="green" style={{ fontSize: 11 }}>已配置</Tag>
      ) : (
        <Tag style={{ fontSize: 11 }}>未配置</Tag>
      )}
      {testResult && (
        testResult.success
          ? <CheckCircleOutlined style={{ color: '#52c41a' }} />
          : <CloseCircleOutlined style={{ color: '#ff4d4f' }} />
      )}
    </Space>
  )
}

/** 提供商配置字段 */
function ProviderFields({
  pid,
  onTest,
  testing,
}: {
  pid: string
  onTest: () => void
  testing: boolean
}) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
      <Form.Item name={`${pid}_api_key`} label="API Key" style={{ marginBottom: 0 }}>
        <Input.Password placeholder="输入API Key" />
      </Form.Item>

      {PROVIDERS_WITH_BASE_URL.includes(pid) && (
        <Form.Item name={`${pid}_base_url`} label="Base URL" style={{ marginBottom: 0 }}>
          <Input placeholder="API地址" />
        </Form.Item>
      )}

      <Form.Item name={`${pid}_model`} label="模型" style={{ marginBottom: 0 }}>
        <Input placeholder="模型名称" />
      </Form.Item>

      <Button
        icon={<ApiOutlined />}
        onClick={onTest}
        loading={testing}
        size="small"
        style={{ alignSelf: 'flex-start', marginTop: 4 }}
      >
        测试连接
      </Button>
    </div>
  )
}

/** 通用参数配置区域 */
function GeneralSection() {
  return (
    <div style={{ marginTop: 16 }}>
      <div style={{ fontSize: 13, fontWeight: 500, marginBottom: 12 }}>
        通用参数
      </div>

      <Form.Item name="temperature" label="Temperature" style={{ marginBottom: 8 }}>
        <Slider min={0} max={1} step={0.1} />
      </Form.Item>

      <Form.Item name="max_tokens" label="Max Tokens" style={{ marginBottom: 8 }}>
        <InputNumber min={256} max={32768} step={256} style={{ width: '100%' }} />
      </Form.Item>

      <Form.Item name="timeout" label="超时(秒)" style={{ marginBottom: 0 }}>
        <InputNumber min={10} max={300} step={10} style={{ width: '100%' }} />
      </Form.Item>
    </div>
  )
}