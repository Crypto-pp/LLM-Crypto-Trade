import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { aiApi } from '@/api/ai'
import type { AIAnalysisRequest, AIConfigUpdate } from '@/types/ai'

/** AI提供商列表 Hook */
export function useAIProviders() {
  return useQuery({
    queryKey: ['ai-providers'],
    queryFn: () => aiApi.getProviders(),
    staleTime: 60_000,
  })
}

/** AI提示词列表 Hook */
export function useAIPrompts() {
  return useQuery({
    queryKey: ['ai-prompts'],
    queryFn: () => aiApi.getPrompts(),
    staleTime: 60_000,
  })
}

/** AI分析 Mutation Hook */
export function useAIAnalyze() {
  return useMutation({
    mutationFn: (req: AIAnalysisRequest) => aiApi.analyze(req),
  })
}

/** AI配置查询 Hook */
export function useAIConfig() {
  return useQuery({
    queryKey: ['ai-config'],
    queryFn: () => aiApi.getConfig(),
    staleTime: 60_000,
  })
}

/** AI配置更新 Mutation Hook */
export function useAIConfigUpdate() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (data: AIConfigUpdate) => aiApi.updateConfig(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['ai-config'] })
      queryClient.invalidateQueries({ queryKey: ['ai-providers'] })
    },
  })
}

/** AI提供商连接测试 Mutation Hook */
export function useAITestProvider() {
  return useMutation({
    mutationFn: (provider: string) => aiApi.testProvider(provider),
  })
}
