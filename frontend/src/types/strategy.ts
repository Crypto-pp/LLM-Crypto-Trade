/** 策略定义 */
export interface Strategy {
  name: string
  description: string
  parameters: Record<string, number>
}

/** 交易信号 */
export interface Signal {
  signal_id: string
  symbol: string
  signal_type: 'BUY' | 'SELL' | 'HOLD'
  entry_price: number
  stop_loss: number
  take_profit: number
  strategy: string
  confidence: number
  timestamp: string
}
