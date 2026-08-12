import React from 'react';
import { fireEvent, render, screen, waitFor } from '@testing-library/react-native';
import { SafeAreaProvider } from 'react-native-safe-area-context';

import { ThemeProvider } from '@/design-system/theme/ThemeProvider';
import { RegisterScreen } from '@/features/auth/RegisterScreen';

const mockRegister = jest.fn<Promise<void>, [unknown]>();

jest.mock('@/store/auth-store', () => ({
  useAuthStore: (selector: (state: { register: typeof mockRegister }) => unknown) => selector({ register: mockRegister }),
}));

jest.mock('@/lib/hooks/useBackHandler', () => ({
  useBackHandler: jest.fn(),
}));

function renderScreen() {
  return render(
    <SafeAreaProvider>
      <ThemeProvider forceScheme="light">
        <RegisterScreen onSignIn={jest.fn()} onExit={jest.fn()} />
      </ThemeProvider>
    </SafeAreaProvider>,
  );
}

function continueToLocation() {
  fireEvent.changeText(screen.getByTestId('register-email'), 'beta@example.com');
  fireEvent.changeText(screen.getByTestId('register-fullname'), 'Beta Tester');
  fireEvent.changeText(screen.getByTestId('register-password'), 'Password123');
  fireEvent.changeText(screen.getByTestId('register-confirm'), 'Password123');
  fireEvent.press(screen.getByTestId('register-continue-account'));
  fireEvent.press(screen.getByTestId('register-continue-style'));
}

describe('RegisterScreen location step', () => {
  beforeEach(() => {
    mockRegister.mockReset();
    mockRegister.mockResolvedValue(undefined);
  });

  it('offers manual city entry without a device-location action', () => {
    renderScreen();
    continueToLocation();

    expect(screen.getByText('Your city')).toBeTruthy();
    expect(screen.getByText('Used for weather-aware suggestions')).toBeTruthy();
    expect(screen.queryByText('Use device location')).toBeNull();
  });

  it('registers the manually entered city for weather-aware recommendations', async () => {
    renderScreen();
    continueToLocation();
    fireEvent.changeText(screen.getByTestId('register-city'), 'Milan');
    fireEvent.press(screen.getByTestId('register-submit'));

    await waitFor(() => {
      expect(mockRegister).toHaveBeenCalledWith({
        email: 'beta@example.com',
        fullName: 'Beta Tester',
        password: 'Password123',
        styleKeywords: [],
        occasions: '',
        location: { kind: 'city', city: 'Milan' },
      });
    });
  });
});
