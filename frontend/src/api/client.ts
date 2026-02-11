import axios from 'axios'
import { ApiError } from '@/types/api'

const client = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '',
  timeout: 15_000,
  headers: { 'Content-Type': 'application/json' },
})

/** 请求拦截器：自动附加 Bearer Token */
client.interceptors.request.use((config) => {
  try {
    const raw = localStorage.getItem('auth-store')
    if (raw) {
      const { state } = JSON.parse(raw)
      if (state?.token) {
        config.headers.Authorization = `Bearer ${state.token}`
      }
    }
  } catch {
    // localStorage 读取失败时静默忽略
  }
  return config
})

/** 响应拦截器：统一错误处理 */
client.interceptors.response.use(
  (res) => {
    const data = res.data
    if (data?.code && data.code !== 200) {
      return Promise.reject(new ApiError(data.code, data.message))
    }
    return data
  },
  (err) => {
    if (err.response) {
      // 401 时清除 token 并跳转登录页
      if (err.response.status === 401) {
        try {
          const raw = localStorage.getItem('auth-store')
          if (raw) {
            const parsed = JSON.parse(raw)
            parsed.state = { ...parsed.state, token: null, username: null, isAuthenticated: false, mustChangePassword: false }
            localStorage.setItem('auth-store', JSON.stringify(parsed))
          }
        } catch {
          localStorage.removeItem('auth-store')
        }
        // 避免在登录页重复跳转
        if (!window.location.pathname.startsWith('/login')) {
          window.location.href = '/login'
        }
      }
      const msg = err.response.data?.detail || err.response.statusText
      return Promise.reject(new ApiError(err.response.status, msg))
    }
    return Promise.reject(err)
  },
)

export default client
