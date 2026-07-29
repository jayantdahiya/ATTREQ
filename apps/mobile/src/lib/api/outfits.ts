import { apiClient } from '@/lib/api/client';
import type { Outfit, OutfitCreatePayload, OutfitList, OutfitSuggestion } from '@/lib/api/types';

// Backend contract: apps/api/src/attreq_api/api/v1/endpoints/outfits.py.
// The "Wear this" flow is two calls: POST /outfits (create), then
// POST /outfits/{id}/wear with the LOCAL date. `weather_context` is never sent.
export const outfitsApi = {
  async list(page = 1, pageSize = 50) {
    const response = await apiClient.get<OutfitList>('/outfits', {
      params: { page, page_size: pageSize },
    });
    return response.data;
  },

  async create(payload: OutfitCreatePayload) {
    const response = await apiClient.post<Outfit>('/outfits', payload);
    return response.data;
  },

  // POST /outfits/{id}/wear — record the outfit worn on `wornDate`
  // ('YYYY-MM-DD', the user's LOCAL calendar day).
  async markWorn(outfitId: string, wornDate: string) {
    const response = await apiClient.post<Outfit>(`/outfits/${outfitId}/wear`, {
      worn_date: wornDate,
    });
    return response.data;
  },

  // POST /outfits/{id}/feedback — like (1) / neutral (0) / dislike (-1).
  async submitFeedback(outfitId: string, feedbackScore: -1 | 0 | 1) {
    const response = await apiClient.post<Outfit>(`/outfits/${outfitId}/feedback`, {
      feedback_score: feedbackScore,
    });
    return response.data;
  },
};

/** RN parity: build the POST /outfits body from a daily suggestion. */
export function outfitPayloadFromSuggestion(suggestion: OutfitSuggestion): OutfitCreatePayload {
  return {
    top_item_id: suggestion.top_item_id ?? undefined,
    bottom_item_id: suggestion.bottom_item_id ?? undefined,
    accessory_ids: suggestion.accessory_item ? [suggestion.accessory_item.id] : [],
    occasion_context: suggestion.occasion_context,
    footwear_item_id: suggestion.footwear_item_id ?? undefined,
    outerwear_item_id: suggestion.outerwear_item_id ?? undefined,
    fullbody_item_id: suggestion.fullbody_item_id ?? undefined,
  };
}

/** Create-or-reuse key: one outfit row per suggestion per generation batch. */
export function suggestionOutfitKey(recommendationId: string, s: OutfitSuggestion): string {
  return `${recommendationId}:${s.top_item_id ?? '-'}:${s.bottom_item_id ?? '-'}:${s.fullbody_item_id ?? '-'}`;
}
