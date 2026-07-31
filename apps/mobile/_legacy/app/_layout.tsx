import '../global.css'

import { QueryClientProvider } from '@tanstack/react-query'
import { useFonts } from 'expo-font'
import { Slot } from 'expo-router'
import { StatusBar } from 'expo-status-bar'
import { useEffect } from 'react'
import { View } from 'react-native'
import { SafeAreaProvider } from 'react-native-safe-area-context'

import { LoadingScreen } from '@/components/common/loading-screen'
import { queryClient } from '@/lib/query/query-client'
import { useAuthStore } from '@/store/auth-store'
import { useThemeColors } from '@/theme/colors'
import { fontMap } from '@/theme/typography'

export default function RootLayout() {
  const bootstrapStatus = useAuthStore((state) => state.bootstrapStatus)
  const [fontsLoaded] = useFonts(fontMap)
  const { colors, isDark } = useThemeColors()

  useEffect(() => {
    void useAuthStore.getState().bootstrap()
  }, [])

  return (
    <QueryClientProvider client={queryClient}>
      <SafeAreaProvider>
        <View style={{ backgroundColor: colors.bgDeep, flex: 1 }}>
          <StatusBar style={isDark ? 'light' : 'dark'} />
          {bootstrapStatus === 'ready' && fontsLoaded ? <Slot /> : <LoadingScreen label="Restoring your session" />}
        </View>
      </SafeAreaProvider>
    </QueryClientProvider>
  )
}
