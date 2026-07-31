# A5 — Profile, Stats, Polish & Audit

> **Milestone file for A5** (final). Built via orchestrated sub-agent (rn-implementer) + orchestrator on-device verification.
> **Status:** ✅ COMPLETE — `tsc` + Jest 56/56; profile Maestro E2E green (29 steps) **on a real device**.

## Goal (A5 gate)

Profile with stats + Style DNA row + preferences + local daily-reminder + sign out; wardrobe stats screen; "how recommendations work"; error/empty/loading states everywhere.

## Backend contract used

`GET /stats/wardrobe` (total_active_items, by_category/color_family/brand, closet_value, cost_per_wear[], most/least_worn, worn_last_30_days), `GET /stats/forgotten` (items + days_since_worn + best_partner), `PUT /users/me`, `PATCH /users/me/location`, `POST /users/change-password`, `DELETE /users/me` (soft-deactivate), `POST /auth/logout`.

## What shipped (apps/mobile/src)

- **API/query:** `lib/api/stats.ts`, `lib/query/stats.ts`, `lib/query/users.ts`; `users.ts` gained `changePassword`, `deleteAccount`. Stats types appended (snake_case).
- **Profile hub** — `features/profile/ProfileScreen.tsx` (rewrite of the placeholder; `MainTabs` updated): identity card + stat tiles (Pieces / Cost-per-wear / Worn 30d), Style DNA row → StyleDnaProfileScreen, Preferences (location edit, daily-reminder toggle, style-preferences edit, change-password), Wardrobe Stats + How-it-works rows, sign out, delete account. Edit modals via a shared `ProfileSheet` (RN Modal + BackHandler): `LocationEditModal`, `StylePreferencesModal`, `ChangePasswordModal`, `DeleteAccountModal`. `MossToggle`, `profileFormat.ts` (initials/name/prefs — unit-tested).
- **Wardrobe Stats** — `features/stats/WardrobeStatsScreen.tsx` (overview, composition bars, cost-per-wear, most/least worn, forgotten pieces; loading/error/empty states; item taps → detail). `statsFormat.ts` (unit-tested).
- **How-it-works** — `features/profile/HowRecommendationsWorkScreen.tsx` (static explainer, copy ported from iOS).

## Notes / divergences

- **Daily reminder = persisted toggle only** (AsyncStorage via existing `get/saveReminderEnabled`); OS scheduling + Android 13+ `POST_NOTIFICATIONS` **deferred** (no notifications module — lowest risk, documented in code).
- **Style preferences device-local** — backend `UserUpdate` ignores `style_preferences` (DNA-owned); best-effort PUT + "Saved on this device only" (mirrors iOS).
- **Location edit** manual-city (device-location deferred, as A1); coordinate-only `PATCH /users/me/location`, city-only routes via `PUT /users/me`.
- **Delete account** = soft-deactivate → sign out, gated behind typing "DELETE".
- Stat tiles are Pieces / Cost-per-wear / Worn-30d (from `/stats/wardrobe`); sparse for fresh users → empty state.

## Verification

- `verifier` static: `tsc --noEmit` → 0; Jest → **56/56** (9 suites; adds stats-format, profile-format).
- `verifier` Maestro (`.maestro/profile-flow.yaml`): login → Profile (assert stats row + Style DNA row + reminder toggle) → Wardrobe Stats → back → How-it-works → back → toggle reminder → sign out → login. **29 steps, 0 failures, on a real Android device.** (Fixed a tab-bar-overlap tap-through by centering scrolled rows + bumping Profile bottom padding.)
- `screenshot-auditor`: Profile hub captured on-device — faithful, live stats (8 pieces, worn 2), all sections present.

## Orchestration note

Implemented by a `general-purpose` sub-agent (rn-implementer). The A5 read-only spec agent failed twice on API errors, so the implementer read its own surface (as A3 did). Orchestrator ran all on-device verification on the real device.
