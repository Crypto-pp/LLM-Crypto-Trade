/** 单个交易所配置 */
export interface ExchangeConfig {
  name: string
  api_key: string
  api_secret: string
  passphrase?: string
  has_key: boolean
}

/** 交易所配置响应 */
export interface ExchangeConfigResponse {
  exchanges: Record<string, ExchangeConfig>
}

/** 交易所配置更新请求 */
export interface ExchangeConfigUpdate {
  [key: string]: string | undefined
}

/** 信号监控任务 */
export interface SignalMonitorTask {
  id: string
  symbol: string
  strategy: string
  interval: string
  enabled: boolean
  created_at: string
  last_run?: string | null
  last_signal?: string | null
}

/** 创建信号监控任务请求 */
export interface SignalMonitorCreate {
  symbol: string
  strategy: string
  interval: string
  enabled?: boolean
}

/** 更新信号监控任务请求 */
export interface SignalMonitorUpdate {
  symbol?: string
  strategy?: string
  interval?: string
  enabled?: boolean
}

/** 通知渠道配置 */
export interface NotificationChannel {
  id: string
  type: 'telegram' | 'feishu'
  name: string
  enabled: boolean
  config: Record<string, string>
}

/** 通知全局设置 */
export interface NotificationSettings {
  notify_on_buy: boolean
  notify_on_sell: boolean
  notify_on_hold: boolean
}

/** 通知配置响应 */
export interface NotificationConfigResponse {
  channels: NotificationChannel[]
  settings: NotificationSettings
}

/** 创建通知渠道请求 */
export interface NotificationChannelCreate {
  type: 'telegram' | 'feishu'
  name: string
  enabled?: boolean
  config: Record<string, string>
}

/** 更新通知渠道请求 */
export interface NotificationChannelUpdate {
  name?: string
  enabled?: boolean
  config?: Record<string, string>
}
