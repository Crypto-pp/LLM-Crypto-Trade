/** 通用 API 响应类型 */
export interface ApiResponse<T> {
  code: number
  message: string
  data: T
  timestamp: string
}

/** 分页响应 */
export interface PaginatedResponse<T> {
  total: number
  limit: number
  offset: number
  items: T[]
}

/** API 错误 */
export class ApiError extends Error {
  code: number
  constructor(code: number, message: string) {
    super(message)
    this.code = code
    this.name = 'ApiError'
  }
}
