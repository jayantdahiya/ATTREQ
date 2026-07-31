import { render, screen } from '@testing-library/react-native'
import ProtectedLayout from '../../app/(protected)/_layout'
import { useAuthStore } from '@/store/auth-store'

jest.mock('expo-router', () => ({
  Redirect: ({ href }: { href: string }) => {
    const { Text } = require('react-native')
    return <Text>Redirect {href}</Text>
  },
  Stack: () => {
    const { Text } = require('react-native')
    return <Text>Authed home</Text>
  },
}))

jest.mock('@/store/auth-store', () => ({
  useAuthStore: jest.fn(),
}))

const mockedUseAuthStore = useAuthStore as unknown as jest.Mock

describe('ProtectedLayout', () => {
  it('redirects guests to the login route', () => {
    mockedUseAuthStore.mockImplementation((selector: (state: { accessToken: string | null }) => unknown) =>
      selector({ accessToken: null })
    )

    render(<ProtectedLayout />)

    expect(screen.getByText('Redirect /(auth)/login')).toBeOnTheScreen()
  })

  it('renders protected content when an access token exists', () => {
    mockedUseAuthStore.mockImplementation((selector: (state: { accessToken: string | null }) => unknown) =>
      selector({ accessToken: 'token' })
    )

    render(<ProtectedLayout />)

    expect(screen.getByText('Authed home')).toBeOnTheScreen()
  })
})
