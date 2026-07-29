import { useQuery } from '@tanstack/react-query'
import { ScrollView, View } from 'react-native'
import { SafeAreaView } from 'react-native-safe-area-context'

import { EditorialCard, EditorialHeader, GarmentTile, MonoLabel, StatusPill, fontFamily } from '@/components/attreq/editorial'
import { EmptyState } from '@/components/common/empty-state'
import { LoadingScreen } from '@/components/common/loading-screen'
import { Text } from '@/components/ui/text'
import { outfitsApi } from '@/lib/api/outfits'
import type { Outfit } from '@/lib/api/types'
import { queryKeys } from '@/lib/query/query-client'
import { useThemeColors } from '@/theme/colors'

function dateKey(outfit: Outfit) {
  return outfit.worn_date ?? outfit.created_at.slice(0, 10)
}

function groupOutfits(items: Outfit[]) {
  return items.reduce<Record<string, Outfit[]>>((acc, item) => {
    const key = dateKey(item)
    acc[key] = [...(acc[key] ?? []), item]
    return acc
  }, {})
}

function formatDay(key: string) {
  const date = new Date(`${key}T00:00:00`)
  if (Number.isNaN(date.getTime())) return key
  return new Intl.DateTimeFormat('en', { weekday: 'long', month: '2-digit', day: '2-digit' }).format(date)
}

function HistoryLookCard({ outfit }: { outfit: Outfit }) {
  const label = outfit.feedback_score === 1 ? 'Loved' : outfit.feedback_score === -1 ? 'Skipped' : outfit.worn_date ? 'Worn' : 'Tracked'
  const variant = outfit.feedback_score === 1 ? 'gold' : outfit.feedback_score === -1 ? 'clay' : outfit.worn_date ? 'moss' : 'muted'

  return (
    <EditorialCard className="flex-row gap-3 p-3">
      <View className="flex-row gap-1">
        <GarmentTile className="h-16 w-12 rounded-xl" tone="top" />
        <GarmentTile className="h-16 w-12 rounded-xl" tone="bottom" />
        <GarmentTile className="h-16 w-12 rounded-xl" tone="accent" />
      </View>
      <View className="min-w-0 flex-1 justify-between">
        <View>
          <Text preset="h3" style={{ fontFamily: fontFamily.displaySemi, fontStyle: 'italic' }}>
            {outfit.occasion_context ?? 'Saved outfit'}
          </Text>
          <MonoLabel>3 pieces</MonoLabel>
        </View>
        <View className="self-start">
          <StatusPill variant={variant}>{label}</StatusPill>
        </View>
      </View>
    </EditorialCard>
  )
}

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
  const grouped = groupOutfits(items)
  const groupKeys = Object.keys(grouped).sort((a, b) => b.localeCompare(a))

  return (
    <SafeAreaView className="flex-1" style={{ backgroundColor: colors.bgDeep }}>
      <ScrollView contentContainerStyle={{ padding: 24, paddingBottom: 130 }}>
        <EditorialHeader
          label="Diary"
          subtitle={`${items.length} looks tracked`}
          title="History"
        />

        {items.length === 0 ? (
          <View className="mt-6">
            <EmptyState
              title="No outfit history yet"
              message="Wear or rate one of today's suggestions to start building history."
            />
          </View>
        ) : (
          <View className="mt-7">
            {groupKeys.map((key) => (
              <View key={key} className="mb-7">
                <View className="mb-3 flex-row items-center gap-3">
                  <Text preset="h2" style={{ fontFamily: fontFamily.displaySemi, fontStyle: 'italic' }}>
                    {formatDay(key)}
                  </Text>
                  <View className="h-px flex-1" style={{ backgroundColor: colors.borderSoft }} />
                  <MonoLabel>{key}</MonoLabel>
                </View>
                <View className="gap-3">
                  {grouped[key].map((outfit) => (
                    <HistoryLookCard key={outfit.id} outfit={outfit} />
                  ))}
                </View>
              </View>
            ))}
          </View>
        )}
      </ScrollView>
    </SafeAreaView>
  )
}
