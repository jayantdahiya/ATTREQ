import { memo } from 'react'
import { View } from 'react-native'

import { Badge } from '@/components/ui/badge'
import { Card } from '@/components/ui/card'
import { Text } from '@/components/ui/text'
import type { Outfit } from '@/lib/api/types'

function OutfitHistoryCardComponent({ outfit }: { outfit: Outfit }) {
  const feedbackLabel = outfit.feedback_score === 1 ? 'liked' : outfit.feedback_score === -1 ? 'skipped' : 'tracked'

  return (
    <Card className="gap-3 px-4 py-4" variant="default">
      <View className="flex-row items-center justify-between">
        <Text preset="h3">{outfit.occasion_context ?? 'Saved outfit'}</Text>
        <Badge label={feedbackLabel} variant={feedbackLabel === 'liked' ? 'moss' : feedbackLabel === 'skipped' ? 'clay' : 'muted'} />
      </View>
      <Text color="textSecondary" preset="bodySmall">
        Top: {outfit.top_item_id ?? 'n/a'} · Bottom: {outfit.bottom_item_id ?? 'n/a'}
      </Text>
      <Text color="textTertiary" preset="mono">
        {outfit.worn_date ? `Worn on ${outfit.worn_date}` : 'Not marked worn yet'}
      </Text>
    </Card>
  )
}

export const OutfitHistoryCard = memo(OutfitHistoryCardComponent)
