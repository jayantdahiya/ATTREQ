import { Redirect, Stack } from 'expo-router'

import { useAuthStore } from '@/store/auth-store'

export default function ProtectedLayout() {
  const accessToken = useAuthStore((state) => state.accessToken)

  if (!accessToken) {
    return <Redirect href="/(auth)/login" />
  }

  return (
    <Stack
      screenOptions={{
        headerShown: false,
      }}
    />
  )
}
