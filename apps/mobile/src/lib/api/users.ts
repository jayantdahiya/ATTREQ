import { apiClient } from '@/lib/api/client';
import type { User } from '@/lib/api/types';

export interface LocationPayload {
  lat: number;
  lon: number;
  city?: string;
}

export interface ProfileUpdatePayload {
  full_name?: string;
  location?: string;
  // Sent for forward-compat; the backend UserUpdate schema ignores it today
  // (style_preferences is Style-DNA-owned) — mirrors the iOS divergence.
  style_preferences?: string;
  saved_city?: string;
}

export const usersApi = {
  async updateLocation(payload: LocationPayload) {
    const response = await apiClient.patch<User>('/users/me/location', payload);
    return response.data;
  },
  async updateProfile(payload: ProfileUpdatePayload) {
    const response = await apiClient.put<User>('/users/me', payload);
    return response.data;
  },
  async completeOnboarding(): Promise<User> {
    const response = await apiClient.post<User>('/users/onboarding/complete');
    return response.data;
  },
};
