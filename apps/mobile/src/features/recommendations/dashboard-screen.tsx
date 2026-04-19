import { Ionicons } from '@expo/vector-icons'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import * as Location from 'expo-location'
import { useState } from 'react'
import { Alert, RefreshControl, ScrollView, View } from 'react-native'
import { SafeAreaView } from 'react-native-safe-area-context'

import { EmptyState } from '@/components/common/empty-state'
import { LoadingScreen } from '@/components/common/loading-screen'
import { ScreenHeader } from '@/components/common/screen-header'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
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
    return (
      <SafeAreaView className="flex-1" style={{ backgroundColor: colors.bgDeep }}>
        <ScrollView contentContainerStyle={{ padding: 24 }}>
          <ScreenHeader
            heading="Weather-aware recommendations need a location first."
            label="TODAY"
            subtitle="ATTREQ can use your current coordinates and store them on your profile for future refreshes."
          />

          <Card className="mt-8 gap-4" variant="premium">
            <Text preset="h3">Set your location</Text>
            <Text color="textSecondary" preset="bodySmall">
              This v1 client uses device coordinates and the backend&apos;s saved-location fallback. Manual city geocoding is intentionally deferred.
            </Text>
            <Button
              icon={<Ionicons color={colors.textPrimary} name="location-outline" size={17} />}
              isLoading={locationMutation.isPending}
              label="Use current location"
              onPress={() => locationMutation.mutate()}
            />
          </Card>
        </ScrollView>
      </SafeAreaView>
    )
  }

  const suggestions = recommendationsQuery.data?.suggestions ?? []

  return (
    <SafeAreaView className="flex-1" style={{ backgroundColor: colors.bgDeep }}>
      <ScrollView
        className="flex-1"
        contentContainerStyle={{ padding: 24, paddingBottom: 120 }}
        refreshControl={
          <RefreshControl
            refreshing={recommendationsQuery.isRefetching}
            tintColor={colors.accentGold}
            onRefresh={() => recommendationsQuery.refetch()}
          />
        }
      >
        <ScreenHeader
          heading={isUsingDeviceLocation ? 'Fresh from your current weather.' : 'Built from your saved location.'}
          label="TODAY"
          subtitle={recommendationsQuery.data?.weather.description ?? 'Pulling the latest conditions for your wardrobe.'}
        />

        <View className="mt-5 flex-row flex-wrap gap-2">
          {recommendationsQuery.data?.weather?.temp != null ? (
            <Badge label={`${Math.round(recommendationsQuery.data.weather.temp)} C`} variant="moss" />
          ) : null}
          {recommendationsQuery.data?.weather?.condition ? (
            <Badge label={recommendationsQuery.data.weather.condition} variant="gold" />
          ) : null}
        </View>

        <View className="mt-6 flex-row gap-3">
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
              title="No suggestions yet"
              message="Add a few more wardrobe items so ATTREQ can build complete outfits."
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
      </ScrollView>
    </SafeAreaView>
  )
}
