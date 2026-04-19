import { useEffect } from 'react'
import { View, type ViewStyle } from 'react-native'
import { LinearGradient } from 'expo-linear-gradient'
import Animated, {
  Easing,
  useAnimatedStyle,
  useSharedValue,
  withRepeat,
  withTiming,
} from 'react-native-reanimated'

import { useThemeColors } from '@/theme/colors'

const AnimatedGradient = Animated.createAnimatedComponent(LinearGradient)

interface ShimmerProps {
  width: number | string
  height: number
  borderRadius?: number
}

export function Shimmer({ width, height, borderRadius = 12 }: ShimmerProps) {
  const { colors } = useThemeColors()
  const offset = useSharedValue(-1)

  useEffect(() => {
    offset.value = withRepeat(withTiming(1, { duration: 1200, easing: Easing.linear }), -1, false)
  }, [offset])

  const animatedStyle = useAnimatedStyle(() => ({
    transform: [{ translateX: `${offset.value * 220}%` as never }],
  }))

  const shellStyle: ViewStyle = {
    width: width as never,
    height,
    borderRadius,
    backgroundColor: colors.bgSurface,
    overflow: 'hidden',
  }

  return (
    <View style={shellStyle}>
      <AnimatedGradient
        colors={['transparent', colors.bgRaised, 'transparent']}
        end={{ x: 1, y: 0 }}
        start={{ x: 0, y: 0 }}
        style={[{ width: '60%', height: '100%', opacity: 0.55 }, animatedStyle]}
      />
    </View>
  )
}
