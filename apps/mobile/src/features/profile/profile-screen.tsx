import { Ionicons } from '@expo/vector-icons'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import * as Location from 'expo-location'
import { router } from 'expo-router'
import { useEffect, useState } from 'react'
import { Alert, ScrollView, Switch, View } from 'react-native'
import { SafeAreaView } from 'react-native-safe-area-context'

import { LoadingScreen } from '@/components/common/loading-screen'
import { ScreenHeader } from '@/components/common/screen-header'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { Text } from '@/components/ui/text'
import { authApi } from '@/lib/api/auth'
import { queryKeys } from '@/lib/query/query-client'
import { disableDailyReminder, enableDailyReminder, getReminderStatus } from '@/lib/storage/notifications'
import { usersApi } from '@/lib/api/users'
import { useAuthStore } from '@/store/auth-store'
import { useThemeColors } from '@/theme/colors'

export function ProfileScreen() {
  const { colors } = useThemeColors()
  const queryClient = useQueryClient()
  const [remindersEnabled, setRemindersEnabled] = useState(false)

  const meQuery = useQuery({
    queryKey: queryKeys.me,
    queryFn: authApi.getCurrentUser,
  })

  useEffect(() => {
    void getReminderStatus().then(setRemindersEnabled)
  }, [])

  const locationMutation = useMutation({
    mutationFn: async () => {
      const permission = await Location.requestForegroundPermissionsAsync()
      if (!permission.granted) {
        throw new Error('Location permission is required to update your saved coordinates.')
      }

      const location = await Location.getCurrentPositionAsync({})
      const geocode = await Location.reverseGeocodeAsync(location.coords)

      return usersApi.updateLocation({
        lat: location.coords.latitude,
        lon: location.coords.longitude,
        city: geocode[0]?.city ?? undefined,
      })
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: queryKeys.me })
      Alert.alert('Location updated', 'Your saved recommendation location has been refreshed.')
    },
    onError: (error: Error) => {
      Alert.alert('Unable to update location', error.message)
    },
  })

  const signOut = useAuthStore((state) => state.signOut)

  if (meQuery.isLoading) {
    return <LoadingScreen label="Loading your profile" />
  }

  const user = meQuery.data

  return (
    <SafeAreaView className="flex-1" style={{ backgroundColor: colors.bgDeep }}>
      <ScrollView contentContainerStyle={{ padding: 24, paddingBottom: 120 }}>
        <ScreenHeader heading="Keep the habit loop alive." label="PROFILE" subtitle="Manage location, reminders, and your active session." />

        <Card className="mt-8 gap-3 p-6" variant="elevated">
          <Text preset="h2">{user?.full_name ?? 'ATTREQ user'}</Text>
          <Text color="textSecondary" preset="bodySmall">
            {user?.email}
          </Text>
          <Text color="textSecondary" preset="bodySmall">
            Saved location: {user?.saved_city ?? 'Not set'}{' '}
            {user?.saved_latitude != null && user?.saved_longitude != null
              ? `(${user.saved_latitude.toFixed(2)}, ${user.saved_longitude.toFixed(2)})`
              : ''}
          </Text>
          <Button
            icon={<Ionicons color={colors.textPrimary} name="location-outline" size={17} />}
            isLoading={locationMutation.isPending}
            label="Refresh saved location"
            onPress={() => locationMutation.mutate()}
            variant="secondary"
          />
        </Card>

        <Card className="mt-5 flex-row items-center justify-between p-6" variant="default">
          <View className="mr-4 flex-1">
            <Text preset="h3">Daily reminder</Text>
            <Text className="mt-1" color="textSecondary" preset="bodySmall">
              Schedule a local 8:00 AM reminder so ATTREQ stays in the daily loop.
            </Text>
          </View>
          <Switch
            onValueChange={async (nextValue) => {
              if (nextValue) {
                const enabled = await enableDailyReminder()
                if (!enabled) {
                  Alert.alert('Notifications disabled', 'Permission is required before reminders can be scheduled.')
                }
                setRemindersEnabled(enabled)
                return
              }

              await disableDailyReminder()
              setRemindersEnabled(false)
            }}
            trackColor={{ false: colors.borderSubtle, true: colors.accentMoss }}
            value={remindersEnabled}
          />
        </Card>

        <Card className="mt-5 gap-3 p-6" variant="outlined">
          <Text color="accentClay" preset="h3">
            Session
          </Text>
          <Text color="textSecondary" preset="bodySmall">
            Refresh tokens stay in SecureStore. Signing out clears local auth state and query caches.
          </Text>
          <Button
            label="Sign out"
            onPress={async () => {
              await signOut()
              router.replace('/(auth)/login')
            }}
            variant="danger"
          />
        </Card>
      </ScrollView>
    </SafeAreaView>
  )
}
