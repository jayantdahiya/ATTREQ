import React from 'react';
import { Text, View } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useTheme } from '@/design-system/theme/ThemeProvider';
import { display } from '@/design-system/theme/typography';
import { MonoLabel } from '@/design-system/components/MonoLabel';
import { BodyText } from '@/design-system/components/BodyText';
import type { AttreqTab } from '@/design-system/components/TabBar';

const COPY: Record<string, { label: string; title: string; milestone: string }> = {
  today: { label: 'TODAY', title: 'Good morning.', milestone: 'A4' },
  history: { label: 'HISTORY', title: 'Your rotation.', milestone: 'A4' },
};

export function TabPlaceholderScreen({ tab }: { tab: AttreqTab }) {
  const t = useTheme();
  const insets = useSafeAreaInsets();
  const c = COPY[tab] ?? { label: tab.toUpperCase(), title: 'Coming soon.', milestone: 'later' };
  return (
    <View style={{ flex: 1, backgroundColor: t.colors.bg, paddingTop: insets.top + 24, paddingHorizontal: 28 }}>
      <MonoLabel style={{ marginBottom: 8 }}>{c.label}</MonoLabel>
      <Text style={[display(34), { color: t.colors.text }]}>{c.title}</Text>
      <BodyText style={{ marginTop: 8 }}>This tab arrives in milestone {c.milestone}.</BodyText>
    </View>
  );
}
