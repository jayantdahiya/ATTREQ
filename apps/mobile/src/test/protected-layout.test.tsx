import { renderRouter, screen } from 'expo-router/testing-library'
import { Text } from 'react-native'

import ProtectedLayout from '../../app/(protected)/_layout'
import { useAuthStore } from '@/store/auth-store'

jest.mock('@/store/auth-store', () => ({
  useAuthStore: jest.fn(),
}))

const mockedUseAuthStore = useAuthStore as unknown as jest.Mock

describe('ProtectedLayout', () => {
  it('redirects guests to the login route', () => {
    mockedUseAuthStore.mockImplementation((selector: (state: { accessToken: string | null }) => unknown) =>
      selector({ accessToken: null })
    )

    renderRouter(
      {
        '(protected)/_layout': ProtectedLayout,
        '(protected)/(tabs)/index': () => <Text>Authed home</Text>,
        '(auth)/login': () => <Text>Login screen</Text>,
      },
      {
        initialUrl: '/(protected)/(tabs)',
      }
    )

    expect(screen.getByText('Login screen')).toBeOnTheScreen()
  })

  it('renders protected content when an access token exists', () => {
    mockedUseAuthStore.mockImplementation((selector: (state: { accessToken: string | null }) => unknown) =>
      selector({ accessToken: 'token' })
    )

    renderRouter(
      {
        '(protected)/_layout': ProtectedLayout,
        '(protected)/(tabs)/index': () => <Text>Authed home</Text>,
        '(auth)/login': () => <Text>Login screen</Text>,
      },
      {
        initialUrl: '/(protected)/(tabs)',
      }
    )

    expect(screen.getByText('Authed home')).toBeOnTheScreen()
  })
})
