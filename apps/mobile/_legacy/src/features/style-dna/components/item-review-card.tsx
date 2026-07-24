import { Pressable, View } from 'react-native'

import { Text } from '@/components/ui/text'
import type { DetectedWardrobeItem } from '@/lib/api/types'
import { useThemeColors } from '@/theme/colors'

interface ItemReviewCardProps {
  item: DetectedWardrobeItem
  index: number
  total: number
  onConfirm: () => void
  onRemove: () => void
  onSkipAll: () => void
}

type ChipProps = { label: string; active?: boolean; onPress?: () => void }

function Chip({ label, active, onPress }: ChipProps) {
  const { colors } = useThemeColors()
  return (
    <Pressable
      onPress={onPress}
      className="rounded-full px-3 py-1.5"
      style={{
        backgroundColor: active ? colors.accentGold : colors.borderSubtle,
      }}
    >
      <Text className="text-xs font-medium" style={{ color: active ? colors.bgDeep : colors.textPrimary }}>
        {label}
      </Text>
    </Pressable>
  )
}

export function ItemReviewCard({ item, index, total, onConfirm, onRemove, onSkipAll }: ItemReviewCardProps) {
  const { colors } = useThemeColors()

  return (
    <View
      className="rounded-2xl p-5"
      style={{ backgroundColor: colors.cardBg, borderColor: colors.borderSubtle, borderWidth: 1 }}
    >
      {/* Header */}
      <View className="flex-row items-center justify-between mb-4">
        <Text className="text-sm" style={{ color: colors.textMuted }}>
          Item {index + 1} of {total}
        </Text>
        <Pressable onPress={onSkipAll}>
          <Text className="text-sm" style={{ color: colors.accentGold }}>
            Skip all →
          </Text>
        </Pressable>
      </View>

      {/* Item placeholder */}
      <View
        className="h-32 rounded-xl mb-4 items-center justify-center"
        style={{ backgroundColor: colors.borderSubtle }}
      >
        <Text className="text-3xl">👕</Text>
        <Text className="text-xs mt-1" style={{ color: colors.textMuted }}>
          {item.bounding_region}
        </Text>
      </View>

      {/* Category */}
      <View className="mb-3">
        <Text className="text-xs font-medium mb-1.5" style={{ color: colors.textMuted }}>
          Category
        </Text>
        <View className="flex-row flex-wrap gap-2">
          <Chip label={item.subcategory || item.category} active />
          <Chip label={item.category} active={!item.subcategory} />
        </View>
      </View>

      {/* Colour */}
      {item.color_primary && (
        <View className="mb-3">
          <Text className="text-xs font-medium mb-1.5" style={{ color: colors.textMuted }}>
            Colour
          </Text>
          <View className="flex-row flex-wrap gap-2">
            <Chip label={item.color_primary} active />
            {item.color_secondary && <Chip label={item.color_secondary} />}
          </View>
        </View>
      )}

      {/* Pattern */}
      {item.pattern && (
        <View className="mb-4">
          <Text className="text-xs font-medium mb-1.5" style={{ color: colors.textMuted }}>
            Pattern
          </Text>
          <View className="flex-row flex-wrap gap-2">
            <Chip label={item.pattern} active />
          </View>
        </View>
      )}

      {/* Actions */}
      <View className="flex-row gap-3 mt-2">
        <Pressable
          onPress={onRemove}
          className="flex-1 items-center rounded-xl py-3"
          style={{ borderColor: colors.borderSubtle, borderWidth: 1 }}
        >
          <Text className="text-sm font-medium" style={{ color: colors.textMuted }}>
            × Remove
          </Text>
        </Pressable>
        <Pressable
          onPress={onConfirm}
          className="flex-1 items-center rounded-xl py-3"
          style={{ backgroundColor: colors.accentGold }}
        >
          <Text className="text-sm font-semibold" style={{ color: colors.bgDeep }}>
            ✓ Looks right
          </Text>
        </Pressable>
      </View>
    </View>
  )
}
