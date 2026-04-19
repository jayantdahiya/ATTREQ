import { Redirect } from 'expo-router'

import { useAuthStore } from '@/store/auth-store'

export default function IndexScreen() {
  const accessToken = useAuthStore((state) => state.accessToken)

  return <Redirect href={accessToken ? '/(protected)/(tabs)' : '/(auth)/login'} />
}
