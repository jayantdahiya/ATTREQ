import { TextStyle } from 'react-native';

// fontFamily values match the bundled .ttf file/PostScript names, linked via
// `npx react-native-asset` (react-native.config.js -> ./assets/fonts).
export const fonts = {
  displayRegular: 'CormorantGaramond-Regular',
  displayMedium: 'CormorantGaramond-Medium',
  displaySemiBold: 'CormorantGaramond-SemiBold',
  displayItalic: 'CormorantGaramond-Italic',
  displayMediumItalic: 'CormorantGaramond-MediumItalic',
  displaySemiBoldItalic: 'CormorantGaramond-SemiBoldItalic',
  bodyLight: 'DMSans-Light',
  bodyRegular: 'DMSans-Regular',
  bodyMedium: 'DMSans-Medium',
  bodySemiBold: 'DMSans-SemiBold',
  monoRegular: 'IBMPlexMono-Regular',
  monoMedium: 'IBMPlexMono-Medium',
} as const;

type SerifWeight = 'regular' | 'medium' | 'semiBold';

/** Cormorant Garamond — display/headline serif. */
export function display(
  size: number,
  opts: { weight?: SerifWeight; italic?: boolean } = {},
): TextStyle {
  const { weight = 'semiBold', italic = false } = opts;
  const map: Record<SerifWeight, string> = {
    regular: italic ? fonts.displayItalic : fonts.displayRegular,
    medium: italic ? fonts.displayMediumItalic : fonts.displayMedium,
    semiBold: italic ? fonts.displaySemiBoldItalic : fonts.displaySemiBold,
  };
  return { fontFamily: map[weight], fontSize: size };
}

type SansWeight = 'light' | 'regular' | 'medium' | 'semiBold';

/** DM Sans — body/UI sans. */
export function body(size: number, weight: SansWeight = 'regular'): TextStyle {
  const map: Record<SansWeight, string> = {
    light: fonts.bodyLight,
    regular: fonts.bodyRegular,
    medium: fonts.bodyMedium,
    semiBold: fonts.bodySemiBold,
  };
  return { fontFamily: map[weight], fontSize: size };
}

type MonoWeight = 'regular' | 'medium';

/** IBM Plex Mono — uppercase micro-labels. */
export function mono(size: number, weight: MonoWeight = 'regular'): TextStyle {
  const map: Record<MonoWeight, string> = {
    regular: fonts.monoRegular,
    medium: fonts.monoMedium,
  };
  return { fontFamily: map[weight], fontSize: size };
}
