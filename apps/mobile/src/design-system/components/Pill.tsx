import React from 'react';
import { Text, View } from 'react-native';
import { useTheme } from '../theme/ThemeProvider';
import { mono } from '../theme/typography';

export type PillVariant = 'muted' | 'gold' | 'moss' | 'clay';

// Status pill — mono 8.5 uppercase, tinted background (attreq-shared ATTREQPill).
export function Pill({ children, variant = 'muted' }: { children: React.ReactNode; variant?: PillVariant }) {
  const t = useTheme();
  const map: Record<PillVariant, { bg: string; color: string }> = {
    muted: { bg: 'rgba(128,120,112,0.10)', color: t.colors.t2 },
    gold: { bg: t.colors.accentSoft, color: t.colors.accent },
    moss: { bg: t.colors.mossSoft, color: t.colors.moss },
    clay: { bg: t.colors.claySoft, color: t.colors.clay },
  };
  const v = map[variant] ?? map.muted;
  return (
    <View style={{ backgroundColor: v.bg, borderRadius: 100, paddingVertical: 3, paddingHorizontal: 9, alignSelf: 'flex-start' }}>
      <Text style={[mono(8.5), { letterSpacing: 0.9, textTransform: 'uppercase', color: v.color }]}>{children}</Text>
    </View>
  );
}
