import { create } from 'zustand'

import { authApi } from '@/lib/api/auth'
import { registerSessionHandlers } from '@/lib/api/session'
import { queryClient, queryKeys } from '@/lib/query/query-client'
import { clearRefreshToken, getRefreshToken, saveRefreshToken } from '@/lib/storage/secure-store'
import type { AuthResponse } from '@/lib/api/types'

type BootstrapStatus = 'idle' | 'loading' | 'ready'

interface AuthState {
  accessToken: string | null
  bootstrapStatus: BootstrapStatus
  signIn: (response: AuthResponse) => Promise<void>
  bootstrap: () => Promise<void>
  refreshSession: () => Promise<boolean>
  signOut: () => Promise<void>
}

export const useAuthStore = create<AuthState>((set, get) => ({
  accessToken: null,
  bootstrapStatus: 'idle',
  async signIn(response) {
    await saveRefreshToken(response.refresh_token)
    set({ accessToken: response.access_token })
    queryClient.setQueryData(queryKeys.me, response.user)
  },
  async bootstrap() {
    if (get().bootstrapStatus === 'loading' || get().bootstrapStatus === 'ready') {
      return
    }

    set({ bootstrapStatus: 'loading' })
    const refreshToken = await getRefreshToken()

    if (!refreshToken) {
      set({ accessToken: null, bootstrapStatus: 'ready' })
      return
    }

    const refreshed = await get().refreshSession()
    if (refreshed) {
      try {
        const currentUser = await authApi.getCurrentUser()
        queryClient.setQueryData(queryKeys.me, currentUser)
      } catch {
        await get().signOut()
      }
    }

    set({ bootstrapStatus: 'ready' })
  },
  async refreshSession() {
    const refreshToken = await getRefreshToken()

    if (!refreshToken) {
      set({ accessToken: null })
      return false
    }

    try {
      const refreshed = await authApi.refresh(refreshToken)
      set({ accessToken: refreshed.access_token })
      return true
    } catch {
      await clearRefreshToken()
      set({ accessToken: null })
      queryClient.clear()
      return false
    }
  },
  async signOut() {
    try {
      await authApi.logout()
    } catch {
      // Logout is best effort because the API is stateless.
    }

    await clearRefreshToken()
    set({ accessToken: null })
    queryClient.clear()
  },
}))

registerSessionHandlers({
  getAccessToken: () => useAuthStore.getState().accessToken,
  refreshSession: () => useAuthStore.getState().refreshSession(),
  signOut: () => useAuthStore.getState().signOut(),
})
