# M5 — Profile, Polish & Design Audit

> **Status:** Planned (written 2026-07-15; starts after M4 commit)
> **Parent:** [`00-goal.md`](00-goal.md). Environment: [`01-milestone-0-scaffold.md`](01-milestone-0-scaffold.md).

## Objective

The last feature milestone: Profile screen (artboard 08) with real data, the deferred Style DNA correction UI, the local daily-reminder, and the full-app polish + design-audit pass that closes out the goal file's exit criteria.

## References

- Design: `assets/design/ios-redesign-v2/attreq-app.jsx` → `ATTREQProfile` (mono "You" + italic display-28 "Profile"; identity card with 3pt accent left border: 50pt accent circle w/ serif italic initials, display-20 name, 13pt email, hairline, stats row gap 28 [Pieces / Worn / Streak — italic display-22 values, streak accented]; "Style DNA" mono label + row card (sparkles icon, "Your Style DNA" 14pt + "Tap to view or edit" mono, chevron); "Preferences" mono label + card of 3 rows (location w/ "Edit" accent action, "Daily reminder" w/ moss toggle, style preferences w/ "Edit") with borderSoft dividers; centered clay "Sign out" mono + "v X.Y.Z — ATTREQ" footer)
- RN behavior: `apps/mobile/src/features/profile/profile-screen.tsx` (what stats mean, what edit actions do)
- Backend: `PUT /users/me`, `PATCH /users/me/location`, `GET /users/style-dna` + `PATCH` (corrections)

## Scope

| WP | Content |
|---|---|
| WP1 | **ProfileScreen** (artboard 08): identity card (initials from full_name, live stats: Pieces = wardrobe totalCount, Worn = outfits with worn_date, Streak = consecutive local days with a worn outfit ending today — compute client-side, mirror RN if it differs), Style DNA row → push StyleDnaProfileView, preferences rows: location (sheet: LocationStepView-style device-location + manual city → PATCH), daily reminder (toggle → UNUserNotificationCenter local daily notification at 8:00, permission flow, persisted in UserDefaults, moss toggle per design), style preferences (sheet with chips like StyleStepView → PUT /users/me best-effort, noting backend gap), Sign out (session.logout), version footer from bundle. Replace the MainTabsView profile stub. |
| WP2 | **Style DNA correction UI** (deferred from M3): edit affordance on StyleDnaProfileView sections (aesthetic primary/secondary, formality label) → `PATCH /users/style-dna` with snake_case corrections; optimistic update + reload. |
| WP3 | **Polish pass**: sweep every screen for missing loading/empty/error/offline states, Dynamic-Type sanity at XL, dark-mode leaks (hardcoded colors), inconsistent copy; fix in place. Verify all accessibility ids still stable for UI tests. |
| WP4 (orchestrator) | **Design audit**: every artboard (01–09 + composed screens) screenshotted light+dark via audit routes, compared against the jsx; divergences fixed or recorded in the audit table below. **Profile E2E UI test** (stats render, sign out works). **Docs**: apps/ios/README.md (build/run/test instructions, architecture map, audit-route list), goal-file compliance check. |

## Exit criteria (closes the goal file)

1. Every artboard-mapped screen + composed screens match the design in both themes (audit table complete, divergences justified).
2. Profile flows work E2E against local backend; full test suite green (unit + all UI smoke flows).
3. Known divergences/registered gaps documented in 00-goal.md status update.
4. Final commit on `ios-native`; goal file marked complete with a summary of what shipped.

## Audit table

(filled during WP4)

| Artboard | Light | Dark | Notes |
|---|---|---|---|
