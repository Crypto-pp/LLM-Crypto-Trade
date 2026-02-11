/** K线时间周期选项 */
export const INTERVALS = [
  { label: '1分', value: '1m' },
  { label: '5分', value: '5m' },
  { label: '15分', value: '15m' },
  { label: '1时', value: '1h' },
  { label: '4时', value: '4h' },
  { label: '1天', value: '1d' },
  { label: '1周', value: '1w' },
] as const

/** 信号类型颜色映射 */
export const SIGNAL_COLORS: Record<string, string> = {
  BUY: '#3fb950',
  SELL: '#f85149',
  HOLD: '#d29922',
}

/** 信号类型中文映射 */
export const SIGNAL_LABELS: Record<string, string> = {
  BUY: '买入',
  SELL: '卖出',
  HOLD: '持有',
}
