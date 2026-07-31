import React, { useState } from 'react';
import { Image, Pressable, Text, View } from 'react-native';

import { useTheme } from '@/design-system/theme/ThemeProvider';
import { display } from '@/design-system/theme/typography';
import { MonoLabel } from '@/design-system/components/MonoLabel';
import { BodyText } from '@/design-system/components/BodyText';
import { PrimaryButton } from '@/design-system/components/PrimaryButton';
import { AttreqIcon } from '@/design-system/icons/AttreqIcon';
import { pickMultipleFromLibrary } from '@/lib/media/image-picker';
import type { UploadAsset } from '@/lib/api/wardrobe';
import type { OnboardingController } from '@/features/onboarding/useOnboardingController';

const PRIVACY_LINES = [
  'Analyzed once by a third-party vendor for undertone and depth — never a season label.',
  "Never stored. The photo isn't saved by us or the vendor once analysis finishes.",
  'Optional and skippable. This has near-zero effect on your recommendations either way.',
];

export function PersonalColorSelfieScreen({ c, onDone }: { c: OnboardingController; onDone: () => void }) {
  const t = useTheme();
  const [selfie, setSelfie] = useState<UploadAsset | null>(null);
  const [consent, setConsent] = useState(false);

  const analyzing = c.personalColorState === 'analyzing';
  const done = c.personalColorState === 'done';

  const pick = async () => {
    const picked = await pickMultipleFromLibrary(1);
    if (picked[0]) {
      setSelfie(picked[0]);
      setConsent(false);
    }
  };

  const analyze = () => {
    if (selfie && consent) void c.estimatePersonalColor(selfie, true);
  };

  return (
    <View testID="selfie-screen" style={{ gap: 0 }}>
      <MonoLabel color={t.colors.accent} style={{ marginBottom: 8 }}>
        Step 05 — Coloring
      </MonoLabel>
      <Text style={[display(34), { color: t.colors.text, marginBottom: 8 }]}>
        Fine-tune your{'\n'}
        <Text style={[display(34, { italic: true }), { color: t.colors.accent }]}>coloring.</Text>
      </Text>
      <BodyText style={{ marginBottom: 20 }}>
        Optional. A single selfie lets us fine-tune color picks to your undertone — skip it any time with no
        downside.
      </BodyText>

      <View style={{ padding: 14, borderRadius: 16, backgroundColor: t.colors.accentSoft, gap: 8, marginBottom: 20 }}>
        {PRIVACY_LINES.map((line) => (
          <View key={line} style={{ flexDirection: 'row', gap: 8 }}>
            <AttreqIcon name="sparkles" size={12} color={t.colors.accent} />
            <BodyText size={13} color={t.colors.text} style={{ flex: 1 }}>
              {line}
            </BodyText>
          </View>
        ))}
      </View>

      {selfie ? (
        <View
          style={{
            flexDirection: 'row',
            alignItems: 'center',
            gap: 12,
            padding: 14,
            borderRadius: 20,
            borderWidth: 1,
            borderColor: t.colors.border,
            backgroundColor: t.colors.surface,
            marginBottom: 16,
          }}>
          <Image
            source={{ uri: selfie.uri }}
            style={{ width: 84, height: 84, borderRadius: 42, borderWidth: 1, borderColor: t.colors.border }}
          />
          <View style={{ gap: 6 }}>
            <Text style={{ color: t.colors.text, fontSize: 14, fontWeight: '500' }}>Selfie ready</Text>
            <Pressable
              onPress={() => {
                setSelfie(null);
                setConsent(false);
              }}
              disabled={analyzing}
              accessibilityRole="button">
              <BodyText size={13}>Choose a different photo</BodyText>
            </Pressable>
          </View>
        </View>
      ) : (
        <Pressable
          onPress={pick}
          testID="selfie-pick"
          accessibilityRole="button"
          style={{
            borderRadius: 20,
            borderWidth: 1.5,
            borderColor: t.colors.border,
            borderStyle: 'dashed',
            backgroundColor: t.colors.surface,
            paddingVertical: 12,
            paddingHorizontal: 13,
            gap: 5,
            marginBottom: 16,
          }}>
          <View
            style={{
              width: 28,
              height: 28,
              borderRadius: 14,
              backgroundColor: t.colors.accentSoft,
              alignItems: 'center',
              justifyContent: 'center',
            }}>
            <AttreqIcon name="person" size={13} color={t.colors.t2} />
          </View>
          <Text style={{ color: t.colors.text, fontSize: 13, fontWeight: '500' }}>Pick a selfie</Text>
          <MonoLabel>A single, clear, well-lit face photo</MonoLabel>
        </Pressable>
      )}

      {selfie ? (
        <Pressable
          onPress={() => setConsent((v) => !v)}
          disabled={analyzing}
          testID="selfie-consent"
          accessibilityRole="checkbox"
          accessibilityState={{ checked: consent }}
          style={{ flexDirection: 'row', gap: 10, marginBottom: 16 }}>
          <View
            style={{
              width: 20,
              height: 20,
              borderRadius: 5,
              alignItems: 'center',
              justifyContent: 'center',
              backgroundColor: consent ? t.colors.accent : 'transparent',
              borderWidth: consent ? 0 : 1.5,
              borderColor: t.colors.t3,
            }}>
            {consent ? <AttreqIcon name="check" size={12} color={t.colors.bg} /> : null}
          </View>
          <BodyText size={13} color={t.colors.text} style={{ flex: 1 }}>
            I consent to this one-time analysis by a third-party vendor. I understand my photo will not be
            stored.
          </BodyText>
        </Pressable>
      ) : null}

      {c.personalColorState === 'failed' && c.personalColorError ? (
        <View style={{ padding: 12, borderRadius: 12, backgroundColor: t.colors.claySoft, marginBottom: 12 }}>
          <BodyText size={13} color={t.colors.clay}>
            Couldn't complete the analysis ({c.personalColorError}) — no problem, continue anytime.
          </BodyText>
        </View>
      ) : null}
      {done ? (
        <View
          style={{
            flexDirection: 'row',
            alignItems: 'center',
            gap: 10,
            padding: 12,
            borderRadius: 14,
            backgroundColor: t.colors.mossSoft,
            marginBottom: 12,
          }}>
          <AttreqIcon name="check" size={14} color={t.colors.moss} />
          <BodyText size={13} color={t.colors.moss}>
            Got it — your color picks are fine-tuned.
          </BodyText>
        </View>
      ) : null}

      <View style={{ gap: 13, marginTop: 16 }}>
        {selfie && !done ? (
          <PrimaryButton
            label="Analyze"
            variant="accent"
            icon="chevron"
            isLoading={analyzing}
            disabled={!consent}
            onPress={analyze}
            testID="selfie-analyze"
          />
        ) : null}
        <PrimaryButton
          label={done ? 'Continue' : 'Skip for now'}
          isLoading={c.isCompleting}
          disabled={analyzing}
          onPress={onDone}
          testID="selfie-skip"
        />
      </View>
    </View>
  );
}
