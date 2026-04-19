import { FlashList } from '@shopify/flash-list'
import { useQuery } from '@tanstack/react-query'
import { View } from 'react-native'
import { SafeAreaView } from 'react-native-safe-area-context'

import { AnimatedListItem } from '@/components/common/animated-list-item'
import { EmptyState } from '@/components/common/empty-state'
import { LoadingScreen } from '@/components/common/loading-screen'
import { ScreenHeader } from '@/components/common/screen-header'
import { OutfitHistoryCard } from '@/features/outfits/outfit-history-card'
import { outfitsApi } from '@/lib/api/outfits'
import { queryKeys } from '@/lib/query/query-client'
import { useThemeColors } from '@/theme/colors'

export function HistoryScreen() {
  const { colors } = useThemeColors()
  const outfitsQuery = useQuery({
    queryKey: queryKeys.outfits,
    queryFn: () => outfitsApi.listOutfits(),
  })

  if (outfitsQuery.isLoading) {
    return <LoadingScreen label="Loading your outfit history" />
  }

  const items = outfitsQuery.data?.items ?? []

  return (
    <SafeAreaView className="flex-1" style={{ backgroundColor: colors.bgDeep }}>
      <FlashList
        contentContainerStyle={{ padding: 24, paddingBottom: 120 }}
        data={items}
        keyExtractor={(item) => item.id}
        ListHeaderComponent={
          <View className="mb-6">
            <ScreenHeader
              heading="Feedback and wear tracking live here."
              label="HISTORY"
              subtitle="Each action from today’s suggestions becomes a concrete outfit record."
            />
            {items.length === 0 ? (
              <View className="mt-6">
                <EmptyState
                  title="No outfit history yet"
                  message="Wear or rate one of today’s suggestions to start building history."
                />
              </View>
            ) : null}
          </View>
        }
        renderItem={({ item, index }) => (
          <AnimatedListItem index={index}>
            <OutfitHistoryCard outfit={item} />
          </AnimatedListItem>
        )}
        ItemSeparatorComponent={() => <View className="h-4" />}
      />
    </SafeAreaView>
  )
}
