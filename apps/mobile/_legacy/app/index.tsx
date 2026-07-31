import { Redirect } from 'expo-router'

import { queryClient, queryKeys } from '@/lib/query/query-client'
import { useAuthStore } from '@/store/auth-store'
import type { User } from '@/lib/api/types'

export default function IndexScreen() {
  const accessToken = useAuthStore((state) => state.accessToken)

  if (!accessToken) {
    return <Redirect href="/(auth)/login" />
  }

  // queryClient has user data from bootstrap — synchronous, no loading needed
  const user = queryClient.getQueryData<User>(queryKeys.me)

  if (user && !user.onboarding_completed) {
    return <Redirect href="/(onboarding)/upload-style" />
  }

  return <Redirect href="/(protected)/(tabs)" />
}
