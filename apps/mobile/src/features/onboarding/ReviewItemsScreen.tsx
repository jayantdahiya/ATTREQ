import React from 'react';
import { Pressable, Text, View } from 'react-native';

import { useTheme } from '@/design-system/theme/ThemeProvider';
import { display } from '@/design-system/theme/typography';
import { MonoLabel } from '@/design-system/components/MonoLabel';
import { BodyText } from '@/design-system/components/BodyText';
import { Card } from '@/design-system/components/Card';
import { Pill } from '@/design-system/components/Pill';
import { PrimaryButton } from '@/design-system/components/PrimaryButton';
import { GarmentPlaceholder } from '@/design-system/components/GarmentPlaceholder';
import { AttreqIcon } from '@/design-system/icons/AttreqIcon';
import type { GarmentTone } from '@/design-system/theme/theme';
import { detectedItemDetail, detectedItemTitle } from '@/features/onboarding/detected-items';
import type { OnboardingController } from '@/features/onboarding/useOnboardingController';
import type { DetectedWardrobeItem } from '@/lib/api/types';

// Category → garment placeholder tone (mirrors iOS ReviewItemsView.tone).
function toneForCategory(category: string): GarmentTone {
  const v = category.toLowerCase();
  if (v.includes('top') || v.includes('shirt') || v.includes('dress')) return 'top';
  if (v.includes('bottom') || v.includes('pant') || v.includes('skirt') || v.includes('jean')) return 'bottom';
  if (v.includes('outer') || v.includes('jacket') || v.includes('coat')) return 'outer';
  if (v.includes('shoe') || v.includes('foot') || v.includes('sneaker') || v.includes('boot')) return 'shoes';
  return 'accent';
}

function ItemRow({
  item,
  index,
  kept,
  onToggle,
}: {
  item: DetectedWardrobeItem;
  index: number;
  kept: boolean;
  onToggle: () => void;
}) {
  const t = useTheme();
  const pct = Math.round(item.confidence * 100);
  return (
    <Pressable
      onPress={onToggle}
      accessibilityRole="button"
      accessibilityState={{ selected: kept }}
      testID={`review-item-${index}`}
      style={{ opacity: kept ? 1 : 0.45 }}>
      <Card padding={12}>
        <View style={{ flexDirection: 'row', alignItems: 'center', gap: 12 }}>
          <GarmentPlaceholder tone={toneForCategory(item.category)} radius={10} style={{ width: 46, height: 58 }} />
          <View style={{ flex: 1, gap: 3 }}>
            <Text style={[display(16, { italic: true }), { color: t.colors.text }]} numberOfLines={1}>
              {detectedItemTitle(item)}
            </Text>
            <MonoLabel>{detectedItemDetail(item)}</MonoLabel>
          </View>
          <Pill variant={item.confidence >= 0.6 ? 'gold' : 'clay'}>{pct}%</Pill>
          <View
            style={{
              width: 24,
              height: 24,
              borderRadius: 12,
              alignItems: 'center',
              justifyContent: 'center',
              backgroundColor: kept ? t.colors.accent : 'transparent',
              borderWidth: kept ? 0 : 1.5,
              borderColor: t.colors.border,
            }}>
            <AttreqIcon name={kept ? 'check' : 'x'} size={12} color={kept ? t.colors.bg : t.colors.t3} />
          </View>
        </View>
      </Card>
    </Pressable>
  );
}

export function ReviewItemsScreen({ c, onConfirm }: { c: OnboardingController; onConfirm: () => void }) {
  const t = useTheme();
  const items = c.detectedItems;

  return (
    <View testID="review-screen" style={{ gap: 0 }}>
      <MonoLabel color={t.colors.accent} style={{ marginBottom: 8 }}>
        Step 03 — Review
      </MonoLabel>
      <Text style={[display(34), { color: t.colors.text, marginBottom: 8 }]}>
        Review your{'\n'}
        <Text style={[display(34, { italic: true }), { color: t.colors.accent }]}>items.</Text>
      </Text>
      <BodyText style={{ marginBottom: 8 }}>
        We found these in your photos. Untick anything that isn't yours — you can edit any item later from
        your wardrobe.
      </BodyText>
      <MonoLabel style={{ marginBottom: 18 }}>
        High-confidence pieces were added to your wardrobe automatically
      </MonoLabel>

      {items.length === 0 ? (
        <BodyText size={13} style={{ marginBottom: 18 }}>
          No wardrobe items were detected in your photos. You can add pieces any time from the Wardrobe tab.
        </BodyText>
      ) : (
        <>
          <View style={{ gap: 10, marginBottom: 12 }}>
            {items.map((item, index) => (
              <ItemRow
                key={index}
                item={item}
                index={index}
                kept={c.reviewSelection.has(index)}
                onToggle={() => c.toggleReviewItem(index)}
              />
            ))}
          </View>
          <MonoLabel style={{ marginBottom: 18 }}>
            {c.reviewSelection.size} of {items.length} kept
          </MonoLabel>
        </>
      )}

      {c.completionError ? (
        <BodyText size={13} color={t.colors.clay} style={{ marginBottom: 12 }}>
          {c.completionError}
        </BodyText>
      ) : null}

      <PrimaryButton
        label="Looks right"
        variant="accent"
        icon="chevron"
        isLoading={c.isCompleting}
        onPress={onConfirm}
        testID="review-continue"
      />
    </View>
  );
}
