import { View, type ViewProps } from 'react-native'

import { cn } from '@/lib/utils/cn'
import { Text } from '@/components/ui/text'
import { useThemeColors } from '@/theme/colors'

type BadgeVariant = 'moss' | 'gold' | 'muted' | 'clay'

interface BadgeProps extends ViewProps {
  label: string
  variant?: BadgeVariant
}

export function Badge({ className, label, variant = 'muted', ...props }: BadgeProps) {
  const { colors } = useThemeColors()
  const palette = {
    moss: { bg: colors.mossSoft, fg: colors.accentOlive, border: 'transparent' },
    gold: { bg: colors.goldSoft, fg: colors.accentGold, border: 'transparent' },
    muted: { bg: 'transparent', fg: colors.textTertiary, border: colors.borderSubtle },
    clay: { bg: 'transparent', fg: colors.accentClay, border: colors.accentClay },
  }[variant]

  return (
    <View
      className={cn('rounded-full border px-3 py-1.5', className)}
      style={{ backgroundColor: palette.bg, borderColor: palette.border }}
      {...props}
    >
      <Text preset="label" style={{ color: palette.fg }}>
        {label}
      </Text>
    </View>
  )
}
