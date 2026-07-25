import { create } from 'zustand';

import { authApi } from '@/lib/api/auth';
import { usersApi } from '@/lib/api/users';
import { registerSessionHandlers } from '@/lib/api/session';
import { queryClient, queryKeys } from '@/lib/query/query-client';
import { clearRefreshToken, getRefreshToken, saveRefreshToken } from '@/lib/storage/secure-store';
import type { AuthResponse, User } from '@/lib/api/types';

type BootstrapStatus = 'idle' | 'loading' | 'ready';

/** Everything gathered by the 3-step register wizard (Account → Style → Location). */
export interface RegistrationData {
  email: string;
  fullName: string;
  password: string;
  styleKeywords: string[];
  occasions: string;
  location?:
    | { kind: 'coordinates'; latitude: number; longitude: number; city: string | null }
    | { kind: 'city'; city: string };
}

interface AuthState {
  accessToken: string | null;
  bootstrapStatus: BootstrapStatus;
  signIn: (response: AuthResponse) => Promise<void>;
  login: (email: string, password: string) => Promise<void>;
  register: (data: RegistrationData) => Promise<void>;
  bootstrap: () => Promise<void>;
  refreshSession: () => Promise<boolean>;
  signOut: () => Promise<void>;
}

export const useAuthStore = create<AuthState>((set, get) => ({
  accessToken: null,
  bootstrapStatus: 'idle',
  async signIn(response) {
    await saveRefreshToken(response.refresh_token);
    set({ accessToken: response.access_token });
    queryClient.setQueryData(queryKeys.me, response.user);
  },
  async login(email, password) {
    const auth = await authApi.login({ username: email, password });
    await get().signIn(auth);
  },
  // Mirrors iOS AppSession.register: register → login → best-effort enrichment → refresh.
  async register(data) {
    const trimmedName = data.fullName.trim();
    await authApi.register({
      email: data.email,
      password: data.password,
      full_name: trimmedName.length > 0 ? trimmedName : undefined,
    });

    const auth = await authApi.login({ username: data.email, password: data.password });
    await get().signIn(auth);

    // Best-effort profile enrichment — must never fail registration.
    const styleParts = [...data.styleKeywords];
    if (data.occasions.trim().length > 0) styleParts.push(data.occasions.trim());
    const profile: Parameters<typeof usersApi.updateProfile>[0] = {};
    if (styleParts.length > 0) profile.style_preferences = styleParts.join(', ');
    if (data.location?.kind === 'city') {
      profile.location = data.location.city;
      profile.saved_city = data.location.city;
    }
    if (profile.style_preferences !== undefined || profile.location !== undefined) {
      try {
        await usersApi.updateProfile(profile);
      } catch {
        // non-fatal
      }
    }
    if (data.location?.kind === 'coordinates') {
      try {
        await usersApi.updateLocation({
          lat: data.location.latitude,
          lon: data.location.longitude,
          city: data.location.city ?? undefined,
        });
      } catch {
        // non-fatal
      }
    }

    // Refresh the cached user so the onboarding gate sees the enrichment.
    try {
      const user = await authApi.getCurrentUser();
      queryClient.setQueryData(queryKeys.me, user);
    } catch {
      queryClient.setQueryData(queryKeys.me, auth.user);
    }
  },
  async bootstrap() {
    if (get().bootstrapStatus === 'loading' || get().bootstrapStatus === 'ready') {
      return;
    }

    set({ bootstrapStatus: 'loading' });
    const refreshToken = await getRefreshToken();

    if (!refreshToken) {
      set({ accessToken: null, bootstrapStatus: 'ready' });
      return;
    }

    const refreshed = await get().refreshSession();
    if (refreshed) {
      try {
        const currentUser = await authApi.getCurrentUser();
        queryClient.setQueryData(queryKeys.me, currentUser);
      } catch {
        await get().signOut();
      }
    }

    set({ bootstrapStatus: 'ready' });
  },
  async refreshSession() {
    const refreshToken = await getRefreshToken();

    if (!refreshToken) {
      set({ accessToken: null });
      return false;
    }

    try {
      const refreshed = await authApi.refresh(refreshToken);
      set({ accessToken: refreshed.access_token });
      return true;
    } catch {
      await clearRefreshToken();
      set({ accessToken: null });
      queryClient.clear();
      return false;
    }
  },
  async signOut() {
    try {
      await authApi.logout();
    } catch {
      // Logout is best effort because the API is stateless.
    }

    await clearRefreshToken();
    set({ accessToken: null });
    queryClient.clear();
  },
}));

// Read current user (cached by signIn/bootstrap) — null until loaded.
export function getCachedUser(): User | null {
  return queryClient.getQueryData<User>(queryKeys.me) ?? null;
}

registerSessionHandlers({
  getAccessToken: () => useAuthStore.getState().accessToken,
  refreshSession: () => useAuthStore.getState().refreshSession(),
  signOut: () => useAuthStore.getState().signOut(),
});
