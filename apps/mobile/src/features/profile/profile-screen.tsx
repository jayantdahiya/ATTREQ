import { Ionicons } from '@expo/vector-icons'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import * as Location from 'expo-location'
import { router } from 'expo-router'
import { useEffect, useState } from 'react'
import { Alert, Pressable, ScrollView, Switch, View } from 'react-native'
import { SafeAreaView } from 'react-native-safe-area-context'

import { EditorialCard, EditorialHeader, MonoLabel, QuietChevron, fontFamily } from '@/components/attreq/editorial'
import { LoadingScreen } from '@/components/common/loading-screen'
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
  const initials = (user?.full_name ?? user?.email ?? 'AU')
    .split(/[ @.]/)
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase())
    .join('')
  const hasLocation = user?.saved_latitude != null && user?.saved_longitude != null

  return (
    <SafeAreaView className="flex-1" style={{ backgroundColor: colors.bgDeep }}>
      <ScrollView contentContainerStyle={{ padding: 24, paddingBottom: 130 }}>
        <EditorialHeader label="You" title="Profile" />

        <EditorialCard accent="gold" className="mt-6 p-5">
          <View className="flex-row items-center gap-4">
            <View className="h-14 w-14 items-center justify-center rounded-full" style={{ backgroundColor: colors.accentGold }}>
              <Text preset="h2" style={{ color: colors.bgDeep, fontFamily: fontFamily.displaySemi, fontStyle: 'italic' }}>
                {initials}
              </Text>
            </View>
            <View className="flex-1">
              <Text preset="h2">{user?.full_name ?? 'ATTREQ user'}</Text>
              <Text className="mt-1" color="textSecondary" preset="bodySmall">
                {user?.email}
              </Text>
            </View>
          </View>
          <View className="mt-5 flex-row gap-7 border-t pt-4" style={{ borderColor: colors.borderSoft }}>
            <View>
              <MonoLabel>Pieces</MonoLabel>
              <Text className="mt-1" preset="h2">-</Text>
            </View>
            <View>
              <MonoLabel>Worn</MonoLabel>
              <Text className="mt-1" preset="h2">-</Text>
            </View>
            <View>
              <MonoLabel>Streak</MonoLabel>
              <Text className="mt-1" color="accentGold" preset="h2" style={{ fontStyle: 'italic' }}>
                0d
              </Text>
            </View>
          </View>
        </EditorialCard>

        <View className="mt-7">
          <MonoLabel>Preferences</MonoLabel>
          <EditorialCard className="mt-3 overflow-hidden p-0">
            <Pressable className="flex-row items-center gap-3 border-b px-5 py-4" onPress={() => locationMutation.mutate()} style={{ borderColor: colors.borderSoft }}>
              <Ionicons color={colors.textSecondary} name="location-outline" size={18} />
              <View className="flex-1">
                <Text preset="bodySmall">{user?.saved_city ?? 'Location not set'}</Text>
                <MonoLabel>
                  {hasLocation ? `${user.saved_latitude?.toFixed(4)} - ${user.saved_longitude?.toFixed(4)}` : 'Coordinates pending'}
                </MonoLabel>
              </View>
              {locationMutation.isPending ? <MonoLabel color="accentGold">Saving</MonoLabel> : <QuietChevron />}
            </Pressable>
            <View className="flex-row items-center gap-3 border-b px-5 py-4" style={{ borderColor: colors.borderSoft }}>
              <Ionicons color={colors.textSecondary} name="notifications-outline" size={18} />
              <View className="flex-1">
                <Text preset="bodySmall">Daily reminder</Text>
                <MonoLabel>8:00 AM - weekdays</MonoLabel>
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
            </View>
            <View className="flex-row items-center gap-3 px-5 py-4">
              <Ionicons color={colors.textSecondary} name="shirt-outline" size={18} />
              <View className="flex-1">
                <Text preset="bodySmall">Style preferences</Text>
                <MonoLabel>{user?.style_preferences ?? 'Minimal - earthy - layered'}</MonoLabel>
              </View>
              <MonoLabel color="accentGold">Edit</MonoLabel>
            </View>
          </EditorialCard>
        </View>

        <Text
          className="mt-7 text-center"
          color="accentClay"
          onPress={async () => {
            await signOut()
            router.replace('/(auth)/login')
          }}
          preset="label"
        >
          Sign out
        </Text>
        <Text className="mt-3 text-center opacity-60" color="textTertiary" preset="label">
          v 1.4.2 - ATTREQ
        </Text>
      </ScrollView>
    </SafeAreaView>
  )
}
