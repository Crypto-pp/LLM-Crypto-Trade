/**
 * 根据价格大小自动计算合适的小数位数
 * 大于1的价格用2位，小于1的价格根据前导零数量自动扩展
 */
export function getSmartPrecision(num: number): number {
  if (num === 0 || isNaN(num)) return 2
  const abs = Math.abs(num)
  if (abs >= 1) return 2
  // 0.00000789 → -log10(0.00000789) ≈ 5.1 → 5个前导零 → 需要 5+2=7 位小数
  const leadingZeros = Math.floor(-Math.log10(abs))
  return Math.min(leadingZeros + 2, 12)
}

/** 格式化价格，添加千分位分隔符；precision 为 undefined 时自动推断 */
export function formatPrice(value: number | string, precision?: number): string {
  const num = typeof value === 'string' ? parseFloat(value) : value
  if (isNaN(num)) return '0.00'
  const p = precision ?? getSmartPrecision(num)
  return num.toLocaleString('en-US', {
    minimumFractionDigits: p,
    maximumFractionDigits: p,
  })
}

/** 格式化百分比，带正负号 */
export function formatPercent(value: number | string, precision = 2): string {
  const num = typeof value === 'string' ? parseFloat(value) : value
  if (isNaN(num)) return '0.00%'
  const sign = num > 0 ? '+' : ''
  return `${sign}${num.toFixed(precision)}%`
}

/** 格式化成交量（缩写） */
export function formatVolume(value: number | string): string {
  const num = typeof value === 'string' ? parseFloat(value) : value
  if (isNaN(num)) return '0'
  if (num >= 1e9) return `${(num / 1e9).toFixed(2)}B`
  if (num >= 1e6) return `${(num / 1e6).toFixed(2)}M`
  if (num >= 1e3) return `${(num / 1e3).toFixed(2)}K`
  return num.toFixed(2)
}

/** 格式化时间戳为本地时间 */
export function formatTime(timestamp: string): string {
  return new Date(timestamp).toLocaleString('zh-CN')
}

/** 格式化运行时间 */
export function formatUptime(seconds: number): string {
  const d = Math.floor(seconds / 86400)
  const h = Math.floor((seconds % 86400) / 3600)
  const m = Math.floor((seconds % 3600) / 60)
  if (d > 0) return `${d}d ${h}h ${m}m`
  if (h > 0) return `${h}h ${m}m`
  return `${m}m`
}
