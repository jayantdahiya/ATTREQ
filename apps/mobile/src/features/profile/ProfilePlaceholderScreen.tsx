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

/** A2 Profile stub — full profile (stats, Style DNA row, prefs, reminder) is A5. */
export function ProfilePlaceholderScreen() {
  const t = useTheme();
  const insets = useSafeAreaInsets();
  const signOut = useAuthStore((s) => s.signOut);
  const { data: user } = useQuery({ queryKey: queryKeys.me, queryFn: authApi.getCurrentUser });

  return (
    <View
      testID="profile-screen"
      style={{ flex: 1, backgroundColor: t.colors.bg, paddingTop: insets.top + 24, paddingHorizontal: 28, paddingBottom: 130, justifyContent: 'space-between' }}>
      <View>
        <MonoLabel style={{ marginBottom: 8 }}>PROFILE</MonoLabel>
        <Text style={[display(34), { color: t.colors.text }]}>
          {user?.full_name?.split(' ')[0] ?? 'You'}
          <Text style={display(34, { italic: true })}>.</Text>
        </Text>
        <BodyText style={{ marginTop: 8 }}>{user?.email ?? ''}</BodyText>
        <Card padding={18} style={{ marginTop: 24 }}>
          <MonoLabel style={{ marginBottom: 8 }}>Coming in A5</MonoLabel>
          <BodyText size={13}>Stats, Style DNA, preferences, and the daily reminder land in milestone A5.</BodyText>
        </Card>
      </View>
      <PrimaryButton label="Sign out" onPress={() => void signOut()} testID="sign-out" />
    </View>
  );
}
