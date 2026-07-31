# RI-7 — Retention Surfaces & Trust Infrastructure

> **Goal:** Ship the features long-term competitor users call "as valuable as Chanel" (wardrobe stats, forgotten items) and the trust infrastructure whose absence is churn-grade (multi-photo items, archive-don't-delete, stat integrity) — plus onboarding that delivers value at ~10 items.
> **Depends on:** RI-1 (wear/feedback events feed stats). Runs in parallel with RI-5/RI-6.
> **Status:** Not started

## Context (self-contained)

- Competitor evidence is unambiguous about what retains and what churns:
  - **Retains:** cost-per-wear, most/least-worn, "forgotten items"/never-worn lists, color/brand breakdowns, closet value ("Style Stats… as valuable as Chanel"; users setting "$1 cost-per-wear then retire" targets; 4-year Stylebook loyalty driven by stats).
  - **Churns:** duplicate items from multi-angle photos "ruin wardrobe statistics" (Whering's #1 gripe); un-deletable errors; sold items skewing counts; **catastrophic data loss** (Stylebook, local-only storage); all-photos permission demands; streak mechanics ("unnecessary pressure").
  - **Upload wall:** 2–3h for 200 items, 4–8h for a modest closet; every incumbent's praised feature (Acloset) or top gripe (Stylebook) is this. Value must arrive at ~10 items; "20 items in 5 minutes" is the hero moment.
- Current state: `WardrobeItem` (`apps/api/src/attreq_api/models/wardrobe.py`) has exactly one image (`original/processed/thumbnail` URLs), `wear_count`, `last_worn`, and **hard delete only**. No `purchase_price`, no archive state, no multi-photo. Outfit history exists (`models/outfit.py`, history screens on iOS/RN); no stats aggregation endpoints. Backend storage is cloud (R2 after launch-M1) — data-loss risk is already addressed server-side.
- Positioning research (Indyx, Echo Look post-mortem): the winning promise is **"control + effortlessness, from clothes you already own"** — user-supported, no affiliate pressure, sustainability framing structurally free via grey-inventory resurfacing (RI-4 already surfaces it in recommendations; this milestone surfaces it in stats).

## Decisions (pre-made)

- **Archive, never delete (by default).** `status` enum on wardrobe items: `active | archived` (sold/donated/stored). Archived items leave recommendation pools but keep outfit history and stats intact. Hard delete remains available but warns about history loss. *Basis: Stylebook power-user pattern (archiving sold items without breaking outfit history); Whering un-deletable-error complaints.*
- **Multi-photo per item, one stats identity.** New `wardrobe_item_photos` table; the item keeps a primary processed image (recommendations/classification unchanged); extra angles attach to the same item. Kills the duplicate-item stat corruption class. *Basis: Whering's top complaint; RI-6's near-duplicate warning offers "add as photo to existing item".*
- **Cost-per-wear uses "since tracking" framing** for pre-owned items (price ÷ wears **since adding**, labeled as such) — no fake estimates of prior wears. *Basis: Stylebook reviewers' skewed-CPW complaint.*
- **Stats are computed from real events** (wear events, RI-1 `user_events`), aggregated server-side in read-only endpoints — no separately maintained counters that can drift.
- **Onboarding target: recommendations from ~10 items** (enough for a few pairs), with batch capture and a granular photo picker (never demand all-photos permission), and explicit "keep adding to improve" framing. *Basis: incremental-cataloging power users; Whering permission-wall churn; "value at ~10 items" guardrail.*
- **No streaks, no guilt.** Progress framing only ("12 items added — 3 more unlocks better matches"). *Basis: Stylebook reviewer on streaks.*
- **State the positioning in-product:** a one-screen "how ATTREQ recommends" note — recommendations come only from your own wardrobe, no ads/affiliate influence. *Basis: Indyx user-supported trust framing; Echo Look opacity failure.*

## Tasks

### 7.1 Schema: archive, price, photos

1. **Alembic migration**: `wardrobe_items` gains `status` (`active|archived`, default active, indexed), `purchase_price` (numeric, nullable), `brand` (nullable string). New `wardrobe_item_photos`: `id`, `item_id` FK, `original/processed/thumbnail` URLs, `is_primary` bool, `created_at`.
2. `models/`, `schemas/`, `endpoints/wardrobe.py`: archive/unarchive actions (`PATCH` status), photo add/remove endpoints (reusing the upload pipeline for background removal of additional photos; no re-classification of non-primary photos), price/brand editable.
3. Recommendation pools (`algorithm.py` filters) and RI-4 pools exclude `archived`.

### 7.2 Stats endpoints

1. New `services/stats/wardrobe_stats.py` + `GET /api/v1/stats/wardrobe`: items by category/color-family/brand, closet value, % never worn ("grey inventory"), most/least worn, cost-per-wear list (since-tracking framing), 30/90-day wear distribution.
2. `GET /api/v1/stats/forgotten`: items with `wear_count=0` or `last_worn` > 60 days, each with its best-scoring partner item (one call into RI-3's pair scorer) → powers "not worn in 6 months — try it with X" copy.
3. All read-only, computed from `wardrobe_items` + outfit wear history + RI-1 events; cache per user (existing Redis) with invalidation on wear/archive.

### 7.3 Clients: stats + item management (iOS primary)

1. `apps/ios/`: Stats tab/section — closet composition (color/category), cost-per-wear list, forgotten-items list with "wear it with…" suggestion rows, closet value. Archive action on item detail (with unarchive in a filterable "Archived" view); multi-photo gallery on item detail with "add photo"; price/brand fields.
2. Duplicate-upload warning (from RI-6, if shipped) offers "add as another photo of …" targeting `wardrobe_item_photos`. Without RI-6, the manual "add photo" flow still lands.
3. Mirror in `apps/mobile/` if maintained.

### 7.4 Onboarding: batch capture at ~10 items

1. `apps/ios/` onboarding: batch capture loop (camera stays open between shots, thumbnails accumulate), granular library picker (limited-photos selection fully supported), progress framing, and a first-recommendation moment as soon as the wardrobe can produce one valid outfit (top+bottom minimum) — do not gate on "finish your closet".
2. Backend batch upload endpoint already exists (`wardrobe.py` batch upload; `workers/batch_image_processor.py`) — verify concurrency/ordering under a 20-image burst and fix as needed.
3. Onboarding copy leads with the overwhelm stat ("~25% of the average closet is never worn") and "recommends only from clothes you already own".

### 7.5 Trust copy

1. "How recommendations work" screen (settings + first-run touchpoint): your-closet-only, no affiliate/ads, what the explanation lines mean, how feedback improves picks. One screen, plain language.

## Out of scope

- Packing lists, capsules/collections, calendar OOTD view (strong candidates for the next phase; noted, not scheduled). Data import from competitor apps (moat-breaker, needs per-app formats — next phase). Resale/declutter integrations, concierge digitization, human-stylist tier (Tier-3). Aggregate "state of wardrobes" PR reports (needs user volume). Social features.

## Exit criteria

- Archiving a worn item removes it from recommendations while its outfits/stats history remains intact and correct.
- An item can hold 3 photos and still count once in every stat.
- Stats endpoints return correct numbers on a fixture wardrobe (hand-computed expectations), and the forgotten-items list pairs each item with a real partner suggestion.
- A fresh user reaching 10 items (incl. ≥1 top, ≥1 bottom) gets a first recommendation during onboarding.
- No all-photos permission requirement anywhere in the iOS flows.

## Verification

```bash
cd apps/api
PYTHONPATH=src ../../.venv/bin/alembic upgrade head
PYTHONPATH=src ../../.venv/bin/pytest tests/ -k "stats or archive or photos or batch_upload"
```

New tests: archived items excluded from pools but present in history queries; CPW math with and without price, since-tracking labeling; multi-photo item counted once in composition stats; forgotten-items query boundaries (60-day edge, wear_count=0); batch upload of 20 images completes with per-image status.

Manual device pass: add price to an item → CPW appears and drops after logging a wear; archive it → gone from Today, still in history; onboarding with 10 items → first outfit recommendation renders.
