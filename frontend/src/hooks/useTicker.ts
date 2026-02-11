import { useQuery } from '@tanstack/react-query'
import { marketApi } from '@/api/market'

/** 实时行情查询 Hook */
export function useTicker(exchange: string, symbol: string) {
  return useQuery({
    queryKey: ['ticker', exchange, symbol],
    queryFn: () => marketApi.getTicker({ exchange, symbol }),
    staleTime: 10_000,
    refetchInterval: 15_000,
    enabled: !!exchange && !!symbol,
  })
}
