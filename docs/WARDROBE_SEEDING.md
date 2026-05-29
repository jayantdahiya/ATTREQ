# Onboarding & Wardrobe Seeding — Design Decisions
**ATTREQ · Feature Specification & Implementation Guide**

***

## 1. The Core Problem

The current onboarding flow drops a new user onto an empty dashboard after registration. The app's entry point (`app/index.tsx`) has exactly two states: authenticated → dashboard, unauthenticated → login. There is no onboarding route, no first-run detection, and no guidance whatsoever.

A new user who signs up experiences:
1. Empty dashboard (recommendations return nothing — `generate_daily_outfits()` requires ≥ 2 wardrobe items with `processing_status = "completed"`)
2. No explanation of why it's empty
3. No instruction on what to do next
4. Location permission prompt with no context (silently breaks weather-based recommendations if denied)

The app's value is entirely locked behind wardrobe setup. There is no path from "just installed" to "first recommendation" that a user can find on their own.

### The Chicken-and-Egg Problem
For recommendations to work, ATTREQ needs a critical mass of wardrobe items — realistically 10–15 items across categories. The current flow requires the user to photograph each item individually, one at a time, with AI processing between each. That means **10–15 separate photo sessions** before any value is seen. Most users will not complete this. Most will uninstall.

***

## 2. What We Ruled Out

We evaluated every possible method to reduce wardrobe-building friction. Three were definitively ruled out:

### ❌ E-commerce Sync (Myntra, Amazon, Flipkart, Ajio)
Myntra's API (`mmip.myntrainfo.com`) is a **seller/vendor-only API** for brands managing product listings — no consumer-facing order history access exists for third-party apps. Amazon's SP-API is similarly restricted to selling partners only; the Orders API retrieves orders placed *with* a merchant, not a consumer's personal purchase history. No public API exists for any major Indian fashion retailer that would allow importing a user's order history. Scraping is a ToS violation and breaks without warning.

**Decision: permanently ruled out.**

### ❌ Email Order Parsing
Parsing order confirmation emails via Gmail OAuth would require accessing the user's full inbox, parsing dozens of different retailer email formats with an LLM, and handling failed extractions silently. Beyond the engineering complexity, it is a significant **privacy violation** — users do not expect a wardrobe app to read their email. The trust cost far outweighs the benefit.

**Decision: permanently ruled out.**

### ❌ Bulk Flat-Lay Photo Mode
Having the user lay all clothes on a bed and photograph them together in one wide shot. The CV problem of detecting, segmenting, and individually classifying multiple overlapping garments in a single image is significantly harder than single-item detection. More importantly, the cropped thumbnails per item would be low resolution and low quality — degrading the entire wardrobe experience downstream. ATTREQ's current Gemini classifier is optimised for single-item photos.

**Decision: permanently ruled out.**

***

## 3. The Key Insight: Style DNA Photos Are Also Wardrobe Data

This was the central breakthrough of the design session.

We were designing two separate onboarding steps:
1. Upload 3–5 photos → extract Style DNA
2. Photograph clothes → build wardrobe

**But the Style DNA photos already contain clothing items.** The user is wearing full outfits in them. The same Gemini Vision call that extracts style signals can simultaneously extract and classify every visible wardrobe item from the same photo — same image, two jobs done in one pass.

**Result:** A user who uploads 5 Style DNA photos walks away with:
- ✅ A complete Style DNA profile (aesthetic, colour palette, patterns, silhouette, formality bias)
- ✅ A wardrobe pre-populated with real items they actually wear
- ✅ Enough data for first-day recommendations

**Zero extra effort. No separate wardrobe-building session needed to get started.**

***

## 4. Revised Onboarding Flow

### Step 1 — Photo Upload (3–8 photos)
User is prompted: *"Show us 5 outfits you've loved wearing — any photos, mirror shots, selfies, anything."*

Same upload screen as Style DNA seeding (see `style_dna_design.md`). Minimum 3 usable photos required. Quality check runs per photo before extraction.

### Step 2 — Single Dual-Purpose Gemini Vision Pass
Each photo goes through one extended Gemini Vision call that returns **both** style signals and detected wardrobe items simultaneously:

```json
{
  "style_signals": {
    "colors": { "primary": ["white", "navy"], "secondary": ["brown"] },
    "patterns": ["solid"],
    "silhouette": "relaxed-fitted",
    "formality_level": 2,
    "aesthetic_vibes": ["smart-casual", "minimalist"],
    "occasion": ["casual", "work"],
    "notable_signals": ["clean-lines", "minimal-accessories"]
  },
  "wardrobe_items_detected": [
    {
      "category": "top",
      "subcategory": "shirt",
      "color_primary": "white",
      "color_secondary": null,
      "pattern": "solid",
      "occasion": ["casual", "smart-casual"],
      "season": ["all"],
      "confidence": 0.91,
      "bounding_region": "upper body"
    },
    {
      "category": "bottom",
      "subcategory": "jeans",
      "color_primary": "navy",
      "color_secondary": null,
      "pattern": "solid",
      "occasion": ["casual"],
      "season": ["all"],
      "confidence": 0.88,
      "bounding_region": "lower body"
    },
    {
      "category": "footwear",
      "subcategory": "sneakers",
      "color_primary": "white",
      "pattern": "solid",
      "occasion": ["casual"],
      "season": ["all"],
      "confidence": 0.76,
      "bounding_region": "feet"
    }
  ]
}
```

5 photos × ~2–3 items each = **10–15 wardrobe items extracted with zero additional user effort.**

### Step 3 — Results Screen (Two Cards)

```
┌─────────────────────────────────────────┐
│  ✦ Your Style DNA                       │
│                                         │
│  Aesthetic    Minimalist · Smart Casual │
│  Palette      Navy  White  Olive  ●●●   │
│  Pattern      Solid, clean lines        │
│  Formality    Casual → Smart Casual     │
│                                         │
│  [ Edit ]          [ Looks right → ]   │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│  👕 We found 11 items in your photos    │
│                                         │
│  [img] [img] [img] [img] [img]          │
│  White shirt · Navy jeans · +6 more     │
│                                         │
│  [ Review items ]   [ Add all → ]      │
└─────────────────────────────────────────┘
```

**"Add all"** — accepts all detected items as-is, adds them to the wardrobe in bulk. User can edit later.
**"Review items"** — opens a quick inline edit flow where the user can correct AI-detected attributes per item (see Section 6).

### Step 4 — First Recommendations Available
User is taken to the dashboard. Recommendations are generated immediately from the seeded wardrobe + Style DNA profile. A soft persistent prompt appears:

> *"You have 3 tops and 2 bottoms. Add more items for better combinations →"*

This is contextual, specific, and non-blocking. The app is already working.

***

## 5. The "Add More Items" Layer (Post-Seeding)

Once the seed wardrobe is built from DNA photos, the add-more flow is psychologically very different — the user is *expanding* something, not *starting* something from scratch.

### Primary Method — Outfit Photo (Selfie / Mirror Shot)
The user photographs themselves wearing an outfit. Gemini detects and segments all visible items (top, bottom, footwear, accessories) from the single photo and adds them as separate wardrobe items. This is the **outfit-first** model — the mental model is natural because people think in outfits, not individual items.

One photo = potentially 3–4 wardrobe items added simultaneously.

### Fallback / Default — Camera Roll Scanning
On the first app open after onboarding completes, ATTREQ requests gallery permission with a clear explanation:

> *"We can scan your gallery for outfit photos to build your wardrobe faster. We never store or share your photos — they're only used to identify clothing items."*

The scan runs in the background and looks for photos that resemble outfit shots (full-body or half-body, single person, clothing visible). Results surface as:

> *"We found 8 outfit photos in your gallery — want to add them to your wardrobe?"*

User sees thumbnails, can deselect any, then confirms. Tapped photos go through the same outfit-first Gemini extraction as above.

**Camera roll scanning is the fallback, not the primary.** It catches the gap between "items they wore in the seed photos" and "everything else in their wardrobe." Most fashion-conscious users already have outfit photos sitting in their camera roll.

### Share Sheet Import (Power User Feature)
The user takes a screenshot of any item from any shopping app — Myntra product page, Zara website, H&M app, anything — and shares it to ATTREQ via the iOS/Android share sheet. ATTREQ's LLM reads the screenshot, extracts item name, colour, category, and pulls the product image. Works with **any retailer with no API required.** Also supports adding wishlist items — items the user wants to buy can be flagged as `owned: false` and excluded from recommendations but tracked separately.

***

## 6. Item Review & Quick Correction UI

This screen solves two problems at once:
1. The immediate need to let users review AI-detected items from seed photos
2. The longstanding missing **wardrobe item editing screen** (the backend has `PUT /api/v1/wardrobe/items/{id}` but no mobile UI existed for it)

### Design Principle
Not a form. Not a modal stack. A **swipe-through card review** — one item per card, key AI-detected attributes shown as tappable chips, user swipes to correct or confirm.

```
┌─────────────────────────────────────────┐
│  Item 3 of 11          [ Skip all → ]  │
│                                         │
│       ┌──────────────────┐              │
│       │                  │              │
│       │   [item photo]   │              │
│       │                  │              │
│       └──────────────────┘              │
│                                         │
│  Category   [Shirt ▾]                   │
│  Colour     [● White]  [● Navy ▾]       │
│  Pattern    [Solid ✓]  [Striped] [Floral]│
│  Occasion   [Casual ✓] [Formal] [Work]  │
│                                         │
│  [ ✓ Looks right ]   [ × Remove ]      │
└─────────────────────────────────────────┘
```

- Tapping a chip toggles it — no forms, no keyboards unless the user taps "Other"
- "Looks right" → confirm and advance to next item
- "Remove" → discard this item from the import
- "Skip all" → accept all remaining as-is

This same screen is also accessible from the Wardrobe tab as the general item-editing flow for any wardrobe item at any time.

***

## 7. DB Changes Required

### `wardrobe_items` — New Field
```sql
ALTER TABLE wardrobe_items
ADD COLUMN classification_source VARCHAR(20);
-- Existing values: "ai" | "fallback"
-- New values: "style_dna_seed" | "camera_roll" | "share_sheet" | "outfit_photo"
```

This lets the system know the provenance of each item — useful for confidence scoring and for future analytics on which onboarding method produces the highest quality wardrobe data.

### `style_dna_photos` — Already Defined
See `style_dna_design.md` for full schema. The `per_photo_extraction` JSONB column now stores both `style_signals` and `wardrobe_items_detected` from the dual-purpose extraction call.

### `users` — New Field
```sql
ALTER TABLE users
ADD COLUMN onboarding_completed BOOLEAN NOT NULL DEFAULT false,
ADD COLUMN onboarding_step VARCHAR(50) DEFAULT 'pending';
-- Steps: pending | style_dna_upload | review | complete
```

Used by `app/index.tsx` to route new users into the onboarding flow instead of directly to the dashboard.

***

## 8. Mobile Routes Required

```
apps/mobile/app/
├── (onboarding)/                        ← NEW route group
│   ├── _layout.tsx
│   ├── upload-style.tsx                 ← Step 1: photo upload (3–8 photos)
│   ├── results.tsx                      ← Step 2: Style DNA card + found items card
│   └── review-items.tsx                 ← Step 3: swipe-through item review
│
└── index.tsx                            ← MODIFIED
    Currently: accessToken ? dashboard : login
    New:       accessToken + onboarding_completed ? dashboard
             : accessToken + !onboarding_completed ? onboarding
             : login
```

***

## 9. Backend Changes Required

### Modified: `style_dna_service.py`
The per-photo extraction prompt is extended to return `wardrobe_items_detected` alongside `style_signals`. After synthesis, detected wardrobe items are bulk-inserted into `wardrobe_items` with `classification_source = "style_dna_seed"`.

### New: `POST /api/v1/users/onboarding/complete`
Sets `onboarding_completed = true` and `onboarding_step = "complete"` on the user record. Called after the review screen is confirmed.

### New: `POST /api/v1/wardrobe/items/bulk`
Accepts an array of wardrobe items to insert in one transaction. Used by the "Add all" button on the results screen.

### Modified: `PUT /api/v1/wardrobe/items/{id}`
Already exists in the backend. No changes needed — the new mobile review screen just finally exposes this endpoint in the UI.

***

## 10. What We Decided

| Decision | Choice | Rationale |
|----------|--------|-----------|
| E-commerce sync | ❌ Ruled out | No public consumer APIs exist for Myntra/Amazon/Flipkart |
| Email parsing | ❌ Ruled out | Privacy violation, engineering complexity |
| Bulk flat-lay photo | ❌ Ruled out | Degrades thumbnail quality, harder CV problem |
| Style DNA photos as wardrobe seed | ✅ Yes | Same photos, two jobs — zero extra user effort |
| Primary add-more method | Outfit photo (selfie) | Natural mental model, one photo = multiple items |
| Fallback add-more method | Camera roll scan | Catches existing outfit photos with no new effort |
| Share sheet import | ✅ Yes (power user) | Works with any retailer, no API needed |
| Item review UI | Swipe-through chips | Low friction, no forms or keyboards |
| Wardrobe item editing | Solved by review screen | Same screen reused for ongoing edits |

***

## 11. What We Left for Later

These were discussed and agreed to be valid but deferred to a future implementation phase:

### Progressive Wardrobe (Deferred)
The idea of showing limited but useful recommendations from just 3 items and using contextual nudges to grow the wardrobe gradually (*"Add 2 more bottoms to unlock weather recommendations"*). This is a good idea and complements the seeding flow — it just requires additional recommendation-engine logic to gracefully handle very sparse wardrobes. Deferred to Phase 2.

### Wishlist / Want-to-Buy Layer
The share sheet import naturally enables adding items the user wants to buy (not yet owned). These could be tracked as `owned: false` in the wardrobe and excluded from recommendations but used for Style DNA signal. The full wishlist feature — browsing, purchase tracking, price alerts — is a separate product scope. Deferred.

### Gamified Wardrobe Completeness
A progress indicator in the Wardrobe tab showing wardrobe coverage by category — *"You're missing footwear and outerwear — add them for complete outfit suggestions."* Pairs well with progressive wardrobe. Deferred to Phase 2.

### Camera Roll Rescan
A manual trigger in Settings to re-run the camera roll scan after the initial onboarding. Useful for users who have taken new outfit photos since onboarding. Deferred.

### Style DNA Re-upload Flow
Allowing the user to re-upload new seed photos to trigger a fresh Style DNA synthesis (e.g. after a style change). The backend supports this (weekly recalibration in `style_dna_design.md`) but the mobile UI for manually triggering re-upload is deferred to Phase 2.

***

## 12. How the Three Problems Connect

This design session resolved three separate product gaps through one coherent feature:

| Original Problem | How It's Resolved |
|-----------------|-------------------|
| No Style DNA / preference learning | Style DNA seeded from onboarding photos + continuous refinement |
| No wardrobe item editing UI | Built as the item review screen in onboarding, reused throughout the app |
| No onboarding flow | Full 3-step onboarding: upload → results → review → first recommendations |

And the key insight that connected them: **the Style DNA upload photos are also wardrobe data.** One upload session serves all three purposes simultaneously.