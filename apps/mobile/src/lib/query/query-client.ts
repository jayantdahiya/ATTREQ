import { QueryClient } from '@tanstack/react-query'

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      staleTime: 30_000,
    },
  },
})

export const queryKeys = {
  me: ['me'] as const,
  wardrobe: ['wardrobe'] as const,
  outfits: ['outfits'] as const,
  recommendations: (paramsKey: string) => ['recommendations', paramsKey] as const,
}
