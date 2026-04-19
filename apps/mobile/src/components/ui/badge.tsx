import { View, type ViewProps } from 'react-native'

import { cn } from '@/lib/utils/cn'
import { Text } from '@/components/ui/text'
import { useThemeColors, type ThemeColors } from '@/theme/colors'

type BadgeVariant = 'moss' | 'gold' | 'muted' | 'clay'

interface BadgeProps extends ViewProps {
  label: string
  variant?: BadgeVariant
}

const styles: Record<BadgeVariant, { bg: keyof ThemeColors; text: 'textPrimary' | 'textSecondary' }> = {
  moss: { bg: 'accentMoss', text: 'textPrimary' },
  gold: { bg: 'accentGold', text: 'textPrimary' },
  muted: { bg: 'bgRaised', text: 'textSecondary' },
  clay: { bg: 'accentClay', text: 'textPrimary' },
}

export function Badge({ className, label, variant = 'muted', ...props }: BadgeProps) {
  const { colors } = useThemeColors()
  const palette = styles[variant]

  return (
    <View
      className={cn('rounded-full px-3 py-1.5', className)}
      style={{ backgroundColor: colors[palette.bg] }}
      {...props}
    >
      <Text preset="label" color={palette.text}>
        {label}
      </Text>
    </View>
  )
}
