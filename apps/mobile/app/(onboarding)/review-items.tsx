import { router, useLocalSearchParams } from 'expo-router'
import { useState } from 'react'
import { Alert, Pressable, ScrollView, View } from 'react-native'
import { SafeAreaView } from 'react-native-safe-area-context'

import { Text } from '@/components/ui/text'
import { ItemReviewCard } from '@/features/style-dna/components/item-review-card'
import type { DetectedWardrobeItem } from '@/lib/api/types'
import { wardrobeApi } from '@/lib/api/wardrobe'
import { usersApi } from '@/lib/api/users'
import { useThemeColors } from '@/theme/colors'

export default function ReviewItemsScreen() {
  const { colors } = useThemeColors()
  const { items: itemsJson } = useLocalSearchParams<{ items: string }>()

  const allItems: DetectedWardrobeItem[] = itemsJson ? JSON.parse(itemsJson) : []
  const [pendingItems, setPendingItems] = useState<DetectedWardrobeItem[]>(allItems)
  const [confirmedItems, setConfirmedItems] = useState<DetectedWardrobeItem[]>([])
  const [isFinishing, setIsFinishing] = useState(false)

  const current = pendingItems[0]

  async function finishReview(finalConfirmed: DetectedWardrobeItem[]) {
    setIsFinishing(true)
    try {
      // Items were already seeded server-side; remove ones the user rejected
      // by just proceeding — no extra bulk call needed
      await usersApi.completeOnboarding()
      router.replace('/(protected)/(tabs)')
    } catch (err) {
      Alert.alert('Error', err instanceof Error ? err.message : 'Something went wrong')
      setIsFinishing(false)
    }
  }

  function handleConfirm() {
    const [head, ...rest] = pendingItems
    const updated = [...confirmedItems, head]
    if (rest.length === 0) {
      void finishReview(updated)
    } else {
      setConfirmedItems(updated)
      setPendingItems(rest)
    }
  }

  function handleRemove() {
    const [, ...rest] = pendingItems
    if (rest.length === 0) {
      void finishReview(confirmedItems)
    } else {
      setPendingItems(rest)
    }
  }

  function handleSkipAll() {
    void finishReview([...confirmedItems, ...pendingItems])
  }

  if (!current || isFinishing) {
    return (
      <SafeAreaView className="flex-1 items-center justify-center" style={{ backgroundColor: colors.bgDeep }}>
        <Text style={{ color: colors.textMuted }}>
          {isFinishing ? 'Setting up your wardrobe…' : 'All done!'}
        </Text>
      </SafeAreaView>
    )
  }

  return (
    <SafeAreaView className="flex-1" style={{ backgroundColor: colors.bgDeep }}>
      <ScrollView contentContainerStyle={{ padding: 24, paddingBottom: 130 }}>
        <Text className="text-2xl font-bold mt-4 mb-6" style={{ color: colors.textPrimary }}>
          Review your items
        </Text>

        <ItemReviewCard
          item={current}
          index={allItems.length - pendingItems.length}
          total={allItems.length}
          onConfirm={handleConfirm}
          onRemove={handleRemove}
          onSkipAll={handleSkipAll}
        />

        <Text className="text-xs text-center mt-6" style={{ color: colors.textMuted }}>
          You can edit any item later from your wardrobe.
        </Text>
      </ScrollView>
    </SafeAreaView>
  )
}
