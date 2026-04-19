import { LinearGradient } from 'expo-linear-gradient'
import { View, type ViewStyle } from 'react-native'

import { useThemeColors } from '@/theme/colors'

type DividerVariant = 'subtle' | 'gold'

interface DividerProps {
  variant?: DividerVariant
  width?: number | '100%'
}

export function Divider({ variant = 'subtle', width = '100%' }: DividerProps) {
  const { colors } = useThemeColors()
  const style: ViewStyle = { width, height: 1 }

  if (variant === 'gold') {
    return (
      <LinearGradient
        colors={['transparent', colors.accentGold, 'transparent']}
        end={{ x: 1, y: 0 }}
        start={{ x: 0, y: 0 }}
        style={style}
      />
    )
  }

  return <View style={[style, { backgroundColor: colors.borderSubtle }]} />
}
