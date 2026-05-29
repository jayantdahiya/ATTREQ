# Style DNA — Full System Design
**ATTREQ · Feature Specification & Implementation Guide**

***

## 1. Problem Statement

The current recommendation algorithm in `algorithm.py` has a fundamentally weak personalisation layer. `get_user_preference_weights()` only reads outfits where `feedback_score = 1`, counts how often each `color_primary` appeared, and awards a maximum **+0.2 bonus** weighted at 20% of the total score. Patterns, silhouette, categories, and dislike signals are computed but silently discarded. The `style_preferences` column on the `users` table exists explicitly for this feature but is never written to or read from.

The result: a Day 1 user and a Day 90 user who never tapped 👍 receive **identical recommendations**. The system's core promise — "the more you use it, the smarter it gets" — is currently false.

***

## 2. The Solution: Photo-Based Style DNA

### Core Insight
A style quiz creates friction and elicits aspirational answers ("I prefer minimalist") that don't match actual behaviour. Photos are ground truth — an outfit someone wore and loved is proof of preference, not a claim about it.

### The Approach
Ask the user to upload **3–8 photos of outfits they've loved wearing** — any photos, any quality, selfies, mirror shots, anything. Pass those photos through a vision-capable LLM to extract a structured Style DNA profile. Store it in `users.style_preferences`. Use it as the dominant weight in recommendation scoring. Refine it continuously from usage signals.

### Why LLM over a Custom CV Model
The LLM understands fashion semantics natively. It already knows that navy chinos + white OCBD + white sneakers = preppy smart-casual, and that an oversized graphic tee + cargo pants = streetwear, without being trained on fashion-specific data. A custom CV pipeline would require separate models for colour, pattern, silhouette, and aesthetic classification — expensive to train, brittle in production, and impossible to generalise across all aesthetic vocabularies.

ATTREQ already uses Gemini Vision for clothing classification in `gemini_classifier.py`. Style DNA reuses this exact infrastructure.

***

## 3. Minimum Photo Requirement: Why 3, Default 5

The LLM is looking for **repeating patterns across multiple outfits**, not describing a single outfit. A signal must appear more than once to be called a preference.

| Photos | Reliability |
|--------|-------------|
| 1 | Describes one outfit. Zero pattern detection. Useless for DNA. |
| 2 | Can spot 1 signal if both share it. Too fragile. |
| **3** | **Bare minimum.** 2/3 agreement = probable preference. 3/3 = confident preference. One outlier can't corrupt the profile. |
| **5** | **Sweet spot.** Majority (3/5) vs minority (2/5) is meaningful. Nuance starts to emerge — e.g. context-aware formality (casual weekends, smart-casual weekdays). |
| 6–7 | Marginally better, diminishing returns. |
| 8+ | No meaningful improvement. User drop-off risk. |

**Rule: minimum 3, default ask for 5, hard cap at 8.**

If fewer than 3 photos are usable (all flagged as low quality), prompt the user to retry. If ≥ 3 are usable, proceed and note reduced confidence in the profile.

***

## 4. Photo Quality Handling

Real users upload blurry mirror selfies, half-cropped photos, and group shots. The system must handle this gracefully without failing silently.

### Quality Check (per photo, before extraction)
Each uploaded photo gets a quick Gemini Vision quality pass before the full extraction call:

```
Can you analyse this photo for style extraction suitability?
Return JSON:
{
  "usable": true | false,
  "reason": "clear outfit visible" | "too blurry" | "outfit partially visible" | "no outfit detected" | "group photo - individual unclear",
  "confidence": 0.0–1.0
}
```

### Decision Logic
```
Count usable photos after quality check:
  ≥ 3 usable  → proceed with extraction on usable photos only
  1–2 usable  → proceed but flag low-confidence profile to user
  0 usable    → block extraction, prompt: 
                "These photos aren't clear enough for us to read your style. 
                 Try photos with good lighting where the full outfit is visible."
```

Photos flagged as low-quality are stored with a `quality_flag: false` marker but never deleted — the user may want to replace them later.

***

## 5. Storage: Separate from Wardrobe Items

Style DNA seed photos are **not wardrobe items**. They may include:
- Outfits with borrowed or rented clothes the user doesn't own
- Screenshots of celebrity or editorial looks they love
- Old photos of items they no longer have

Storing them as wardrobe items would corrupt the wardrobe, pollute search results, and create confusing phantom items in recommendations.

### New DB Table: `style_dna_photos`

```sql
CREATE TABLE style_dna_photos (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    s3_key      VARCHAR(500) NOT NULL,
    s3_url      VARCHAR(500) NOT NULL,
    quality_ok  BOOLEAN NOT NULL DEFAULT true,
    quality_reason VARCHAR(100),
    per_photo_extraction JSONB,         -- raw LLM output for this photo
    created_at  TIMESTAMP WITH TIME ZONE DEFAULT now(),
    updated_at  TIMESTAMP WITH TIME ZONE DEFAULT now()
);

CREATE INDEX idx_style_dna_photos_user_id ON style_dna_photos(user_id);
```

### S3 Path Convention
```
style-dna/{user_id}/{photo_id}.jpg
```
Separate from wardrobe item uploads at `wardrobe/{user_id}/{item_id}/`.

### `users.style_preferences` — New JSON Schema

The existing `style_preferences TEXT` column receives a structured JSON string:

```json
{
  "version": 2,
  "generated_at": "2026-05-02T22:39:00Z",
  "seed_photo_count": 5,
  "confidence": 0.82,

  "aesthetic": {
    "primary": ["minimalist", "smart-casual"],
    "secondary": ["preppy"],
    "confidence": 0.88
  },

  "color_palette": {
    "dominant": ["navy", "white", "olive"],
    "accent": ["burgundy"],
    "avoids": [],
    "confidence": 0.91
  },

  "patterns": {
    "preferred": ["solid", "subtle-stripe"],
    "avoids": ["floral", "graphic-print"],
    "confidence": 0.79
  },

  "silhouette": {
    "value": "relaxed-fitted",
    "confidence": 0.74
  },

  "formality": {
    "bias": 2.1,
    "context_aware": {
      "casual": 1.5,
      "work": 2.8
    },
    "confidence": 0.80
  },

  "layering": {
    "tendency": "moderate",
    "confidence": 0.65
  },

  "accessory_preference": {
    "level": "minimal",
    "confidence": 0.71
  },

  "behaviour_weights": {
    "colors": {"navy": 1.4, "white": 1.2, "olive": 1.1, "yellow": 0.6},
    "patterns": {"solid": 1.3, "floral": 0.4},
    "categories": {"jeans": 1.2, "t-shirt": 1.1},
    "last_updated": "2026-05-02T22:39:00Z"
  },

  "user_corrections": [],
  "last_llm_synthesis": "2026-05-02T22:39:00Z"
}
```

The `behaviour_weights` sub-object is updated in real-time by numeric signals (Phase 2). The rest is updated only by LLM synthesis (Phase 1 and Phase 3).

***

## 6. System Architecture: Three Phases

### Phase 1 — Seeding (One-time, Onboarding)

```
User uploads 3–8 photos
        │
        ▼
[Quality Check] — parallel Gemini Vision calls per photo
        │
        ├─ < 3 usable ──→ Prompt retry
        │
        └─ ≥ 3 usable ──→
                │
                ▼
        [Per-Photo Extraction] — parallel Gemini Vision calls
        Each photo → structured JSON:
          { colors, patterns, silhouette, formality,
            aesthetic_vibe, occasion, notable_signals }
                │
                ▼
        [Synthesis Call] — single Gemini call
        Input: all per-photo extractions
        Output: unified Style DNA JSON
                │
                ▼
        Write to users.style_preferences
        Store photos in style_dna_photos table
                │
                ▼
        Return Style DNA Card to mobile app
        User views + optionally edits
```

**API Endpoint:**
```
POST /api/v1/users/style-dna/upload
Content-Type: multipart/form-data
Body: photos[] (3–8 files)

Response:
{
  "status": "success",
  "photos_processed": 5,
  "photos_skipped": 0,
  "style_dna": { ... }
}
```

**New service:** `apps/api/src/attreq_api/services/style_dna/style_dna_service.py`

This service mirrors the pattern of `gemini_classifier.py` — it already handles vision calls, structured JSON extraction, and error handling. Style DNA extraction reuses the same Gemini client.

***

### Phase 2 — Real-Time Numeric Fine-Tuning

No LLM involved. Triggered on every user action that signals preference. Fast, cheap, immediate.

**Signal weights (applied to `behaviour_weights` in style_preferences):**

| Action | Signal Strength | Rationale |
|--------|----------------|-----------|
| `feedback_score = 1` (👍 liked) | +0.15 | Explicit positive |
| `feedback_score = -1` (👎 disliked) | −0.20 | Explicit negative; stronger than like |
| Outfit marked as worn (`worn_date` set) | +0.10 | Acted on it — stronger than a like |
| Recommendation skipped (no action) | −0.05 | Mild negative; not engaged |

**Time decay:** Weights are multiplied by a recency factor before being applied:
```
decay = e^(-λ * days_since_action)   where λ = 0.01 (half-life ≈ 70 days)
```
An action from 6 months ago (~180 days) carries ~16% of the weight of a fresh action. This prevents old preferences from dominating as a user's style evolves.

**Implementation:** A lightweight `update_behaviour_weights(user_id, outfit_id, signal)` function in `style_dna_service.py`, called from the existing feedback endpoint in `algorithm.py`.

***

### Phase 3 — Weekly LLM Deep Recalibration

Catches style drift that numeric updates move slowly. Runs as a background worker (Celery beat task, matching the existing task pattern in the codebase).

**Inputs to the synthesis call:**
- Original seed photos (permanent S3 URLs from `style_dna_photos`)
- Top 10 most-liked outfits from `outfits` table
- Top 5 most-worn `wardrobe_items` by `wear_count`
- Current `style_preferences` JSON (as context, not as constraint)

**Output:** Refreshed Style DNA JSON written back to `users.style_preferences` with `last_llm_synthesis` timestamp updated.

**Trigger condition:** Only runs for users who have had ≥ 5 new feedback actions since `last_llm_synthesis`. No point recalibrating a dormant user.

***

## 7. How Style DNA Changes the Scoring Formula

### Current formula (algorithm.py line ~290):
```python
total_score = (color_score * 0.4) + (formality_score * 0.4) + (preference_bonus * 0.2)
```
where `preference_bonus` maxes out at 0.2 from color frequency alone.

### New formula with Style DNA:
```python
total_score = (
    color_score          * 0.20 +   # base color harmony (reduced)
    formality_score      * 0.20 +   # base formality match (reduced)
    style_dna_score      * 0.40 +   # Style DNA alignment (dominant)
    behaviour_score      * 0.20     # real-time behaviour weights
)
```

**`style_dna_score` computation:**
```python
def calculate_style_dna_score(outfit_items, style_dna):
    score = 0.0

    # Aesthetic alignment
    outfit_aesthetic = infer_aesthetic(outfit_items)
    if outfit_aesthetic in style_dna["aesthetic"]["primary"]:
        score += 0.35
    elif outfit_aesthetic in style_dna["aesthetic"]["secondary"]:
        score += 0.15

    # Pattern check — penalise avoided patterns
    for item in outfit_items:
        if item.pattern in style_dna["patterns"]["avoids"]:
            score -= 0.25      # active penalty, not just missing bonus
        elif item.pattern in style_dna["patterns"]["preferred"]:
            score += 0.10

    # Silhouette alignment
    outfit_silhouette = infer_silhouette(outfit_items)
    if outfit_silhouette == style_dna["silhouette"]["value"]:
        score += 0.20

    # Colour palette alignment
    for item in outfit_items:
        if item.color_primary in style_dna["color_palette"]["dominant"]:
            score += 0.10
        elif item.color_primary in style_dna["color_palette"]["avoids"]:
            score -= 0.15

    return max(0.0, min(1.0, score))
```

The key change: **disliked signals now actively penalise scores**, not just fail to add a bonus. A floral item shown to a user who avoids florals gets a -0.25 hit. The previous system would give it +0.0. Those are very different outcomes over hundreds of recommendations.

***

## 8. The Style DNA Card (Mobile UI)

After the initial synthesis completes, the user sees a Style DNA Card in the app. This is the transparency moment that makes the AI feel trustworthy.

### Display Format
```
┌──────────────────────────────────────────┐
│  ✦ Your Style DNA                        │
│                                          │
│  Aesthetic      Minimalist · Smart Casual│
│  Palette        Navy  White  Olive       │
│                 ●     ●      ●            │
│  Pattern        Solid, clean lines       │
│  Silhouette     Relaxed but fitted       │
│  Formality      Casual → Smart Casual    │
│  Accessories    Minimal                  │
│                                          │
│  [ Edit ]        [ Looks right → ]       │
└──────────────────────────────────────────┘
```

### Edit Behaviour
Any field is tappable. Corrections are stored in `user_corrections` array in the JSON with a `source: "manual"` flag. Manual corrections carry a **2× weight multiplier** in scoring — a user who explicitly says "I don't wear florals" should never see florals again, regardless of what the LLM inferred.

### Access After Onboarding
The Style DNA Card is accessible from the Profile tab at any time. The user can:
- Re-upload seed photos (triggers a full re-synthesis)
- Edit individual fields
- See the `confidence` score per field — fields with confidence < 0.6 are displayed with a "Based on limited data" note

***

## 9. Files to Create / Modify

### New Files
```
apps/api/src/attreq_api/
├── models/
│   └── style_dna.py                    # StyleDnaPhoto SQLAlchemy model
├── services/
│   └── style_dna/
│       ├── __init__.py
│       ├── style_dna_service.py        # Main service: quality check, extraction, synthesis
│       ├── scoring.py                  # calculate_style_dna_score()
│       └── prompts.py                  # LLM prompt templates (extraction + synthesis)
├── api/v1/
│   └── style_dna.py                    # POST /users/style-dna/upload
│                                       # GET  /users/style-dna
│                                       # PATCH /users/style-dna (edit corrections)
└── tasks/
    └── style_dna_recalibration.py      # Weekly Celery beat task

apps/mobile/app/(protected)/
└── style-dna.tsx                       # Style DNA Card screen

apps/mobile/app/(onboarding)/           # New route group
└── upload-style.tsx                    # Photo upload screen
```

### Modified Files
```
apps/api/src/attreq_api/
├── models/user.py                      # No schema change needed; style_preferences already exists
├── services/recommendation/algorithm.py
│   ├── get_user_preference_weights()   # Now reads style_preferences JSON
│   ├── generate_daily_outfits()        # New scoring formula with style_dna_score
│   └── + update_behaviour_weights()    # New function called on feedback
└── alembic/versions/
    └── XXXX_add_style_dna_photos.py    # Migration for new table

apps/mobile/app/
└── index.tsx                           # Check style_dna_setup_complete on auth
                                        # Redirect new users to /(onboarding)/upload-style
```

***

## 10. LLM Prompt Templates

### Per-Photo Extraction Prompt
```
You are a fashion analyst. Analyse the outfit in this photo and extract style signals.

If the outfit is not clearly visible (blurry, partially cropped, group photo where the
individual is unclear), set "usable": false and explain in "reason".

Return ONLY valid JSON in this exact structure:
{
  "usable": true,
  "reason": "clear outfit visible",
  "colors": {
    "primary": ["navy", "white"],
    "secondary": ["brown"]
  },
  "patterns": ["solid", "subtle-texture"],
  "silhouette": "relaxed-fitted",
  "formality_level": 2,
  "aesthetic_vibes": ["smart-casual", "minimalist"],
  "occasion": ["casual", "work"],
  "notable_signals": ["layered", "minimal-accessories", "clean-lines"]
}

Formality scale: 1=athletic/loungewear, 2=casual, 3=smart-casual, 4=business, 5=formal
```

### Synthesis Prompt
```
You are a personal stylist building a Style DNA profile for a user.

Below are structured analyses of {n} outfits this user has worn and loved.
Identify consistent patterns and preferences across all outfits.

Outfits data:
{per_photo_extractions_json}

Return a unified Style DNA profile as JSON:
{
  "aesthetic": {
    "primary": ["..."],        // max 2 — most consistent aesthetics
    "secondary": ["..."],      // max 2 — present but not dominant
    "confidence": 0.0–1.0
  },
  "color_palette": {
    "dominant": ["..."],       // colours appearing in ≥ 40% of outfits
    "accent": ["..."],         // used occasionally but notably
    "avoids": ["..."],         // if a colour family is conspicuously absent
    "confidence": 0.0–1.0
  },
  "patterns": {
    "preferred": ["..."],
    "avoids": ["..."],         // only if clearly absent across all outfits
    "confidence": 0.0–1.0
  },
  "silhouette": {
    "value": "...",            // fitted | relaxed-fitted | relaxed | oversized | tailored
    "confidence": 0.0–1.0
  },
  "formality": {
    "bias": 0.0–5.0,          // average across outfits
    "context_aware": {},       // if formality clearly varies by occasion context
    "confidence": 0.0–1.0
  },
  "layering": {
    "tendency": "none | light | moderate | heavy",
    "confidence": 0.0–1.0
  },
  "accessory_preference": {
    "level": "none | minimal | moderate | heavy",
    "confidence": 0.0–1.0
  },
  "overall_confidence": 0.0–1.0
}

Rules:
- Only set "avoids" if genuinely absent — do not guess
- If fewer than 3 photos were analysed, set overall_confidence < 0.6
- Be specific, not generic. "minimalist" is better than "stylish"
```

***

## 11. Edge Cases & Decisions

| Scenario | Decision |
|----------|----------|
| User skips the upload entirely | Allowed. Recommendations fall back to current algorithm. Show a persistent soft prompt: "Personalise your recommendations →" |
| User uploads 3 photos, all low quality | Block + retry prompt. Do not generate a profile from bad data. |
| User uploads exactly 3 usable photos | Generate profile with `overall_confidence` note. Prompt: "Add 2 more photos for a more accurate profile." |
| User manually corrects a field | Store in `user_corrections[]` with `source: "manual"`. Apply 2× weight in scoring. Never overwrite manual corrections in weekly recalibration without user action. |
| User changes style significantly | Re-upload flow available in Profile tab. Full re-synthesis triggered. Old profile backed up in `user_corrections` history. |
| LLM returns malformed JSON | Retry once. If still malformed, store raw response and flag profile as `status: "pending_review"`. Do not write corrupt data to `style_preferences`. |
| User has no outfit feedback history yet | Phase 2 behaviour weights are all neutral (1.0). Style DNA from seed photos drives all personalization until enough feedback accumulates. |
| Weekly recalibration for new user (< 5 actions) | Skip. No meaningful behaviour data to incorporate. |

***

## 12. Success Metrics

Once shipped, the following metrics confirm the feature is working:

| Metric | Baseline (current) | Target |
|--------|-------------------|--------|
| Recommendation like rate (`feedback_score = 1`) | Measure at launch | +25% at 30 days |
| Recommendation skip rate (no action) | Measure at launch | −20% at 30 days |
| Outfit worn rate (`worn_date` set after recommendation) | Measure at launch | +30% at 60 days |
| Style DNA setup completion rate | N/A | ≥ 60% of new users |
| Profile confidence score (avg) | N/A | ≥ 0.75 |
| LLM extraction error rate | N/A | < 5% |

***

## 13. Open Questions (Resolved)

| Question | Decision |
|----------|----------|
| Quiz vs photos for cold-start? | **Photos.** Less friction, ground truth data, not aspirational self-report. |
| Minimum photo count? | **3 minimum, 5 default, 8 cap.** 3 enables 2/3 majority rule. 5 adds nuance. 8+ has no meaningful improvement. |
| Store with wardrobe items or separately? | **Separately** in `style_dna_photos` table. They are style references, not owned clothing items. |
| Real-time updates or batch? | **Both.** Numeric updates on every feedback action (fast, cheap). LLM re-synthesis weekly (deep, accurate). |
| Show user their Style DNA? | **Yes.** Transparent, builds trust, allows corrections that become the highest-weight signals in scoring. |
| Messy/low-quality photos? | Quality check per photo. Proceed if ≥ 3 usable. Prompt retry if all fail. |