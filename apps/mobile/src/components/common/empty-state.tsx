import type { ReactNode } from 'react'
import { View } from 'react-native'
import Animated, { FadeIn, ZoomIn } from 'react-native-reanimated'

import { Text } from '@/components/ui/text'
import { useThemeColors } from '@/theme/colors'

export function EmptyState({
  icon,
  message,
  title,
}: {
  icon?: ReactNode
  title: string
  message: string
}) {
  const { colors } = useThemeColors()

  return (
    <Animated.View
      entering={FadeIn.duration(380)}
      style={{
        borderColor: colors.accentGold,
        backgroundColor: colors.bgSurface,
        borderRadius: 24,
        borderStyle: 'dashed',
        borderWidth: 1,
        paddingHorizontal: 20,
        paddingVertical: 26,
      }}
    >
      <Animated.View entering={ZoomIn.duration(380)}>
        {icon ? <View className="mb-3">{icon}</View> : null}
        <Text preset="h2">{title}</Text>
        <Text className="mt-2" color="textSecondary" preset="bodySmall">
          {message}
        </Text>
      </Animated.View>
    </Animated.View>
  )
}
