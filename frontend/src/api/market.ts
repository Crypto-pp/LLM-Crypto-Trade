import client from './client'
import type { Kline, Ticker, Exchange } from '@/types/market'

/** 市场数据 API */
export const marketApi = {
  /** 获取K线数据 */
  getKlines(params: {
    exchange: string
    symbol: string
    interval: string
    limit?: number
  }) {
    return client.get<unknown, { klines: Kline[]; total: number }>(
      '/api/v1/market/klines',
      { params },
    )
  },

  /** 获取实时行情 */
  getTicker(params: { exchange: string; symbol: string }) {
    return client.get<unknown, { ticker: Ticker }>(
      '/api/v1/market/ticker',
      { params },
    )
  },

  /** 获取交易对列表 */
  getSymbols(exchange?: string) {
    return client.get<unknown, { symbols: string[] }>(
      '/api/v1/market/symbols',
      { params: { exchange } },
    )
  },

  /** 获取交易所列表 */
  getExchanges() {
    return client.get<unknown, { exchanges: Exchange[] }>(
      '/api/v1/market/exchanges',
    )
  },
}
