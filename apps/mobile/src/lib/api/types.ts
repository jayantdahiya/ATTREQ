// API types — regenerated against the current backend schemas
// (apps/api/src/attreq_api/schemas). Grown per-milestone; A1 covers auth + user.

export interface User {
  id: string;
  email: string;
  full_name: string | null;
  location: string | null;
  saved_latitude: number | null;
  saved_longitude: number | null;
  saved_city: string | null;
  is_active: boolean;
  is_verified: boolean;
  created_at: string;
  updated_at: string;
  last_login: string | null;
  oauth_provider: string | null;
  style_preferences: string | null;
  onboarding_completed: boolean;
  onboarding_step: string | null;
}

export interface AuthResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  user: User;
}

// ── Wardrobe (A2) — mirrors apps/api schemas/wardrobe.py ──────────────────────

export type WardrobeItemStatus = 'active' | 'archived';
export type ProcessingStatus = 'pending' | 'processing' | 'completed' | 'failed';

export interface PaletteColor {
  lab: [number, number, number];
  hex: string;
  share: number;
  is_neutral: boolean;
  name: string;
}

export interface WardrobeItemPhoto {
  id: string;
  original_image_url: string;
  processed_image_url: string | null;
  thumbnail_url: string | null;
  is_primary: boolean;
  created_at: string;
}

export interface WardrobeItem {
  id: string;
  user_id: string;
  category: string | null;
  color_primary: string | null;
  color_secondary: string | null;
  pattern: string | null;
  season: string[] | null;
  occasion: string[] | null;
  original_image_url: string;
  processed_image_url: string | null;
  thumbnail_url: string | null;
  detection_confidence: number | null;
  classification_source: string | null;
  processing_status: ProcessingStatus;
  status: WardrobeItemStatus;
  purchase_price: number | null;
  brand: string | null;
  wear_count: number;
  last_worn: string | null;
  created_at: string;
  updated_at: string;
  // Detail-only (present on GET /items/{id}); absent in list entries.
  photos?: WardrobeItemPhoto[];
  // Classifier schema v2 (RI-2) — optional.
  texture?: string | null;
  silhouette?: string | null;
  neckline?: string | null;
  sleeve_length?: string | null;
  statement_level?: string | null;
  llm_formality?: number | null;
  is_fullbody?: boolean;
  color_palette?: PaletteColor[] | null;
  schema_version?: number;
  possible_duplicate_of?: string | null;
  needs_review?: boolean;
  review_reason?: string | null;
}

export interface WardrobeListResponse {
  items: WardrobeItem[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface WardrobeUploadResponse {
  id: string;
  status: string;
  message: string;
  original_image_url: string;
}

export interface WardrobeItemUpdatePayload {
  category?: string | null;
  color_primary?: string | null;
  color_secondary?: string | null;
  pattern?: string | null;
  season?: string[] | null;
  occasion?: string[] | null;
  purchase_price?: number | null;
  brand?: string | null;
  texture?: string | null;
  silhouette?: string | null;
  neckline?: string | null;
  sleeve_length?: string | null;
  statement_level?: string | null;
  is_fullbody?: boolean | null;
}
