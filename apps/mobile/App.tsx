import React, { useEffect } from 'react';
import { StatusBar, useColorScheme } from 'react-native';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import { QueryClientProvider } from '@tanstack/react-query';

import { ThemeProvider } from '@/design-system/theme/ThemeProvider';
import { queryClient } from '@/lib/query/query-client';
import { RootNavigator } from '@/navigation/RootNavigator';
import { useAuthStore } from '@/store/auth-store';

function App(): React.JSX.Element {
  const isDark = useColorScheme() === 'dark';
  const bootstrap = useAuthStore((s) => s.bootstrap);

  useEffect(() => {
    void bootstrap();
  }, [bootstrap]);

  return (
    <SafeAreaProvider>
      <QueryClientProvider client={queryClient}>
        <ThemeProvider>
          <StatusBar barStyle={isDark ? 'light-content' : 'dark-content'} backgroundColor="transparent" translucent />
          <RootNavigator />
        </ThemeProvider>
      </QueryClientProvider>
    </SafeAreaProvider>
  );
}

export default App;
