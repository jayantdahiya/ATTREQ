import { apiClient } from '@/lib/api/client'
import type { DailySuggestionsResponse } from '@/lib/api/types'

export interface RecommendationsParams {
  lat?: number
  lon?: number
  occasion?: string
  force_refresh?: boolean
}

export const recommendationsApi = {
  async getDailySuggestions(params: RecommendationsParams) {
    const response = await apiClient.get<DailySuggestionsResponse>('/recommendations/daily', {
      params,
    })
    return response.data
  },
}
