import React, { useState } from 'react';
import { KeyboardAvoidingView, Platform, ScrollView, Text, View } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

import { useTheme } from '@/design-system/theme/ThemeProvider';
import { body, display } from '@/design-system/theme/typography';
import { MonoLabel } from '@/design-system/components/MonoLabel';
import { BodyText } from '@/design-system/components/BodyText';
import { Card } from '@/design-system/components/Card';
import { UnderlineInput } from '@/design-system/components/UnderlineInput';
import { PrimaryButton } from '@/design-system/components/PrimaryButton';
import { useAuthStore } from '@/store/auth-store';
import { describeAuthError } from '@/lib/api/errors';

export function LoginScreen({ onCreateAccount }: { onCreateAccount: () => void }) {
  const t = useTheme();
  const insets = useSafeAreaInsets();
  const login = useAuthStore((s) => s.login);

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const onSubmit = async () => {
    setError(null);
    setLoading(true);
    try {
      await login(email.trim(), password);
    } catch (e) {
      setError(describeAuthError(e));
    } finally {
      setLoading(false);
    }
  };

  return (
    <View style={{ flex: 1, backgroundColor: t.colors.bg }}>
      <KeyboardAvoidingView style={{ flex: 1 }} behavior={Platform.OS === 'ios' ? 'padding' : undefined}>
        <ScrollView
          contentContainerStyle={{
            flexGrow: 1,
            paddingHorizontal: 28,
            paddingTop: insets.top + 42,
            paddingBottom: insets.bottom + 32,
            justifyContent: 'space-between',
          }}
          keyboardShouldPersistTaps="handled">
          {/* Wordmark header */}
          <View style={{ alignItems: 'center' }}>
            <View style={{ flexDirection: 'row', alignItems: 'center', gap: 14, marginBottom: 24, alignSelf: 'stretch' }}>
              <View style={{ flex: 1, height: 1, backgroundColor: t.colors.border }} />
              <MonoLabel>Est. 2026 — Personal Styling</MonoLabel>
              <View style={{ flex: 1, height: 1, backgroundColor: t.colors.border }} />
            </View>
            <Text style={[display(56, { weight: 'semiBold' }), { letterSpacing: 8, color: t.colors.text, marginBottom: 14 }]}>
              ATTREQ
            </Text>
            <Text style={[display(19, { weight: 'regular', italic: true }), { color: t.colors.t2 }]}>
              Your closet, curated.
            </Text>
          </View>

          {/* Sign-in card */}
          <Card padding={24} style={{ marginVertical: 28 }}>
            <Text style={[display(24), { color: t.colors.text, marginBottom: 4 }]}>Welcome back</Text>
            <BodyText size={13} style={{ marginBottom: 24 }}>
              Sign in to your wardrobe.
            </BodyText>
            <View style={{ gap: 20, marginBottom: 24 }}>
              <UnderlineInput
                label="Email address"
                value={email}
                onChangeText={setEmail}
                keyboardType="email-address"
                placeholder="hi@natasha.com"
                testID="login-email"
              />
              <UnderlineInput label="Password" value={password} onChangeText={setPassword} secureTextEntry testID="login-password" />
            </View>
            {error ? (
              <BodyText size={13} color={t.colors.clay} style={{ marginBottom: 14 }}>
                {error}
              </BodyText>
            ) : null}
            <PrimaryButton label={loading ? 'Signing in…' : 'Sign in'} isLoading={loading} onPress={onSubmit} testID="login-submit" />
            <View style={{ alignItems: 'center', marginTop: 14 }}>
              {/* No backend reset endpoint yet — inert, per the goal doc. */}
              <MonoLabel color={t.colors.t3}>Forgot password</MonoLabel>
            </View>
          </Card>

          {/* Create-account link */}
          <View style={{ flexDirection: 'row', justifyContent: 'center' }}>
            <BodyText size={13}>New here? </BodyText>
            <Text
              onPress={onCreateAccount}
              style={[body(13, 'medium'), { color: t.colors.accent }]}
              accessibilityRole="link">
              Create account
            </Text>
          </View>
        </ScrollView>
      </KeyboardAvoidingView>
    </View>
  );
}
