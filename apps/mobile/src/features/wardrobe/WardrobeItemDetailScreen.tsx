import React from 'react';
import { Image, Pressable, ScrollView, Text, View } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

import { useTheme } from '@/design-system/theme/ThemeProvider';
import { display } from '@/design-system/theme/typography';
import { MonoLabel } from '@/design-system/components/MonoLabel';
import { BodyText } from '@/design-system/components/BodyText';
import { Card } from '@/design-system/components/Card';
import { Pill } from '@/design-system/components/Pill';
import { PrimaryButton } from '@/design-system/components/PrimaryButton';
import { GarmentPlaceholder } from '@/design-system/components/GarmentPlaceholder';
import { AttreqIcon } from '@/design-system/icons/AttreqIcon';
import { useSetItemStatus, useWardrobeItem } from '@/lib/query/wardrobe';
import { resolveImageUrl } from '@/lib/utils/images';

function Row({ label, value }: { label: string; value: string | null | undefined }) {
  const t = useTheme();
  if (!value) return null;
  return (
    <View style={{ flexDirection: 'row', justifyContent: 'space-between', paddingVertical: 8, borderBottomWidth: 1, borderBottomColor: t.colors.borderSoft }}>
      <MonoLabel>{label}</MonoLabel>
      <BodyText size={13} color={t.colors.text}>{value}</BodyText>
    </View>
  );
}

export function WardrobeItemDetailScreen({ itemId, onBack }: { itemId: string; onBack: () => void }) {
  const t = useTheme();
  const insets = useSafeAreaInsets();
  const { data: item, isLoading } = useWardrobeItem(itemId);
  const setStatus = useSetItemStatus();

  const uri = resolveImageUrl(item?.processed_image_url ?? item?.original_image_url);
  const archived = item?.status === 'archived';

  const toggleArchive = () => {
    if (!item) return;
    setStatus.mutate({ itemId: item.id, status: archived ? 'active' : 'archived' }, { onSuccess: onBack });
  };

  return (
    <View testID="item-detail-screen" style={{ flex: 1, backgroundColor: t.colors.bg }}>
      <ScrollView contentContainerStyle={{ paddingTop: insets.top + 12, paddingBottom: insets.bottom + 24, paddingHorizontal: 24, gap: 20 }}>
        <Pressable onPress={onBack} hitSlop={10} accessibilityRole="button" accessibilityLabel="Back" style={{ width: 30, height: 30, borderRadius: 100, borderWidth: 1, borderColor: t.colors.border, alignItems: 'center', justifyContent: 'center' }}>
          <AttreqIcon name="back" size={14} color={t.colors.t2} />
        </Pressable>

        {isLoading || !item ? (
          <BodyText style={{ marginTop: 24 }}>Loading…</BodyText>
        ) : (
          <>
            <View style={{ borderRadius: 20, overflow: 'hidden', aspectRatio: 0.9, backgroundColor: t.colors.surface, borderWidth: 1, borderColor: t.colors.border }}>
              {uri ? <Image source={{ uri }} style={{ width: '100%', height: '100%' }} resizeMode="cover" /> : <GarmentPlaceholder tone="top" style={{ flex: 1 }} />}
            </View>

            <View style={{ flexDirection: 'row', alignItems: 'center', gap: 8 }}>
              <Text style={[display(28), { color: t.colors.text }]}>{item.category ?? 'Unclassified'}</Text>
              {archived && <Pill variant="muted">Archived</Pill>}
              {item.processing_status !== 'completed' && (
                <Pill variant={item.processing_status === 'failed' ? 'clay' : 'gold'}>{item.processing_status}</Pill>
              )}
            </View>

            <Card padding={18}>
              <Row label="Colors" value={[item.color_primary, item.color_secondary].filter(Boolean).join(' · ') || null} />
              <Row label="Pattern" value={item.pattern} />
              <Row label="Texture" value={item.texture} />
              <Row label="Silhouette" value={item.silhouette} />
              <Row label="Neckline" value={item.neckline} />
              <Row label="Sleeve" value={item.sleeve_length} />
              <Row label="Brand" value={item.brand} />
              <Row label="Season" value={item.season?.join(', ') ?? null} />
              <Row label="Occasion" value={item.occasion?.join(', ') ?? null} />
              <Row label="Worn" value={`${item.wear_count} time${item.wear_count === 1 ? '' : 's'}`} />
            </Card>

            <PrimaryButton
              label={setStatus.isPending ? 'Saving…' : archived ? 'Restore to wardrobe' : 'Archive piece'}
              variant={archived ? 'accent' : 'default'}
              isLoading={setStatus.isPending}
              onPress={toggleArchive}
              testID="archive-toggle"
            />
          </>
        )}
      </ScrollView>
    </View>
  );
}
