import { useInfiniteQuery } from '@tanstack/react-query';

import { outfitsApi } from '@/lib/api/outfits';
import { queryKeys } from '@/lib/query/query-client';

const PAGE_SIZE = 50;

/**
 * GET /outfits — the diary, paginated. `page_size` 50, next page fetched via
 * `fetchNextPage()` when the list nears its end. Invalidate `queryKeys.outfits`
 * after a wear/feedback so a new entry shows without a manual pull-to-refresh.
 */
export function useOutfitHistory() {
  return useInfiniteQuery({
    queryKey: queryKeys.outfits,
    queryFn: ({ pageParam }) => outfitsApi.list(pageParam, PAGE_SIZE),
    initialPageParam: 1,
    getNextPageParam: (last) => (last.page < last.total_pages ? last.page + 1 : undefined),
  });
}
