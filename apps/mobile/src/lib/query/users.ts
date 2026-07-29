import { useMutation, useQueryClient } from '@tanstack/react-query';

import { usersApi, type ChangePasswordPayload, type ProfileUpdatePayload } from '@/lib/api/users';
import { authApi } from '@/lib/api/auth';
import { queryKeys } from '@/lib/query/query-client';

/** PUT /users/me — profile update, then refetch the cached user so the
 * Profile rows reflect it. style_preferences is device-local (backend ignores). */
export function useUpdateProfile() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: ProfileUpdatePayload) => usersApi.updateProfile(payload),
    onSuccess: (user) => qc.setQueryData(queryKeys.me, user),
  });
}

/** PATCH /users/me/location — manual-city save routes through PUT /users/me
 * instead (that path lives in the Location modal); this covers coordinate saves. */
export function useUpdateLocation() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: { lat: number; lon: number; city?: string }) =>
      usersApi.updateLocation(payload),
    onSuccess: (user) => qc.setQueryData(queryKeys.me, user),
  });
}

/** POST /users/change-password. */
export function useChangePassword() {
  return useMutation({
    mutationFn: (payload: ChangePasswordPayload) => usersApi.changePassword(payload),
  });
}

/** DELETE /users/me — deactivate. On success the caller must sign out. */
export function useDeleteAccount() {
  return useMutation({
    mutationFn: () => usersApi.deleteAccount(),
  });
}

/** Re-fetch GET /users/me into the cache (used after a profile edit). */
export function refetchCurrentUser() {
  return authApi.getCurrentUser();
}
