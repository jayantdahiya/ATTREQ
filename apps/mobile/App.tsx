import React from 'react';
import { StatusBar, useColorScheme } from 'react-native';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import { ThemeProvider } from '@/design-system/theme/ThemeProvider';
import { ComponentGallery } from '@/design-system/gallery/ComponentGallery';

function App(): React.JSX.Element {
  const isDark = useColorScheme() === 'dark';
  return (
    <SafeAreaProvider>
      <ThemeProvider>
        <StatusBar barStyle={isDark ? 'light-content' : 'dark-content'} backgroundColor="transparent" translucent />
        <ComponentGallery />
      </ThemeProvider>
    </SafeAreaProvider>
  );
}

export default App;
