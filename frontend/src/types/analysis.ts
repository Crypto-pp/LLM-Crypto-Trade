/** 技术指标结果 */
export interface IndicatorResult {
  symbol: string
  interval: string
  indicators: Record<string, number | Record<string, number>>
  timestamp: string
}

/** 形态识别结果 */
export interface PatternResult {
  symbol: string
  interval: string
  market_structure: Record<string, unknown>
  timestamp: string
}

/** 支撑阻力位 */
export interface SupportResistanceLevel {
  price: number
  touches: number
}

/** 支撑阻力结果 */
export interface SupportResistanceResult {
  symbol: string
  interval: string
  support_levels: SupportResistanceLevel[]
  resistance_levels: SupportResistanceLevel[]
  timestamp: string
}
