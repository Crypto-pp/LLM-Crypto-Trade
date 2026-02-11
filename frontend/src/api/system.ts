import client from './client'

/** 系统 API */
export const systemApi = {
  /** 健康检查 */
  health() {
    return client.get<unknown, Record<string, unknown>>('/health/api')
  },

  /** Prometheus 指标 */
  metrics() {
    return client.get<unknown, string>('/metrics')
  },
}
