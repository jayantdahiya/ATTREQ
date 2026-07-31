import { apiClient } from '@/lib/api/client';
import type { ForgottenItemsResponse, WardrobeStatsResponse } from '@/lib/api/types';

// Wardrobe stats & forgotten-items retention surfaces (RI-7 / A5).
// Backend contract: apps/api/src/attreq_api/api/v1/endpoints/stats.py
//   GET /stats/wardrobe?force_refresh=            → WardrobeStatsResponse
//   GET /stats/forgotten?force_refresh=&days_threshold= → ForgottenItemsResponse
// Both are computed over ACTIVE items only and cached server-side for 1h.
export const statsApi = {
  async getWardrobeStats(forceRefresh = false) {
    const response = await apiClient.get<WardrobeStatsResponse>('/stats/wardrobe', {
      params: { force_refresh: forceRefresh },
    });
    return response.data;
  },
  async getForgottenItems(forceRefresh = false, daysThreshold = 60) {
    const response = await apiClient.get<ForgottenItemsResponse>('/stats/forgotten', {
      params: { force_refresh: forceRefresh, days_threshold: daysThreshold },
    });
    return response.data;
  },
};
