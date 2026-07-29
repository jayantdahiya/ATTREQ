import React, { useState } from 'react';
import { ActivityIndicator, Pressable, ScrollView, Text, View } from 'react-native';
import { useQuery } from '@tanstack/react-query';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

import { useTheme } from '@/design-system/theme/ThemeProvider';
import { display } from '@/design-system/theme/typography';
import { MonoLabel } from '@/design-system/components/MonoLabel';
import { BodyText } from '@/design-system/components/BodyText';
import { Card } from '@/design-system/components/Card';
import { PrimaryButton } from '@/design-system/components/PrimaryButton';
import { AttreqIcon } from '@/design-system/icons/AttreqIcon';
import { StyleDnaCard } from '@/features/style-dna/StyleDnaCard';
import { StyleDnaProfileScreen } from '@/features/style-dna/StyleDnaProfileScreen';
import { useStyleDna } from '@/lib/query/style-dna';
import { authApi } from '@/lib/api/auth';
import { queryKeys } from '@/lib/query/query-client';
import { useAuthStore } from '@/store/auth-store';

/** A3 Profile — Style DNA card + row on top; full profile (stats, prefs, reminder) is A5. */
export function ProfilePlaceholderScreen() {
  const t = useTheme();
  const insets = useSafeAreaInsets();
  const signOut = useAuthStore((s) => s.signOut);
  const { data: user } = useQuery({ queryKey: queryKeys.me, queryFn: authApi.getCurrentUser });
  const { data: styleDna, isLoading } = useStyleDna();
  const [screen, setScreen] = useState<'main' | 'style-dna'>('main');

  if (screen === 'style-dna') {
    return <StyleDnaProfileScreen onBack={() => setScreen('main')} />;
  }

  const dna = styleDna?.style_dna ?? null;

  return (
    <View testID="profile-screen" style={{ flex: 1, backgroundColor: t.colors.bg }}>
      <ScrollView
        contentContainerStyle={{
          paddingTop: insets.top + 24,
          paddingHorizontal: 28,
          paddingBottom: 130,
          gap: 20,
        }}>
        <View>
          <MonoLabel style={{ marginBottom: 8 }}>PROFILE</MonoLabel>
          <Text style={[display(34), { color: t.colors.text }]}>
            {user?.full_name?.split(' ')[0] ?? 'You'}
            <Text style={display(34, { italic: true })}>.</Text>
          </Text>
          <BodyText style={{ marginTop: 8 }}>{user?.email ?? ''}</BodyText>
        </View>

        {/* Style DNA — card when present, otherwise a prompt row. Tapping opens
            the full Style DNA profile (GET/PATCH/regenerate/delete-photos). */}
        <Pressable
          onPress={() => setScreen('style-dna')}
          accessibilityRole="button"
          testID="profile-style-dna-row">
          {isLoading ? (
            <Card padding={18}>
              <ActivityIndicator color={t.colors.t2} />
            </Card>
          ) : dna ? (
            <StyleDnaCard dna={dna} />
          ) : (
            <Card padding={18}>
              <View style={{ flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' }}>
                <View style={{ flex: 1, gap: 4 }}>
                  <MonoLabel>Style DNA</MonoLabel>
                  <BodyText size={13}>Not built yet — open to view or regenerate your profile.</BodyText>
                </View>
                <AttreqIcon name="chevron" size={16} color={t.colors.t3} />
              </View>
            </Card>
          )}
        </Pressable>

        <Card padding={18}>
          <MonoLabel style={{ marginBottom: 8 }}>Coming in A5</MonoLabel>
          <BodyText size={13}>Stats, preferences, and the daily reminder land in milestone A5.</BodyText>
        </Card>

        <PrimaryButton label="Sign out" onPress={() => void signOut()} testID="sign-out" />
      </ScrollView>
    </View>
  );
}
