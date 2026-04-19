import { Ionicons } from '@expo/vector-icons'
import { Image } from 'expo-image'
import { View } from 'react-native'

import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { Text } from '@/components/ui/text'
import { resolveApiImageUrl } from '@/lib/utils/images'
import type { OutfitSuggestion } from '@/lib/api/types'
import { useThemeColors } from '@/theme/colors'

interface RecommendationCardProps {
  suggestion: OutfitSuggestion
  isSubmitting?: boolean
  onWear: () => void
  onFeedback: (score: -1 | 1) => void
}

function RecommendationImage({
  label,
  uri,
}: {
  label: string
  uri?: string
}) {
  const { colors } = useThemeColors()

  return (
    <View className="flex-1 overflow-hidden rounded-2xl" style={{ backgroundColor: colors.bgRaised }}>
      {uri ? (
        <Image contentFit="cover" source={{ uri }} style={{ aspectRatio: 0.8, width: '100%' }} />
      ) : (
        <View className="aspect-[4/5] items-center justify-center" style={{ backgroundColor: colors.bgRaised }}>
          <Text color="textSecondary" preset="caption">
            {label}
          </Text>
        </View>
      )}
      <View className="px-3 py-2">
        <Text color="textTertiary" preset="label">
          {label}
        </Text>
      </View>
    </View>
  )
}

export function RecommendationCard({
  suggestion,
  isSubmitting = false,
  onWear,
  onFeedback,
}: RecommendationCardProps) {
  const { colors } = useThemeColors()

  return (
    <Card className="gap-4" onPress={onWear} variant="elevated">
      <View className="flex-row items-start justify-between gap-3">
        <View className="flex-1">
          <Text preset="h2">Today&apos;s Outfit</Text>
          <Text className="mt-1" color="textSecondary" preset="bodySmall">
            {suggestion.occasion_context} · score {suggestion.scores.total.toFixed(2)}
          </Text>
        </View>
        <Badge label={suggestion.weather_context.condition} variant="gold" />
      </View>

      <View className="flex-row gap-3">
        <RecommendationImage label="Top" uri={resolveApiImageUrl(suggestion.top_item.image_url ?? suggestion.top_item.thumbnail_url)} />
        <RecommendationImage
          label="Bottom"
          uri={resolveApiImageUrl(suggestion.bottom_item.image_url ?? suggestion.bottom_item.thumbnail_url)}
        />
        <RecommendationImage
          label="Accent"
          uri={resolveApiImageUrl(
            suggestion.accessory_item?.image_url ?? suggestion.accessory_item?.thumbnail_url
          )}
        />
      </View>

      <View className="rounded-2xl px-4 py-3" style={{ backgroundColor: colors.bgRaised }}>
        <Text preset="bodySmall" style={{ fontFamily: 'DMSans_600SemiBold' }}>
          {Math.round(suggestion.weather_context.temp)} C feels like {Math.round(suggestion.weather_context.feels_like)} C
        </Text>
        <Text className="mt-1" color="textSecondary" preset="bodySmall">
          {suggestion.weather_context.description}
        </Text>
      </View>

      <View className="flex-row gap-3">
        <Button
          className="flex-1"
          icon={<Ionicons color={colors.textPrimary} name="checkmark-circle-outline" size={17} />}
          isLoading={isSubmitting}
          label="Wear this"
          onPress={onWear}
        />
        <Button
          className="flex-1"
          disabled={isSubmitting}
          icon={<Ionicons color={colors.accentGold} name="heart-outline" size={17} />}
          label="Like"
          onPress={() => onFeedback(1)}
          variant="ghost"
        />
        <Button
          className="flex-1"
          disabled={isSubmitting}
          icon={<Ionicons color={colors.textSecondary} name="close-outline" size={19} />}
          label="Skip"
          onPress={() => onFeedback(-1)}
          variant="secondary"
        />
      </View>
    </Card>
  )
}
