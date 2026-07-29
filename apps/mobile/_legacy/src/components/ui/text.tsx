import { Text as RNText, type TextProps as RNTextProps, type TextStyle } from 'react-native'

import { cn } from '@/lib/utils/cn'
import { useThemeColors, type ThemeColors } from '@/theme/colors'
import { typeScale, type TextPreset } from '@/theme/typography'

interface TextProps extends RNTextProps {
  preset?: TextPreset
  color?: keyof ThemeColors
}

export function Text({ preset = 'body', color, className, style, ...props }: TextProps) {
  const { colors } = useThemeColors()
  const typography = typeScale[preset]

  const resolvedStyle: TextStyle = {
    ...typography,
    color: color ? colors[color] : colors.textPrimary,
  }

  return <RNText className={cn(className)} style={[resolvedStyle, style]} {...props} />
}
