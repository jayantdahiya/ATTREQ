import React from 'react';
import { Text, View } from 'react-native';

import { useTheme } from '@/design-system/theme/ThemeProvider';
import { display } from '@/design-system/theme/typography';
import { Card } from '@/design-system/components/Card';
import { MonoLabel } from '@/design-system/components/MonoLabel';
import { BodyText } from '@/design-system/components/BodyText';
import { Pill } from '@/design-system/components/Pill';
import { swatchColor } from '@/features/style-dna/swatch-colors';
import type { StyleDna } from '@/lib/api/types';

function cap(value: string): string {
  return value.length > 0 ? value.charAt(0).toUpperCase() + value.slice(1) : value;
}

function Swatch({ name }: { name: string }) {
  const t = useTheme();
  return (
    <View style={{ flexDirection: 'row', alignItems: 'center', gap: 5 }}>
      <View
        style={{
          width: 14,
          height: 14,
          borderRadius: 4,
          backgroundColor: swatchColor(name),
          borderWidth: 1,
          borderColor: t.colors.border,
        }}
      />
      <MonoLabel size={8.5} color={t.colors.t2}>
        {name}
      </MonoLabel>
    </View>
  );
}

/**
 * Compact Style DNA summary card — aesthetic headline, secondary chips, a
 * dominant palette swatch row, and formality. Rendered on the Profile tab and
 * as the header of the Style DNA profile screen. testID `style-dna-card`.
 */
export function StyleDnaCard({ dna, testID = 'style-dna-card' }: { dna: StyleDna; testID?: string }) {
  const t = useTheme();
  const aesthetic = dna.aesthetic;
  const palette = dna.color_palette;
  const formality = dna.formality_bias;
  const dominant = palette?.dominant ?? [];

  return (
    <Card padding={18} style={{ gap: 12 }}>
      <View testID={testID} style={{ gap: 12 }}>
        <View>
          <MonoLabel style={{ marginBottom: 6 }}>Your Style DNA</MonoLabel>
          <Text style={[display(22, { italic: true }), { color: t.colors.text }]}>
            {aesthetic?.primary ? cap(aesthetic.primary) : 'Not yet analyzed'}
          </Text>
        </View>

        {aesthetic && aesthetic.secondary.length > 0 ? (
          <View style={{ flexDirection: 'row', flexWrap: 'wrap', gap: 6 }}>
            {aesthetic.secondary.map((name) => (
              <Pill key={name} variant="muted">
                {name}
              </Pill>
            ))}
          </View>
        ) : null}

        {dominant.length > 0 ? (
          <View style={{ gap: 6 }}>
            <MonoLabel size={8.5}>Palette</MonoLabel>
            <View style={{ flexDirection: 'row', flexWrap: 'wrap', gap: 10 }}>
              {dominant.slice(0, 5).map((name) => (
                <Swatch key={name} name={name} />
              ))}
            </View>
          </View>
        ) : null}

        {formality ? (
          <View style={{ flexDirection: 'row', alignItems: 'center', gap: 8 }}>
            <MonoLabel size={8.5}>Formality</MonoLabel>
            <Pill variant="gold">{formality.label}</Pill>
            <BodyText size={12} color={t.colors.t3}>
              {formality.level.toFixed(1)} / 3
            </BodyText>
          </View>
        ) : null}
      </View>
    </Card>
  );
}
