import { apiClient } from '@/lib/api/client'
import type { Outfit, OutfitListResponse, OutfitSuggestion } from '@/lib/api/types'

export const outfitsApi = {
  async listOutfits(page = 1) {
    const response = await apiClient.get<OutfitListResponse>('/outfits', {
      params: { page, page_size: 50 },
    })
    return response.data
  },
  async createFromSuggestion(suggestion: OutfitSuggestion) {
    const response = await apiClient.post<Outfit>('/outfits', {
      top_item_id: suggestion.top_item_id,
      bottom_item_id: suggestion.bottom_item_id,
      accessory_ids: suggestion.accessory_item ? [suggestion.accessory_item.id] : [],
      occasion_context: suggestion.occasion_context,
    })
    return response.data
  },
  async markAsWorn(outfitId: string, wornDate: string) {
    const response = await apiClient.post<Outfit>(`/outfits/${outfitId}/wear`, {
      worn_date: wornDate,
    })
    return response.data
  },
  async submitFeedback(outfitId: string, feedbackScore: -1 | 0 | 1) {
    const response = await apiClient.post<Outfit>(`/outfits/${outfitId}/feedback`, {
      feedback_score: feedbackScore,
    })
    return response.data
  },
}
