# M4 — Today Dashboard & Outfits

> **Status:** Planned (written 2026-07-15; starts after M3 commit)
> **Parent:** [`00-goal.md`](00-goal.md). Environment: [`01-milestone-0-scaffold.md`](01-milestone-0-scaffold.md).
> **⚠️ Dependency:** weather context requires `OPENWEATHER_API_KEY` in `apps/api/.env`. Without it recommendations must still render (weather strip degrades gracefully — verify what the backend returns keyless and mirror RN's handling).

## Objective

The Today tab (artboard 05) shows daily weather-aware outfit suggestions with Wear/Skip/feedback actions; wearing an outfit records it and it appears in the History tab (artboard 07), grouped by date with status pills. Both in light and dark.

## References

- Design: `assets/design/ios-redesign-v2/attreq-app.jsx` → `ATTREQDashboard` (greeting header w/ date mono + "Good morning, *Name.*" display 32 + menu circle; `ATTREQWeatherStrip` city/temp/condition; "Today's looks" italic 20 + "N looks" mono; `ATTREQRecoCard`: Look No. mono accent + italic title 22 + match pill, garment collage 190pt (54% left + stacked right), weather/occasion mono row, hairline, Skip / Wear mono actions + heart/x circles, "Wear this" primary CTA; pull-down hint card) and `ATTREQHistory` (Diary header, "N looks tracked", date-grouped sections with hairline + ISO date mono, outfit cards: 3 mini garment tiles 34×50 r9 + italic title + "N pieces" mono + status pill Worn/Loved/Skipped)
- RN behavior: `apps/mobile/src/features/recommendations/dashboard-screen.tsx`, `recommendation-card.tsx`, `src/features/outfits/history-screen.tsx`, `outfit-history-card.tsx`, `src/lib/api/recommendations.ts`, `outfits.ts` (daily params incl. occasion/refresh, wear/feedback semantics, history pagination/grouping)
- Backend: `endpoints/recommendations.py` (GET /recommendations/daily params: lat/lon/occasion/refresh; caching), `endpoints/outfits.py` (POST /outfits body incl. feedback_score, worn_date; GET /outfits pagination)

## Key mappings (design → API)

- Weather strip + reco weather row: `DailySuggestionsResponse.weather` (city from user profile).
- Look title: design shows názvy like "The Long Walk" — RN has no titles; generate deterministic display names client-side from suggestion index/occasion (e.g. "Look No. 01" as heading already; italic title from a small curated list keyed by occasion+index) — keep it clearly presentational; note in doc.
- Match pill: `scores.total` as percentage.
- "Wear this" / Wear action → `POST /outfits` (top/bottom ids, occasion, worn_date today, weather_context) then refresh history; feedback: heart → feedback_score 1, x/skip → advance to next suggestion (and feedback_score -1 if RN does that — mirror RN exactly).
- Suggestion paging: RN shows multiple suggestions — mirror its navigation (index-based next on Skip).
- Pull-to-refresh → `GET /recommendations/daily?refresh=true`.
- History pills: worn_date != nil → Worn (moss); feedback_score 1 → Loved (gold); -1 → Skipped (clay) — verify against RN `outfit-history-card.tsx` and mirror.
- Garment tiles: real item thumbnails when available (AsyncImage) with GarmentPlaceholder fallback.

## Work packages

| WP | Files | Content |
|---|---|---|
| WP1 | Features/Today/RecommendationsRepository.swift, TodayViewModel.swift + tests; Features/History/OutfitsRepository.swift, HistoryViewModel.swift + tests | daily fetch (+location params from user), wear/feedback posting, history list + date grouping; mock-URLProtocol tests |
| WP2 | Features/Today/TodayScreen.swift, WeatherStrip.swift, RecommendationCard.swift | artboard 05 pixel-faithful incl. all states (loading skeleton, no-wardrobe empty state, keyless-weather degraded state) |
| WP3 | Features/History/HistoryScreen.swift, OutfitHistoryCard.swift; MainTabsView wiring (today + history tabs live) | artboard 07 pixel-faithful; empty state |
| WP4 (orchestrator, post-integration) | ATTREQUITests | Extend smoke: wear-flow E2E (needs ≥1 top + ≥1 bottom in wardrobe — provision via API using synthetic uploads, categories may be null without classifier key → check recommendation algorithm's category requirements; if unmeetable keyless, test the empty/degraded state instead and note it) |

## Exit criteria

1. Today tab renders suggestions (or honest degraded/empty states keyless); Wear records an outfit; History shows it grouped by date with the right pill.
2. Unit + UI tests green.
3. Screenshots match artboards 05 & 07 light + dark.
4. Committed on `ios-native`.
