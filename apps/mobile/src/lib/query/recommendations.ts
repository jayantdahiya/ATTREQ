import { useCallback, useRef } from 'react';
import { useQuery } from '@tanstack/react-query';
import type { AxiosError } from 'axios';

import { recommendationsApi } from '@/lib/api/recommendations';
import { queryKeys } from '@/lib/query/query-client';

// 4xx (no-location 400, insufficient-wardrobe 404, swipe-cap 429) and weather
// 503 are meaningful terminal responses, not transient errors — never retry.
function retryPolicy(count: number, error: unknown): boolean {
  const status = (error as AxiosError | undefined)?.response?.status;
  if (status && [400, 404, 429, 503].includes(status)) return false;
  return count < 1;
}

/**
 * GET /recommendations/daily. Steady-state saved-location path (no lat/lon).
 * Pull-to-refresh calls `forceRefresh()`, which flips a ref read at fetch time
 * so the next fetch sends `force_refresh=true` (bypassing the 24h daily cache),
 * then resets. Changing occasion/hint changes the key and refetches on its own.
 */
export function useDailySuggestions(occasion: string, occasionHint: string | null) {
  const forceRef = useRef(false);
  const query = useQuery({
    queryKey: queryKeys.recommendations(`daily:${occasion}:${occasionHint ?? 'none'}`),
    queryFn: () => {
      const forceRefresh = forceRef.current;
      forceRef.current = false;
      return recommendationsApi.daily({ occasion, occasionHint, forceRefresh });
    },
    retry: retryPolicy,
    staleTime: 5 * 60_000,
  });
  const forceRefresh = useCallback(async () => {
    forceRef.current = true;
    await query.refetch();
  }, [query]);
  return { ...query, forceRefresh };
}

/** GET /recommendations/swipe-deck — fresh, uncached deck; only fetched when open. */
export function useSwipeDeck(enabled: boolean) {
  return useQuery({
    queryKey: queryKeys.recommendations('swipe-deck'),
    queryFn: () => recommendationsApi.swipeDeck(),
    enabled,
    gcTime: 0,
    staleTime: 0,
    retry: retryPolicy,
  });
}

/** GET /recommendations/swipe-deck/status — best-effort entry-point gating. */
export function useSwipeDeckStatus() {
  return useQuery({
    queryKey: queryKeys.recommendations('swipe-deck-status'),
    queryFn: () => recommendationsApi.swipeDeckStatus(),
    retry: false,
  });
}
