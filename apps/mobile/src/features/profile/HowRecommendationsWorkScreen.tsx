import React from 'react';
import { Pressable, ScrollView, Text, View } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

import { useTheme } from '@/design-system/theme/ThemeProvider';
import { display } from '@/design-system/theme/typography';
import { MonoLabel } from '@/design-system/components/MonoLabel';
import { BodyText } from '@/design-system/components/BodyText';
import { Card } from '@/design-system/components/Card';
import { AttreqIcon, type AttreqIconName } from '@/design-system/icons/AttreqIcon';

// Static "trust" screen (RI-7) — copy ported verbatim from the iOS
// HowRecommendationsWorkView.swift. No network calls.
const SECTIONS: { icon: AttreqIconName; title: string; body: string }[] = [
  {
    icon: 'shirt',
    title: 'Only your own clothes',
    body: "Every recommendation is built from pieces already in your wardrobe. We never suggest anything to buy, and nothing here is sponsored, an ad, or an affiliate link — if it's in your closet, it's fair game; if it isn't, it never shows up.",
  },
  {
    icon: 'sparkles',
    title: '"Why we picked this"',
    body: "Under each outfit you'll see a short line explaining the thinking behind it. That reasoning is still getting richer — today it reflects things like color and formality matching your occasion; over time it will speak more specifically to your taste as that part of ATTREQ matures.",
  },
  {
    icon: 'heart',
    title: 'Your feedback trains it',
    body: "Loving, skipping, or wearing an outfit isn't just for your own history — each one quietly adjusts what gets suggested next. Wear something often and you'll see more like it; skip something and ATTREQ leans away from it.",
  },
];

export function HowRecommendationsWorkScreen({ onBack }: { onBack: () => void }) {
  const t = useTheme();
  const insets = useSafeAreaInsets();

  return (
    <View testID="how-it-works-screen" style={{ flex: 1, backgroundColor: t.colors.bg }}>
      <ScrollView
        showsVerticalScrollIndicator={false}
        contentContainerStyle={{ paddingTop: insets.top + 12, paddingBottom: 130, paddingHorizontal: 24, gap: 18 }}>
        <View style={{ flexDirection: 'row', alignItems: 'flex-start', gap: 14 }}>
          <Pressable
            onPress={onBack}
            hitSlop={10}
            accessibilityRole="button"
            accessibilityLabel="Back"
            testID="how-it-works-back"
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
          <View style={{ gap: 5 }}>
            <MonoLabel>Trust</MonoLabel>
            <Text style={[display(30, { italic: true }), { color: t.colors.text }]}>How this{'\n'}works.</Text>
          </View>
        </View>

        <View style={{ gap: 18, marginTop: 4 }}>
          {SECTIONS.map((s) => (
            <Card key={s.title} padding={16}>
              <View style={{ flexDirection: 'row', alignItems: 'center', gap: 10, marginBottom: 10 }}>
                <View
                  style={{
                    width: 30,
                    height: 30,
                    borderRadius: 100,
                    backgroundColor: t.colors.accentSoft,
                    alignItems: 'center',
                    justifyContent: 'center',
                  }}>
                  <AttreqIcon name={s.icon} size={14} color={t.colors.accent} />
                </View>
                <Text style={[display(18, { italic: true }), { color: t.colors.text }]}>{s.title}</Text>
              </View>
              <BodyText size={13.5}>{s.body}</BodyText>
            </Card>
          ))}
        </View>
      </ScrollView>
    </View>
  );
}
