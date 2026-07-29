import React from 'react';
import { Text, View } from 'react-native';

import { useTheme } from '@/design-system/theme/ThemeProvider';
import { display } from '@/design-system/theme/typography';
import { Card } from '@/design-system/components/Card';
import { MonoLabel } from '@/design-system/components/MonoLabel';
import { Pill, type PillVariant } from '@/design-system/components/Pill';
import { GarmentPlaceholder } from '@/design-system/components/GarmentPlaceholder';
import type { GarmentTone } from '@/design-system/theme/theme';

const TILE_TONES: GarmentTone[] = ['top', 'bottom', 'accent'];

export function OutfitHistoryCard({
  outfitId,
  title,
  piecesCount,
  pillLabel,
  pillVariant,
}: {
  outfitId: string;
  title: string;
  piecesCount: number;
  pillLabel: string;
  pillVariant: PillVariant;
}) {
  const t = useTheme();
  return (
    <View testID={`history-entry-${outfitId}`}>
      <Card padding={0}>
        <View style={{ flexDirection: 'row', alignItems: 'center', paddingVertical: 11, paddingHorizontal: 14, gap: 10 }}>
          <View style={{ flexDirection: 'row', gap: 3 }}>
            {TILE_TONES.map((tone) => (
              <GarmentPlaceholder key={tone} tone={tone} radius={9} style={{ width: 34, height: 50 }} />
            ))}
          </View>
          <View style={{ flex: 1, gap: 2 }}>
            <Text numberOfLines={1} style={[display(15, { italic: true }), { color: t.colors.text }]}>
              {title}
            </Text>
            <MonoLabel>{`${piecesCount} ${piecesCount === 1 ? 'piece' : 'pieces'}`}</MonoLabel>
          </View>
          <Pill variant={pillVariant}>{pillLabel}</Pill>
        </View>
      </Card>
    </View>
  );
}
