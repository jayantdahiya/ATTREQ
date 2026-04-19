import { memo } from 'react'
import { Image } from 'expo-image'
import { View } from 'react-native'

import { Badge } from '@/components/ui/badge'
import { Card } from '@/components/ui/card'
import { Text } from '@/components/ui/text'
import { resolveApiImageUrl } from '@/lib/utils/images'
import type { WardrobeItem } from '@/lib/api/types'
import { useThemeColors } from '@/theme/colors'

function WardrobeItemCardComponent({ item }: { item: WardrobeItem }) {
  const { colors } = useThemeColors()
  const imageUri = resolveApiImageUrl(item.thumbnail_url ?? item.processed_image_url ?? item.original_image_url)

  return (
    <Card className="flex-row gap-4 px-4 py-4" onPress={() => undefined} variant="default">
      <Image
        contentFit="cover"
        source={imageUri ? { uri: imageUri } : undefined}
        style={{ width: 96, height: 120, borderRadius: 16, backgroundColor: colors.bgRaised }}
      />
      <View className="flex-1 justify-between">
        <View>
          <Text className="capitalize" preset="h3">
            {item.category ?? 'Processing item'}
          </Text>
          <Text className="mt-1 capitalize" color="textSecondary" preset="bodySmall">
            {item.color_primary ?? 'Color pending'} · {item.pattern ?? 'Pattern pending'}
          </Text>
        </View>
        <View className="flex-row items-center justify-between">
          <Badge label={item.processing_status} variant={item.processing_status === 'completed' ? 'moss' : 'gold'} />
          <Text color="textTertiary" preset="mono">
            Worn {item.wear_count}x
          </Text>
        </View>
      </View>
    </Card>
  )
}

export const WardrobeItemCard = memo(WardrobeItemCardComponent)
