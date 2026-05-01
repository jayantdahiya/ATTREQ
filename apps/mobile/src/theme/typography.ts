import {
  CormorantGaramond_600SemiBold,
  CormorantGaramond_700Bold,
} from '@expo-google-fonts/cormorant-garamond'
import { DMSans_400Regular, DMSans_500Medium, DMSans_600SemiBold } from '@expo-google-fonts/dm-sans'
import { IBMPlexMono_400Regular, IBMPlexMono_500Medium } from '@expo-google-fonts/ibm-plex-mono'

export const fontMap = {
  CormorantGaramond_600SemiBold,
  CormorantGaramond_700Bold,
  DMSans_400Regular,
  DMSans_500Medium,
  DMSans_600SemiBold,
  IBMPlexMono_400Regular,
  IBMPlexMono_500Medium,
}

export const fontFamily = {
  displayBold: 'CormorantGaramond_700Bold',
  displaySemi: 'CormorantGaramond_600SemiBold',
  bodyRegular: 'DMSans_400Regular',
  bodyMedium: 'DMSans_500Medium',
  bodySemi: 'DMSans_600SemiBold',
  monoRegular: 'IBMPlexMono_400Regular',
  monoMedium: 'IBMPlexMono_500Medium',
} as const

export const typeScale = {
  display: {
    fontFamily: fontFamily.displayBold,
    fontSize: 38,
    lineHeight: 42,
    letterSpacing: 0,
  },
  wordmark: {
    fontFamily: fontFamily.displaySemi,
    fontSize: 56,
    lineHeight: 58,
    letterSpacing: 4.5,
  },
  h1: {
    fontFamily: fontFamily.displaySemi,
    fontSize: 36,
    lineHeight: 38,
    letterSpacing: 0,
  },
  h2: {
    fontFamily: fontFamily.displaySemi,
    fontSize: 22,
    lineHeight: 28,
    letterSpacing: 0,
  },
  h3: {
    fontFamily: fontFamily.bodySemi,
    fontSize: 18,
    lineHeight: 24,
    letterSpacing: 0,
  },
  body: {
    fontFamily: fontFamily.bodyRegular,
    fontSize: 16,
    lineHeight: 24,
    letterSpacing: 0,
  },
  bodySmall: {
    fontFamily: fontFamily.bodyRegular,
    fontSize: 14,
    lineHeight: 20,
    letterSpacing: 0,
  },
  caption: {
    fontFamily: fontFamily.bodyMedium,
    fontSize: 12,
    lineHeight: 16,
    letterSpacing: 0.2,
  },
  label: {
    fontFamily: fontFamily.monoMedium,
    fontSize: 10,
    lineHeight: 14,
    letterSpacing: 1.8,
    textTransform: 'uppercase' as const,
  },
  mono: {
    fontFamily: fontFamily.monoRegular,
    fontSize: 13,
    lineHeight: 18,
    letterSpacing: 0.3,
  },
} as const

export type TextPreset = keyof typeof typeScale
