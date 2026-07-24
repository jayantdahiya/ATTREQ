import React from 'react';
import { StyleProp, View, ViewStyle } from 'react-native';
import { useTheme } from '../theme/ThemeProvider';
import { cardShadow } from '../theme/theme';

// Signature 20-radius surface card with hairline border + per-theme soft shadow.
export function Card({
  children,
  padding = 16,
  style,
}: {
  children: React.ReactNode;
  padding?: number;
  style?: StyleProp<ViewStyle>;
}) {
  const t = useTheme();
  return (
    <View
      style={[
        {
          backgroundColor: t.colors.surface,
          borderRadius: 20,
          borderWidth: 1,
          borderColor: t.colors.border,
          padding,
        },
        cardShadow(t.isDark),
        style,
      ]}>
      {children}
    </View>
  );
}
