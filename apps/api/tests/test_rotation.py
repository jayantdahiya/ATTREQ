"""Tests for services/recommendation/rotation.py + the cold-start/rediscovery
dispatch in services/recommendation/composition.py (RI-4)."""

from __future__ import annotations

import uuid
from datetime import date, timedelta

from attreq_api.services.recommendation import composition as comp, rotation
from tests.conftest import build_wardrobe_item

USER_ID = uuid.uuid4()
TODAY = date(2026, 4, 20)


def _item(**overrides):
    return build_wardrobe_item(user_id=USER_ID, **overrides)


# ---------------------------------------------------------------------------
# item_decay_penalty — linear across the 7-day window
# ---------------------------------------------------------------------------


def test_item_decay_penalty_zero_at_or_beyond_window():
    item_id = uuid.uuid4()
    ctx = rotation.RotationContext(
        recent_item_last_shown={item_id: TODAY - timedelta(days=7)}, today=TODAY
    )
    assert rotation.item_decay_penalty(item_id, ctx) == 0.0


def test_item_decay_penalty_max_when_shown_today():
    item_id = uuid.uuid4()
    ctx = rotation.RotationContext(recent_item_last_shown={item_id: TODAY}, today=TODAY)
    assert rotation.item_decay_penalty(item_id, ctx) == -rotation.ITEM_DECAY_MAX_PENALTY


def test_item_decay_penalty_linear_midpoint():
    item_id = uuid.uuid4()
    # 4 days ago -> partway through the 7-day window -> strictly between the
    # two extremes (date-level granularity means an exact half-day midpoint
    # isn't representable, so this checks the linear-ramp property instead).
    ctx = rotation.RotationContext(
        recent_item_last_shown={item_id: TODAY - timedelta(days=4)}, today=TODAY
    )
    penalty = rotation.item_decay_penalty(item_id, ctx)
    assert -rotation.ITEM_DECAY_MAX_PENALTY < penalty < 0.0


def test_item_decay_penalty_zero_when_never_shown():
    ctx = rotation.RotationContext(today=TODAY)
    assert rotation.item_decay_penalty(uuid.uuid4(), ctx) == 0.0


def test_item_decay_penalty_monotonically_shrinks_as_days_pass():
    item_id = uuid.uuid4()
    penalties = []
    for days_ago in range(0, 8):
        ctx = rotation.RotationContext(
            recent_item_last_shown={item_id: TODAY - timedelta(days=days_ago)}, today=TODAY
        )
        penalties.append(rotation.item_decay_penalty(item_id, ctx))
    # Strictly non-decreasing (less negative) as days_ago increases.
    assert all(penalties[i] <= penalties[i + 1] for i in range(len(penalties) - 1))
    assert penalties[-1] == 0.0


# ---------------------------------------------------------------------------
# rediscovery_bonus_for_stale_item — cap + staleness ramp
# ---------------------------------------------------------------------------


def test_rediscovery_bonus_zero_below_stale_threshold():
    item = _item(wear_count=3, last_worn=TODAY - timedelta(days=rotation.REDISCOVERY_STALE_DAYS - 1))
    assert rotation.rediscovery_bonus_for_stale_item(item, TODAY) == 0.0


def test_rediscovery_bonus_capped_at_max_beyond_ramp():
    item = _item(wear_count=3, last_worn=TODAY - timedelta(days=rotation.REDISCOVERY_RAMP_DAYS + 30))
    assert rotation.rediscovery_bonus_for_stale_item(item, TODAY) == rotation.REDISCOVERY_MAX_BONUS


def test_rediscovery_bonus_ramps_between_thresholds():
    midpoint_days = (rotation.REDISCOVERY_STALE_DAYS + rotation.REDISCOVERY_RAMP_DAYS) // 2
    item = _item(wear_count=3, last_worn=TODAY - timedelta(days=midpoint_days))
    bonus = rotation.rediscovery_bonus_for_stale_item(item, TODAY)
    assert 0.0 < bonus < rotation.REDISCOVERY_MAX_BONUS


def test_rediscovery_bonus_zero_when_never_worn_and_no_last_worn_date():
    """`rediscovery_bonus_for_stale_item` handles only the STALE-but-owned
    case; a true `wear_count == 0` item with no `last_worn` is routed
    elsewhere (full bonus) by `composition.classify_item_bonus`, not this
    function — see the mutual-exclusivity test below."""
    item = _item(wear_count=3, last_worn=None)
    assert rotation.rediscovery_bonus_for_stale_item(item, TODAY) == 0.0


# ---------------------------------------------------------------------------
# Cold-start / rediscovery mutual exclusivity (section 5.4)
# ---------------------------------------------------------------------------


def test_cold_start_and_rediscovery_are_mutually_exclusive_for_never_worn_item():
    """A genuinely new item (wear_count==0, no prior events, recently added)
    takes the cold-start path; an otherwise-identical item that DOES have
    prior events takes rediscovery instead. Never both for the same item."""
    warm_items = [_item(category="shirt", color_primary="blue", wear_count=10) for _ in range(3)]

    genuinely_new = _item(
        category="shirt", color_primary="blue", wear_count=0, last_worn=None,
        created_at=TODAY - timedelta(days=2),
    )
    kind_new, bonus_new = comp.classify_item_bonus(
        genuinely_new, warm_items=warm_items, items_with_prior_events=set(), today=TODAY
    )
    assert kind_new == "cold_start"
    assert bonus_new > 0.0

    owned_but_neglected = _item(
        category="shirt", color_primary="blue", wear_count=0, last_worn=None,
        created_at=TODAY - timedelta(days=2),
    )
    kind_owned, bonus_owned = comp.classify_item_bonus(
        owned_but_neglected,
        warm_items=warm_items,
        items_with_prior_events={owned_but_neglected.id},  # has prior events -> not "new"
        today=TODAY,
    )
    assert kind_owned == "rediscovery"
    assert bonus_owned == rotation.REDISCOVERY_MAX_BONUS


def test_cold_start_and_rediscovery_mutually_exclusive_for_old_never_worn_item():
    """A `wear_count == 0` item created long ago (not "recently added") is
    owned-but-neglected, not genuinely new — rediscovery, never cold-start,
    even with zero prior events."""
    old_grey_item = _item(
        category="shirt", color_primary="blue", wear_count=0, last_worn=None,
        created_at=date(2020, 1, 1),
    )
    kind, bonus = comp.classify_item_bonus(
        old_grey_item, warm_items=[], items_with_prior_events=set(), today=TODAY
    )
    assert kind == "rediscovery"
    assert bonus == rotation.REDISCOVERY_MAX_BONUS


def test_classify_item_bonus_none_for_a_well_worn_recently_worn_item():
    item = _item(wear_count=5, last_worn=TODAY - timedelta(days=3))
    kind, bonus = comp.classify_item_bonus(
        item, warm_items=[], items_with_prior_events=set(), today=TODAY
    )
    assert kind == "none"
    assert bonus == 0.0
