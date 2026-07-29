import React from 'react';
import { Text, View } from 'react-native';

import { useTheme } from '@/design-system/theme/ThemeProvider';
import { display } from '@/design-system/theme/typography';
import { MonoLabel } from '@/design-system/components/MonoLabel';
import { BodyText } from '@/design-system/components/BodyText';
import { PrimaryButton } from '@/design-system/components/PrimaryButton';
import { StyleDnaCard } from '@/features/style-dna/StyleDnaCard';
import { detectedItemsPreview } from '@/features/onboarding/detected-items';
import type { OnboardingController } from '@/features/onboarding/useOnboardingController';

export function ResultsScreen({ c, onContinue }: { c: OnboardingController; onContinue: () => void }) {
  const t = useTheme();
  const response = c.uploadResponse;
  const dna = response?.style_dna ?? null;
  const items = c.detectedItems;

  const subtitle = response
    ? `Based on ${response.photos_processed} photo${response.photos_processed === 1 ? '' : 's'}.` +
      (response.photos_skipped > 0 ? ` ${response.photos_skipped} skipped (low quality).` : '')
    : '';

  return (
    <View testID="results-screen" style={{ gap: 0 }}>
      <MonoLabel color={t.colors.accent} style={{ marginBottom: 8 }}>
        Step 02 — Results
      </MonoLabel>
      <Text style={[display(34), { color: t.colors.text, marginBottom: 8 }]}>
        Your{'\n'}
        <Text style={[display(34, { italic: true }), { color: t.colors.accent }]}>Style DNA.</Text>
      </Text>
      <BodyText style={{ marginBottom: 20 }}>{subtitle}</BodyText>

      {dna ? (
        <View style={{ marginBottom: 14 }}>
          <StyleDnaCard dna={dna} testID="results-dna-card" />
        </View>
      ) : (
        <View
          style={{
            marginBottom: 14,
            padding: 14,
            borderRadius: 16,
            backgroundColor: t.colors.claySoft,
            gap: 6,
          }}>
          <MonoLabel color={t.colors.clay}>Extraction failed</MonoLabel>
          <BodyText size={13} color={t.colors.clay}>
            We couldn't read your style from these photos this time. Your photos are saved — you can
            regenerate your Style DNA from your profile later.
          </BodyText>
        </View>
      )}

      {items.length > 0 ? (
        <View style={{ marginBottom: 14, padding: 16, borderRadius: 16, backgroundColor: t.colors.accentSoft, gap: 5 }}>
          <MonoLabel color={t.colors.accent}>Wardrobe</MonoLabel>
          <Text style={[display(20, { italic: true }), { color: t.colors.text }]}>
            {items.length} wardrobe item{items.length === 1 ? '' : 's'} found
          </Text>
          <BodyText size={13}>{detectedItemsPreview(items)}</BodyText>
        </View>
      ) : null}

      {c.completionError ? (
        <BodyText size={13} color={t.colors.clay} style={{ marginBottom: 12 }}>
          {c.completionError}
        </BodyText>
      ) : null}

      <View style={{ marginTop: 16 }}>
        <PrimaryButton
          label={items.length === 0 ? 'Looks right' : 'Review items'}
          variant="accent"
          icon="chevron"
          isLoading={c.isCompleting}
          onPress={onContinue}
          testID="results-continue"
        />
      </View>
    </View>
  );
}
