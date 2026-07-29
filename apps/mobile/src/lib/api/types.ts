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

// ── Style DNA (A3) — mirrors apps/api schemas/style_dna.py + iOS Core/Models/StyleDna.swift ──
//
// The backend stores `style_dna` as `dict[str, Any]` (the synthesis LLM's raw
// output), so the concrete shape is only a convention — the interface below is
// permissive (every section optional, plus an index signature) and must never
// be relied on to fully decode. The known section shapes come from the
// synthesis prompt (services/style_dna/prompts.py) and StyleDna.swift; JSON
// keys are the backend's snake_case form (`color_palette`, `formality_bias`,
// `personal_color`, `behaviour_weights`).

export interface StyleDnaAesthetic {
  primary: string;
  secondary: string[];
  confidence: number;
}

export interface StyleDnaColorPalette {
  dominant: string[];
  accent: string[];
  avoids: string[];
  confidence: number;
}

export interface StyleDnaPatterns {
  preferred: string[];
  confidence: number;
}

export interface StyleDnaSilhouette {
  /** slim-fitted|relaxed-fitted|oversized|structured|draped|tailored|mixed */
  preference: string;
  confidence: number;
}

export interface StyleDnaFormalityBias {
  /** 0.0–3.0 weighted average (0 = athletic … 3 = formal). */
  level: number;
  /** athletic|casual|smart-casual|business|formal */
  label: string;
  confidence: number;
}

export interface StyleDnaOccasions {
  primary: string[];
  confidence: number;
}

/**
 * RI-3 `personal_color` — two continuous axes estimated from an optional,
 * opt-in selfie (never a self-declared "season"). Both `[-1, 1]`
 * (+1 = deep/warm, -1 = light/cool); `confidence` is `[0, 1]`. Absent until
 * the user completes `POST /users/style-dna/selfie` at least once.
 */
export interface PersonalColor {
  undertone_warm_cool: number;
  depth_light_deep: number;
  confidence: number;
}

/** Loose Style DNA profile — every section optional; extra keys tolerated. */
export interface StyleDna {
  aesthetic?: StyleDnaAesthetic;
  color_palette?: StyleDnaColorPalette;
  patterns?: StyleDnaPatterns;
  silhouette?: StyleDnaSilhouette;
  formality_bias?: StyleDnaFormalityBias;
  occasions?: StyleDnaOccasions;
  behaviour_weights?: Record<string, Record<string, number>>;
  personal_color?: PersonalColor;
  [key: string]: unknown;
}

export interface StyleDnaPhoto {
  id: string;
  user_id: string;
  file_path: string;
  file_url: string;
  quality_ok: boolean;
  quality_reason: string | null;
  per_photo_extraction: Record<string, unknown> | null;
  created_at: string;
}

export interface StyleDnaUploadResponse {
  photos_processed: number;
  photos_skipped: number;
  wardrobe_items_seeded: number;
  style_dna: StyleDna | null;
  photos: StyleDnaPhoto[];
}

export interface StyleDnaProfileResponse {
  style_dna: StyleDna | null;
  photos: StyleDnaPhoto[];
}

/** PATCH /users/style-dna body — deep-merged server-side (snake_case keys). */
export interface StyleDnaCorrection {
  corrections: Record<string, unknown>;
}

/**
 * A wardrobe item detected inside a Style DNA outfit photo, flattened out of
 * `photos[].per_photo_extraction.wardrobe_items_detected` (see
 * features/onboarding/detected-items.ts). Advisory only on the client — the
 * backend already seeded these during upload.
 */
export interface DetectedWardrobeItem {
  category: string;
  subcategory: string;
  colorPrimary: string | null;
  colorSecondary: string | null;
  pattern: string | null;
  occasion: string[];
  season: string[];
  confidence: number;
  boundingRegion: string;
}
