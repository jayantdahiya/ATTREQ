import { darkColors, lightColors } from '@/theme/colors'

export const theme = {
  colors: {
    dark: darkColors,
    light: lightColors,
  },
  spacing: {
    xs: 4,
    sm: 8,
    md: 12,
    lg: 16,
    xl: 20,
    '2xl': 24,
    '3xl': 32,
  },
  radius: {
    sm: 12,
    md: 16,
    lg: 20,
    xl: 24,
    '2xl': 28,
    pill: 999,
  },
  shadow: {
    moss: {
      shadowColor: '#36664A',
      shadowOpacity: 0.18,
      shadowRadius: 16,
      shadowOffset: { width: 0, height: 8 },
      elevation: 6,
    },
    gold: {
      shadowColor: '#D4A854',
      shadowOpacity: 0.18,
      shadowRadius: 12,
      shadowOffset: { width: 0, height: 6 },
      elevation: 4,
    },
  },
} as const
