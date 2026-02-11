import { create } from 'zustand'

interface WebSocketState {
  connected: boolean
  prices: Record<string, number>
  latency: number
  setConnected: (connected: boolean) => void
  updatePrice: (symbol: string, price: number) => void
  setLatency: (latency: number) => void
}

export const useWebSocketStore = create<WebSocketState>()((set) => ({
  connected: false,
  prices: {},
  latency: 0,
  setConnected: (connected) => set({ connected }),
  updatePrice: (symbol, price) =>
    set((state) => ({
      prices: { ...state.prices, [symbol]: price },
    })),
  setLatency: (latency) => set({ latency }),
}))
