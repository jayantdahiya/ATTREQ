import React, { useState } from 'react';
import { KeyboardAvoidingView, Platform, ScrollView, Text, View } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

import { useTheme } from '@/design-system/theme/ThemeProvider';
import { body, display } from '@/design-system/theme/typography';
import { MonoLabel } from '@/design-system/components/MonoLabel';
import { BodyText } from '@/design-system/components/BodyText';
import { Card } from '@/design-system/components/Card';
import { Chip } from '@/design-system/components/Chip';
import { UnderlineInput } from '@/design-system/components/UnderlineInput';
import { PrimaryButton } from '@/design-system/components/PrimaryButton';
import { StepNav } from '@/design-system/components/StepNav';
import { AttreqIcon } from '@/design-system/icons/AttreqIcon';
import { useAuthStore, type RegistrationData } from '@/store/auth-store';
import { describeAuthError } from '@/lib/api/errors';
import { useBackHandler } from '@/lib/hooks/useBackHandler';

const STYLE_OPTIONS = ['Minimal', 'Earthy', 'Tailored', 'Layered', 'Casual', 'Formal', 'Streetwear', 'Athleisure'];
const EMAIL_RE = /^[^@\s]+@[^@\s]+\.[^@\s]+$/;

export function RegisterScreen({ onSignIn, onExit }: { onSignIn: () => void; onExit: () => void }) {
  const t = useTheme();
  const insets = useSafeAreaInsets();
  const register = useAuthStore((s) => s.register);

  const [step, setStep] = useState(0);
  const [email, setEmail] = useState('');
  const [fullName, setFullName] = useState('');
  const [password, setPassword] = useState('');
  const [confirm, setConfirm] = useState('');
  const [selected, setSelected] = useState<string[]>([]);
  const [occasions, setOccasions] = useState('');
  const [manualCity, setManualCity] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  // Mirrors the backend policy (UserCreate.validate_password) + iOS RegisterViewModel.
  const validateAccount = (): boolean => {
    setError(null);
    if (!EMAIL_RE.test(email.trim())) return fail('Enter a valid email address.');
    if (!fullName.trim()) return fail('Enter your full name.');
    if (password.length < 8) return fail('Password must be at least 8 characters.');
    if (password.length > 72) return fail('Password must be 72 characters or fewer.');
    if (!/[A-Z]/.test(password)) return fail('Password must contain at least one uppercase letter.');
    if (!/[a-z]/.test(password)) return fail('Password must contain at least one lowercase letter.');
    if (!/[0-9]/.test(password)) return fail('Password must contain at least one digit.');
    if (password !== confirm) return fail("Passwords don't match.");
    return true;
  };
  const fail = (msg: string): boolean => {
    setError(msg);
    return false;
  };

  const onBack = () => {
    setError(null);
    if (step > 0) setStep(step - 1);
    else onExit();
  };

  // Hardware back mirrors the on-screen chevron: previous step, or back to the
  // sign-in screen from step 0. The auth stack root (LoginScreen) keeps the
  // default behaviour (exit).
  useBackHandler(() => {
    onBack();
    return true;
  });

  const onNext = () => {
    if (step === 0) {
      if (validateAccount()) setStep(1);
    } else if (step === 1) {
      setStep(2);
    }
  };

  const toggleKeyword = (k: string) =>
    setSelected((prev) => (prev.includes(k) ? prev.filter((x) => x !== k) : [...prev, k]));

  const onSubmit = async () => {
    setError(null);
    setLoading(true);
    const city = manualCity.trim();
    const location: RegistrationData['location'] = city ? { kind: 'city', city } : undefined;
    try {
      await register({ email: email.trim(), fullName, password, styleKeywords: selected, occasions, location });
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
          contentContainerStyle={{ flexGrow: 1, paddingHorizontal: 28, paddingTop: insets.top + 8, paddingBottom: insets.bottom + 24 }}
          keyboardShouldPersistTaps="handled">
          <View style={{ marginBottom: 26 }}>
            <StepNav step={step} onBack={onBack} />
          </View>

          {step === 0 && (
            <>
              <MonoLabel color={t.colors.accent} style={{ marginBottom: 8 }}>
                Step 01 — Account
              </MonoLabel>
              <Text style={[display(36), { color: t.colors.text, lineHeight: 40 }]}>
                Make this{' '}
                <Text style={display(36, { italic: true })}>your closet.</Text>
              </Text>
              <BodyText style={{ marginTop: 6, marginBottom: 20 }}>A few details, then we'll curate every look.</BodyText>
              <Card padding={20}>
                <View style={{ gap: 18 }}>
                  <UnderlineInput label="Email address" value={email} onChangeText={setEmail} keyboardType="email-address" placeholder="hi@natasha.com" testID="register-email" />
                  <UnderlineInput label="Full name" value={fullName} onChangeText={setFullName} autoCapitalize="words" placeholder="Natasha A." testID="register-fullname" />
                  <UnderlineInput label="Password" value={password} onChangeText={setPassword} secureTextEntry testID="register-password" />
                  <UnderlineInput label="Confirm password" value={confirm} onChangeText={setConfirm} secureTextEntry testID="register-confirm" />
                </View>
              </Card>
              {error ? <BodyText size={13} color={t.colors.clay} style={{ marginTop: 14 }}>{error}</BodyText> : null}
              <View style={{ marginTop: 16 }}>
                <PrimaryButton label="Continue" icon="chevron" onPress={onNext} testID="register-continue-account" />
              </View>
              <View style={{ flexDirection: 'row', justifyContent: 'center', marginTop: 12 }}>
                <BodyText size={13}>Have an account? </BodyText>
                <Text onPress={onSignIn} style={[body(13, 'medium'), { color: t.colors.accent }]}>
                  Sign in
                </Text>
              </View>
            </>
          )}

          {step === 1 && (
            <>
              <MonoLabel color={t.colors.accent} style={{ marginBottom: 8 }}>
                Step 02 — Style
              </MonoLabel>
              <Text style={[display(36), { color: t.colors.text, lineHeight: 40 }]}>
                Define your{' '}
                <Text style={display(36, { italic: true })}>aesthetic.</Text>
              </Text>
              <BodyText style={{ marginTop: 6, marginBottom: 20 }}>Tell us how you dress. We'll learn the rest.</BodyText>
              <Card padding={20}>
                <MonoLabel style={{ marginBottom: 14 }}>Style keywords</MonoLabel>
                <View style={{ flexDirection: 'row', flexWrap: 'wrap', gap: 7, marginBottom: 20 }}>
                  {STYLE_OPTIONS.map((s) => (
                    <Chip key={s} label={s} selected={selected.includes(s)} onPress={() => toggleKeyword(s)} />
                  ))}
                </View>
                <View style={{ height: 1, backgroundColor: t.colors.borderSoft, marginBottom: 20 }} />
                <UnderlineInput label="Occasions (optional)" value={occasions} onChangeText={setOccasions} autoCapitalize="sentences" placeholder="Work, weekend, travel…" testID="register-occasions" />
              </Card>
              <View style={{ marginTop: 16 }}>
                <PrimaryButton label="Continue" icon="chevron" onPress={onNext} testID="register-continue-style" />
              </View>
            </>
          )}

          {step === 2 && (
            <>
              <MonoLabel color={t.colors.accent} style={{ marginBottom: 8 }}>
                Step 03 — Location
              </MonoLabel>
              <Text style={[display(34), { color: t.colors.text, lineHeight: 38 }]}>
                The weather decides{' '}
                <Text style={display(34, { italic: true })}>before you do.</Text>
              </Text>
              <BodyText style={{ marginTop: 6, marginBottom: 20 }}>Share your city for weather-aware suggestions.</BodyText>

              <View style={{ alignItems: 'center', marginBottom: 22 }}>
                <View style={{ width: 116, height: 116, alignItems: 'center', justifyContent: 'center' }}>
                  <View style={{ position: 'absolute', width: 116, height: 116, borderRadius: 58, borderWidth: 1, borderColor: t.colors.border }} />
                  <View style={{ position: 'absolute', width: 82, height: 82, borderRadius: 41, borderWidth: 1.5, borderStyle: 'dashed', borderColor: t.colors.accent, backgroundColor: t.colors.accentSoft }} />
                  <View style={{ width: 50, height: 50, borderRadius: 25, backgroundColor: t.colors.text, alignItems: 'center', justifyContent: 'center' }}>
                    <AttreqIcon name="location" size={20} color={t.colors.bg} />
                  </View>
                </View>
              </View>

              <Card padding={20}>
                <UnderlineInput label="Your city" value={manualCity} onChangeText={setManualCity} autoCapitalize="words" placeholder="New York, London, Tokyo…" testID="register-city" />
                <MonoLabel style={{ marginTop: 8 }}>Used for weather-aware suggestions</MonoLabel>
              </Card>

              {error ? <BodyText size={13} color={t.colors.clay} style={{ marginTop: 14 }}>{error}</BodyText> : null}
              <View style={{ marginTop: 16 }}>
                <PrimaryButton label={loading ? 'Creating account…' : 'Create account'} variant="accent" icon="chevron" isLoading={loading} onPress={onSubmit} testID="register-submit" />
              </View>
            </>
          )}
        </ScrollView>
      </KeyboardAvoidingView>
    </View>
  );
}
