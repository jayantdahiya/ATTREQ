import { useColorScheme as useDeviceColorScheme } from 'react-native'

export const darkColors = {
  bgDeep: '#0D1210',
  bgSurface: '#141C18',
  bgRaised: '#1B2620',
  bgSunk: '#090D0B',

  accentMoss: '#5C8C72',
  accentOlive: '#8FB89A',
  accentGold: '#D4A854',
  accentClay: '#C9604A',

  textPrimary: '#F0EDE6',
  textSecondary: '#9B978E',
  textTertiary: '#5C5850',

  borderSubtle: '#1D2922',
  borderSoft: 'rgba(240, 237, 230, 0.07)',
  borderAccent: 'rgba(92, 140, 114, 0.20)',

  mossSoft: 'rgba(92, 140, 114, 0.20)',
  goldSoft: 'rgba(212, 168, 84, 0.18)',
  glowMoss: 'rgba(92, 140, 114, 0.08)',
  glowGold: 'rgba(212, 168, 84, 0.07)',

  navBg: 'rgba(27, 38, 32, 0.95)',
  cardBg: 'rgba(27, 38, 32, 0.82)',
} as const

export const lightColors = {
  bgDeep: '#EEE8DC',
  bgSurface: '#F5F0E8',
  bgRaised: '#FFFFFF',
  bgSunk: '#E5DFD0',

  accentMoss: '#2F5A40',
  accentOlive: '#5A7344',
  accentGold: '#A8842F',
  accentClay: '#A8492F',

  textPrimary: '#1C2219',
  textSecondary: '#6A6659',
  textTertiary: '#9A9689',

  borderSubtle: 'rgba(28, 34, 25, 0.10)',
  borderSoft: 'rgba(28, 34, 25, 0.07)',
  borderAccent: 'rgba(47, 90, 64, 0.14)',

  mossSoft: 'rgba(47, 90, 64, 0.12)',
  goldSoft: 'rgba(168, 132, 47, 0.16)',
  glowMoss: 'rgba(47, 90, 64, 0.05)',
  glowGold: 'rgba(168, 132, 47, 0.06)',

  navBg: 'rgba(255, 255, 255, 0.94)',
  cardBg: 'rgba(255, 255, 255, 0.88)',
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
