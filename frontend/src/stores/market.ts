import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface MarketState {
  exchange: string
  symbol: string
  interval: string
  setExchange: (exchange: string) => void
  setSymbol: (symbol: string) => void
  setInterval: (interval: string) => void
}

export const useMarketStore = create<MarketState>()(
  persist(
    (set) => ({
      exchange: import.meta.env.VITE_DEFAULT_EXCHANGE || 'binance',
      symbol: import.meta.env.VITE_DEFAULT_SYMBOL || 'BTC/USDT',
      interval: import.meta.env.VITE_DEFAULT_INTERVAL || '1h',
      setExchange: (exchange) => set({ exchange }),
      setSymbol: (symbol) => set({ symbol }),
      setInterval: (interval) => set({ interval }),
    }),
    { name: 'market-store' },
  ),
)
