import { useQuery } from '@tanstack/react-query';

import { statsApi } from '@/lib/api/stats';
import { queryKeys } from '@/lib/query/query-client';

/** GET /stats/wardrobe — composition, closet value, cost-per-wear, most/least worn. */
export function useWardrobeStats() {
  return useQuery({
    queryKey: [...queryKeys.stats, 'wardrobe'],
    queryFn: () => statsApi.getWardrobeStats(),
  });
}

/** GET /stats/forgotten — never-worn / long-unworn active items + pairings. */
export function useForgottenItems() {
  return useQuery({
    queryKey: [...queryKeys.stats, 'forgotten'],
    queryFn: () => statsApi.getForgottenItems(),
  });
}
