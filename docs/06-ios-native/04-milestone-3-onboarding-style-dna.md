# M3 — Onboarding & Style DNA

> **Status:** Planned (written 2026-07-15; starts after M2 commit)
> **Parent:** [`00-goal.md`](00-goal.md). Environment: [`01-milestone-0-scaffold.md`](01-milestone-0-scaffold.md).
> **⚠️ Dependency:** Style DNA extraction calls the LLM classifier — requires `GROQ_API_KEY` (or alternative) in `apps/api/.env`. Flows must degrade gracefully without it (upload succeeds, extraction fails → skip path still works).

## Objective

A fresh account completes the full onboarding: Style DNA photo upload (artboard 09) → results view → review/confirm detected wardrobe items → lands on tabs. The Style DNA profile screen (view/correct/regenerate DNA, manage photos) is reachable from Profile later (M5 wires the row; the screen ships now with an audit route).

## References

- Design artboard 09: `assets/design/ios-redesign-v2/attreq-onboarding.jsx` (ATTREQStyleDNA — back circle + "Style DNA Setup" mono header, "Step 01 — Upload" accent mono, "Show us / *your style.*" display 34, body copy, 3×3-ish photo grid: 3:4 tiles radius 14, filled = image, empty = dashed 1.5 border + plus icon, 6 tiles; progress bar 3pt (accent fill, fraction = photos/8) + "N of 8 photos" mono; accent CTA "Build my Style DNA →"; "Skip for now" mono link)
- Screens 10–11 have NO artboards — compose in the design language (serif italic headlines, cards, mono labels, pills) reusing M0 components. RN reference for content/structure: `apps/mobile/app/(onboarding)/results.tsx`, `review-items.tsx`, `app/(protected)/style-dna/profile.tsx`, `src/features/style-dna/**` (StyleDnaCard, PhotoGrid, FoundItemsCard, ItemReviewCard, ConfidenceBadge, use-style-dna hooks)
- API wrappers: `apps/mobile/src/lib/api/style-dna.ts`; backend: `apps/api/src/attreq_api/api/v1/endpoints/style_dna.py`, `services/style_dna/style_dna_service.py` (multipart field names for photo upload, regenerate/correct/delete-photo shapes, wardrobe seeding behavior)

## Flow (mirror RN)

1. Root gate: `authenticated && !onboarding_completed` → onboarding stack (upload-style).
2. Upload-style: pick 3–8 photos (library; camera optional) → multipart `POST /users/style-dna` (verify exact path/fields in backend) → response has `style_dna`, `photos`, `wardrobe_items_seeded` + detected items. "Skip for now" → `POST /users/onboarding/complete` directly → tabs.
3. Results: show extracted DNA (aesthetic primary/secondary + confidence badges, color palette swatches dominant/accent/avoids, patterns, silhouette, formality label, occasions) + "N wardrobe items found" card → continue.
4. Review-items: list detected/seeded wardrobe items (reuse WardrobeItemCard where possible), allow deselect/confirm → `POST /wardrobe/items/bulk` for confirmed (verify RN behavior: does RN bulk-add here or are items already seeded server-side? Read `review-items.tsx` + backend; mirror exactly) → `POST /users/onboarding/complete` → tabs.
5. Style DNA profile screen: `GET /users/style-dna` render DNA + photo grid; correct (PATCH), regenerate (POST), delete photo (DELETE). Reachable via `-screen style-dna` audit route now; Profile row in M5.

## Work packages

| WP | Files | Content |
|---|---|---|
| WP1 | Features/StyleDna/StyleDnaRepository.swift (+ ViewModels) + tests | upload photos multipart, get/patch/regenerate/delete, onboarding-complete; mock-URLProtocol tests |
| WP2 | Features/StyleDna/Onboarding/ (UploadStyleView per artboard 09, ResultsView, ReviewItemsView) | screens + flow shell; RootView onboarding gate swap (replace OnboardingPlaceholderView) |
| WP3 | Features/StyleDna/Profile/ (StyleDnaProfileView + components: ConfidenceBadge, PaletteRow, PhotoGrid) | profile screen + audit route |
| WP4 (post-integration) | ATTREQUITests | Extend/adjust smoke: fresh register → upload-style appears; skip path → tabs. (Full photo-pick UI automation only if simulator picker cooperates; otherwise skip path is the tested route + manual verification of upload.) |

## Exit criteria

1. Fresh account: register → upload-style screen; skip → tabs. With photos: upload → results → review → tabs (classifier-dependent parts verified if key present; graceful failure otherwise).
2. Unit tests green; UI smoke updated and green.
3. Screenshots: artboard 09 match light+dark; results/review/profile screens consistent with design language.
4. Committed on `ios-native`.
