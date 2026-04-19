import { fireEvent, render, screen, waitFor } from '@testing-library/react-native'
import { Text } from 'react-native'

import { LoginScreen } from '@/features/auth/login-screen'
import { TestProviders } from '@/test/test-providers'

jest.mock('expo-router', () => ({
  Link: ({ children }: { children: React.ReactNode }) => <Text>{children}</Text>,
  router: { replace: jest.fn() },
}))

describe('LoginScreen', () => {
  it('shows validation messages before submitting invalid credentials', async () => {
    render(
      <TestProviders>
        <LoginScreen />
      </TestProviders>
    )

    fireEvent.press(screen.getByText('Sign in'))

    await waitFor(() => {
      expect(screen.getByText('Enter a valid email address')).toBeOnTheScreen()
      expect(screen.getByText('Password must be at least 8 characters')).toBeOnTheScreen()
    })
  })
})
