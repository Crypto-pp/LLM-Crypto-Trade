import { useQuery } from '@tanstack/react-query'
import { marketApi } from '@/api/market'

/** K线数据查询 Hook */
export function useKlines(
  exchange: string,
  symbol: string,
  interval: string,
  limit = 500,
) {
  return useQuery({
    queryKey: ['klines', exchange, symbol, interval, limit],
    queryFn: () =>
      marketApi.getKlines({ exchange, symbol, interval, limit }),
    staleTime: 30_000,
    refetchInterval: 60_000,
    enabled: !!exchange && !!symbol,
  })
}
