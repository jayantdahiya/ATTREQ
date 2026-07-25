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
