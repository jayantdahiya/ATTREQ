import { create } from 'zustand'
import { persist, PersistStorage } from 'zustand/middleware'
import { User } from '@/lib/api/auth'
import Cookies from 'js-cookie'

interface AuthState {
  user: User | null
  accessToken: string | null
  refreshToken: string | null
  isAuthenticated: boolean
  setUser: (user: User) => void
  setTokens: (accessToken: string, refreshToken?: string) => void
  setAccessToken: (accessToken: string) => void
  logout: () => void
}

const cookieStorage: PersistStorage<AuthState> = {
  getItem: (name) => {
    const str = Cookies.get(name)
    if (!str) {
      return null
    }
    return JSON.parse(str)
  },
  setItem: (name, value) => {
    Cookies.set(name, JSON.stringify(value), { expires: 7 }) // Expires in 7 days
  },
  removeItem: (name) => {
    Cookies.remove(name)
  },
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      accessToken: null,
      refreshToken: null,
      isAuthenticated: false,
      setUser: (user) => {
        console.log('Setting user:', user)
        set({ user, isAuthenticated: true })
      },
      setTokens: (accessToken, refreshToken) => {
        console.log('Setting tokens:', { accessToken, refreshToken })
        set((state) => ({
          accessToken,
          refreshToken: refreshToken || state.refreshToken,
          isAuthenticated: true,
        }))
      },
      setAccessToken: (accessToken) => set({ accessToken }),
      logout: () =>
        set({
          user: null,
          accessToken: null,
          refreshToken: null,
          isAuthenticated: false,
        }),
    }),
    {
      name: 'auth-storage',
      storage: cookieStorage,
    }
  )
)
