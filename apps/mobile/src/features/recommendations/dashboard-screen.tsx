import { Ionicons } from '@expo/vector-icons'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import * as Location from 'expo-location'
import { useState } from 'react'
import { Alert, RefreshControl, ScrollView, View } from 'react-native'
import { SafeAreaView } from 'react-native-safe-area-context'

import { AppSurface, EditorialCard, EditorialHeader, IconCircle, MonoLabel, WeatherStrip, fontFamily } from '@/components/attreq/editorial'
import { EmptyState } from '@/components/common/empty-state'
import { LoadingScreen } from '@/components/common/loading-screen'
import { Button } from '@/components/ui/button'
import { Text } from '@/components/ui/text'
import { outfitsApi } from '@/lib/api/outfits'
import { recommendationsApi } from '@/lib/api/recommendations'
import { authApi } from '@/lib/api/auth'
import { usersApi } from '@/lib/api/users'
import { queryKeys } from '@/lib/query/query-client'
import { RecommendationCard } from '@/features/recommendations/recommendation-card'
import { useThemeColors } from '@/theme/colors'

function formatRecommendationKey(topItemId: string, bottomItemId: string) {
  return `${topItemId}:${bottomItemId}`
}

function LocationPermissionState({
  isLoading,
  onAllow,
}: {
  isLoading: boolean
  onAllow: () => void
}) {
  const { colors } = useThemeColors()

  return (
    <AppSurface scroll={false} contentClassName="flex-1 px-7">
      <View className="pt-4">
        <MonoLabel>Step 02</MonoLabel>
      </View>
      <View className="flex-1 items-center justify-center pb-20">
        <View className="h-44 w-44 items-center justify-center rounded-full border" style={{ borderColor: colors.borderSoft, backgroundColor: colors.glowMoss }}>
          <View className="h-28 w-28 items-center justify-center rounded-full border border-dashed" style={{ borderColor: colors.mossSoft }}>
            <View className="h-16 w-16 items-center justify-center rounded-full" style={{ backgroundColor: colors.accentMoss }}>
              <Ionicons color="#F0EDE6" name="location-outline" size={28} />
            </View>
          </View>
        </View>
        <Text className="mt-12 text-center" preset="display">
          The weather decides{'\n'}
          <Text color="accentGold" preset="display" style={{ fontFamily: fontFamily.displaySemi, fontStyle: 'italic' }}>
            before you do.
          </Text>
        </Text>
        <Text className="mt-4 max-w-[300px] text-center" color="textSecondary" preset="bodySmall">
          Share your location and we&apos;ll pair tomorrow&apos;s looks to tomorrow&apos;s sky.
        </Text>
      </View>
      <View className="pb-10">
        <Button
          icon={<Ionicons color="#1A1410" name="location-outline" size={17} />}
          isLoading={isLoading}
          label="Allow location access"
          onPress={onAllow}
          variant="premium"
        />
        <Text className="mt-4 text-center" color="textTertiary" preset="label">
          Maybe later
        </Text>
      </View>
    </AppSurface>
  )
}

export function DashboardScreen() {
  const { colors } = useThemeColors()
  const queryClient = useQueryClient()
  const [isUsingDeviceLocation, setIsUsingDeviceLocation] = useState(false)
  const [currentCoords, setCurrentCoords] = useState<{ lat: number; lon: number } | null>(null)
  const [persistedOutfits, setPersistedOutfits] = useState<Record<string, string>>({})

  const currentUserQuery = useQuery({
    queryKey: queryKeys.me,
    queryFn: authApi.getCurrentUser,
  })

  const hasSavedLocation = Boolean(
    currentUserQuery.data?.saved_latitude != null && currentUserQuery.data?.saved_longitude != null
  )

  const recommendationsQuery = useQuery({
    enabled: currentUserQuery.isSuccess && (hasSavedLocation || currentCoords !== null),
    queryKey: queryKeys.recommendations(
      JSON.stringify({
        lat: currentCoords?.lat ?? null,
        lon: currentCoords?.lon ?? null,
        saved: hasSavedLocation,
      })
    ),
    queryFn: () =>
      recommendationsApi.getDailySuggestions({
        occasion: 'casual',
        lat: currentCoords?.lat,
        lon: currentCoords?.lon,
      }),
  })

  const persistSuggestionMutation = useMutation({
    mutationFn: outfitsApi.createFromSuggestion,
  })

  const wearMutation = useMutation({
    mutationFn: async ({
      suggestionKey,
      suggestion,
    }: {
      suggestionKey: string
      suggestion: Parameters<typeof outfitsApi.createFromSuggestion>[0]
    }) => {
      const existingOutfitId = persistedOutfits[suggestionKey]
      const outfit = existingOutfitId ? { id: existingOutfitId } : await outfitsApi.createFromSuggestion(suggestion)

      if (!existingOutfitId) {
        setPersistedOutfits((current) => ({ ...current, [suggestionKey]: outfit.id }))
      }

      return outfitsApi.markAsWorn(outfit.id, new Date().toISOString().slice(0, 10))
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: queryKeys.outfits })
      Alert.alert('Outfit tracked', 'That look has been saved to your outfit history.')
    },
    onError: (error: Error) => {
      Alert.alert('Unable to track outfit', error.message)
    },
  })

  const feedbackMutation = useMutation({
    mutationFn: async ({
      score,
      suggestion,
      suggestionKey,
    }: {
      score: -1 | 1
      suggestion: Parameters<typeof outfitsApi.createFromSuggestion>[0]
      suggestionKey: string
    }) => {
      const existingOutfitId = persistedOutfits[suggestionKey]
      const outfit = existingOutfitId ? { id: existingOutfitId } : await outfitsApi.createFromSuggestion(suggestion)

      if (!existingOutfitId) {
        setPersistedOutfits((current) => ({ ...current, [suggestionKey]: outfit.id }))
      }

      return outfitsApi.submitFeedback(outfit.id, score)
    },
    onSuccess: async (_, variables) => {
      await queryClient.invalidateQueries({ queryKey: queryKeys.outfits })
      Alert.alert(
        variables.score === 1 ? 'Saved as a good fit' : 'Feedback recorded',
        variables.score === 1 ? 'We will bias toward outfits like this.' : 'We will steer away from looks like this.'
      )
    },
    onError: (error: Error) => {
      Alert.alert('Unable to save feedback', error.message)
    },
  })

  const locationMutation = useMutation({
    mutationFn: async () => {
      const permission = await Location.requestForegroundPermissionsAsync()
      if (!permission.granted) {
        throw new Error('Location permission is required to fetch weather-aware recommendations.')
      }

      const location = await Location.getCurrentPositionAsync({})
      const geocode = await Location.reverseGeocodeAsync(location.coords)
      const city = geocode[0]?.city ?? undefined

      await usersApi.updateLocation({
        lat: location.coords.latitude,
        lon: location.coords.longitude,
        city,
      })

      setCurrentCoords({
        lat: location.coords.latitude,
        lon: location.coords.longitude,
      })
      setIsUsingDeviceLocation(true)

      await queryClient.invalidateQueries({ queryKey: queryKeys.me })
      return location
    },
    onError: (error: Error) => {
      Alert.alert('Location unavailable', error.message)
    },
  })

  if (currentUserQuery.isLoading) {
    return <LoadingScreen label="Loading your profile" />
  }

  if (currentUserQuery.isError) {
    return (
      <SafeAreaView className="flex-1" style={{ backgroundColor: colors.bgDeep }}>
        <View className="flex-1 px-6 pt-8">
          <EmptyState title="Session check failed" message="Refresh your session by signing in again." />
        </View>
      </SafeAreaView>
    )
  }

  if (!hasSavedLocation && !currentCoords) {
    return <LocationPermissionState isLoading={locationMutation.isPending} onAllow={() => locationMutation.mutate()} />
  }

  const suggestions = recommendationsQuery.data?.suggestions ?? []
  const userName = currentUserQuery.data?.full_name?.split(' ')[0] ?? 'there'
  const city = currentUserQuery.data?.saved_city ?? (isUsingDeviceLocation ? 'Current location' : 'Saved location')

  return (
    <SafeAreaView className="flex-1" style={{ backgroundColor: colors.bgDeep }}>
      <ScrollView
        className="flex-1"
        contentContainerStyle={{ padding: 24, paddingBottom: 130 }}
        refreshControl={
          <RefreshControl
            refreshing={recommendationsQuery.isRefetching}
            tintColor={colors.accentGold}
            title="Weaving today's looks..."
            titleColor={colors.accentGold}
            onRefresh={() => recommendationsQuery.refetch()}
          />
        }
      >
        <EditorialHeader
          label={new Intl.DateTimeFormat('en', { weekday: 'long', month: '2-digit', day: '2-digit' }).format(new Date())}
          right={
            <IconCircle onPress={() => recommendationsQuery.refetch()}>
              <Ionicons color={colors.textSecondary} name="reorder-three-outline" size={18} />
            </IconCircle>
          }
          title={
            <>
              Good morning,{'\n'}
              <Text color="accentGold" preset="h1" style={{ fontFamily: fontFamily.displaySemi, fontStyle: 'italic' }}>
                {userName}.
              </Text>
            </>
          }
        />

        <WeatherStrip
          city={city}
          condition={recommendationsQuery.data?.weather.description}
          temp={recommendationsQuery.data?.weather.temp}
        />

        <View className="mt-6 flex-row items-center justify-between">
          <Text preset="h2" style={{ fontFamily: fontFamily.displaySemi, fontStyle: 'italic' }}>
            Today&apos;s looks
          </Text>
          <MonoLabel>{suggestions.length} looks</MonoLabel>
        </View>

        <View className="mt-4 flex-row gap-3">
          <Button
            icon={<Ionicons color={colors.textPrimary} name="refresh-outline" size={17} />}
            label="Refresh"
            onPress={() => recommendationsQuery.refetch()}
            variant="secondary"
          />
          <Button
            icon={<Ionicons color={colors.accentGold} name="navigate-outline" size={17} />}
            isLoading={locationMutation.isPending}
            label={isUsingDeviceLocation ? 'Refresh location' : 'Use device location'}
            onPress={() => locationMutation.mutate()}
            variant="ghost"
          />
        </View>

        {recommendationsQuery.isLoading ? (
          <View className="mt-8">
            <LoadingScreen label="Generating your outfit suggestions" />
          </View>
        ) : null}

        {!recommendationsQuery.isLoading && suggestions.length === 0 ? (
          <View className="mt-8">
            <EmptyState
              title="An empty closet, a quiet morning."
              message="Add a few favorites and we will start composing looks. Five pieces is enough to begin."
              icon={
                <View className="items-center gap-1 opacity-60">
                  {[0, 1, 2].map((i) => (
                    <View key={i} style={{ backgroundColor: colors.bgRaised, borderRadius: 4, height: 14, width: 118 - i * 12 }} />
                  ))}
                </View>
              }
            />
          </View>
        ) : null}

        <View className="mt-8 gap-5">
          {suggestions.map((suggestion) => {
            const suggestionKey = formatRecommendationKey(suggestion.top_item_id, suggestion.bottom_item_id)

            return (
              <RecommendationCard
                key={suggestionKey}
                suggestion={suggestion}
                isSubmitting={
                  wearMutation.isPending || feedbackMutation.isPending || persistSuggestionMutation.isPending
                }
                onWear={() => wearMutation.mutate({ suggestionKey, suggestion })}
                onFeedback={(score) => feedbackMutation.mutate({ score, suggestion, suggestionKey })}
              />
            )
          })}
        </View>

        {suggestions.length > 0 ? (
          <EditorialCard accent="gold" className="mt-5">
            <MonoLabel color="accentGold">Motion note</MonoLabel>
            <Text className="mt-2" color="textSecondary" preset="bodySmall">
              Pull down to weave new looks from weather, wardrobe, and recent feedback.
            </Text>
          </EditorialCard>
        ) : null}
      </ScrollView>
    </SafeAreaView>
  )
}
