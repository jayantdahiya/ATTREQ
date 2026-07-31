# Milestone 2 — Data Model & Contract Hardening

> **Goal:** Every wardrobe item has a canonical, slot-prefixed category; the backend↔mobile API contract is documented and enforced by tests (closes **TKT-002**); weather has a geocoding fallback chain; the Google OAuth ghost config is removed.
> **Depends on:** Milestone 1 (verification runs against the prod VPS; do the work any time)
> **Status:** Not started
> **Why now:** there are zero production users — data migrations and contract changes are free. After beta launch they are not.

## Context (self-contained)

- `WardrobeItem.category` (`apps/api/src/attreq_api/models/wardrobe.py`) is a **free-text VARCHAR**. AI classifiers emit variants ("t-shirt", "Tshirt", "Tee Shirt") that are never normalized, which breaks:
  - **Slotting** in `apps/api/src/attreq_api/services/recommendation/algorithm.py` (~lines 531–542): tops are found via `"top" in item.category.lower()`, bottoms via `"bottom" in ...`, accessories via substring match on `["accessory", "shoe", "bag"]`. A category of "t-shirt" doesn't contain "top" → falls into a blind half-split fallback.
  - **Formality scoring**: `formality_map` at `algorithm.py:254-269` keys on free-text substrings ("suit", "dress shirt", "jeans", …) matched via `key in category` at line 279.
  - Mobile wardrobe grid grouping / filters.
- Classifier output flows through `apps/api/src/attreq_api/services/ai/schema_mapper.py` — `map_gemini_to_wardrobe_schema()` (used by **all** providers despite the legacy name; Groq is the live default, Claude/OpenAI swappable via `services/ai/classifier_factory.py`). This is the single choke point for normalization.
- Auth is JWT access+refresh; mobile uses an Axios client with a refresh interceptor (`apps/mobile/src/`), TanStack Query, Zod schemas. The exact contract (response shapes, refresh semantics, recommendation→outfit materialization) is undocumented — this is **TKT-002** in `docs/00-current-status/02-next-phase-tickets.md`.
- Weather/recommendations accept `?lat=&lon=`; there is **no geocoding provider and no fallback** when GPS is unavailable. `User` has saved `latitude`/`longitude`/`city` columns. The OpenWeather key already exists (`OPENWEATHER_API_KEY` in `config/settings.py`).
- Google OAuth is a **ghost feature**: `settings.py` lines ~60-62 define `google_client_id/secret/redirect_uri`, `.env.example` documents them, `users` table has `oauth_provider`/`oauth_id` columns — but zero endpoints/handlers exist.
- Backend contract tests live in `apps/api/tests/test_client_contracts.py` (with `conftest.py` fixtures); `alembic upgrade head` is checked in CI.

## Decisions (pre-made)

- **Slot-prefixed string enum**, stored in the existing VARCHAR column (no PG enum type — avoids migration pain when adding values). Canonical value format: `<slot>.<name>`.
- **Normalization is enforcement**: classifier prompts are tightened to request canonical labels, but the normalizer always runs — never trust the model.
- **Geocoding via OpenWeather Geocoding API** (`https://api.openweathermap.org/geo/1.0/direct`) — same key, zero new credentials.
- **OAuth: remove config, keep columns.** Nullable DB columns are harmless and save a migration round-trip if OAuth lands later; document them as reserved.

## Tasks

### 2.1 Category taxonomy + normalization

1. **New** `apps/api/src/attreq_api/domain/taxonomy.py` (new `domain/` package with `__init__.py`):

   ```python
   class Category(StrEnum):
       # tops
       TSHIRT = "tops.tshirt"; SHIRT = "tops.shirt"; BLOUSE = "tops.blouse"
       SWEATER = "tops.sweater"; HOODIE = "tops.hoodie"; TANK = "tops.tank"
       TOP_UNKNOWN = "tops.unknown"
       # bottoms
       JEANS = "bottoms.jeans"; CHINOS = "bottoms.chinos"; TROUSERS = "bottoms.trousers"
       SHORTS = "bottoms.shorts"; SKIRT = "bottoms.skirt"; SWEATPANTS = "bottoms.sweatpants"
       BOTTOM_UNKNOWN = "bottoms.unknown"
       # dresses (one-piece; counts as top+bottom in slotting)
       DRESS = "dresses.dress"
       # outerwear
       JACKET = "outerwear.jacket"; COAT = "outerwear.coat"; BLAZER = "outerwear.blazer"
       OUTERWEAR_UNKNOWN = "outerwear.unknown"
       # footwear
       SNEAKERS = "footwear.sneakers"; BOOTS = "footwear.boots"
       DRESS_SHOES = "footwear.dress_shoes"; SANDALS = "footwear.sandals"
       FOOTWEAR_UNKNOWN = "footwear.unknown"
       # accessories
       BAG = "accessories.bag"; BELT = "accessories.belt"; HAT = "accessories.hat"
       SCARF = "accessories.scarf"; JEWELRY = "accessories.jewelry"
       ACCESSORY_UNKNOWN = "accessories.unknown"
       # last resort
       UNKNOWN = "other.unknown"
   ```

   Plus `normalize_category(raw: str | None) -> Category`:
   1. Lowercase, strip, collapse whitespace, remove hyphens/underscores.
   2. **Synonym map** lookup — seed with at least: `tee shirt/tshirt/tee/short sleeve top → TSHIRT`; `dress shirt/button down/button up → SHIRT`; `pants/slacks → TROUSERS`; `denim → JEANS`; `jumper/pullover/knit → SWEATER`; `sweatshirt → HOODIE`; `trainers/running shoes → SNEAKERS`; `heels/loafers/oxfords → DRESS_SHOES`; `parka/puffer/overcoat → COAT`; `purse/handbag/backpack → BAG`; `cap/beanie → HAT`; `suit → BLAZER` (jacket half; suits aren't modeled as one item).
   3. **Keyword→slot fallback**: if a slot word appears ("shirt"→tops, "pant/trouser/jean/skirt/short"→bottoms, "shoe/boot/sneaker/sandal/heel"→footwear, "jacket/coat/blazer"→outerwear, "dress"→dresses) return that slot's `*_UNKNOWN`.
   4. Otherwise `Category.UNKNOWN` — and `logger.warning` the raw value so the synonym map can grow.
   Also export `slot_of(category: str) -> str` (prefix before the dot) and `display_name(category: str) -> str` (part after the dot, underscores→spaces, title-cased).

2. **Hook into `schema_mapper.py`**: in `map_gemini_to_wardrobe_schema()`, replace `"category": gemini_result.get("category")` with `"category": normalize_category(gemini_result.get("category")).value`. All three providers normalize uniformly through this one line.

3. **Tighten classifier prompts** (`groq_classifier.py`, `claude_classifier.py`, `openai_classifier.py` in `services/ai/`): instruct the model to answer with one of the canonical values, listed explicitly in the prompt. Accuracy win only — normalization stays mandatory.

4. **Pydantic validation** on wardrobe create/update request schemas (`apps/api/src/attreq_api/schemas/`): a `field_validator` that accepts only `Category` values (manual edits from mobile go through the same enum). Reject with 422 listing valid values.

5. **Alembic data migration**: new revision (chain after current head) running the synonym map over existing `wardrobe_items.category` rows. Implement as a Python online migration calling `normalize_category` per distinct value (row counts are tiny pre-launch); unmappable → `other.unknown`.

6. **Update `algorithm.py`**:
   - Slotting (~531–542): `tops = [i for i in items if i.category.startswith(("tops.",))]`, dresses count as a top with no bottom required, `bottoms` via `bottoms.`, `accessories` via `accessories.` (footwear/outerwear pools arrive in M3 — for now footwear/outerwear items are simply excluded from top/bottom pools instead of mis-slotted). Delete the half-split inference fallback (~546–550) — with enforced taxonomy it can only mis-slot.
   - `formality_map` (254–269): re-key on canonical values (`"outerwear.blazer": 3, "tops.shirt": 3, "bottoms.trousers": 3, "dresses.dress": 3, "bottoms.skirt": 2, "tops.blouse": 2, "bottoms.chinos": 2, "bottoms.jeans": 1, "tops.tshirt": 1, "bottoms.shorts": 1, "tops.hoodie": 1, "bottoms.sweatpants": 0`); replace the substring loop at 276–282 with a dict `.get(category, 1)`.

7. **Mobile updates** (`apps/mobile/src/`): wardrobe grid grouping and any category pickers/filters render via a mirrored constant (slot → display names); item edit forms submit canonical values. Mirror `display_name` logic client-side (string after the dot).

### 2.2 API contract documentation + enforcement (TKT-002)

1. **New** `docs/api-contract.md` documenting, with exact JSON shapes copied from real responses:
   - `POST /api/v1/auth/register`, `/login`, `/refresh` — token payload shape, expiry fields, error codes; **refresh semantics** the mobile Axios interceptor must implement (when to refresh, retry-once rule, logout on refresh failure).
   - `GET /api/v1/recommendations/daily` — full suggestion payload, and the **materialization mapping**: which suggestion fields the client sends to `POST /api/v1/outfits/` when the user accepts an outfit.
   - Wear tracking (`POST /wardrobe/items/{id}/wear`) and outfit feedback shapes.
   - Location: query params, precision, and the fallback chain (see 2.3) including the `weather_unavailable` flag.
   - Reserved fields note: `users.oauth_provider`/`oauth_id` exist but are unused.
2. **Enforce in tests**: extend `apps/api/tests/test_client_contracts.py` so every documented shape has an assertion (exact keys, types). Drift between code and doc must fail CI.

### 2.3 Geocoding + weather fallback chain

In the recommendations/weather path (`services/` weather client + `endpoints/recommendations.py`):

1. Request `lat`/`lon` provided → use them.
2. Else user's saved `latitude`/`longitude` → use them.
3. Else user's saved `city` → geocode via OpenWeather Geocoding API (`/geo/1.0/direct?q={city}&limit=1`), cache result in Redis (key `geocode:{city}`, long TTL), persist resolved lat/lon to the user row.
4. Else (or on geocoding failure) → return recommendations **without weather filtering** plus a top-level `"weather_unavailable": true` flag; mobile renders a non-weather banner instead of erroring. Document the flag in `docs/api-contract.md`.

### 2.4 Remove the OAuth ghost

- Delete `google_client_id`, `google_client_secret`, `google_redirect_uri` from `config/settings.py` and the `GOOGLE_*` lines from `apps/api/.env.example`. (M1 already removed them from prod compose.)
- Keep `users.oauth_provider`/`oauth_id` columns; documented as reserved in `docs/api-contract.md`.

## Out of scope

- Footwear/outerwear **outfit slots and scoring** (M3 — this milestone only makes those pools identifiable).
- Broad test expansion beyond contract tests (M4). Mobile Sentry/EAS (M5). Any `apps/web` changes.

## Exit criteria

- No non-canonical category can enter the DB (classifier path normalized; manual path validated; existing rows migrated).
- `docs/api-contract.md` exists and every documented shape is asserted in `test_client_contracts.py`.
- Recommendations succeed with GPS off (saved-location or `weather_unavailable` path).
- `GOOGLE_*` config gone from settings and `.env.example`.

## Verification

```bash
cd apps/api
PYTHONPATH=src ../../.venv/bin/pytest tests/ -k "taxonomy or contract"   # new unit tests for normalize_category synonym corpus + contract suite
PYTHONPATH=src ../../.venv/bin/alembic upgrade head                       # data migration applies cleanly (also enforced in CI)
ruff check src

cd ../../apps/mobile && npm run typecheck && npm test
```

Manual: wardrobe grid on device shows merged category groups (no duplicate "T-shirt"/"Tshirt" sections); create an item with an invalid category via the API → 422; recommendations with location services disabled → response carries `weather_unavailable` and the app renders it.
