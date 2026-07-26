import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { wardrobeApi, type UploadAsset } from '@/lib/api/wardrobe';
import { queryKeys } from '@/lib/query/query-client';
import type { WardrobeItem, WardrobeItemStatus } from '@/lib/api/types';

const listKey = (status: WardrobeItemStatus) => [...queryKeys.wardrobe, status] as const;

function hasProcessing(items: WardrobeItem[] | undefined): boolean {
  return !!items?.some((i) => i.processing_status === 'pending' || i.processing_status === 'processing');
}

/** Wardrobe list with automatic status polling (~2s) while items are processing. */
export function useWardrobeItems(status: WardrobeItemStatus = 'active') {
  return useQuery({
    queryKey: listKey(status),
    queryFn: () => wardrobeApi.list(status),
    refetchInterval: (query) => (hasProcessing(query.state.data?.items) ? 2000 : false),
  });
}

export function useWardrobeItem(itemId: string | null) {
  return useQuery({
    queryKey: [...queryKeys.wardrobe, 'item', itemId],
    queryFn: () => wardrobeApi.getItem(itemId as string),
    enabled: !!itemId,
  });
}

export function useUploadItem() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (asset: UploadAsset) => wardrobeApi.upload(asset),
    onSuccess: () => qc.invalidateQueries({ queryKey: queryKeys.wardrobe }),
  });
}

export function useSetItemStatus() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ itemId, status }: { itemId: string; status: WardrobeItemStatus }) =>
      wardrobeApi.setStatus(itemId, status),
    onSuccess: () => qc.invalidateQueries({ queryKey: queryKeys.wardrobe }),
  });
}
