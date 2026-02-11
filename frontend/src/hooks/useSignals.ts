import { useQuery } from '@tanstack/react-query'
import { strategiesApi } from '@/api/strategies'

/** 交易信号查询 Hook */
export function useSignals(symbol?: string, limit = 10) {
  return useQuery({
    queryKey: ['signals', symbol, limit],
    queryFn: () => strategiesApi.getSignals({ symbol, limit }),
    refetchInterval: 30_000,
  })
}
