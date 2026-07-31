import { Ionicons } from '@expo/vector-icons'
import { LinearGradient } from 'expo-linear-gradient'
import { useRef, useState } from 'react'
import { PanResponder, StyleSheet, View } from 'react-native'
import Animated, {
  interpolate,
  useAnimatedStyle,
  useSharedValue,
  withSpring,
} from 'react-native-reanimated'

import { EditorialCard, GarmentTile, MonoLabel, StatusPill } from '@/components/attreq/editorial'
import { Button } from '@/components/ui/button'
import { Text } from '@/components/ui/text'
import { resolveApiImageUrl } from '@/lib/utils/images'
import type { OutfitSuggestion } from '@/lib/api/types'
import { useThemeColors } from '@/theme/colors'
import { fontFamily } from '@/theme/typography'

const SWIPE_THRESHOLD = 80

interface RecommendationCardProps {
  suggestion: OutfitSuggestion
  isSubmitting?: boolean
  onWear: () => void
  onFeedback: (score: -1 | 1) => void
}

export function RecommendationCard({
  suggestion,
  isSubmitting = false,
  onWear,
  onFeedback,
}: RecommendationCardProps) {
  const { colors } = useThemeColors()
  const offsetX = useSharedValue(0)
  const [decision, setDecision] = useState<'wear' | 'skip' | null>(null)

  // stable refs so PanResponder closure always calls current callbacks
  const onWearRef = useRef(onWear)
  const onFeedbackRef = useRef(onFeedback)
  onWearRef.current = onWear
  onFeedbackRef.current = onFeedback

  const panResponder = useRef(
    PanResponder.create({
      onMoveShouldSetPanResponder: (_, gs) =>
        Math.abs(gs.dx) > 8 && Math.abs(gs.dx) > Math.abs(gs.dy) * 1.5,
      onPanResponderMove: (_, gs) => {
        offsetX.value = gs.dx
        if (gs.dx > SWIPE_THRESHOLD / 2) setDecision('wear')
        else if (gs.dx < -SWIPE_THRESHOLD / 2) setDecision('skip')
        else setDecision(null)
      },
      onPanResponderRelease: (_, gs) => {
        if (gs.dx > SWIPE_THRESHOLD) onWearRef.current()
        else if (gs.dx < -SWIPE_THRESHOLD) onFeedbackRef.current(-1)
        offsetX.value = withSpring(0, { damping: 20, stiffness: 200 })
        setDecision(null)
      },
      onPanResponderTerminate: () => {
        offsetX.value = withSpring(0, { damping: 20, stiffness: 200 })
        setDecision(null)
      },
    })
  ).current

  const cardStyle = useAnimatedStyle(() => ({
    transform: [{ translateX: offsetX.value }, { rotate: `${offsetX.value * 0.025}deg` }],
    zIndex: 1,
  }))

  const wearOpacity = useAnimatedStyle(() => ({
    opacity: interpolate(offsetX.value, [0, SWIPE_THRESHOLD / 2, SWIPE_THRESHOLD], [0, 0.5, 1], 'clamp'),
  }))

  const skipOpacity = useAnimatedStyle(() => ({
    opacity: interpolate(offsetX.value, [-SWIPE_THRESHOLD, -SWIPE_THRESHOLD / 2, 0], [1, 0.5, 0], 'clamp'),
  }))

  const topUri = resolveApiImageUrl(suggestion.top_item.image_url ?? suggestion.top_item.thumbnail_url)
  const bottomUri = resolveApiImageUrl(suggestion.bottom_item.image_url ?? suggestion.bottom_item.thumbnail_url)
  const accessoryUri = resolveApiImageUrl(
    suggestion.accessory_item?.image_url ?? suggestion.accessory_item?.thumbnail_url
  )
  const score = Math.round(suggestion.scores.total * 100)
  const lookName = suggestion.occasion_context
    ? `${suggestion.occasion_context[0]?.toUpperCase()}${suggestion.occasion_context.slice(1)}`
    : 'The Long Walk'

  return (
    <View>
      {/* Wear overlay — peeks from left as card drags right */}
      <Animated.View pointerEvents="none" style={[StyleSheet.absoluteFillObject, { borderRadius: 24, overflow: 'hidden' }, wearOpacity]}>
        <LinearGradient
          colors={[colors.mossSoft, 'transparent']}
          end={{ x: 0.65, y: 0.5 }}
          start={{ x: 0, y: 0.5 }}
          style={[StyleSheet.absoluteFillObject, { alignItems: 'center', flexDirection: 'row', gap: 6, paddingLeft: 20 }]}
        >
          <Ionicons color={colors.accentMoss} name="checkmark-circle-outline" size={18} />
          <Text preset="label" style={{ color: colors.accentMoss }}>Wear this</Text>
        </LinearGradient>
      </Animated.View>

      {/* Skip overlay — peeks from right as card drags left */}
      <Animated.View pointerEvents="none" style={[StyleSheet.absoluteFillObject, { borderRadius: 24, overflow: 'hidden' }, skipOpacity]}>
        <LinearGradient
          colors={['transparent', 'rgba(201, 96, 74, 0.22)']}
          end={{ x: 1, y: 0.5 }}
          start={{ x: 0.35, y: 0.5 }}
          style={[StyleSheet.absoluteFillObject, { alignItems: 'center', flexDirection: 'row', gap: 6, justifyContent: 'flex-end', paddingRight: 20 }]}
        >
          <Text preset="label" style={{ color: colors.accentClay }}>Skip</Text>
          <Ionicons color={colors.accentClay} name="close-outline" size={18} />
        </LinearGradient>
      </Animated.View>

      {/* Draggable card */}
      <Animated.View style={cardStyle} {...panResponder.panHandlers}>
        <EditorialCard style={{ gap: 14, padding: 16 }}>
          <View style={{ flexDirection: 'row', alignItems: 'flex-start', gap: 8, justifyContent: 'space-between' }}>
            <View style={{ flex: 1 }}>
              <MonoLabel color="accentGold">Look No. 01</MonoLabel>
              <Text
                preset="h2"
                style={{ fontFamily: fontFamily.displaySemi, fontStyle: 'italic', marginTop: 2 }}
              >
                {lookName}
              </Text>
            </View>
            <StatusPill variant="muted">{score}% match</StatusPill>
          </View>

          <View style={{ flexDirection: 'row', gap: 8, height: 216 }}>
            <GarmentTile className="flex-[1.6]" label={suggestion.top_item.category ?? 'Top'} tone="top" uri={topUri} />
            <View style={{ flex: 1, gap: 8 }}>
              <GarmentTile className="flex-[1.6]" label={suggestion.bottom_item.category ?? 'Bottom'} tone="bottom" uri={bottomUri} />
              <GarmentTile className="flex-1" label={suggestion.accessory_item?.category ?? 'Accent'} tone="accent" uri={accessoryUri} />
            </View>
          </View>

          <View style={{ flexDirection: 'row', flexWrap: 'wrap', gap: 8 }}>
            <Text color="textTertiary" preset="label">
              {Math.round(suggestion.weather_context.temp)}°C — {suggestion.weather_context.condition}
            </Text>
            <Text preset="label" style={{ color: colors.accentOlive }}>
              — {suggestion.weather_context.description ?? 'Layered'}
            </Text>
          </View>

          <View style={{ height: 1, backgroundColor: colors.borderSoft }} />

          <View style={{ alignItems: 'center', flexDirection: 'row', justifyContent: 'space-between' }}>
            <View style={{ alignItems: 'center', flexDirection: 'row', gap: 8 }}>
              <View style={{ alignItems: 'center', flexDirection: 'row', gap: 4 }}>
                <Ionicons color={colors.textTertiary} name="arrow-back-outline" size={14} />
                <Text color="textTertiary" preset="label">Skip</Text>
              </View>
              <View style={{ backgroundColor: colors.borderSubtle, height: 12, width: 1 }} />
              <View style={{ alignItems: 'center', flexDirection: 'row', gap: 4 }}>
                <Text preset="label" style={{ color: colors.accentMoss }}>Wear</Text>
                <Ionicons color={colors.accentMoss} name="arrow-forward-outline" size={14} />
              </View>
            </View>
            <View style={{ flexDirection: 'row', gap: 8 }}>
              <Button
                className="w-14"
                disabled={isSubmitting}
                icon={<Ionicons color={colors.accentGold} name="heart-outline" size={17} />}
                onPress={() => onFeedback(1)}
                variant="ghost"
              />
              <Button
                className="w-14"
                disabled={isSubmitting}
                icon={<Ionicons color={colors.textSecondary} name="close-outline" size={19} />}
                onPress={() => onFeedback(-1)}
                variant="secondary"
              />
            </View>
          </View>

          <Button
            icon={<Ionicons color="#F0EDE6" name="checkmark-circle-outline" size={17} />}
            isLoading={isSubmitting}
            label="Wear this"
            onPress={onWear}
          />
        </EditorialCard>
      </Animated.View>
    </View>
  )
}
