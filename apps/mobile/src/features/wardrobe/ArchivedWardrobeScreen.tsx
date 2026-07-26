import React, { useMemo } from 'react';
import { Pressable, ScrollView, Text, View } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

import { useTheme } from '@/design-system/theme/ThemeProvider';
import { display } from '@/design-system/theme/typography';
import { MonoLabel } from '@/design-system/components/MonoLabel';
import { BodyText } from '@/design-system/components/BodyText';
import { AttreqIcon } from '@/design-system/icons/AttreqIcon';
import { useWardrobeItems } from '@/lib/query/wardrobe';
import { WardrobeItemCard } from '@/features/wardrobe/WardrobeItemCard';

export function ArchivedWardrobeScreen({ onBack, onOpenItem }: { onBack: () => void; onOpenItem: (id: string) => void }) {
  const t = useTheme();
  const insets = useSafeAreaInsets();
  const { data, isLoading } = useWardrobeItems('archived');
  const items = data?.items ?? [];
  const rows = useMemo(() => {
    const out: (typeof items)[] = [];
    for (let i = 0; i < items.length; i += 2) out.push(items.slice(i, i + 2));
    return out;
  }, [items]);

  return (
    <View testID="archived-screen" style={{ flex: 1, backgroundColor: t.colors.bg }}>
      <ScrollView contentContainerStyle={{ paddingTop: insets.top + 12, paddingBottom: 130, paddingHorizontal: 24, gap: 20 }}>
        <Pressable onPress={onBack} hitSlop={10} accessibilityRole="button" accessibilityLabel="Back" style={{ width: 30, height: 30, borderRadius: 100, borderWidth: 1, borderColor: t.colors.border, alignItems: 'center', justifyContent: 'center' }}>
          <AttreqIcon name="back" size={14} color={t.colors.t2} />
        </Pressable>
        <View>
          <MonoLabel style={{ marginBottom: 8 }}>ARCHIVED</MonoLabel>
          <Text style={[display(32), { color: t.colors.text }]}>
            Out of{' '}
            <Text style={display(32, { italic: true })}>rotation.</Text>
          </Text>
        </View>
        {isLoading ? (
          <BodyText>Loading…</BodyText>
        ) : items.length === 0 ? (
          <BodyText>Nothing archived. Archived pieces stay out of recommendations but aren't deleted.</BodyText>
        ) : (
          <View style={{ gap: 16 }}>
            {rows.map((row, ri) => (
              <View key={ri} style={{ flexDirection: 'row', gap: 16 }}>
                {row.map((item) => (
                  <WardrobeItemCard key={item.id} item={item} onPress={() => onOpenItem(item.id)} />
                ))}
                {row.length === 1 && <View style={{ flex: 1 }} />}
              </View>
            ))}
          </View>
        )}
      </ScrollView>
    </View>
  );
}
