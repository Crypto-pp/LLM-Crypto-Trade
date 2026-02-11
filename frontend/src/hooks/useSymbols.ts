import { useQuery } from '@tanstack/react-query'
import { marketApi } from '@/api/market'

/** 交易对列表 Hook（从交易所动态加载） */
export function useSymbols(exchange?: string) {
  return useQuery({
    queryKey: ['symbols', exchange],
    queryFn: () => marketApi.getSymbols(exchange),
    staleTime: 600_000,
    gcTime: 3600_000,
  })
}
