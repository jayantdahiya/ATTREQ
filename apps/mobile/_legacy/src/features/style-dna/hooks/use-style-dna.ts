import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { styleDnaApi } from '@/lib/api/style-dna'
import type { StyleDnaCorrection, StylePhotoAsset } from '@/lib/api/style-dna'
import { queryKeys } from '@/lib/query/query-client'

export function useStyleDna() {
  return useQuery({
    queryKey: queryKeys.styleDna,
    queryFn: styleDnaApi.getStyleDna,
  })
}

export function useUploadStylePhotos() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (photos: StylePhotoAsset[]) => styleDnaApi.uploadStylePhotos(photos),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: queryKeys.styleDna })
      void queryClient.invalidateQueries({ queryKey: queryKeys.me })
      void queryClient.invalidateQueries({ queryKey: queryKeys.wardrobe })
    },
  })
}

export function useUpdateStyleDna() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (correction: StyleDnaCorrection) => styleDnaApi.updateStyleDna(correction),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: queryKeys.styleDna })
      void queryClient.invalidateQueries({ queryKey: queryKeys.me })
    },
  })
}

export function useRegenerateStyleDna() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: styleDnaApi.regenerateStyleDna,
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: queryKeys.styleDna })
      void queryClient.invalidateQueries({ queryKey: queryKeys.me })
    },
  })
}
