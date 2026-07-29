import React from 'react';
import { StyleProp, Text, TextStyle } from 'react-native';
import { useTheme } from '../theme/ThemeProvider';
import { body } from '../theme/typography';

type Weight = 'light' | 'regular' | 'medium' | 'semiBold';

// DM Sans body copy — 14pt, 1.5 line-height (attreq-shared ATTREQBody).
export function BodyText({
  children,
  color,
  weight = 'regular',
  size = 14,
  style,
  testID,
}: {
  children: React.ReactNode;
  color?: string;
  weight?: Weight;
  size?: number;
  style?: StyleProp<TextStyle>;
  testID?: string;
}) {
  const t = useTheme();
  return (
    <Text testID={testID} style={[body(size, weight), { lineHeight: size * 1.5, color: color ?? t.colors.t2 }, style]}>
      {children}
    </Text>
  );
}
