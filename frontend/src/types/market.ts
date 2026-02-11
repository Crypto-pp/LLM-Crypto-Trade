/** K线数据 */
export interface Kline {
  timestamp: string
  open: string
  high: string
  low: string
  close: string
  volume: string
  quote_volume: string | null
  trades_count: number | null
}

/** 实时行情 */
export interface Ticker {
  exchange: string
  symbol: string
  last_price: string
  bid_price: string | null
  ask_price: string | null
  volume_24h: string | null
  price_change_24h: string | null
  timestamp: string
}

/** 交易所信息 */
export interface Exchange {
  id: string
  name: string
  enabled: boolean
}
