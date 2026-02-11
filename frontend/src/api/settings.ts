import client from './client'
import type {
  ExchangeConfigResponse,
  ExchangeConfigUpdate,
  SignalMonitorTask,
  SignalMonitorCreate,
  SignalMonitorUpdate,
  NotificationConfigResponse,
  NotificationChannel,
  NotificationChannelCreate,
  NotificationChannelUpdate,
  NotificationSettings,
} from '@/types/settings'

/** 系统设置 API */
export const settingsApi = {
  /** 获取交易所配置（敏感字段已脱敏） */
  getExchangeConfig() {
    return client.get<unknown, ExchangeConfigResponse>(
      '/api/v1/settings/exchange',
    )
  },

  /** 更新交易所配置 */
  updateExchangeConfig(data: ExchangeConfigUpdate) {
    return client.put<unknown, ExchangeConfigResponse>(
      '/api/v1/settings/exchange',
      data,
    )
  },

  /** 获取所有信号监控任务 */
  getSignalMonitors() {
    return client.get<unknown, { tasks: SignalMonitorTask[] }>(
      '/api/v1/settings/signal-monitors',
    )
  },

  /** 添加信号监控任务 */
  addSignalMonitor(data: SignalMonitorCreate) {
    return client.post<unknown, { task: SignalMonitorTask }>(
      '/api/v1/settings/signal-monitors',
      data,
    )
  },

  /** 更新信号监控任务 */
  updateSignalMonitor(id: string, data: SignalMonitorUpdate) {
    return client.put<unknown, { task: SignalMonitorTask }>(
      `/api/v1/settings/signal-monitors/${id}`,
      data,
    )
  },

  /** 删除信号监控任务 */
  deleteSignalMonitor(id: string) {
    return client.delete(`/api/v1/settings/signal-monitors/${id}`)
  },

  /** 手动触发执行信号监控任务（超时延长，策略分析耗时较长） */
  runSignalMonitor(id: string) {
    return client.post<unknown, { signals: unknown[] }>(
      `/api/v1/settings/signal-monitors/${id}/run`,
      null,
      { timeout: 120_000 },
    )
  },

  /** 获取通知配置（敏感字段已脱敏） */
  getNotificationConfig() {
    return client.get<unknown, NotificationConfigResponse>(
      '/api/v1/settings/notifications',
    )
  },

  /** 更新通知全局设置 */
  updateNotificationSettings(data: Partial<NotificationSettings>) {
    return client.put<unknown, { settings: NotificationSettings }>(
      '/api/v1/settings/notifications/settings',
      data,
    )
  },

  /** 添加通知渠道 */
  addNotificationChannel(data: NotificationChannelCreate) {
    return client.post<unknown, { channel: NotificationChannel }>(
      '/api/v1/settings/notifications/channels',
      data,
    )
  },

  /** 更新通知渠道 */
  updateNotificationChannel(id: string, data: NotificationChannelUpdate) {
    return client.put<unknown, { channel: NotificationChannel }>(
      `/api/v1/settings/notifications/channels/${id}`,
      data,
    )
  },

  /** 删除通知渠道 */
  deleteNotificationChannel(id: string) {
    return client.delete(`/api/v1/settings/notifications/channels/${id}`)
  },

  /** 测试通知渠道 */
  testNotificationChannel(id: string) {
    return client.post<unknown, { success: boolean; message: string }>(
      `/api/v1/settings/notifications/channels/${id}/test`,
    )
  },
}
