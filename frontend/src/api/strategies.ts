import client from './client'
import type { Strategy, Signal } from '@/types/strategy'

/** 策略 API */
export const strategiesApi = {
  /** 获取策略列表 */
  list() {
    return client.get<unknown, { strategies: Strategy[]; total: number }>(
      '/api/v1/strategies/strategies',
    )
  },

  /** 执行策略分析 */
  analyze(name: string, params: { symbol: string; interval?: string }) {
    return client.post<unknown, Record<string, unknown>>(
      `/api/v1/strategies/strategies/${name}/analyze`,
      null,
      { params },
    )
  },

  /** 获取交易信号 */
  getSignals(params?: {
    symbol?: string
    strategy?: string
    limit?: number
  }) {
    return client.get<unknown, { signals: Signal[]; total: number }>(
      '/api/v1/strategies/signals',
      { params },
    )
  },
}
