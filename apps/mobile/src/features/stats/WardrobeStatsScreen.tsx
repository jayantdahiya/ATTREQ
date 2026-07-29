import React, { useState } from 'react';
import { ActivityIndicator, Image, Pressable, RefreshControl, ScrollView, Text, View } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

import { useTheme } from '@/design-system/theme/ThemeProvider';
import { display } from '@/design-system/theme/typography';
import { MonoLabel } from '@/design-system/components/MonoLabel';
import { BodyText } from '@/design-system/components/BodyText';
import { Card } from '@/design-system/components/Card';
import { Pill } from '@/design-system/components/Pill';
import { GarmentPlaceholder } from '@/design-system/components/GarmentPlaceholder';
import { AttreqIcon } from '@/design-system/icons/AttreqIcon';
import type { GarmentTone } from '@/design-system/theme/theme';
import { WardrobeItemDetailScreen } from '@/features/wardrobe/WardrobeItemDetailScreen';
import { bucketFor } from '@/features/wardrobe/categories';
import { useForgottenItems, useWardrobeStats } from '@/lib/query/stats';
import { resolveImageUrl } from '@/lib/utils/images';
import { describeAuthError } from '@/lib/api/errors';
import {
  forgottenSubtitle,
  formatCurrency,
  formatPercent,
  itemTitle,
  outfitCountLabel,
  wornSubtitle,
} from '@/features/stats/statsFormat';
import type {
  CostPerWearEntry,
  ForgottenItemEntry,
  WardrobeStatsResponse,
  WornItemEntry,
} from '@/lib/api/types';

const TONE_FOR_BUCKET: Record<string, GarmentTone> = {
  all: 'top',
  tops: 'top',
  bottoms: 'bottom',
  outer: 'outer',
  accents: 'accent',
  shoes: 'shoes',
};

function Thumbnail({ url, category, size = 46 }: { url: string | null; category: string | null; size?: number }) {
  const t = useTheme();
  const uri = resolveImageUrl(url);
  const tone = TONE_FOR_BUCKET[bucketFor(category)] ?? 'top';
  return (
    <View
      style={{
        width: size,
        height: size * 1.25,
        borderRadius: 10,
        overflow: 'hidden',
        borderWidth: 1,
        borderColor: t.colors.borderSoft,
      }}>
      {uri ? (
        <Image source={{ uri }} style={{ width: '100%', height: '100%' }} resizeMode="cover" />
      ) : (
        <GarmentPlaceholder tone={tone} radius={10} style={{ flex: 1 }} />
      )}
    </View>
  );
}

/** Proportional bar group (no charting lib), mirrors iOS StatsScreen.barGroup. */
function BarGroup({ title, entries }: { title: string; entries: { label: string; count: number }[] }) {
  const t = useTheme();
  const maxCount = Math.max(...entries.map((e) => e.count), 1);
  return (
    <View style={{ gap: 9 }}>
      <MonoLabel size={8.5}>{title}</MonoLabel>
      <View style={{ gap: 8 }}>
        {entries.map((e, i) => {
          const fraction = e.count / maxCount;
          return (
            <View key={`${e.label}-${i}`} style={{ gap: 4 }}>
              <View style={{ flexDirection: 'row', alignItems: 'center' }}>
                <BodyText size={12.5} weight="medium" color={t.colors.text} style={{ flex: 1 }}>
                  {e.label}
                </BodyText>
                <MonoLabel size={9}>{String(e.count)}</MonoLabel>
              </View>
              <View style={{ height: 6, borderRadius: 100, backgroundColor: t.colors.borderSoft, overflow: 'hidden' }}>
                <View
                  style={{
                    height: 6,
                    borderRadius: 100,
                    backgroundColor: t.colors.accent,
                    width: `${Math.max(4, fraction * 100)}%`,
                  }}
                />
              </View>
            </View>
          );
        })}
      </View>
    </View>
  );
}

export function WardrobeStatsScreen({ onBack }: { onBack: () => void }) {
  const t = useTheme();
  const insets = useSafeAreaInsets();
  const stats = useWardrobeStats();
  const forgotten = useForgottenItems();
  const [detailId, setDetailId] = useState<string | null>(null);

  if (detailId) {
    return <WardrobeItemDetailScreen itemId={detailId} onBack={() => setDetailId(null)} />;
  }

  const data = stats.data;
  const forgottenData = forgotten.data;
  const isLoading = stats.isLoading;
  const isError = stats.isError;
  const isRefetching = stats.isRefetching || forgotten.isRefetching;

  const divider = <View style={{ height: 1, backgroundColor: t.colors.borderSoft }} />;

  const BackButton = (
    <Pressable
      onPress={onBack}
      hitSlop={10}
      accessibilityRole="button"
      accessibilityLabel="Back"
      testID="stats-back"
      style={{
        width: 30,
        height: 30,
        borderRadius: 100,
        borderWidth: 1,
        borderColor: t.colors.border,
        alignItems: 'center',
        justifyContent: 'center',
      }}>
      <AttreqIcon name="back" size={14} color={t.colors.t2} />
    </Pressable>
  );

  const refresh = () => {
    void stats.refetch();
    void forgotten.refetch();
  };

  const ItemRow = ({
    entry,
    trailing,
    subtitle,
  }: {
    entry: WornItemEntry | CostPerWearEntry;
    subtitle: string;
    trailing: React.ReactNode;
  }) => (
    <Pressable
      onPress={() => setDetailId(entry.item_id)}
      accessibilityRole="button"
      testID="stats-item-row"
      style={{ flexDirection: 'row', alignItems: 'center', gap: 12, paddingVertical: 8 }}>
      <Thumbnail url={entry.thumbnail_url} category={entry.category} />
      <View style={{ flex: 1, gap: 2 }}>
        <BodyText size={13.5} weight="medium" color={t.colors.text}>
          {itemTitle(entry.category, entry.color_primary)}
        </BodyText>
        <MonoLabel size={8.5}>{subtitle}</MonoLabel>
      </View>
      {trailing}
    </Pressable>
  );

  return (
    <View testID="stats-screen" style={{ flex: 1, backgroundColor: t.colors.bg }}>
      <ScrollView
        showsVerticalScrollIndicator={false}
        contentContainerStyle={{ paddingTop: insets.top + 12, paddingBottom: 130, paddingHorizontal: 24, gap: 18 }}
        refreshControl={<RefreshControl refreshing={isRefetching} onRefresh={refresh} tintColor={t.colors.accent} />}>
        {/* Header */}
        <View style={{ flexDirection: 'row', alignItems: 'flex-start', gap: 14 }}>
          {BackButton}
          <View style={{ gap: 5 }}>
            <MonoLabel>Closet</MonoLabel>
            <Text style={[display(28, { italic: true }), { color: t.colors.text }]}>Stats</Text>
          </View>
        </View>

        {/* Loading / error / empty */}
        {isLoading ? (
          <View style={{ paddingTop: 48, alignItems: 'center' }}>
            <ActivityIndicator color={t.colors.t2} />
          </View>
        ) : isError || !data ? (
          <View style={{ gap: 12 }}>
            <View style={{ backgroundColor: t.colors.claySoft, borderRadius: 12, paddingVertical: 10, paddingHorizontal: 13 }}>
              <BodyText size={13} color={t.colors.clay}>
                {describeAuthError(stats.error)}
              </BodyText>
            </View>
            <Pressable
              onPress={refresh}
              accessibilityRole="button"
              testID="stats-retry"
              style={{
                alignSelf: 'flex-start',
                paddingVertical: 9,
                paddingHorizontal: 18,
                borderRadius: 100,
                borderWidth: 1,
                borderColor: t.colors.border,
              }}>
              <MonoLabel size={10} color={t.colors.text}>
                Retry
              </MonoLabel>
            </Pressable>
          </View>
        ) : data.total_active_items === 0 ? (
          <Card padding={20}>
            <MonoLabel style={{ marginBottom: 8 }}>Nothing to measure yet</MonoLabel>
            <BodyText size={13}>
              Add a few pieces to your wardrobe and start wearing outfits — your closet value, cost per wear,
              and most-worn items will show up here.
            </BodyText>
          </Card>
        ) : (
          <>
            {/* Overview */}
            <Card padding={0} style={{ paddingVertical: 18, paddingHorizontal: 20 }}>
              <View style={{ flexDirection: 'row', gap: 20 }}>
                {[
                  { label: 'Active pieces', value: String(data.total_active_items), accent: false },
                  { label: 'Closet value', value: formatCurrency(data.closet_value), accent: false },
                  {
                    label: 'Never worn',
                    value: formatPercent(data.never_worn_percent),
                    accent: data.never_worn_percent >= 25,
                  },
                ].map((s) => (
                  <View key={s.label} style={{ flex: 1, gap: 3 }}>
                    <MonoLabel>{s.label}</MonoLabel>
                    <Text
                      numberOfLines={1}
                      style={[display(20, { italic: true }), { color: s.accent ? t.colors.clay : t.colors.text }]}>
                      {s.value}
                    </Text>
                  </View>
                ))}
              </View>
            </Card>

            {data.items_missing_price > 0 && (
              <View
                style={{
                  flexDirection: 'row',
                  gap: 10,
                  backgroundColor: t.colors.accentSoft,
                  borderRadius: 14,
                  padding: 12,
                }}>
                <AttreqIcon name="sparkles" size={14} color={t.colors.accent} />
                <BodyText size={12.5} color={t.colors.text} style={{ flex: 1 }}>
                  {data.items_missing_price} piece{data.items_missing_price === 1 ? '' : 's'} missing a price — add
                  one from the item's detail screen to see its cost per wear.
                </BodyText>
              </View>
            )}

            {/* Composition */}
            {(data.by_category.length > 0 || data.by_color_family.length > 0 || data.by_brand.length > 0) && (
              <>
                <MonoLabel>Composition</MonoLabel>
                <Card padding={16}>
                  <View style={{ gap: 16 }}>
                    {data.by_category.length > 0 && (
                      <BarGroup
                        title="By category"
                        entries={data.by_category.map((c) => ({ label: capitalizeLabel(c.category), count: c.count }))}
                      />
                    )}
                    {data.by_color_family.length > 0 && (
                      <>
                        {data.by_category.length > 0 && divider}
                        <BarGroup
                          title="By color family"
                          entries={data.by_color_family.map((c) => ({ label: capitalizeLabel(c.family), count: c.count }))}
                        />
                      </>
                    )}
                    {data.by_brand.length > 0 && (
                      <>
                        {(data.by_category.length > 0 || data.by_color_family.length > 0) && divider}
                        <BarGroup title="By brand" entries={data.by_brand.map((b) => ({ label: b.brand, count: b.count }))} />
                      </>
                    )}
                  </View>
                </Card>
              </>
            )}

            {/* Cost per wear */}
            {data.cost_per_wear.length > 0 && (
              <>
                <MonoLabel>Cost per wear</MonoLabel>
                <Card padding={12}>
                  {data.cost_per_wear.map((entry, i) => (
                    <React.Fragment key={entry.item_id}>
                      {i > 0 && divider}
                      <ItemRow
                        entry={entry}
                        subtitle={`${formatCurrency(entry.purchase_price)} · worn in ${outfitCountLabel(entry.wear_count)}`}
                        trailing={
                          entry.cost_per_wear != null ? (
                            <Text style={[display(15, { italic: true }), { color: t.colors.accent }]}>
                              {formatCurrency(entry.cost_per_wear)}
                            </Text>
                          ) : (
                            <Pill variant="muted">Not worn yet</Pill>
                          )
                        }
                      />
                    </React.Fragment>
                  ))}
                </Card>
              </>
            )}

            {/* Most worn */}
            {data.most_worn.length > 0 && (
              <>
                <MonoLabel>Most worn</MonoLabel>
                <WornList entries={data.most_worn} divider={divider} onOpen={setDetailId} />
              </>
            )}

            {/* Least worn */}
            {data.least_worn.length > 0 && (
              <>
                <MonoLabel>Least worn</MonoLabel>
                <WornList entries={data.least_worn} divider={divider} onOpen={setDetailId} />
              </>
            )}
          </>
        )}

        {/* Forgotten pieces (independent query; only when non-empty) */}
        {forgottenData && forgottenData.items.length > 0 && (
          <>
            <MonoLabel>Forgotten pieces</MonoLabel>
            <Card padding={16}>
              <BodyText size={12.5} style={{ marginBottom: 12 }}>
                Pieces you own but haven't reached for lately.
              </BodyText>
              {forgottenData.items.map((entry, i) => (
                <React.Fragment key={entry.item_id}>
                  {i > 0 && divider}
                  <ForgottenRow entry={entry} onOpen={setDetailId} />
                </React.Fragment>
              ))}
            </Card>
          </>
        )}
      </ScrollView>
    </View>
  );
}

function capitalizeLabel(s: string): string {
  return s ? s.charAt(0).toUpperCase() + s.slice(1) : s;
}

function WornList({
  entries,
  divider,
  onOpen,
}: {
  entries: WornItemEntry[];
  divider: React.ReactNode;
  onOpen: (id: string) => void;
}) {
  const t = useTheme();
  return (
    <Card padding={12}>
      {entries.map((entry, i) => (
        <React.Fragment key={entry.item_id}>
          {i > 0 && divider}
          <Pressable
            onPress={() => onOpen(entry.item_id)}
            accessibilityRole="button"
            testID="stats-item-row"
            style={{ flexDirection: 'row', alignItems: 'center', gap: 12, paddingVertical: 8 }}>
            <Thumbnail url={entry.thumbnail_url} category={entry.category} />
            <View style={{ flex: 1, gap: 2 }}>
              <BodyText size={13.5} weight="medium" color={t.colors.text}>
                {itemTitle(entry.category, entry.color_primary)}
              </BodyText>
              <MonoLabel size={8.5}>{wornSubtitle(entry)}</MonoLabel>
            </View>
            <Pill variant="gold">{outfitCountLabel(entry.wear_count)}</Pill>
          </Pressable>
        </React.Fragment>
      ))}
    </Card>
  );
}

function ForgottenRow({ entry, onOpen }: { entry: ForgottenItemEntry; onOpen: (id: string) => void }) {
  const t = useTheme();
  return (
    <View style={{ paddingVertical: 10, gap: 10 }}>
      <Pressable
        onPress={() => onOpen(entry.item_id)}
        accessibilityRole="button"
        testID="stats-item-row"
        style={{ flexDirection: 'row', alignItems: 'center', gap: 12 }}>
        <Thumbnail url={entry.thumbnail_url} category={entry.category} />
        <View style={{ flex: 1, gap: 2 }}>
          <BodyText size={13.5} weight="medium" color={t.colors.text}>
            {itemTitle(entry.category, entry.color_primary)}
          </BodyText>
          <MonoLabel size={8.5}>{forgottenSubtitle(entry)}</MonoLabel>
        </View>
        <AttreqIcon name="chevron" size={12} color={t.colors.t3} />
      </Pressable>
      {entry.best_partner && (
        <Pressable
          onPress={() => onOpen(entry.best_partner!.item_id)}
          accessibilityRole="button"
          style={{ flexDirection: 'row', alignItems: 'center', gap: 8, paddingLeft: 8 }}>
          <MonoLabel size={8}>Wear it with</MonoLabel>
          <Thumbnail url={entry.best_partner.thumbnail_url} category={entry.best_partner.category} size={32} />
          <BodyText size={12} style={{ flex: 1 }}>
            {itemTitle(entry.best_partner.category, entry.best_partner.color_primary)}
          </BodyText>
        </Pressable>
      )}
    </View>
  );
}
