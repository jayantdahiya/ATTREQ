import { router, useLocalSearchParams } from 'expo-router'
import { useState } from 'react'
import { Alert, Pressable, ScrollView, View } from 'react-native'
import { SafeAreaView } from 'react-native-safe-area-context'

import { Text } from '@/components/ui/text'
import { StyleDnaCard } from '@/features/style-dna/components/style-dna-card'
import { FoundItemsCard } from '@/features/style-dna/components/found-items-card'
import type { DetectedWardrobeItem, StyleDna, StyleDnaUploadResponse } from '@/lib/api/types'
import { usersApi } from '@/lib/api/users'
import { useThemeColors } from '@/theme/colors'

export default function ResultsScreen() {
  const { colors } = useThemeColors()
  const { data } = useLocalSearchParams<{ data: string }>()
  const [isLoading, setIsLoading] = useState(false)

  const uploadResult: StyleDnaUploadResponse | null = data ? JSON.parse(data) : null
  const styleDna = uploadResult?.style_dna as StyleDna | null

  // Collect all detected items from photos
  const detectedItems: DetectedWardrobeItem[] = (uploadResult?.photos ?? []).flatMap((photo) => {
    const extraction = photo.per_photo_extraction as { wardrobe_items_detected?: DetectedWardrobeItem[] } | null
    return extraction?.wardrobe_items_detected ?? []
  })

  async function handleAddAll() {
    setIsLoading(true)
    try {
      await usersApi.completeOnboarding()
      router.replace('/(protected)/(tabs)')
    } catch (err) {
      Alert.alert('Error', err instanceof Error ? err.message : 'Something went wrong')
    } finally {
      setIsLoading(false)
    }
  }

  function handleReviewItems() {
    router.push({
      pathname: '/(onboarding)/review-items',
      params: { items: JSON.stringify(detectedItems) },
    })
  }

  if (!uploadResult || !styleDna) {
    return (
      <SafeAreaView className="flex-1 items-center justify-center" style={{ backgroundColor: colors.bgDeep }}>
        <Text style={{ color: colors.textMuted }}>No results found.</Text>
        <Pressable onPress={() => router.back()} className="mt-4">
          <Text style={{ color: colors.accentGold }}>Go back</Text>
        </Pressable>
      </SafeAreaView>
    )
  }

  return (
    <SafeAreaView className="flex-1" style={{ backgroundColor: colors.bgDeep }}>
      <ScrollView contentContainerStyle={{ padding: 24, paddingBottom: 130 }}>
        <Text className="text-2xl font-bold mt-4 mb-2" style={{ color: colors.textPrimary }}>
          Your Style DNA
        </Text>
        <Text className="text-sm mb-6" style={{ color: colors.textMuted }}>
          Based on {uploadResult.photos_processed} photo{uploadResult.photos_processed !== 1 ? 's' : ''}.
          {uploadResult.photos_skipped > 0 ? ` ${uploadResult.photos_skipped} skipped (low quality).` : ''}
        </Text>

        <StyleDnaCard styleDna={styleDna} />

        {detectedItems.length > 0 && (
          <FoundItemsCard
            items={detectedItems}
            onReview={handleReviewItems}
            onAddAll={handleAddAll}
            isLoading={isLoading}
          />
        )}

        {detectedItems.length === 0 && (
          <Pressable
            onPress={handleAddAll}
            disabled={isLoading}
            className="mt-6 rounded-2xl py-4 items-center"
            style={{ backgroundColor: colors.accentGold }}
          >
            <Text className="text-base font-semibold" style={{ color: colors.bgDeep }}>
              {isLoading ? 'Setting up…' : 'Looks right →'}
            </Text>
          </Pressable>
        )}
      </ScrollView>
    </SafeAreaView>
  )
}
