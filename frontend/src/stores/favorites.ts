import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface FavoriteState {
  symbols: string[]
  addFavorite: (symbol: string) => void
  removeFavorite: (symbol: string) => void
  isFavorite: (symbol: string) => boolean
}

export const useFavoriteStore = create<FavoriteState>()(
  persist(
    (set, get) => ({
      symbols: ['BTC/USDT', 'ETH/USDT'],
      addFavorite: (symbol) =>
        set((state) => ({
          symbols: state.symbols.includes(symbol)
            ? state.symbols
            : [...state.symbols, symbol],
        })),
      removeFavorite: (symbol) =>
        set((state) => ({
          symbols: state.symbols.filter((s) => s !== symbol),
        })),
      isFavorite: (symbol) => get().symbols.includes(symbol),
    }),
    { name: 'favorite-store' },
  ),
)
