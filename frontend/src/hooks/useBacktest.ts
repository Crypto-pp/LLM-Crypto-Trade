import { useQuery, useMutation } from '@tanstack/react-query'
import { backtestApi } from '@/api/backtest'
import type { BacktestRequest } from '@/types/backtest'

/** 回测历史列表查询 */
export function useBacktestList(limit = 10, offset = 0) {
  return useQuery({
    queryKey: ['backtests', limit, offset],
    queryFn: () => backtestApi.list({ limit, offset }),
  })
}

/** 回测结果查询 */
export function useBacktestResults(id: string) {
  return useQuery({
    queryKey: ['backtest-results', id],
    queryFn: () => backtestApi.getResults(id),
    enabled: !!id,
  })
}

/** 运行回测 Mutation */
export function useRunBacktest() {
  return useMutation({
    mutationFn: (data: BacktestRequest) => backtestApi.run(data),
  })
}
