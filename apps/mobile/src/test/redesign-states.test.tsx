import { render, screen, waitFor } from '@testing-library/react-native'

import { DashboardScreen } from '@/features/recommendations/dashboard-screen'
import { WardrobeScreen } from '@/features/wardrobe/wardrobe-screen'
import { TestProviders } from '@/test/test-providers'

jest.mock('@/lib/api/auth', () => ({
  authApi: {
    getCurrentUser: jest.fn(() =>
      Promise.resolve({
        email: 'iris@attreq.app',
        full_name: 'Iris Andersen',
        saved_city: null,
        saved_latitude: null,
        saved_longitude: null,
      })
    ),
  },
}))

jest.mock('@/lib/api/wardrobe', () => ({
  wardrobeApi: {
    listItems: jest.fn(() => Promise.resolve({ items: [] })),
    uploadItem: jest.fn(),
  },
}))

jest.mock('@/lib/api/recommendations', () => ({
  recommendationsApi: {
    getDailySuggestions: jest.fn(),
  },
}))

jest.mock('@/lib/api/outfits', () => ({
  outfitsApi: {
    createFromSuggestion: jest.fn(),
    markAsWorn: jest.fn(),
    submitFeedback: jest.fn(),
  },
}))

jest.mock('@/lib/api/users', () => ({
  usersApi: {
    updateLocation: jest.fn(),
  },
}))

describe('redesigned mobile states', () => {
  it('shows the editorial location permission state on Today when no saved location exists', async () => {
    render(
      <TestProviders>
        <DashboardScreen />
      </TestProviders>
    )

    await waitFor(() => {
      expect(screen.getByText('Allow location access')).toBeOnTheScreen()
      expect(screen.getByText('before you do.')).toBeOnTheScreen()
    })
  })

  it('shows the redesigned empty wardrobe state', async () => {
    render(
      <TestProviders>
        <WardrobeScreen />
      </TestProviders>
    )

    await waitFor(() => {
      expect(screen.getByText('Wardrobe')).toBeOnTheScreen()
      expect(screen.getByText('No wardrobe items yet')).toBeOnTheScreen()
    })
  })
})
