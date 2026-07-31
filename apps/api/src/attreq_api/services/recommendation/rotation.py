"""Anti-repetition + grey-inventory rotation (RI-4).

Pure functions/dataclasses over plain Python values (dates, UUIDs) — no DB
access. `RotationContext` is built once per generation batch (either from
real `RecommendationEvent` rows by the DB shell in `algorithm.py`, or from an
in-memory accumulator in `scripts/eval_seven_day.py`) and threaded through
`composition.generate_outfits`.

Two independent signals, matching the milestone doc's distinct windows:
- `item_decay_penalty` — soft, linear over a 7-day window on individual items
  shown recently (beyond the pre-existing 14-day *worn* hard exclusion in
  `algorithm.get_recently_worn_items`, which is unrelated and unchanged).
- Combo repetition — HARD-excluded during generation (see
  `composition.generate_outfits`) over a 14-day window; `combo_penalty` here
  is only the small residual soft nudge used in the feasibility-fallback case
  (small wardrobe, every combo already seen).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from uuid import UUID

    from attreq_api.models.wardrobe import WardrobeItem

# Item-level decay window (days). 0 penalty at/after this many days.
ITEM_DECAY_WINDOW_DAYS = 7
ITEM_DECAY_MAX_PENALTY = 0.15

# Combo hard-exclusion window (days) — distinct from the item decay window.
COMBO_WINDOW_DAYS = 14

# Residual soft penalty applied only when the hard-exclusion feasibility gate
# falls back to allowing a repeated combo (see composition.py).
COMBO_SOFT_PENALTY = 0.25

# Grey-inventory rediscovery bonus.
REDISCOVERY_MAX_BONUS = 0.05
REDISCOVERY_STALE_DAYS = 60
REDISCOVERY_RAMP_DAYS = 2 * REDISCOVERY_STALE_DAYS  # 120 — full bonus at/after this
REDISCOVERY_LABEL_FLOOR = 0.01  # below this, the bonus applies but is never *labeled*


@dataclass(frozen=True)
class RotationContext:
    """Anti-repetition state for one generation call.

    `recent_item_last_shown`: item id -> most recent date it was shown,
    restricted to the last `ITEM_DECAY_WINDOW_DAYS` (older entries are
    pointless to keep — they'd score 0 penalty anyway).
    `recent_combos`: exact top+bottom (or solo-fullbody) id-sets shown within
    `COMBO_WINDOW_DAYS` — hard-excluded during generation.
    `today`: the generation date (injectable for tests / the eval harness).
    """

    recent_item_last_shown: dict[UUID, date] = field(default_factory=dict)
    recent_combos: set[frozenset[UUID]] = field(default_factory=set)
    today: date = field(default_factory=date.today)


def build_rotation_context(
    shown_events: list[dict], today: date | None = None
) -> RotationContext:
    """Build a `RotationContext` from a list of shown-event-shaped dicts.

    Each event dict is expected to carry (at minimum) a `date` (a `date`
    object) and an `item_ids` (iterable of UUIDs forming that outfit's core
    combo — top+bottom, or the single fullbody id). This shape is
    intentionally decoupled from the ORM `RecommendationEvent` model so the
    pure core (and `scripts/eval_seven_day.py`) never need a real row.
    """
    today = today or date.today()
    last_shown: dict[UUID, date] = {}
    combos: set[frozenset[UUID]] = set()

    item_cutoff = today.toordinal() - ITEM_DECAY_WINDOW_DAYS
    combo_cutoff = today.toordinal() - COMBO_WINDOW_DAYS

    for event in shown_events:
        event_date: date = event["date"]
        item_ids: frozenset[UUID] = frozenset(event["item_ids"])
        if not item_ids:
            continue

        if event_date.toordinal() >= combo_cutoff:
            combos.add(item_ids)

        if event_date.toordinal() >= item_cutoff:
            for item_id in item_ids:
                existing = last_shown.get(item_id)
                if existing is None or event_date > existing:
                    last_shown[item_id] = event_date

    return RotationContext(recent_item_last_shown=last_shown, recent_combos=combos, today=today)


def item_decay_penalty(item_id: UUID, ctx: RotationContext) -> float:
    """Soft, linear decay: 0 at >= `ITEM_DECAY_WINDOW_DAYS` days since last
    shown, `-ITEM_DECAY_MAX_PENALTY` if shown today (0 days ago)."""
    last_shown = ctx.recent_item_last_shown.get(item_id)
    if last_shown is None:
        return 0.0

    days_since = (ctx.today - last_shown).days
    if days_since >= ITEM_DECAY_WINDOW_DAYS:
        return 0.0
    days_since = max(days_since, 0)
    fraction = 1.0 - (days_since / ITEM_DECAY_WINDOW_DAYS)
    return round(-ITEM_DECAY_MAX_PENALTY * fraction, 4)


def combo_in_recent(combo: frozenset[UUID], ctx: RotationContext) -> bool:
    """Whether this exact combo was already shown within the combo window."""
    return combo in ctx.recent_combos


def combo_penalty(combo: frozenset[UUID], ctx: RotationContext) -> float:
    """Residual soft penalty — only meaningful in the feasibility-fallback
    path (see `composition.generate_outfits`); the primary mechanism is the
    hard exclusion, not this."""
    return -COMBO_SOFT_PENALTY if combo_in_recent(combo, ctx) else 0.0


def rediscovery_bonus_for_stale_item(item: WardrobeItem, today: date) -> float:
    """Grey-inventory bonus for an OWNED item with a stale `last_worn`.

    Ramps 0 -> `REDISCOVERY_MAX_BONUS` linearly between `REDISCOVERY_STALE_DAYS`
    and `REDISCOVERY_RAMP_DAYS` days since last worn. Callers must not invoke
    this for `wear_count == 0` items with no `last_worn` — see
    `composition.classify_grey_inventory_bonus`, which routes those
    separately (full bonus, no ramp — there's no "last worn" to ramp from).
    """
    if not item.last_worn:
        return 0.0
    days_since = (today - item.last_worn).days
    if days_since < REDISCOVERY_STALE_DAYS:
        return 0.0
    span = REDISCOVERY_RAMP_DAYS - REDISCOVERY_STALE_DAYS
    fraction = min(1.0, (days_since - REDISCOVERY_STALE_DAYS) / span)
    return round(REDISCOVERY_MAX_BONUS * fraction, 4)
