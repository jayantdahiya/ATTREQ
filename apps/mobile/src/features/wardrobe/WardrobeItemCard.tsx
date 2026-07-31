import React from 'react';
import { Image, Pressable, View } from 'react-native';
import { useTheme } from '@/design-system/theme/ThemeProvider';
import { MonoLabel } from '@/design-system/components/MonoLabel';
import { Pill } from '@/design-system/components/Pill';
import { GarmentPlaceholder } from '@/design-system/components/GarmentPlaceholder';
import { resolveImageUrl } from '@/lib/utils/images';
import type { WardrobeItem } from '@/lib/api/types';

export function WardrobeItemCard({ item, onPress }: { item: WardrobeItem; onPress: () => void }) {
  const t = useTheme();
  const uri = resolveImageUrl(item.thumbnail_url ?? item.processed_image_url ?? item.original_image_url);
  const processing = item.processing_status === 'pending' || item.processing_status === 'processing';
  const failed = item.processing_status === 'failed';

  return (
    <Pressable onPress={onPress} style={{ flex: 1 }} accessibilityRole="button" testID="wardrobe-item-card">
      <View
        style={{
          borderRadius: 14,
          overflow: 'hidden',
          aspectRatio: 0.82,
          backgroundColor: t.colors.surface,
          borderWidth: 1,
          borderColor: t.colors.border,
        }}>
        {uri ? (
          <Image source={{ uri }} style={{ width: '100%', height: '100%' }} resizeMode="cover" />
        ) : (
          <GarmentPlaceholder tone="top" style={{ flex: 1 }} />
        )}
        {(processing || failed) && (
          <View style={{ position: 'absolute', top: 8, left: 8 }}>
            <Pill variant={failed ? 'clay' : 'gold'}>{failed ? 'Failed' : 'Processing'}</Pill>
          </View>
        )}
      </View>
      <MonoLabel style={{ marginTop: 6 }} color={t.colors.t2}>
        {item.category ?? 'Unclassified'}
      </MonoLabel>
    </Pressable>
  );
}
