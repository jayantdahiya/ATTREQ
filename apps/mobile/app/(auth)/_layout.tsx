import { Redirect, Stack } from 'expo-router'

import { useAuthStore } from '@/store/auth-store'

export default function AuthLayout() {
  const accessToken = useAuthStore((state) => state.accessToken)

  if (accessToken) {
    return <Redirect href="/(protected)/(tabs)" />
  }

  return (
    <Stack
      screenOptions={{
        headerShown: false,
      }}
    />
  )
}
