import { Pressable, View } from 'react-native'

import { Text } from '@/components/ui/text'
import type { DetectedWardrobeItem } from '@/lib/api/types'
import { useThemeColors } from '@/theme/colors'

interface FoundItemsCardProps {
  items: DetectedWardrobeItem[]
  onReview: () => void
  onAddAll: () => void
  isLoading?: boolean
}

export function FoundItemsCard({ items, onReview, onAddAll, isLoading }: FoundItemsCardProps) {
  const { colors } = useThemeColors()

  const preview = items
    .slice(0, 3)
    .map((i) => `${i.color_primary ?? ''} ${i.subcategory ?? i.category}`.trim())
    .join(' · ')
  const remaining = items.length - 3

  return (
    <View
      className="rounded-2xl p-5 mt-4"
      style={{ backgroundColor: colors.cardBg, borderColor: colors.borderSubtle, borderWidth: 1 }}
    >
      <Text className="text-base font-semibold mb-1" style={{ color: colors.textPrimary }}>
        👕 We found {items.length} items in your photos
      </Text>
      <Text className="text-sm mb-4" style={{ color: colors.textMuted }}>
        {preview}
        {remaining > 0 ? ` · +${remaining} more` : ''}
      </Text>

      <View className="flex-row gap-3">
        <Pressable
          onPress={onReview}
          className="flex-1 items-center rounded-xl py-3"
          style={{ borderColor: colors.borderSubtle, borderWidth: 1 }}
        >
          <Text className="text-sm font-medium" style={{ color: colors.textPrimary }}>
            Review items
          </Text>
        </Pressable>
        <Pressable
          onPress={onAddAll}
          disabled={isLoading}
          className="flex-1 items-center rounded-xl py-3"
          style={{ backgroundColor: colors.accentGold }}
        >
          <Text className="text-sm font-semibold" style={{ color: colors.bgDeep }}>
            {isLoading ? 'Adding…' : 'Add all →'}
          </Text>
        </Pressable>
      </View>
    </View>
  )
}
