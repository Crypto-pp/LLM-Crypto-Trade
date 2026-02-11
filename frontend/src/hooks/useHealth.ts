import { useQuery } from '@tanstack/react-query'
import { systemApi } from '@/api/system'

/** 健康状态查询 Hook */
export function useHealth() {
  return useQuery({
    queryKey: ['health'],
    queryFn: () => systemApi.health(),
    refetchInterval: 10_000,
  })
}
