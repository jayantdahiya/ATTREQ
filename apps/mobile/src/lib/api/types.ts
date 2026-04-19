export interface User {
  id: string
  email: string
  full_name: string | null
  location: string | null
  saved_latitude: number | null
  saved_longitude: number | null
  saved_city: string | null
  is_active: boolean
  is_verified: boolean
  created_at: string
  updated_at: string
  last_login: string | null
  oauth_provider: string | null
  style_preferences: string | null
}

export interface AuthResponse {
  access_token: string
  refresh_token: string
  token_type: string
  user: User
}

export interface WardrobeItem {
  id: string
  user_id: string
  original_image_url: string
  processed_image_url: string | null
  thumbnail_url: string | null
  category: string | null
  color_primary: string | null
  color_secondary: string | null
  pattern: string | null
  season: string[] | null
  occasion: string[] | null
  detection_confidence: number | null
  processing_status: 'pending' | 'processing' | 'completed' | 'failed'
  wear_count: number
  last_worn: string | null
  created_at: string
  updated_at: string
}

export interface WardrobeListResponse {
  items: WardrobeItem[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

export interface WardrobeUploadResponse {
  id: string
  status: string
  message: string
  original_image_url: string
}

export interface WeatherData {
  temp: number
  feels_like: number
  condition: string
  description: string
  humidity: number
  wind_speed: number
  icon: string
}

export interface OutfitItemDetail {
  id: string
  category: string | null
  color_primary: string | null
  pattern: string | null
  image_url: string | null
  thumbnail_url: string | null
}

export interface OutfitScores {
  color_harmony: number
  formality: number
  preference_bonus: number
  total: number
}

export interface OutfitSuggestion {
  top_item_id: string
  top_item: OutfitItemDetail
  bottom_item_id: string
  bottom_item: OutfitItemDetail
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

export interface Outfit {
  id: string
  user_id: string
  top_item_id: string | null
  bottom_item_id: string | null
  accessory_ids: string[] | null
  occasion_context: string | null
  worn_date: string | null
  feedback_score: number | null
  weather_context: Record<string, unknown> | null
  created_at: string
  updated_at: string
}

export interface OutfitListResponse {
  items: Outfit[]
  total: number
  page: number
  page_size: number
  total_pages: number
}
