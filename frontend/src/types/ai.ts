/** AI提供商 */
export interface AIProvider {
  id: string
  name: string
  model: string
  enabled: boolean
}

/** AI预设提示词 */
export interface AIPrompt {
  id: string
  name: string
  description: string
  category: string
}

/** AI分析请求 */
export interface AIAnalysisRequest {
  symbol: string
  interval: string
  prompt_id: string
  provider?: string
}

/** AI分析结果 */
export interface AIAnalysisResult {
  symbol: string
  interval: string
  provider: string
  model: string
  prompt_id: string
  analysis: string
  market_context_summary: string
  timestamp: string
}

/** AI提供商配置 */
export interface AIProviderConfig {
  api_key: string
  base_url?: string
  model: string
  has_key: boolean
}

/** AI配置响应 */
export interface AIConfigResponse {
  default_provider: string
  providers: Record<string, AIProviderConfig>
  general: {
    max_tokens: number
    temperature: number
    timeout: number
  }
}

/** AI配置更新请求 */
export interface AIConfigUpdate {
  [key: string]: string | number | undefined
}

/** AI提供商测试结果 */
export interface AITestResult {
  provider: string
  success: boolean
  message: string
}
