import { View } from 'react-native'
import Animated, { Easing, FadeInDown } from 'react-native-reanimated'

import { Text } from '@/components/ui/text'
import { useThemeColors } from '@/theme/colors'

interface ScreenHeaderProps {
  label: string
  heading: string
  subtitle?: string
}

const easing = Easing.bezier(0.25, 0.46, 0.45, 0.94)

export function ScreenHeader({ label, heading, subtitle }: ScreenHeaderProps) {
  const { colors } = useThemeColors()

  return (
    <View>
      <Animated.View entering={FadeInDown.delay(0).duration(400).easing(easing)}>
        <Text preset="label" color="accentGold">
          {label}
        </Text>
      </Animated.View>

      <Animated.View entering={FadeInDown.delay(80).duration(500).easing(easing)}>
        <Text className="mt-3" preset="h1" style={{ color: colors.textPrimary }}>
          {heading}
        </Text>
      </Animated.View>

      {subtitle ? (
        <Animated.View entering={FadeInDown.delay(160).duration(500).easing(easing)}>
          <Text className="mt-3" color="textSecondary">
            {subtitle}
          </Text>
        </Animated.View>
      ) : null}
    </View>
  )
}
