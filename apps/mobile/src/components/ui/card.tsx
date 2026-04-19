import { type ReactNode } from 'react'
import { Pressable, View, type PressableProps, type ViewProps } from 'react-native'
import Animated, { Easing, useAnimatedStyle, useSharedValue, withTiming } from 'react-native-reanimated'

import { cn } from '@/lib/utils/cn'
import { useThemeColors } from '@/theme/colors'

type CardVariant = 'default' | 'elevated' | 'outlined' | 'premium'

interface CardProps extends Omit<ViewProps, 'children'> {
  children: ReactNode
  variant?: CardVariant
  onPress?: PressableProps['onPress']
}

const AnimatedView = Animated.createAnimatedComponent(View)

export function Card({ children, className, onPress, variant = 'default', ...props }: CardProps) {
  const { colors } = useThemeColors()
  const scale = useSharedValue(1)
  const animatedStyle = useAnimatedStyle(() => ({
    transform: [{ scale: scale.value }],
  }))

  const surfaceStyle: Record<CardVariant, { bg: string; border: string; topAccent?: string; shadow: string }> = {
    default: { bg: colors.bgSurface, border: colors.borderSubtle, shadow: colors.glowMoss },
    elevated: { bg: colors.bgRaised, border: colors.borderSubtle, shadow: colors.glowMoss },
    outlined: { bg: 'transparent', border: colors.borderSubtle, shadow: 'transparent' },
    premium: { bg: colors.bgSurface, border: colors.borderSubtle, topAccent: colors.accentGold, shadow: colors.glowGold },
  }

  const content = (
    <AnimatedView
      className={cn('overflow-hidden rounded-3xl border p-5', className)}
      style={[
        animatedStyle,
        {
          backgroundColor: surfaceStyle[variant].bg,
          borderColor: surfaceStyle[variant].border,
          shadowColor: surfaceStyle[variant].shadow,
          shadowOpacity: 0.35,
          shadowRadius: 18,
          shadowOffset: { width: 0, height: 8 },
          elevation: 5,
        },
      ]}
      {...props}
    >
      {surfaceStyle[variant].topAccent ? (
        <View
          pointerEvents="none"
          style={{
            backgroundColor: surfaceStyle[variant].topAccent,
            height: 2,
            left: 0,
            position: 'absolute',
            right: 0,
            top: 0,
          }}
        />
      ) : null}
      {children}
    </AnimatedView>
  )

  if (!onPress) {
    return content
  }

  return (
    <Pressable
      onPress={onPress}
      onPressIn={() => {
        scale.value = withTiming(0.97, { duration: 100, easing: Easing.out(Easing.quad) })
      }}
      onPressOut={() => {
        scale.value = withTiming(1, { duration: 200, easing: Easing.out(Easing.quad) })
      }}
    >
      {content}
    </Pressable>
  )
}
