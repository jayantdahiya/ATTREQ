import { View } from 'react-native'

import { Text } from '@/components/ui/text'
import type { StyleDna } from '@/lib/api/types'
import { useThemeColors } from '@/theme/colors'
import { ConfidenceBadge } from './confidence-badge'

interface StyleDnaCardProps {
  styleDna: StyleDna
  onEditField?: (field: string) => void
}

function Row({ label, value, confidence }: { label: string; value: string; confidence?: number }) {
  const { colors } = useThemeColors()
  return (
    <View className="flex-row items-start justify-between py-2 border-b" style={{ borderColor: colors.borderSubtle }}>
      <Text className="text-sm font-medium w-24" style={{ color: colors.textMuted }}>
        {label}
      </Text>
      <View className="flex-1 flex-row flex-wrap gap-1 justify-end">
        <Text className="text-sm text-right" style={{ color: colors.textPrimary }}>
          {value}
        </Text>
        {confidence !== undefined && <ConfidenceBadge confidence={confidence} />}
      </View>
    </View>
  )
}

export function StyleDnaCard({ styleDna }: StyleDnaCardProps) {
  const { colors } = useThemeColors()

  const aesthetic =
    [styleDna.aesthetic.primary, ...styleDna.aesthetic.secondary].join(' · ') || '—'
  const palette = styleDna.color_palette.dominant.slice(0, 4).join('  ') || '—'
  const patterns = styleDna.patterns.preferred.join(', ') || 'Solid'
  const silhouette = styleDna.silhouette.preference || '—'
  const formality = `${styleDna.formality_bias.label} (${styleDna.formality_bias.level.toFixed(1)}/3)`

  return (
    <View
      className="rounded-2xl p-5"
      style={{ backgroundColor: colors.cardBg, borderColor: colors.borderSubtle, borderWidth: 1 }}
    >
      <View className="flex-row items-center gap-2 mb-4">
        <Text className="text-base font-semibold" style={{ color: colors.textPrimary }}>
          ✦ Your Style DNA
        </Text>
      </View>

      <Row label="Aesthetic" value={aesthetic} confidence={styleDna.aesthetic.confidence} />
      <Row label="Palette" value={palette} confidence={styleDna.color_palette.confidence} />
      <Row label="Pattern" value={patterns} confidence={styleDna.patterns.confidence} />
      <Row label="Silhouette" value={silhouette} confidence={styleDna.silhouette.confidence} />
      <Row label="Formality" value={formality} confidence={styleDna.formality_bias.confidence} />
    </View>
  )
}
