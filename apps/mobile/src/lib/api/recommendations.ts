import { apiClient } from '@/lib/api/client';
import type {
  DailySuggestionsResponse,
  RecommendationFeedbackPayload,
  SwipeDeckStatusResponse,
} from '@/lib/api/types';

// Backend contract: apps/api/src/attreq_api/api/v1/endpoints/recommendations.py.
// Steady state uses the SAVED-location path (never sends lat/lon); the backend
// falls back to the user's profile coords and answers 400 if none are saved.
// RN always requests occasion=casual (backend default). `occasion_hint` is the
// RI-5 morning-vibe nudge — omitted (not "") until the user answers.
export const recommendationsApi = {
  async daily(params: {
    occasion?: string;
    occasionHint?: string | null;
    forceRefresh?: boolean;
  } = {}) {
    const query: Record<string, string | boolean> = {};
    if (params.occasion) query.occasion = params.occasion;
    if (params.occasionHint) query.occasion_hint = params.occasionHint;
    if (params.forceRefresh) query.force_refresh = true;
    const response = await apiClient.get<DailySuggestionsResponse>('/recommendations/daily', {
      params: query,
    });
    return response.data;
  },

  // RI-5: a fresh, uncached deck (<=5) of outfits to rate. Never itself
  // rate-limited — only the ratings (submitted via `feedback`) are capped.
  async swipeDeck(occasion?: string) {
    const response = await apiClient.get<DailySuggestionsResponse>('/recommendations/swipe-deck', {
      params: occasion ? { occasion } : undefined,
    });
    return response.data;
  },

  async swipeDeckStatus() {
    const response = await apiClient.get<SwipeDeckStatusResponse>('/recommendations/swipe-deck/status');
    return response.data;
  },

  // POST /recommendations/{id}/feedback — recommendation-level telemetry.
  // 429 = swipe-deck daily cap. rejection_reason/note only persisted server-side
  // when action === 'rejected' (the request schema is forgiving otherwise).
  async submitFeedback(recommendationId: string, payload: RecommendationFeedbackPayload) {
    await apiClient.post(`/recommendations/${recommendationId}/feedback`, payload);
  },
};
