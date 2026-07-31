import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { styleDnaApi } from '@/lib/api/style-dna';
import { queryKeys } from '@/lib/query/query-client';
import type { StyleDnaCorrection } from '@/lib/api/types';

/** GET /users/style-dna — profile + seed photos. */
export function useStyleDna() {
  return useQuery({ queryKey: queryKeys.styleDna, queryFn: styleDnaApi.getStyleDna });
}

/** PATCH /users/style-dna — manual corrections; response replaces cache. */
export function useUpdateStyleDna() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (correction: StyleDnaCorrection) => styleDnaApi.updateStyleDna(correction),
    onSuccess: (data) => qc.setQueryData(queryKeys.styleDna, data),
  });
}

/** POST /users/style-dna/regenerate — re-synthesize from stored photos. */
export function useRegenerate() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: () => styleDnaApi.regenerate(),
    onSuccess: () => qc.invalidateQueries({ queryKey: queryKeys.styleDna }),
  });
}

/** DELETE /users/style-dna/photos — remove ALL seed photos. */
export function useDeleteStylePhotos() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: () => styleDnaApi.deleteStylePhotos(),
    onSuccess: () => qc.invalidateQueries({ queryKey: queryKeys.styleDna }),
  });
}
