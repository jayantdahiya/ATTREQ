import { View } from 'react-native'

import { Text } from '@/components/ui/text'
import { useThemeColors } from '@/theme/colors'

interface ConfidenceBadgeProps {
  confidence: number
}

export function ConfidenceBadge({ confidence }: ConfidenceBadgeProps) {
  const { colors } = useThemeColors()

  if (confidence >= 0.6) return null

  return (
    <View
      className="rounded px-2 py-0.5"
      style={{ backgroundColor: colors.accentGold + '30' }}
    >
      <Text className="text-xs" style={{ color: colors.accentGold }}>
        Based on limited data
      </Text>
    </View>
  )
}
