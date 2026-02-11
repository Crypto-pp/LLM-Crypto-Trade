import client from './client'
import type {
  AIProvider, AIPrompt, AIAnalysisRequest, AIAnalysisResult,
  AIConfigResponse, AIConfigUpdate, AITestResult,
} from '@/types/ai'

/** AI分析 API */
export const aiApi = {
  /** 获取可用AI提供商列表 */
  getProviders() {
    return client.get<unknown, { providers: AIProvider[]; total: number }>(
      '/api/v1/ai/providers',
    )
  },

  /** 获取预设提示词列表 */
  getPrompts() {
    return client.get<unknown, { prompts: AIPrompt[]; total: number }>(
      '/api/v1/ai/prompts',
    )
  },

  /** 执行AI分析（普通响应） */
  analyze(req: AIAnalysisRequest) {
    return client.post<unknown, AIAnalysisResult>(
      '/api/v1/ai/analyze',
      req,
      { timeout: 120_000 },
    )
  },

  /** 获取AI配置（API Key已脱敏） */
  getConfig() {
    return client.get<unknown, AIConfigResponse>('/api/v1/ai/config')
  },

  /** 更新AI配置 */
  updateConfig(data: AIConfigUpdate) {
    return client.put<unknown, AIConfigResponse>('/api/v1/ai/config', data)
  },

  /** 测试提供商连接 */
  testProvider(provider: string) {
    return client.post<unknown, AITestResult>(
      '/api/v1/ai/config/test',
      { provider },
    )
  },
}
