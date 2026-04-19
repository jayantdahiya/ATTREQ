import { apiClient } from '@/lib/api/client'
import type { User } from '@/lib/api/types'

export interface LocationPayload {
  lat: number
  lon: number
  city?: string
}

export const usersApi = {
  async updateLocation(payload: LocationPayload) {
    const response = await apiClient.patch<User>('/users/me/location', payload)
    return response.data
  },
  async updateProfile(payload: Partial<Pick<User, 'full_name' | 'location'>>) {
    const response = await apiClient.put<User>('/users/me', payload)
    return response.data
  },
}
