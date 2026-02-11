import { useEffect } from 'react'
import {
  Form, Input, Button, Collapse, Tag, message,
} from 'antd'
import { LoadingOutlined } from '@ant-design/icons'
import { useExchangeConfig, useExchangeConfigUpdate } from '@/hooks/useSettings'
import type { ExchangeConfigResponse } from '@/types/settings'

/** 交易所元数据 */
const EXCHANGE_META: Record<string, {
  name: string
  fields: { key: string; label: string }[]
}> = {
  binance: {
    name: 'Binance',
    fields: [
      { key: 'binance_api_key', label: 'API Key' },
      { key: 'binance_api_secret', label: 'API Secret' },
    ],
  },
  okx: {
    name: 'OKX',
    fields: [
      { key: 'okx_api_key', label: 'API Key' },
      { key: 'okx_api_secret', label: 'API Secret' },
      { key: 'okx_passphrase', label: 'Passphrase' },
    ],
  },
  coinbase: {
    name: 'Coinbase',
    fields: [
      { key: 'coinbase_api_key', label: 'API Key' },
      { key: 'coinbase_api_secret', label: 'API Secret' },
    ],
  },
}

/** 交易所配置面板 */
export default function ExchangeConfigPanel() {
  const { data: config, isLoading } = useExchangeConfig()
  const updateMutation = useExchangeConfigUpdate()
  const [form] = Form.useForm()

  useEffect(() => {
    if (config) {
      fillForm(config)
    }
  }, [config])

  const fillForm = (cfg: ExchangeConfigResponse) => {
    const values: Record<string, string> = {}
    for (const [eid, eCfg] of Object.entries(cfg.exchanges)) {
      const meta = EXCHANGE_META[eid]
      if (!meta) continue
      for (const field of meta.fields) {
        const shortName = field.key.replace(`${eid}_`, '')
        values[field.key] = eCfg[shortName as keyof typeof eCfg] as string || ''
      }
    }
    form.setFieldsValue(values)
  }

  const handleSave = async () => {
    const values = await form.validateFields()
    updateMutation.mutate(values, {
      onSuccess: () => message.success('交易所配置已保存'),
      onError: () => message.error('保存失败'),
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
      <Collapse
        defaultActiveKey={['binance']}
        ghost
        items={Object.entries(EXCHANGE_META).map(([eid, meta]) => ({
          key: eid,
          label: (
            <ExchangeLabel
              name={meta.name}
              hasKey={config?.exchanges[eid]?.has_key ?? false}
            />
          ),
          children: (
            <ExchangeFields fields={meta.fields} />
          ),
        }))}
      />
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

/** 交易所折叠面板标题 */
function ExchangeLabel({ name, hasKey }: { name: string; hasKey: boolean }) {
  return (
    <span style={{ display: 'inline-flex', alignItems: 'center', gap: 8 }}>
      <span>{name}</span>
      {hasKey ? (
        <Tag color="green" style={{ fontSize: 11 }}>已配置</Tag>
      ) : (
        <Tag style={{ fontSize: 11 }}>未配置</Tag>
      )}
    </span>
  )
}

/** 交易所配置字段 */
function ExchangeFields({ fields }: { fields: { key: string; label: string }[] }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
      {fields.map((field) => (
        <Form.Item
          key={field.key}
          name={field.key}
          label={field.label}
          style={{ marginBottom: 0 }}
        >
          <Input.Password placeholder={`输入${field.label}`} />
        </Form.Item>
      ))}
    </div>
  )
}