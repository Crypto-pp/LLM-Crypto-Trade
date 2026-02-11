/** 回测请求 */
export interface BacktestRequest {
  strategy: string
  symbol: string
  start_date: string
  end_date: string
  initial_capital: number
  params?: Record<string, unknown>
}

/** 回测响应 */
export interface BacktestResponse {
  backtest_id: string
  status: string
  message: string
}

/** 回测结果 */
export interface BacktestResult {
  backtest_id: string
  summary: Record<string, unknown>
  metrics: {
    total_return: number
    sharpe_ratio: number
    max_drawdown: number
    win_rate: number
    total_trades: number
  }
  rating: Record<string, unknown>
}

/** 回测任务 */
export interface BacktestTask {
  status: string
  request: BacktestRequest
  created_at: string
}
