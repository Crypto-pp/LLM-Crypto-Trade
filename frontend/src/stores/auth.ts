import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface AuthState {
  token: string | null
  username: string | null
  mustChangePassword: boolean
  isAuthenticated: boolean
  login: (token: string, username: string, mustChangePassword: boolean) => void
  logout: () => void
  setMustChange: (value: boolean) => void
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      token: null,
      username: null,
      mustChangePassword: false,
      isAuthenticated: false,
      login: (token, username, mustChangePassword) =>
        set({
          token,
          username,
          mustChangePassword,
          isAuthenticated: true,
        }),
      logout: () =>
        set({
          token: null,
          username: null,
          mustChangePassword: false,
          isAuthenticated: false,
        }),
      setMustChange: (value) => set({ mustChangePassword: value }),
    }),
    { name: 'auth-store' },
  ),
)
