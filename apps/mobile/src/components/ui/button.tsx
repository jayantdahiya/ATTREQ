import { type ReactNode, useEffect } from 'react'
import * as Haptics from 'expo-haptics'
import { Pressable, type PressableProps, View } from 'react-native'
import Animated, {
  Easing,
  useAnimatedStyle,
  useSharedValue,
  withRepeat,
  withTiming,
} from 'react-native-reanimated'

import { Text } from '@/components/ui/text'
import { cn } from '@/lib/utils/cn'
import { useThemeColors } from '@/theme/colors'

type ButtonVariant = 'primary' | 'secondary' | 'ghost' | 'danger' | 'premium'

interface ButtonProps extends Omit<PressableProps, 'children'> {
  variant?: ButtonVariant
  isLoading?: boolean
  label?: string
  icon?: ReactNode
  children?: ReactNode
}

const AnimatedView = Animated.createAnimatedComponent(View)

export function Button({
  children,
  className,
  disabled,
  icon,
  isLoading = false,
  label,
  onPress,
  onPressIn,
  onPressOut,
  variant = 'primary',
  ...props
}: ButtonProps) {
  const { colors } = useThemeColors()
  const scale = useSharedValue(1)
  const pulse = useSharedValue(0.4)

  useEffect(() => {
    if (isLoading) {
      pulse.value = withRepeat(withTiming(1, { duration: 700, easing: Easing.inOut(Easing.quad) }), -1, true)
    }
  }, [isLoading, pulse])

  const animatedStyle = useAnimatedStyle(() => ({
    transform: [{ scale: scale.value }],
  }))

  const pulseStyle = useAnimatedStyle(() => ({
    opacity: pulse.value,
  }))

  const content = typeof children === 'string' ? children : label

  const palette: Record<ButtonVariant, { bg: string; border: string; text: string }> = {
    primary: { bg: colors.accentMoss, border: colors.accentMoss, text: colors.textPrimary },
    secondary: { bg: colors.bgRaised, border: colors.borderSubtle, text: colors.textPrimary },
    ghost: { bg: 'transparent', border: 'transparent', text: colors.accentGold },
    danger: { bg: colors.accentClay, border: colors.accentClay, text: colors.textPrimary },
    premium: { bg: 'transparent', border: colors.accentGold, text: colors.accentGold },
  }

  return (
    <Pressable
      className={cn('overflow-hidden rounded-2xl', (disabled || isLoading) && 'opacity-60', className)}
      disabled={disabled || isLoading}
      onPress={async (event) => {
        try {
          await Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light)
        } catch {
          // no-op
        }
        onPress?.(event)
      }}
      onPressIn={(event) => {
        scale.value = withTiming(0.95, { duration: 80, easing: Easing.out(Easing.quad) })
        onPressIn?.(event)
      }}
      onPressOut={(event) => {
        scale.value = withTiming(1, { duration: 150, easing: Easing.out(Easing.quad) })
        onPressOut?.(event)
      }}
      {...props}
    >
      <AnimatedView
        className="min-h-12 flex-row items-center justify-center gap-2 border px-4 py-3"
        style={[animatedStyle, { backgroundColor: palette[variant].bg, borderColor: palette[variant].border }]}
      >
        {isLoading ? (
          <Animated.View className="h-2.5 w-2.5 rounded-full" style={[pulseStyle, { backgroundColor: colors.accentGold }]} />
        ) : (
          icon
        )}
        {content ? (
          <Text preset="bodySmall" style={{ color: palette[variant].text, fontFamily: 'DMSans_600SemiBold' }}>
            {content}
          </Text>
        ) : (
          children
        )}
      </AnimatedView>
    </Pressable>
  )
}
