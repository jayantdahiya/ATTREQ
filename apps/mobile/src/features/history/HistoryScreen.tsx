import React, { useMemo } from 'react';
import { ActivityIndicator, NativeScrollEvent, RefreshControl, ScrollView, Text, View } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

import { useTheme } from '@/design-system/theme/ThemeProvider';
import { display } from '@/design-system/theme/typography';
import { MonoLabel } from '@/design-system/components/MonoLabel';
import { BodyText } from '@/design-system/components/BodyText';
import { PrimaryButton } from '@/design-system/components/PrimaryButton';
import { OutfitHistoryCard } from '@/features/history/OutfitHistoryCard';
import { groupOutfits, PILL_LABEL, PILL_VARIANT } from '@/features/history/historyGrouping';
import { useOutfitHistory } from '@/lib/query/outfits';

function nearBottom({ layoutMeasurement, contentOffset, contentSize }: NativeScrollEvent): boolean {
  return layoutMeasurement.height + contentOffset.y >= contentSize.height - 400;
}

export function HistoryScreen() {
  const t = useTheme();
  const insets = useSafeAreaInsets();
  const query = useOutfitHistory();

  const items = useMemo(() => query.data?.pages.flatMap((p) => p.items) ?? [], [query.data]);
  const groups = useMemo(() => groupOutfits(items), [items]);
  const total = query.data?.pages[0]?.total ?? 0;

  return (
    <View testID="history-screen" style={{ flex: 1, backgroundColor: t.colors.bg }}>
      <ScrollView
        showsVerticalScrollIndicator={false}
        scrollEventThrottle={200}
        onScroll={({ nativeEvent }) => {
          if (nearBottom(nativeEvent) && query.hasNextPage && !query.isFetchingNextPage) {
            query.fetchNextPage();
          }
        }}
        contentContainerStyle={{ paddingTop: insets.top + 10, paddingHorizontal: 24, paddingBottom: 120 }}
        refreshControl={
          <RefreshControl refreshing={query.isRefetching} onRefresh={query.refetch} tintColor={t.colors.accent} />
        }>
        {/* Header */}
        <View style={{ marginBottom: 20, gap: 5 }}>
          <MonoLabel>Diary</MonoLabel>
          <View style={{ flexDirection: 'row', alignItems: 'flex-end' }}>
            <Text style={[display(28, { italic: true }), { color: t.colors.text }]}>History</Text>
            <View style={{ flex: 1 }} />
            <MonoLabel>{`${total} ${total === 1 ? 'look' : 'looks'} tracked`}</MonoLabel>
          </View>
        </View>

        {query.isLoading ? (
          <View style={{ paddingTop: 64, alignItems: 'center' }}>
            <ActivityIndicator color={t.colors.t2} />
          </View>
        ) : query.isError ? (
          <View style={{ gap: 14 }}>
            <View style={{ backgroundColor: t.colors.claySoft, borderRadius: 12, paddingVertical: 10, paddingHorizontal: 13 }}>
              <BodyText size={13} color={t.colors.clay}>
                Couldn't load your outfit history.
              </BodyText>
            </View>
            <PrimaryButton label="Retry" onPress={() => query.refetch()} />
          </View>
        ) : items.length === 0 ? (
          <View style={{ paddingTop: 48, alignItems: 'center', gap: 10, paddingHorizontal: 16 }}>
            <MonoLabel size={11}>No looks tracked yet</MonoLabel>
            <BodyText size={13} style={{ textAlign: 'center' }}>
              Wear one of today's suggestions and it will be recorded here, day by day.
            </BodyText>
          </View>
        ) : (
          <View style={{ gap: 20 }}>
            {groups.map((group) => (
              <View key={group.isoLabel} style={{ gap: 10 }}>
                <View style={{ flexDirection: 'row', alignItems: 'center', gap: 10 }}>
                  <Text style={[display(16, { italic: true }), { color: t.colors.text }]} numberOfLines={1}>
                    {group.dateLabel}
                  </Text>
                  <View style={{ flex: 1, height: 1, backgroundColor: t.colors.borderSoft }} />
                  <MonoLabel>{group.isoLabel}</MonoLabel>
                </View>
                <View style={{ gap: 8 }}>
                  {group.entries.map((entry) => (
                    <OutfitHistoryCard
                      key={entry.outfit.id}
                      outfitId={entry.outfit.id}
                      title={entry.title}
                      piecesCount={entry.pieces}
                      pillLabel={PILL_LABEL[entry.pill]}
                      pillVariant={PILL_VARIANT[entry.pill]}
                    />
                  ))}
                </View>
              </View>
            ))}
            {query.isFetchingNextPage && (
              <View style={{ paddingVertical: 16, alignItems: 'center' }}>
                <ActivityIndicator color={t.colors.t2} />
              </View>
            )}
          </View>
        )}
      </ScrollView>
    </View>
  );
}
