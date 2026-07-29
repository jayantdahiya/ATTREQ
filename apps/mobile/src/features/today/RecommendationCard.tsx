import React from 'react';
import { Pressable, Text, View } from 'react-native';

import { useTheme } from '@/design-system/theme/ThemeProvider';
import { display } from '@/design-system/theme/typography';
import { Card } from '@/design-system/components/Card';
import { MonoLabel } from '@/design-system/components/MonoLabel';
import { BodyText } from '@/design-system/components/BodyText';
import { Pill } from '@/design-system/components/Pill';
import { PrimaryButton } from '@/design-system/components/PrimaryButton';
import { AttreqIcon } from '@/design-system/icons/AttreqIcon';
import { GarmentCollage } from '@/features/today/GarmentCollage';
import type { OutfitSuggestion } from '@/lib/api/types';

export function RecommendationCard({
  suggestion,
  lookNumber,
  title,
  isWearing,
  isSubmittingFeedback,
  onWear,
  onSkip,
  onLove,
  onDismiss,
}: {
  suggestion: OutfitSuggestion;
  lookNumber: number;
  title: string;
  isWearing: boolean;
  isSubmittingFeedback: boolean;
  onWear: () => void;
  onSkip: () => void;
  onLove: () => void;
  onDismiss: () => void;
}) {
  const t = useTheme();
  const busy = isWearing || isSubmittingFeedback;
  const lowConfidence = suggestion.confidence === 'low';
  const percent = Math.min(100, Math.max(0, Math.round((suggestion.scores.total ?? 0) * 100)));
  const weatherLine = `${Math.round(suggestion.weather_context.temp)}°C — ${suggestion.weather_context.condition}`;
  const explanation = suggestion.explanation?.trim();

  return (
    <Card padding={16}>
      {/* Title row */}
      <View style={{ flexDirection: 'row', alignItems: 'flex-start', marginBottom: 14 }}>
        <View style={{ flex: 1, gap: 3 }}>
          <MonoLabel color={t.colors.accent}>{`Look No. ${String(lookNumber).padStart(2, '0')}`}</MonoLabel>
          <Text style={[display(22, { italic: true }), { color: t.colors.text }]}>{title}</Text>
        </View>
        <View style={{ alignItems: 'flex-end', gap: 6, marginLeft: 10 }}>
          {lowConfidence ? <Pill variant="clay">Experimental</Pill> : <Pill variant="muted">{`${percent}% match`}</Pill>}
          {suggestion.rediscovery && <Pill variant="gold">Rediscover</Pill>}
        </View>
      </View>

      <View style={{ marginBottom: 12 }}>
        <GarmentCollage suggestion={suggestion} layout="card" />
      </View>

      {/* Explanation */}
      {explanation ? (
        <View style={{ marginBottom: 11, gap: 6 }}>
          {lowConfidence && (
            <View style={{ height: 1, borderTopWidth: 1, borderColor: t.colors.clay, borderStyle: 'dashed' }} />
          )}
          <BodyText size={13} color={lowConfidence ? t.colors.clay : t.colors.t2} testID="label-explanation">
            {explanation}
          </BodyText>
        </View>
      ) : null}

      {/* Context row */}
      <View style={{ flexDirection: 'row', gap: 10, marginBottom: 11 }}>
        <MonoLabel>{weatherLine}</MonoLabel>
        <MonoLabel color={t.colors.accent}>{`— ${suggestion.occasion_context}`}</MonoLabel>
      </View>

      <View style={{ height: 1, backgroundColor: t.colors.borderSoft, marginBottom: 11 }} />

      {/* Actions row */}
      <View style={{ flexDirection: 'row', alignItems: 'center', marginBottom: 11 }}>
        <View style={{ flexDirection: 'row', alignItems: 'center', gap: 10 }}>
          <Pressable
            onPress={onSkip}
            disabled={busy}
            accessibilityRole="button"
            accessibilityLabel="Skip look"
            testID="action-skip"
            style={{ flexDirection: 'row', alignItems: 'center', gap: 4 }}>
            <AttreqIcon name="arrowLeft" size={11} color={t.colors.t3} />
            <MonoLabel>Skip</MonoLabel>
          </Pressable>
          <View style={{ width: 1, height: 11, backgroundColor: t.colors.border }} />
          <Pressable
            onPress={onWear}
            disabled={busy}
            accessibilityRole="button"
            accessibilityLabel="Wear look"
            testID="action-wear"
            style={{ flexDirection: 'row', alignItems: 'center', gap: 4 }}>
            <MonoLabel color={t.colors.moss}>Wear</MonoLabel>
            <AttreqIcon name="arrowRight" size={11} color={t.colors.moss} />
          </Pressable>
        </View>

        <View style={{ flex: 1 }} />

        <View style={{ flexDirection: 'row', alignItems: 'center', gap: 6 }}>
          <Pressable
            onPress={onLove}
            disabled={busy}
            accessibilityRole="button"
            accessibilityLabel="Love look"
            testID="action-love"
            style={{
              width: 33,
              height: 33,
              borderRadius: 999,
              borderWidth: 1,
              borderColor: t.colors.border,
              alignItems: 'center',
              justifyContent: 'center',
            }}>
            <AttreqIcon name="heart" size={13} color={t.colors.accent} />
          </Pressable>
          <Pressable
            onPress={onDismiss}
            disabled={busy}
            accessibilityRole="button"
            accessibilityLabel="Dismiss look"
            testID="action-dismiss"
            style={{
              width: 33,
              height: 33,
              borderRadius: 999,
              backgroundColor: t.colors.accentSoft,
              alignItems: 'center',
              justifyContent: 'center',
            }}>
            <AttreqIcon name="x" size={13} color={t.colors.t2} />
          </Pressable>
        </View>
      </View>

      <PrimaryButton
        label="Wear this"
        icon="check"
        isLoading={isWearing}
        disabled={isSubmittingFeedback}
        onPress={onWear}
        testID="today-wear-cta"
      />
    </Card>
  );
}
