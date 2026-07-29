// ATTREQ design tokens — source of truth: assets/design/ios-redesign-v2/attreq-shared.jsx
// (ATTREQ_C light / ATTREQ_DARK_C dark), mirrored from apps/ios DesignSystem/Theme/Theme.swift.

export interface ThemeColors {
  bg: string;
  surface: string;
  deep: string;
  text: string;
  t2: string;
  t3: string;
  accent: string;
  accentSoft: string;
  border: string;
  borderSoft: string;
  clay: string;
  claySoft: string;
  moss: string;
  mossSoft: string;
}

export const lightColors: ThemeColors = {
  bg: '#F5F2EE',
  surface: '#FFFFFF',
  deep: '#1C1917',
  text: '#1C1917',
  t2: '#78716C',
  t3: '#A8A29E',
  accent: '#9B7B5A',
  accentSoft: 'rgba(155,123,90,0.10)',
  border: 'rgba(28,25,23,0.08)',
  borderSoft: 'rgba(28,25,23,0.05)',
  clay: '#BF5C45',
  claySoft: 'rgba(191,92,69,0.10)',
  moss: '#5A8A6A',
  mossSoft: 'rgba(90,138,106,0.12)',
};

export const darkColors: ThemeColors = {
  bg: '#181512',
  surface: '#231F1B',
  deep: '#EDE9E3',
  text: '#EDE9E3',
  t2: '#9A9088',
  t3: '#6E6862',
  accent: '#BA9272',
  accentSoft: 'rgba(186,146,114,0.13)',
  border: 'rgba(237,233,227,0.08)',
  borderSoft: 'rgba(237,233,227,0.05)',
  clay: '#D4705A',
  claySoft: 'rgba(212,112,90,0.12)',
  moss: '#72AA86',
  mossSoft: 'rgba(114,170,134,0.14)',
};

export type GarmentTone = 'top' | 'bottom' | 'outer' | 'accent' | 'shoes';

// Two-stop garment placeholder gradients (CSS linear-gradient(155deg, start, end)).
export const garmentGradients: Record<'light' | 'dark', Record<GarmentTone, [string, string]>> = {
  light: {
    top: ['#EDE7DF', '#DDD6CC'],
    bottom: ['#DAD4CC', '#CAC3BA'],
    outer: ['#E3DACE', '#D5CCBF'],
    accent: ['#F0EBE3', '#E5DED5'],
    shoes: ['#DFD9D2', '#D3CCC5'],
  },
  dark: {
    top: ['#3C3630', '#302A24'],
    bottom: ['#343030', '#28242A'],
    outer: ['#423A2C', '#362E22'],
    accent: ['#403C36', '#343028'],
    shoes: ['#3A3632', '#2E2A26'],
  },
};

export const spacing = {
  xs: 4,
  sm: 8,
  md: 12,
  lg: 16,
  xl: 20,
  '2xl': 24,
  '3xl': 32,
} as const;

export const radius = {
  xs: 8,
  sm: 12,
  md: 16,
  lg: 20,
  xl: 24,
  '2xl': 28,
  pill: 999,
} as const;

export interface CardShadow {
  shadowColor: string;
  shadowOpacity: number;
  shadowRadius: number;
  shadowOffset: { width: number; height: number };
  elevation: number;
}

// Handoff cardStyle box-shadow: light 0 2px 8px rgba(0,0,0,0.04), dark 0 2px 12px rgba(0,0,0,0.28).
export const cardShadow = (isDark: boolean): CardShadow =>
  isDark
    ? { shadowColor: '#000', shadowOpacity: 0.28, shadowRadius: 12, shadowOffset: { width: 0, height: 2 }, elevation: 5 }
    : { shadowColor: '#000', shadowOpacity: 0.04, shadowRadius: 8, shadowOffset: { width: 0, height: 2 }, elevation: 2 };

// Floating pill tab bar surface. Android has no cheap system-wide blur — semi-opaque approximation
// of the handoff's backdrop-blur(20) (documented divergence in docs/08-android-native/00-goal.md).
export const tabBarSurface = (isDark: boolean): string =>
  isDark ? 'rgba(24,21,18,0.96)' : 'rgba(245,242,238,0.95)';

export const tabActiveBg = (isDark: boolean): string =>
  isDark ? 'rgba(237,233,227,0.08)' : 'rgba(28,25,23,0.07)';

export interface Theme {
  colors: ThemeColors;
  isDark: boolean;
  garment: Record<GarmentTone, [string, string]>;
  spacing: typeof spacing;
  radius: typeof radius;
}

export const makeTheme = (isDark: boolean): Theme => ({
  colors: isDark ? darkColors : lightColors,
  isDark,
  garment: isDark ? garmentGradients.dark : garmentGradients.light,
  spacing,
  radius,
});
