import React from 'react';
import { Image, StyleProp, View, ViewStyle } from 'react-native';

import { useTheme } from '@/design-system/theme/ThemeProvider';
import { GarmentPlaceholder } from '@/design-system/components/GarmentPlaceholder';
import { MonoLabel } from '@/design-system/components/MonoLabel';
import type { GarmentTone } from '@/design-system/theme/theme';
import { resolveImageUrl } from '@/lib/utils/images';
import type { OutfitItemDetail, OutfitSuggestion } from '@/lib/api/types';

// One collage tile: real item thumbnail when available, otherwise the toned
// GarmentPlaceholder. A mono label is pinned bottom-left in both cases.
function GarmentTile({
  item,
  tone,
  label,
  style,
}: {
  item: OutfitItemDetail | null;
  tone: GarmentTone;
  label: string;
  style?: StyleProp<ViewStyle>;
}) {
  const t = useTheme();
  const uri = resolveImageUrl(item?.thumbnail_url ?? item?.image_url);
  return (
    <View style={[{ borderRadius: 16, overflow: 'hidden' }, style]}>
      {uri ? (
        <>
          <Image source={{ uri }} style={{ width: '100%', height: '100%' }} resizeMode="cover" />
          <View style={{ position: 'absolute', bottom: 7, left: 8 }}>
            <MonoLabel size={7.5} color={t.colors.t3}>
              {label}
            </MonoLabel>
          </View>
        </>
      ) : (
        <GarmentPlaceholder tone={tone} label={label} radius={16} style={{ flex: 1 }} />
      )}
    </View>
  );
}

/**
 * Garment collage for a suggestion. `card` layout (Today card): left tile 54%
 * + a stacked right column (Bottom 57% / Accent). `deck` layout (swipe deck):
 * Top + Bottom side by side. Either way a fullbody-anchored outfit drops the
 * Bottom tile and shows the fullbody item under a "Look" label.
 */
export function GarmentCollage({
  suggestion,
  layout = 'card',
  height = 190,
}: {
  suggestion: OutfitSuggestion;
  layout?: 'card' | 'deck';
  height?: number;
}) {
  const isFullbody = !!suggestion.fullbody_item;
  const primary = suggestion.fullbody_item ?? suggestion.top_item;

  if (layout === 'deck') {
    return (
      <View style={{ height, flexDirection: 'row', gap: 8 }}>
        <GarmentTile item={primary} tone="top" label={isFullbody ? 'Look' : 'Top'} style={{ flex: isFullbody ? 1 : 0.5 }} />
        {!isFullbody && (
          <GarmentTile item={suggestion.bottom_item} tone="bottom" label="Bottom" style={{ flex: 0.5 }} />
        )}
      </View>
    );
  }

  return (
    <View style={{ height, flexDirection: 'row', gap: 8 }}>
      <GarmentTile item={primary} tone="top" label={isFullbody ? 'Look' : 'Top'} style={{ width: '54%' }} />
      <View style={{ flex: 1, gap: 8 }}>
        {!isFullbody && (
          <GarmentTile item={suggestion.bottom_item} tone="bottom" label="Bottom" style={{ flex: 0.57 }} />
        )}
        <GarmentTile item={suggestion.accessory_item} tone="accent" label="Accent" style={{ flex: 0.43 }} />
      </View>
    </View>
  );
}
