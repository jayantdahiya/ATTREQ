import React, { useState } from 'react';
import { ScrollView, View } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

import { useTheme } from '@/design-system/theme/ThemeProvider';
import { MonoLabel } from '@/design-system/components/MonoLabel';
import { StepNav } from '@/design-system/components/StepNav';
import { useOnboardingController } from '@/features/onboarding/useOnboardingController';
import { UploadStyleScreen } from '@/features/onboarding/UploadStyleScreen';
import { ResultsScreen } from '@/features/onboarding/ResultsScreen';
import { ReviewItemsScreen } from '@/features/onboarding/ReviewItemsScreen';
import { WardrobeCaptureScreen } from '@/features/onboarding/WardrobeCaptureScreen';
import { PersonalColorSelfieScreen } from '@/features/onboarding/PersonalColorSelfieScreen';

type Step = 'upload' | 'results' | 'review' | 'capture' | 'selfie';

const STEP_INDEX: Record<Step, number> = {
  upload: 0,
  results: 1,
  review: 2,
  capture: 3,
  selfie: 4,
};

/**
 * Style DNA onboarding flow shell — a JS-only step state machine (no React
 * Navigation, matching WardrobeStack). Mirrors iOS OnboardingFlowView:
 * upload → results → (review | skip to capture) → wardrobe capture (RI-7) →
 * optional personal-color selfie (RI-3) → complete. Completion flips
 * `onboarding_completed`, which the root gate observes to route to the tabs.
 */
export function OnboardingFlow() {
  const t = useTheme();
  const insets = useSafeAreaInsets();
  const c = useOnboardingController();
  const [step, setStep] = useState<Step>('upload');

  const build = async () => {
    const ok = await c.build();
    if (ok) setStep('results');
  };

  // From results: review when items were detected, else straight to capture.
  const advanceFromResults = () => {
    setStep(c.detectedItems.length === 0 ? 'capture' : 'review');
  };

  return (
    <View testID="onboarding-screen" style={{ flex: 1, backgroundColor: t.colors.bg }}>
      <ScrollView
        contentContainerStyle={{
          paddingTop: insets.top + 12,
          paddingBottom: insets.bottom + 36,
          paddingHorizontal: 28,
        }}
        keyboardShouldPersistTaps="handled">
        {/* Shared header + progress affordance (StepNav). Back is unused during
            onboarding — there is nothing before the gate and re-uploads would
            duplicate — so no onBack is wired. */}
        <View style={{ flexDirection: 'row', alignItems: 'center', gap: 10, marginBottom: 10 }}>
          <MonoLabel>Style DNA Setup</MonoLabel>
        </View>
        <View style={{ marginBottom: 26 }}>
          <StepNav step={STEP_INDEX[step]} total={5} />
        </View>

        {step === 'upload' ? (
          <UploadStyleScreen c={c} onBuild={() => void build()} onSkip={() => setStep('capture')} />
        ) : step === 'results' ? (
          <ResultsScreen c={c} onContinue={advanceFromResults} />
        ) : step === 'review' ? (
          <ReviewItemsScreen c={c} onConfirm={() => setStep('capture')} />
        ) : step === 'capture' ? (
          <WardrobeCaptureScreen c={c} onFinish={() => setStep('selfie')} />
        ) : (
          <PersonalColorSelfieScreen c={c} onDone={() => void c.complete()} />
        )}
      </ScrollView>
    </View>
  );
}
