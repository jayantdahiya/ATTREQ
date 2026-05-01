import { useEffect } from 'react'
import { View } from 'react-native'
import Animated, { Easing, useAnimatedStyle, useSharedValue, withRepeat, withTiming } from 'react-native-reanimated'

import { MonoLabel } from '@/components/attreq/editorial'
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
    <View className="flex-1 px-6 pt-20" style={{ backgroundColor: colors.bgDeep }}>
      <Animated.View style={animatedStyle}>
        <MonoLabel color="accentGold">{label}</MonoLabel>
      </Animated.View>
      <View className="mt-8 gap-4">
        <View className="h-3 w-32 rounded-full" style={{ backgroundColor: colors.bgSurface }} />
        <View className="h-8 w-56 rounded-xl" style={{ backgroundColor: colors.bgSurface }} />
        <View className="mt-4 h-16 rounded-2xl" style={{ backgroundColor: colors.bgSurface }} />
        <View className="h-72 rounded-3xl border p-4" style={{ backgroundColor: colors.bgSurface, borderColor: colors.borderSoft }}>
          <View className="h-3 w-28 rounded-full" style={{ backgroundColor: colors.bgRaised }} />
          <View className="mt-3 h-6 w-44 rounded-lg" style={{ backgroundColor: colors.bgRaised }} />
          <View className="mt-5 flex-1 flex-row gap-2">
            <View className="flex-[1.6] rounded-2xl" style={{ backgroundColor: colors.bgRaised }} />
            <View className="flex-1 gap-2">
              <View className="flex-[1.4] rounded-2xl" style={{ backgroundColor: colors.bgRaised }} />
              <View className="flex-1 rounded-2xl" style={{ backgroundColor: colors.bgRaised }} />
            </View>
          </View>
        </View>
      </View>
      <Text className="mt-8 text-center" color="accentGold" preset="wordmark">
        ATTREQ
      </Text>
    </View>
  )
}
