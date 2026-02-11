import client from './client'
import type {
  BacktestRequest,
  BacktestResponse,
  BacktestResult,
  BacktestTask,
} from '@/types/backtest'

/** 回测 API */
export const backtestApi = {
  /** 运行回测 */
  run(data: BacktestRequest) {
    return client.post<unknown, BacktestResponse>(
      '/api/v1/backtest/run',
      data,
    )
  },

  /** 获取回测结果 */
  getResults(id: string) {
    return client.get<unknown, BacktestResult>(
      `/api/v1/backtest/${id}/results`,
    )
  },

  /** 获取回测报告 */
  getReport(id: string) {
    return client.get<unknown, Record<string, unknown>>(
      `/api/v1/backtest/${id}/report`,
    )
  },

  /** 获取回测历史列表 */
  list(params?: { limit?: number; offset?: number }) {
    return client.get<
      unknown,
      { total: number; items: BacktestTask[] }
    >('/api/v1/backtest/list', { params })
  },
}
