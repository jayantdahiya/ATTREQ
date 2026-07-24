import React from 'react';
import { render, screen } from '@testing-library/react-native';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import { ThemeProvider } from '@/design-system/theme/ThemeProvider';
import { ComponentGallery } from '@/design-system/gallery/ComponentGallery';

function renderGallery(scheme: 'light' | 'dark') {
  return render(
    <SafeAreaProvider>
      <ThemeProvider forceScheme={scheme}>
        <ComponentGallery />
      </ThemeProvider>
    </SafeAreaProvider>,
  );
}

describe('ComponentGallery', () => {
  it('renders every design-system section in light theme', () => {
    renderGallery('light');
    expect(screen.getByText('Component Gallery')).toBeTruthy();
    expect(screen.getByText('01 — Type Ramp')).toBeTruthy();
    expect(screen.getByText('08 — Icons')).toBeTruthy();
    expect(screen.getByText('09 — Step Nav')).toBeTruthy();
  });

  it('renders in dark theme without crashing', () => {
    renderGallery('dark');
    expect(screen.getByText('Component Gallery')).toBeTruthy();
  });
});
