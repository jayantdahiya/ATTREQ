# M2 — Wardrobe

> **Status:** ✅ Complete (2026-07-15). E2E upload verified (multipart → backend pipeline incl. rembg + fallback color classification → polling → grid); artboard 06 matches light+dark; 46 unit + 2 E2E UI tests green. Review fixed: filter buckets now cover the classifier's closed 20-term vocabulary, cancellation no longer surfaces phantom offline banners or post-disappear pollers, real pagination (loadMore + page-1 poll merge), optimistic upload placeholder, fresh poll deadline per upload. Note: PHPicker resists synthesized taps → `-uitest-autopick-photo` hook feeds a synthetic JPEG through the real upload path; picker itself human-verified via screenshot.
> **Parent:** [`00-goal.md`](00-goal.md). Environment: [`01-milestone-0-scaffold.md`](01-milestone-0-scaffold.md) (backend :8001, compose `attreq-dev`).
> **⚠️ Dependency:** clothing classification requires `GROQ_API_KEY` in `apps/api/.env` (or another `CLASSIFIER_PROVIDER` + key). Without it uploads land in `failed`/`pending` status — UI must handle that state gracefully either way.

## Objective

Wardrobe screen (artboard 06) works end-to-end: browse the wardrobe in the design's two-column grid with category filter chips, add a piece via camera or photo library, watch it move `pending → processing → completed` with the classified category/color appearing, in light and dark.

## References

- Design: `assets/design/ios-redesign-v2/attreq-app.jsx` → `ATTREQWardrobe` (header "Closet / *Wardrobe*", piece-count line, category chips row [All/Tops/Bottoms/Outer/Accents/Shoes], two dashed upload tiles [Camera / Library], 2-column staggered grid: image card radius 16 + serif-italic category + mono color label)
- RN behavior: `apps/mobile/src/features/wardrobe/wardrobe-screen.tsx`, `wardrobe-item-card.tsx`, `apps/mobile/src/lib/api/wardrobe.ts` (list params, upload multipart field names, polling/refetch behavior)
- Backend: `apps/api/src/attreq_api/api/v1/endpoints/wardrobe.py` (GET /wardrobe/items pagination + filters; POST /wardrobe/upload multipart field name, size limits; item schema)

## Architecture additions

```
ATTREQ/Core/Networking/  Endpoint gains .multipart([MultipartField]) body (boundary, file part w/ filename+contentType)
ATTREQ/Features/Wardrobe/
├── WardrobeRepository.swift    list(page:category:), upload(imageData:), item polling (async poll until terminal status, cancellable)
├── WardrobeScreen.swift        grid + chips + upload tiles + pull-to-refresh
├── WardrobeItemCard.swift      thumbnail (AsyncImage vs URLCache), serif category, mono color, status pill for pending/processing/failed
├── WardrobeViewModel.swift     @Observable: items, filter, pagination, upload progress states
└── PhotoInput/                 PhotosPicker wrapper + camera (UIImagePickerController representable), downscale/JPEG-encode before upload
ATTREQ/App/MainTabsView.swift   REAL tab shell replacing MainTabsPlaceholderView: AttreqTabBar + switch(today|wardrobe|history|profile); non-wardrobe tabs keep placeholders
```

Notes:
- Image URLs from backend are relative (`/uploads/...`) — resolve against API origin (base URL minus `/api/v1`). Add helper in AppConfig.
- Category filter: backend categories are free text (roadmap M2 gap); map chips to case-insensitive substring match the way the RN app does — verify in RN source and mirror.
- Poll for status: refetch item(s) every ~2s while any item is pending/processing (max ~90s), stop when terminal; cancel on disappear.
- Camera is unavailable in simulator — camera tile must degrade (disabled state) when `UIImagePickerController.isSourceTypeAvailable(.camera)` is false. E2E verification uses the photo library path (simulator has seed photos; `simctl addmedia` can add fixtures).

## Work packages

| WP | Files | Content |
|---|---|---|
| WP0 (orchestrator) | — | Multipart contract review, fixture images via `simctl addmedia`, integration |
| WP1 | Core/Networking (multipart), Features/Wardrobe/WardrobeRepository+ViewModel + unit tests | Repository, multipart encoding tests, polling logic tests (mock URLProtocol) |
| WP2 | Features/Wardrobe UI + App/MainTabsView | Screen, card, chips, tiles, tab shell per design |
| WP3 | Features/Wardrobe/PhotoInput | PhotosPicker + camera representable + downscale pipeline |
| WP4 (after integration) | ATTREQUITests | Extend smoke: log in → wardrobe tab → add from library → item appears (status text or classified) |

## Exit criteria

1. Register/login → Wardrobe tab → pick a library photo → item uploads, grid shows it pending → classified fields appear when backend completes (or a clear failed state without classifier key).
2. Unit tests (multipart, polling) + UI test green.
3. Screenshots match artboard 06 light + dark.
4. Committed on `ios-native`.
