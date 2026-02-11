import client from './client'

/** 认证 API */
export const authApi = {
  /** 登录 */
  login(username: string, password: string) {
    return client.post<unknown, { token: string; username: string; must_change_password: boolean }>(
      '/api/v1/auth/login',
      { username, password },
    )
  },

  /** 修改密码 */
  changePassword(oldPassword: string, newPassword: string) {
    return client.post<unknown, { success: boolean; message: string }>(
      '/api/v1/auth/change-password',
      { old_password: oldPassword, new_password: newPassword },
    )
  },

  /** 登出 */
  logout() {
    return client.post('/api/v1/auth/logout')
  },

  /** 获取当前用户信息 */
  me() {
    return client.get<unknown, { username: string }>('/api/v1/auth/me')
  },
}
