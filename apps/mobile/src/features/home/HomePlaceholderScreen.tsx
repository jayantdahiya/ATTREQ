import React from 'react';
import { Text, View } from 'react-native';
import { useQuery } from '@tanstack/react-query';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

import { useTheme } from '@/design-system/theme/ThemeProvider';
import { display } from '@/design-system/theme/typography';
import { MonoLabel } from '@/design-system/components/MonoLabel';
import { BodyText } from '@/design-system/components/BodyText';
import { Card } from '@/design-system/components/Card';
import { PrimaryButton } from '@/design-system/components/PrimaryButton';
import { authApi } from '@/lib/api/auth';
import { queryKeys } from '@/lib/query/query-client';
import { useAuthStore } from '@/store/auth-store';

/**
 * A1 authenticated landing stub. The real tab shell (Today / Wardrobe / History /
 * Profile) is built in A2–A5; this exists so the auth + logout flow is testable.
 */
export function HomePlaceholderScreen() {
  const t = useTheme();
  const insets = useSafeAreaInsets();
  const signOut = useAuthStore((s) => s.signOut);
  const { data: user } = useQuery({ queryKey: queryKeys.me, queryFn: authApi.getCurrentUser });

  return (
    <View testID="home-screen" style={{ flex: 1, backgroundColor: t.colors.bg, paddingTop: insets.top + 24, paddingHorizontal: 28, paddingBottom: insets.bottom + 24, justifyContent: 'space-between' }}>
      <View>
        <MonoLabel style={{ marginBottom: 8 }}>ATTREQ</MonoLabel>
        <Text style={[display(34), { color: t.colors.text }]}>
          Good day,{' '}
          <Text style={display(34, { italic: true })}>{user?.full_name?.split(' ')[0] ?? 'there'}.</Text>
        </Text>
        <BodyText style={{ marginTop: 8 }}>You're signed in{user ? ` as ${user.email}` : ''}.</BodyText>

        <Card padding={20} style={{ marginTop: 24 }}>
          <MonoLabel style={{ marginBottom: 8 }}>Coming next</MonoLabel>
          <BodyText size={13}>
            The Today / Wardrobe / History / Profile tabs land in milestones A2–A5. This screen confirms the
            networking core, session, and onboarding gate are working.
          </BodyText>
        </Card>
      </View>

      <PrimaryButton label="Sign out" onPress={() => void signOut()} testID="sign-out" />
    </View>
  );
}
