import { router } from 'expo-router'
import { Alert, Pressable, ScrollView, View } from 'react-native'
import { SafeAreaView } from 'react-native-safe-area-context'

import { Text } from '@/components/ui/text'
import { StyleDnaCard } from '@/features/style-dna/components/style-dna-card'
import { useStyleDna, useRegenerateStyleDna } from '@/features/style-dna/hooks/use-style-dna'
import { useThemeColors } from '@/theme/colors'

export default function StyleDnaProfileScreen() {
  const { colors } = useThemeColors()
  const { data, isLoading } = useStyleDna()
  const regenerateMutation = useRegenerateStyleDna()

  if (isLoading) {
    return (
      <SafeAreaView className="flex-1 items-center justify-center" style={{ backgroundColor: colors.bgDeep }}>
        <Text style={{ color: colors.textMuted }}>Loading your style profile…</Text>
      </SafeAreaView>
    )
  }

  if (!data?.style_dna) {
    return (
      <SafeAreaView className="flex-1 items-center justify-center px-6" style={{ backgroundColor: colors.bgDeep }}>
        <Text className="text-center mb-4" style={{ color: colors.textMuted }}>
          No Style DNA profile yet. Upload some outfit photos to get started.
        </Text>
        <Pressable
          onPress={() => router.push('/(onboarding)/upload-style')}
          className="rounded-2xl px-6 py-3"
          style={{ backgroundColor: colors.accentGold }}
        >
          <Text className="font-semibold" style={{ color: colors.bgDeep }}>
            Upload photos →
          </Text>
        </Pressable>
      </SafeAreaView>
    )
  }

  return (
    <SafeAreaView className="flex-1" style={{ backgroundColor: colors.bgDeep }}>
      <ScrollView contentContainerStyle={{ padding: 24, paddingBottom: 130 }}>
        <View className="flex-row items-center justify-between mb-6 mt-4">
          <Text className="text-2xl font-bold" style={{ color: colors.textPrimary }}>
            Style DNA
          </Text>
          <Pressable onPress={() => router.back()}>
            <Text style={{ color: colors.textMuted }}>Done</Text>
          </Pressable>
        </View>

        <StyleDnaCard styleDna={data.style_dna} />

        <Text className="text-xs mt-3 mb-6" style={{ color: colors.textMuted }}>
          Based on {data.photos.length} seed photo{data.photos.length !== 1 ? 's' : ''}.
        </Text>

        <Pressable
          onPress={() => router.push('/(onboarding)/upload-style')}
          className="rounded-2xl py-4 items-center mb-3"
          style={{ borderColor: colors.borderSubtle, borderWidth: 1 }}
        >
          <Text className="text-sm font-medium" style={{ color: colors.textPrimary }}>
            Re-upload photos
          </Text>
        </Pressable>

        <Pressable
          onPress={() => {
            Alert.alert(
              'Regenerate Style DNA',
              'Re-run synthesis from your existing photos?',
              [
                { text: 'Cancel', style: 'cancel' },
                {
                  text: 'Regenerate',
                  onPress: () => regenerateMutation.mutate(),
                },
              ]
            )
          }}
          disabled={regenerateMutation.isPending}
          className="rounded-2xl py-4 items-center"
          style={{ borderColor: colors.borderSubtle, borderWidth: 1 }}
        >
          <Text className="text-sm" style={{ color: colors.textMuted }}>
            {regenerateMutation.isPending ? 'Regenerating…' : 'Regenerate from existing photos'}
          </Text>
        </Pressable>
      </ScrollView>
    </SafeAreaView>
  )
}
