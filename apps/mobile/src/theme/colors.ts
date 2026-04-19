import { useColorScheme as useDeviceColorScheme } from 'react-native'

export const darkColors = {
  bgDeep: '#0D1210',
  bgSurface: '#151E1A',
  bgRaised: '#1C2923',

  accentMoss: '#36664A',
  accentOlive: '#6F8B57',
  accentGold: '#D4A854',
  accentClay: '#C9604A',

  textPrimary: '#F0EDE6',
  textSecondary: '#9B978E',
  textTertiary: '#5C5850',

  borderSubtle: '#252E28',
  borderAccent: 'rgba(54, 102, 74, 0.20)',

  glowMoss: 'rgba(54, 102, 74, 0.08)',
  glowGold: 'rgba(212, 168, 84, 0.06)',
} as const

export const lightColors = {
  bgDeep: '#F7F3EC',
  bgSurface: '#FFFFFF',
  bgRaised: '#F0EBE1',

  accentMoss: '#36664A',
  accentOlive: '#6F8B57',
  accentGold: '#B8923F',
  accentClay: '#C9604A',

  textPrimary: '#1C2A22',
  textSecondary: '#5C6860',
  textTertiary: '#9B978E',

  borderSubtle: '#E5DFD4',
  borderAccent: 'rgba(54, 102, 74, 0.15)',

  glowMoss: 'rgba(54, 102, 74, 0.06)',
  glowGold: 'rgba(184, 146, 63, 0.04)',
} as const

export type ThemeColors = typeof darkColors

export function useThemeColors() {
  const scheme = useDeviceColorScheme()
  const isDark = scheme !== 'light'

  return {
    colors: isDark ? darkColors : lightColors,
    isDark,
  }
}
