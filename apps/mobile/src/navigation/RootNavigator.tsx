import React, { useState } from 'react';
import { ActivityIndicator, Text, View } from 'react-native';
import { useQuery } from '@tanstack/react-query';

import { useTheme } from '@/design-system/theme/ThemeProvider';
import { display } from '@/design-system/theme/typography';
import { LoginScreen } from '@/features/auth/LoginScreen';
import { RegisterScreen } from '@/features/auth/RegisterScreen';
import { MainTabs } from '@/navigation/MainTabs';
import { OnboardingFlow } from '@/features/onboarding/OnboardingFlow';
import { authApi } from '@/lib/api/auth';
import { queryKeys } from '@/lib/query/query-client';
import { useAuthStore } from '@/store/auth-store';

// A1 uses a lightweight JS screen switch instead of React Navigation, because
// react-native-screens' codegen is incompatible with this env's RN 0.83 codegen
// (UnionTypeAnnotation event props). React Navigation + native-stack are
// reintroduced in a later milestone once that toolchain conflict is resolved.

function Splash() {
  const t = useTheme();
  return (
    <View style={{ flex: 1, alignItems: 'center', justifyContent: 'center', backgroundColor: t.colors.bg, gap: 20 }}>
      <Text style={[display(44, { weight: 'semiBold' }), { letterSpacing: 6, color: t.colors.text }]}>ATTREQ</Text>
      <ActivityIndicator color={t.colors.accent} />
    </View>
  );
}

function AuthFlow() {
  const [screen, setScreen] = useState<'login' | 'register'>('login');
  if (screen === 'register') {
    return <RegisterScreen onSignIn={() => setScreen('login')} onExit={() => setScreen('login')} />;
  }
  return <LoginScreen onCreateAccount={() => setScreen('register')} />;
}

/** Root routing gate — mirrors iOS RootView/AppSession: loading → auth → onboarding → app. */
export function RootNavigator() {
  const bootstrapStatus = useAuthStore((s) => s.bootstrapStatus);
  const accessToken = useAuthStore((s) => s.accessToken);
  const { data: user } = useQuery({
    queryKey: queryKeys.me,
    queryFn: authApi.getCurrentUser,
    enabled: !!accessToken,
  });

  if (bootstrapStatus !== 'ready') return <Splash />;
  if (!accessToken) return <AuthFlow />;
  if (user && !user.onboarding_completed) return <OnboardingFlow />;
  return <MainTabs />;
}
