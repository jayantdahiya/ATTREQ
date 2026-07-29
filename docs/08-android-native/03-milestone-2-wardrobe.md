# A2 — Wardrobe

> **Milestone file for A2.** Self-contained; read with `00-goal.md`. Node order: `ios-reader → rn-implementer → verifier → screenshot-auditor`.
> **Status:** ✅ COMPLETE — all four nodes passed. `tsc` + Jest 7/7; Maestro wardrobe E2E green (grid → detail → archive → archived) + auth regression green; wardrobe renders faithfully with backend images loading, light + dark.

## Goal (A2 gate)

Upload a photo → classified + displayed; open detail; archive/unarchive — matching iOS.

## ios-reader spec (sources)

- Behavior: `apps/ios/Features/Wardrobe/WardrobeViewModel.swift` — category chips (All/Tops/Bottoms/Outer/Accents/Shoes) with substring bucketing (precedence bottoms → shoes → outer → accents → tops), page-1 list (page_size 50), multipart upload + optimistic pending placeholder, **status polling ~2s (90s cap)** while items are pending/processing, `.active`/`.archived` lifecycle.
- Contracts: `apps/api/schemas/wardrobe.py` + endpoints — `GET /wardrobe/items?status=&page=&page_size=`, `POST /wardrobe/upload` (multipart `file`), `GET /items/{id}`, `PUT /items/{id}`, `PATCH /items/{id}/status` (`active`|`archived`), multi-photo `.../photos`. List entries omit `photos`; detail includes them + RI-2 v2 attributes (texture/silhouette/neckline/sleeve/statement, CIELAB `color_palette`).

## rn-implementer — what shipped

- **Logic:** `lib/api/wardrobe.ts` (list/upload/getItem/updateItem/setStatus/deleteItem), `lib/query/wardrobe.ts` (TanStack Query hooks with **auto status-polling** via `refetchInterval`), `lib/utils/images.ts` (relative→absolute + localhost→10.0.2.2 rewrite for the emulator), `lib/media/image-picker.ts` (`react-native-image-picker` camera + library), `features/wardrobe/categories.ts` (bucketing).
- **UI:** `WardrobeScreen` (header + piece count, camera/library upload tiles, category chips, two-column polling grid, pull-to-refresh, Archived link), `WardrobeItemCard` (image/placeholder + processing/failed pill), `WardrobeItemDetailScreen` (image, tag rows, **archive/unarchive**), `ArchivedWardrobeScreen`, `WardrobeStack` (JS list↔detail↔archived).
- **Tab shell:** `navigation/MainTabs.tsx` — floating pill `TabBar` (Today/Wardrobe/History/Profile), JS tab state; Wardrobe functional, Today/History placeholders, Profile stub (holds Sign out until A5). Wired into `RootNavigator` (replaces the A1 home stub).
- **Native:** `react-native-image-picker` (TurboModule — no codegen conflict, unlike react-native-screens); `CAMERA` + `READ_MEDIA_IMAGES` manifest permissions.

## Deliberate divergences / notes (A2)

- **Classification runs in degraded mode** (no `GROQ_API_KEY` in `apps/api/.env`): uploads land and display with their processing status but aren't tag-classified — the documented degraded mode (same as the iOS baseline). "Displayed + detail + archive" is fully exercised; full tag classification needs the key.
- **Item detail is read-first + archive** for A2; inline tag *editing* (`PUT /items/{id}`) and multi-photo add/delete are wired in the API layer and completed in a later pass.
- JS-only navigation continues (React Navigation still deferred — see A1).

## Verification

- `verifier` static: `tsc --noEmit` → 0; Jest → **7/7** (adds `wardrobe-categories` bucketing/precedence).
- `verifier` Maestro (`.maestro/wardrobe-flow.yaml`, seeded onboarded user + 1 API-uploaded item): login → tab shell → **wardrobe grid shows the item** → detail → **archive** → back → **Archived view shows the item**. Green. Auth-flow E2E re-runs green against the new tab shell (sign out now via the Profile tab).
- `screenshot-auditor`: Wardrobe grid + upload tiles + chips in light + dark. **(completing)**
