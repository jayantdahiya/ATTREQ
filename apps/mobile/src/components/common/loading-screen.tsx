import { useEffect } from 'react'
import { View } from 'react-native'
import Animated, { Easing, useAnimatedStyle, useSharedValue, withRepeat, withTiming } from 'react-native-reanimated'

import { Text } from '@/components/ui/text'
import { useThemeColors } from '@/theme/colors'

export function LoadingScreen({ label }: { label: string }) {
  const { colors } = useThemeColors()
  const opacity = useSharedValue(0.5)

  useEffect(() => {
    opacity.value = withRepeat(withTiming(1, { duration: 900, easing: Easing.inOut(Easing.quad) }), -1, true)
  }, [opacity])

  const animatedStyle = useAnimatedStyle(() => ({
    opacity: opacity.value,
  }))

  return (
    <View className="flex-1 items-center justify-center px-6" style={{ backgroundColor: colors.bgDeep }}>
      <Animated.View style={animatedStyle}>
        <Text color="accentGold" preset="display">
          ATTREQ
        </Text>
      </Animated.View>
      <Text className="mt-4 text-center" color="textSecondary" preset="bodySmall">
        {label}
      </Text>
    </View>
  )
}
