import { apiClient } from '@/lib/api/client'
import type { AuthResponse, User } from '@/lib/api/types'

export interface RegisterPayload {
  email: string
  password: string
  full_name?: string
  location?: string
}

export interface LoginPayload {
  username: string
  password: string
}

export const authApi = {
  async register(payload: RegisterPayload) {
    const response = await apiClient.post<User>('/auth/register', payload)
    return response.data
  },
  async login(payload: LoginPayload) {
    const formData = new URLSearchParams()
    formData.append('username', payload.username)
    formData.append('password', payload.password)

    const response = await apiClient.post<AuthResponse>('/auth/login', formData.toString(), {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
    })

    return response.data
  },
  async refresh(refreshToken: string) {
    const response = await apiClient.post<Pick<AuthResponse, 'access_token' | 'token_type'>>(
      '/auth/refresh',
      { refresh_token: refreshToken }
    )
    return response.data
  },
  async logout() {
    await apiClient.post('/auth/logout')
  },
  async getCurrentUser() {
    const response = await apiClient.get<User>('/users/me')
    return response.data
  },
}
