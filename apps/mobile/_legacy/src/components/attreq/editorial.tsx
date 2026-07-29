import { Ionicons } from '@expo/vector-icons'
import { Image } from 'expo-image'
import { LinearGradient } from 'expo-linear-gradient'
import type { ReactNode } from 'react'
import { Pressable, ScrollView, View, type ViewProps } from 'react-native'
import Animated, { Easing, FadeInDown } from 'react-native-reanimated'
import { SafeAreaView } from 'react-native-safe-area-context'

import { Text } from '@/components/ui/text'
import { cn } from '@/lib/utils/cn'
import { useThemeColors, type ThemeColors } from '@/theme/colors'
import { fontFamily } from '@/theme/typography'

type Accent = 'gold' | 'moss' | 'clay' | 'muted'

const garmentTones = {
  top: ['#3A4A3E', '#2A3A2E', '#6F8B57'],
  bottom: ['#2A2620', '#1A1612', '#8A6F4A'],
  accent: ['#5A3E2E', '#4A2E1E', '#C9604A'],
  shoes: ['#1A1A18', '#0A0A08', '#5C5850'],
  outer: ['#3E3A30', '#2E2A20', '#D4A854'],
  bag: ['#4A3E2A', '#3A2E1A', '#A8842F'],
} as const

export type GarmentTone = keyof typeof garmentTones

export function AppSurface({
  children,
  scroll = true,
  contentClassName,
  contentStyle,
}: {
  children: ReactNode
  scroll?: boolean
  contentClassName?: string
  contentStyle?: ViewProps['style']
}) {
  const { colors } = useThemeColors()

  const content = (
    <View className={cn('px-6 pt-3', contentClassName)} style={contentStyle}>
      {children}
    </View>
  )

  return (
    <SafeAreaView className="flex-1" style={{ backgroundColor: colors.bgDeep }}>
      <LinearGradient
        colors={[colors.bgSurface, colors.bgDeep]}
        locations={[0, 0.42]}
        pointerEvents="none"
        style={{ height: 360, left: 0, opacity: 0.42, position: 'absolute', right: 0, top: 0 }}
      />
      {scroll ? (
        <ScrollView className="flex-1" contentContainerStyle={{ paddingBottom: 124 }}>
          {content}
        </ScrollView>
      ) : (
        content
      )}
    </SafeAreaView>
  )
}

export function MonoLabel({
  children,
  color = 'textTertiary',
  className,
}: {
  children: ReactNode
  color?: keyof ThemeColors
  className?: string
}) {
  return (
    <Text className={cn('uppercase', className)} color={color} preset="label">
      {children}
    </Text>
  )
}

export function EditorialTitle({
  children,
  className,
  color,
}: {
  children: ReactNode
  className?: string
  color?: keyof ThemeColors
}) {
  return (
    <Text className={className} color={color} preset="h1">
      {children}
    </Text>
  )
}

export function EditorialHeader({
  label,
  title,
  subtitle,
  right,
}: {
  label: string
  title: ReactNode
  subtitle?: ReactNode
  right?: ReactNode
}) {
  return (
    <View className="flex-row items-start justify-between gap-4">
      <View className="flex-1">
        <Animated.View entering={FadeInDown.duration(380).easing(Easing.out(Easing.quad))}>
          <MonoLabel>{label}</MonoLabel>
        </Animated.View>
        <Animated.View entering={FadeInDown.delay(70).duration(450).easing(Easing.out(Easing.quad))}>
          <EditorialTitle className="mt-2">{title}</EditorialTitle>
        </Animated.View>
        {subtitle ? (
          <Animated.View entering={FadeInDown.delay(130).duration(450).easing(Easing.out(Easing.quad))}>
            <Text className="mt-2" color="textSecondary" preset="bodySmall">
              {subtitle}
            </Text>
          </Animated.View>
        ) : null}
      </View>
      {right}
    </View>
  )
}

export function IconCircle({
  children,
  onPress,
}: {
  children: ReactNode
  onPress?: () => void
}) {
  const { colors } = useThemeColors()

  return (
    <Pressable
      className="h-10 w-10 items-center justify-center rounded-full border"
      onPress={onPress}
      style={{ backgroundColor: colors.bgSurface, borderColor: colors.borderSoft }}
    >
      {children}
    </Pressable>
  )
}

export function EditorialCard({
  children,
  className,
  accent,
  onPress,
  style,
}: {
  children: ReactNode
  className?: string
  accent?: Accent
  onPress?: () => void
  style?: ViewProps['style']
}) {
  const { colors } = useThemeColors()
  const accentColor = accent === 'gold' ? colors.accentGold : accent === 'moss' ? colors.accentMoss : accent === 'clay' ? colors.accentClay : undefined
  const Wrapper = onPress ? Pressable : View

  return (
    <Wrapper
      className={cn('overflow-hidden rounded-3xl border p-4', className)}
      onPress={onPress}
      style={[
        {
          backgroundColor: colors.bgSurface,
          borderColor: colors.borderSoft,
          shadowColor: '#000',
          shadowOpacity: 0.18,
          shadowRadius: 22,
          shadowOffset: { width: 0, height: 10 },
          elevation: 4,
        },
        style,
      ]}
    >
      {accentColor ? (
        <View
          pointerEvents="none"
          style={{
            backgroundColor: accentColor,
            height: 2,
            left: 18,
            position: 'absolute',
            right: 18,
            top: 0,
          }}
        />
      ) : null}
      {children}
    </Wrapper>
  )
}

export function GarmentTile({
  label,
  uri,
  tone = 'top',
  className,
  imageStyle,
  children,
}: {
  label?: string
  uri?: string | null
  tone?: GarmentTone
  className?: string
  imageStyle?: ViewProps['style']
  children?: ReactNode
}) {
  const { colors } = useThemeColors()
  const [a, b, c] = garmentTones[tone]

  return (
    <View className={cn('overflow-hidden rounded-2xl', className)} style={[{ backgroundColor: colors.bgRaised }, imageStyle]}>
      {uri ? (
        <Image contentFit="cover" source={{ uri }} style={{ height: '100%', width: '100%' }} />
      ) : (
        <LinearGradient colors={[a, b]} start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }} style={{ flex: 1 }}>
          <View style={{ backgroundColor: c, borderRadius: 3, height: 6, opacity: 0.7, position: 'absolute', right: 10, top: 10, width: 6 }} />
        </LinearGradient>
      )}
      {label ? (
        <LinearGradient
          colors={['transparent', 'rgba(0,0,0,0.62)']}
          style={{ bottom: 0, left: 0, padding: 10, position: 'absolute', right: 0 }}
        >
          <Text color="textPrimary" preset="label" style={{ color: '#F0EDE6' }}>
            {label}
          </Text>
        </LinearGradient>
      ) : null}
      {children}
    </View>
  )
}

export function StatusPill({
  children,
  variant = 'muted',
}: {
  children: ReactNode
  variant?: Accent
}) {
  const { colors } = useThemeColors()
  const palette = {
    gold: { bg: colors.goldSoft, fg: colors.accentGold, border: 'transparent' },
    moss: { bg: colors.mossSoft, fg: colors.accentOlive, border: 'transparent' },
    clay: { bg: 'transparent', fg: colors.accentClay, border: colors.accentClay },
    muted: { bg: 'transparent', fg: colors.textTertiary, border: colors.borderSubtle },
  }[variant]

  return (
    <View className="rounded-full border px-3 py-1" style={{ backgroundColor: palette.bg, borderColor: palette.border }}>
      <Text preset="label" style={{ color: palette.fg }}>
        {children}
      </Text>
    </View>
  )
}

export function WeatherStrip({
  city,
  temp,
  condition,
  feel,
}: {
  city: string
  temp?: number | null
  condition?: string | null
  feel?: string
}) {
  const { colors } = useThemeColors()

  return (
    <View
      className="mt-5 flex-row items-center gap-3"
      style={{
        backgroundColor: colors.cardBg,
        borderColor: colors.borderSoft,
        borderRadius: 18,
        borderWidth: 1,
        padding: 14,
        paddingHorizontal: 16,
      }}
    >
      <View
        style={{
          alignItems: 'center',
          backgroundColor: colors.glowGold,
          borderColor: colors.goldSoft,
          borderRadius: 21,
          borderWidth: 1,
          height: 42,
          justifyContent: 'center',
          width: 42,
        }}
      >
        <Ionicons color={colors.accentGold} name="sunny-outline" size={20} />
      </View>
      <View className="flex-1">
        <Text preset="bodySmall" style={{ fontFamily: fontFamily.bodyMedium }}>
          {city}
        </Text>
        <Text className="mt-0.5" color="textSecondary" preset="caption">
          {condition ?? 'Finding the weather'}{feel ? ` — ${feel}` : ''}
        </Text>
      </View>
      <Text preset="h1" style={{ color: colors.accentOlive, fontFamily: fontFamily.displaySemi }}>
        {temp != null ? `${Math.round(temp)}°` : '—'}
      </Text>
    </View>
  )
}

export function QuietChevron() {
  const { colors } = useThemeColors()
  return <Ionicons color={colors.textTertiary} name="chevron-forward" size={16} />
}

export { fontFamily }
