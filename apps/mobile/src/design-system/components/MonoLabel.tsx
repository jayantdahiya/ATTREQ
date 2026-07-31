import React from 'react';
import { StyleProp, Text, TextStyle } from 'react-native';
import { useTheme } from '../theme/ThemeProvider';
import { mono } from '../theme/typography';

// IBM Plex Mono uppercase micro-label — 9.5pt, 1.6 letter-spacing (attreq-shared ATTREQML).
export function MonoLabel({
  children,
  color,
  size = 9.5,
  style,
}: {
  children: React.ReactNode;
  color?: string;
  size?: number;
  style?: StyleProp<TextStyle>;
}) {
  const t = useTheme();
  return (
    <Text
      style={[
        mono(size),
        {
          letterSpacing: 1.6,
          textTransform: 'uppercase',
          color: color ?? t.colors.t3,
          lineHeight: size * 1.4,
        },
        style,
      ]}>
      {children}
    </Text>
  );
}
