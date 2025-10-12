import apiClient from './client'
import { WardrobeItem } from './wardrobe'

export interface WeatherData {
  temp: number
  feels_like: number
  condition: string
  description: string
  humidity: number
  wind_speed: number
  icon: string
}

export interface OutfitScores {
  color_harmony: number
  formality: number
  preference_bonus: number
  total: number
}

export interface OutfitItemDetail {
  id: string
  category: string | null
  color_primary: string | null
  pattern: string | null
  image_url: string | null
  thumbnail_url: string | null
}

export interface OutfitSuggestion {
  top_item_id: string
  top_item: OutfitItemDetail
  bottom_item_id: string
  bottom_item: OutfitItemDetail
  accessory_item_id: string | null
  accessory_item: OutfitItemDetail | null
  scores: OutfitScores
  weather_context: WeatherData
  occasion_context: string
}

export interface DailySuggestionsResponse {
  suggestions: OutfitSuggestion[]
  total_suggestions: number
  generated_at: string
  weather: WeatherData
  occasion: string
  cached: boolean
}

export const recommendationsApi = {
  getDailySuggestions: async (params: {
    lat: number
    lon: number
    occasion?: string
    force_refresh?: boolean
  }): Promise<DailySuggestionsResponse> => {
    const response = await apiClient.get('/recommendations/daily', { params })
    return response.data
  },

  clearCache: async (): Promise<void> => {
    await apiClient.delete('/recommendations/cache')
  },
}
