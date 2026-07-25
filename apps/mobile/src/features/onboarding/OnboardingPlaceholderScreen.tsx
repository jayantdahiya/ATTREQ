import React, { useState } from 'react';
import { Text, View } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

import { useTheme } from '@/design-system/theme/ThemeProvider';
import { display } from '@/design-system/theme/typography';
import { MonoLabel } from '@/design-system/components/MonoLabel';
import { BodyText } from '@/design-system/components/BodyText';
import { PrimaryButton } from '@/design-system/components/PrimaryButton';
import { usersApi } from '@/lib/api/users';
import { queryClient, queryKeys } from '@/lib/query/query-client';
import { useAuthStore } from '@/store/auth-store';
import { describeAuthError } from '@/lib/api/errors';

/**
 * A1 onboarding-gate stub. The real Style-DNA onboarding (upload → results →
 * review, selfie, batch capture) is A3. Completing here flips
 * `onboarding_completed`, which the root gate observes to route to Home.
 */
export function OnboardingPlaceholderScreen() {
  const t = useTheme();
  const insets = useSafeAreaInsets();
  const signOut = useAuthStore((s) => s.signOut);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const complete = async () => {
    setError(null);
    setLoading(true);
    try {
      const user = await usersApi.completeOnboarding();
      queryClient.setQueryData(queryKeys.me, user);
    } catch (e) {
      setError(describeAuthError(e));
    } finally {
      setLoading(false);
    }
  };

  return (
    <View testID="onboarding-screen" style={{ flex: 1, backgroundColor: t.colors.bg, paddingTop: insets.top + 24, paddingHorizontal: 28, paddingBottom: insets.bottom + 24, justifyContent: 'space-between' }}>
      <View>
        <MonoLabel color={t.colors.accent} style={{ marginBottom: 8 }}>
          Almost there
        </MonoLabel>
        <Text style={[display(34), { color: t.colors.text }]}>
          Let's build your{' '}
          <Text style={display(34, { italic: true })}>Style DNA.</Text>
        </Text>
        <BodyText style={{ marginTop: 8 }}>
          The full onboarding (photo upload, results, review, personal-color selfie, batch capture) arrives in A3.
          For now, continue to finish setup.
        </BodyText>
        {error ? <BodyText size={13} color={t.colors.clay} style={{ marginTop: 14 }}>{error}</BodyText> : null}
      </View>

      <View style={{ gap: 12 }}>
        <PrimaryButton label={loading ? 'Finishing…' : 'Continue'} variant="accent" isLoading={loading} onPress={complete} testID="complete-onboarding" />
        <PrimaryButton label="Sign out" onPress={() => void signOut()} testID="sign-out" />
      </View>
    </View>
  );
}
