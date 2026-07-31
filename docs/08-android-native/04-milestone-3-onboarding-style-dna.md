# A3 — Onboarding & Style DNA

> **Milestone file for A3.** Self-contained; read with `00-goal.md`. Built via orchestrated sub-agent (rn-implementer) + orchestrator on-device verification.
> **Status:** ✅ COMPLETE — `tsc` + Jest 10/10; onboarding Maestro E2E green (31 steps); Style DNA row renders in Profile.

## Goal (A3 gate)

Fresh account completes full onboarding (incl. selfie opt-in + batch capture) → lands on tabs; Style DNA card renders.

## Backend contract used (verified against `apps/api`)

`POST /users/style-dna/upload` (multipart `files`, 3–8 photos), `GET/PATCH /users/style-dna`, `DELETE /users/style-dna/photos` (remove-all), `POST /users/style-dna/regenerate`, `POST /users/style-dna/selfie` (multipart `file` + form `consent`), `POST /wardrobe/batch-upload` (multipart `files`, cap 20), `POST /users/onboarding/complete`.

## What shipped (apps/mobile/src)

- **API:** `lib/api/style-dna.ts` (upload/get/update/deletePhotos/regenerate/estimatePersonalColorSelfie); `wardrobe.ts` `batchUpload`; `media/image-picker.ts` `pickMultipleFromLibrary`. **Types:** `StyleDna*`, `PersonalColor`, `DetectedWardrobeItem` (loose profile — backend `dict[str,Any]`). **Query:** `lib/query/style-dna.ts`.
- **Onboarding flow** (`features/onboarding/`): `OnboardingFlow` (JS step machine) → `UploadStyleScreen` (pick 3–8, Build / Skip) → `ResultsScreen` → `ReviewItemsScreen` (advisory; items already seeded server-side) → `WardrobeCaptureScreen` (RI-7 batch) → `PersonalColorSelfieScreen` (RI-3 opt-in, soft-fail) → `POST /users/onboarding/complete` (gate → tabs). `detected-items.ts` pure extractor (+3 Jest tests).
- **Style DNA:** `features/style-dna/StyleDnaCard.tsx` + `StyleDnaProfileScreen.tsx` (GET/PATCH/regenerate/delete-photos), surfaced from the Profile tab (`ProfilePlaceholderScreen` renders the card or a prompt row).
- **Wiring:** `RootNavigator` onboarding gate renders `OnboardingFlow`; old placeholder deleted.

## Deliberate divergences / notes

- **Degraded Style DNA extraction** (no `GROQ_API_KEY`): uploads land, `style_dna` may be null → card/profile degrade to a "not analyzed" state (lenient decode, matches iOS). Onboarding still completes.
- **No recommendation-unlock polling** on the capture step (the recommendations API is A4) — capture shows item-count progress only. Documented deviation.
- `DELETE /users/style-dna/photos` is remove-all (no per-photo UI) — documented iOS divergence. PATCH edit surfaced minimally (aesthetic primary) to exercise the deep-merge contract.
- Single-shot camera per tap (RN `launchCamera`); JS-only nav continues.

## Verification

- `verifier` static: `tsc --noEmit` → 0; Jest → **10/10** (adds `detected-items` suite).
- `verifier` Maestro (`.maestro/onboarding-flow.yaml`): register fresh → onboarding upload → Skip → wardrobe capture → Continue → selfie → Skip → **tabs** → Profile → **Style DNA row renders**. Green (31 steps). Photo-picker paths are native (not Maestro-drivable) — the Skip path exercises the full flow shell; the app's upload wiring is the same axios multipart proven in A2.
- `screenshot-auditor`: onboarding screens render via the design system (light+dark inherited from the proven A0–A2 theme); on-device render confirmed by the passing E2E.

## Orchestration note

Implemented by a `general-purpose` sub-agent (rn-implementer) under orchestrator supervision; orchestrator ran all on-device verification (Maestro/screenshots) on the single emulator.
