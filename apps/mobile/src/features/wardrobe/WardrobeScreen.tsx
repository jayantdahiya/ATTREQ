import React, { useMemo, useState } from 'react';
import { Pressable, RefreshControl, ScrollView, Text, View } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

import { useTheme } from '@/design-system/theme/ThemeProvider';
import { body, display } from '@/design-system/theme/typography';
import { MonoLabel } from '@/design-system/components/MonoLabel';
import { BodyText } from '@/design-system/components/BodyText';
import { Chip } from '@/design-system/components/Chip';
import { AttreqIcon } from '@/design-system/icons/AttreqIcon';
import { useUploadItem, useWardrobeItems } from '@/lib/query/wardrobe';
import { pickFromCamera, pickFromLibrary } from '@/lib/media/image-picker';
import { WARDROBE_FILTERS, matchesFilter, type WardrobeFilter } from '@/features/wardrobe/categories';
import { WardrobeItemCard } from '@/features/wardrobe/WardrobeItemCard';

export function WardrobeScreen({
  onOpenItem,
  onOpenArchived,
}: {
  onOpenItem: (id: string) => void;
  onOpenArchived: () => void;
}) {
  const t = useTheme();
  const insets = useSafeAreaInsets();
  const [filter, setFilter] = useState<WardrobeFilter>('all');
  const { data, isLoading, refetch, isRefetching } = useWardrobeItems('active');
  const upload = useUploadItem();

  const items = data?.items ?? [];
  const filtered = useMemo(() => items.filter((i) => matchesFilter(filter, i.category)), [items, filter]);
  const rows = useMemo(() => {
    const out: (typeof filtered)[] = [];
    for (let i = 0; i < filtered.length; i += 2) out.push(filtered.slice(i, i + 2));
    return out;
  }, [filtered]);

  const addFrom = async (source: 'camera' | 'library') => {
    const asset = await (source === 'camera' ? pickFromCamera() : pickFromLibrary());
    if (asset) upload.mutate(asset);
  };

  const UploadTile = ({ icon, label, onPress }: { icon: 'camera' | 'image'; label: string; onPress: () => void }) => (
    <Pressable
      onPress={onPress}
      disabled={upload.isPending}
      accessibilityRole="button"
      style={{
        flex: 1,
        height: 92,
        borderRadius: 16,
        borderWidth: 1,
        borderColor: t.colors.border,
        borderStyle: 'dashed',
        alignItems: 'center',
        justifyContent: 'center',
        gap: 8,
        backgroundColor: t.colors.surface,
        opacity: upload.isPending ? 0.6 : 1,
      }}>
      <AttreqIcon name={icon} size={22} color={t.colors.accent} />
      <MonoLabel color={t.colors.t2}>{label}</MonoLabel>
    </Pressable>
  );

  return (
    <View testID="wardrobe-screen" style={{ flex: 1, backgroundColor: t.colors.bg }}>
      <ScrollView
        contentContainerStyle={{ paddingTop: insets.top + 16, paddingBottom: 130, paddingHorizontal: 24, gap: 20 }}
        refreshControl={<RefreshControl refreshing={isRefetching} onRefresh={refetch} tintColor={t.colors.accent} />}>
        {/* Header */}
        <View>
          <MonoLabel style={{ marginBottom: 8 }}>WARDROBE</MonoLabel>
          <Text style={[display(34), { color: t.colors.text }]}>
            Your closet,{' '}
            <Text style={display(34, { italic: true })}>curated.</Text>
          </Text>
          <View style={{ flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', marginTop: 6 }}>
            <BodyText size={13}>{data ? `${data.total} piece${data.total === 1 ? '' : 's'}` : ' '}</BodyText>
            <Text onPress={onOpenArchived} style={[body(13, 'medium'), { color: t.colors.accent }]} accessibilityRole="link">
              Archived
            </Text>
          </View>
        </View>

        {/* Upload tiles */}
        <View style={{ flexDirection: 'row', gap: 12 }}>
          <UploadTile icon="camera" label={upload.isPending ? 'Uploading…' : 'Camera'} onPress={() => addFrom('camera')} />
          <UploadTile icon="image" label={upload.isPending ? 'Uploading…' : 'Library'} onPress={() => addFrom('library')} />
        </View>

        {/* Category chips */}
        <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={{ gap: 7 }}>
          {WARDROBE_FILTERS.map((f) => (
            <Chip key={f.key} label={f.label} selected={filter === f.key} onPress={() => setFilter(f.key)} />
          ))}
        </ScrollView>

        {/* Grid */}
        {isLoading ? (
          <BodyText style={{ marginTop: 24 }}>Loading your wardrobe…</BodyText>
        ) : filtered.length === 0 ? (
          <BodyText style={{ marginTop: 24 }}>
            {items.length === 0 ? 'No pieces yet — add one with the camera or your library.' : 'Nothing in this category.'}
          </BodyText>
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
