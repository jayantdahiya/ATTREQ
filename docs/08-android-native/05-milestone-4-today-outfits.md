# A4 — Today, Recommendations & Outfits

> **Milestone file for A4.** Built via orchestrated sub-agent (rn-implementer, from a read-only spec agent's blueprint) + orchestrator on-device verification.
> **Status:** ✅ COMPLETE — `tsc` + Jest 29/29; Today/outfits Maestro E2E green (30 steps) **on a real device**.

## Goal (A4 gate)

Daily suggestions render with weather + explanation; wear/skip/reject flows work; swipe deck feeds feedback; worn outfits appear in History.

## Backend contract used

`GET /recommendations/daily?occasion=casual[&occasion_hint=][&force_refresh=]` (saved-location path; 404=empty, 400=no location, 503=weather), `GET /recommendations/swipe-deck[/status]`, `POST /recommendations/{id}/feedback {outfit_index, action, rejection_reason?, rejection_note?}` (fire-and-forget), `GET /outfits`, `POST /outfits`, `POST /outfits/{id}/wear {worn_date}` (LOCAL day), `POST /outfits/{id}/feedback {feedback_score}`.

## What shipped (apps/mobile/src)

- **API/query:** `lib/api/{recommendations,outfits}.ts`, `lib/query/{recommendations,outfits}.ts` (useInfiniteQuery history), `lib/utils/dates.ts` (local-day helpers). Types appended (snake_case).
- **Today:** `features/today/` — TodayScreen (greeting, WeatherStrip, vibe chips, RecommendationCard, hint, swipe-deck entry), RecommendationCard (look title, match%/Experimental, garment collage, explanation, context, SKIP/WEAR/♥/✕), RejectionReasonSheet (RN Modal, 6 reasons, BackHandler, fires once), SwipeDeckModal (like/dislike → feedback, 429 quiet, "All set" empty state), lookTitles, GarmentCollage.
- **History:** `features/history/` — HistoryScreen (date groups, N looks tracked), OutfitHistoryCard (tiles + pill), historyGrouping (dayKey local, pill precedence feedback>worn).
- **Wiring:** `MainTabs` today→TodayScreen, history→HistoryScreen; default tab now `today`. Icons added (arrowLeft/Right, thumbsUp/Down); Chip/BodyText gained `testID`.

## Behavior specifics

Wear = create-or-reuse outfit (module dedupe map) → `/wear`(local date) → fire `accepted` → advance + invalidate outfits. Love = feedback 1, no advance. Skip = rejection sheet → `rejected`, advance. Dismiss = outfit feedback -1 + `rejected`, advance. All recommendation feedback fire-and-forget.

## Notes / divergences

- **Recommendations need completed, categorized items** — in the keyless dev env the classifier can't categorize (items complete with colors but null category), so verification seeds categories via SQL to simulate real classification. Weather renders via backend defaults (no OPENWEATHER key). Swipe deck needs enough variety (≥ several looks) — a small wardrobe shows the "All set" empty state (correct behavior).
- worn_date + History grouping use the LOCAL calendar day (documented iOS divergence). Vibe "answered" state is per-session (not persisted) — minor divergence.

## Verification

- `verifier` static: `tsc --noEmit` → 0; Jest → **29/29** (7 suites; adds lookTitles/dates/historyGrouping).
- `verifier` Maestro (`.maestro/today-outfits-flow.yaml`, seeded located user + 8 categorized items): login → Today (assert greeting + weather-strip + label-explanation + wear-cta) → **action-wear** → **action-skip → rejection-sheet → reason → submit** → scroll → **swipe-deck → like → close** → **HISTORY → "Worn" pill**. **30 steps, 0 failures, on a real Android device.**
- `screenshot-auditor`: Today dashboard + History captured on-device (real rendering) — faithful; recommendation card shows a real algorithm explanation.

## Environment note

Verification moved to a **real Android device** (wireless debugging) after the headless emulator degraded (disk pressure → `screencap` failures); the dev backend URL is now `127.0.0.1:8001` + `adb reverse` (device-agnostic, works on device + emulator).
