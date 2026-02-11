import client from './client'
import type {
  IndicatorResult,
  PatternResult,
  SupportResistanceResult,
} from '@/types/analysis'

/** 技术分析 API */
export const analysisApi = {
  /** 计算技术指标 */
  getIndicators(params: {
    symbol: string
    interval: string
    indicators: string[]
  }) {
    return client.get<unknown, IndicatorResult>(
      '/api/v1/analysis/indicators',
      { params },
    )
  },

  /** 识别价格形态 */
  getPatterns(params: { symbol: string; interval: string }) {
    return client.get<unknown, PatternResult>(
      '/api/v1/analysis/patterns',
      { params },
    )
  },

  /** 获取支撑阻力位 */
  getSupportResistance(params: {
    symbol: string
    interval: string
  }) {
    return client.get<unknown, SupportResistanceResult>(
      '/api/v1/analysis/support-resistance',
      { params },
    )
  },
}
