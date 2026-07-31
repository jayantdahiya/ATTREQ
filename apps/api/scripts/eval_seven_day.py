#!/usr/bin/env python
"""RI-4 seven-day eval gate — drives the PURE `compose_daily_outfits` core.

No DB, no session, no sqlite: simulates 7 consecutive daily generations for a
synthetic wardrobe by accumulating a plain in-memory list of shown-event-
shaped dicts (the same shape `algorithm._load_recent_shown_events` builds from
real `RecommendationEvent` rows) and advancing `today` once per iteration.
This is the point of the pure-core refactor in
`services/recommendation/composition.py` — the gate is deterministic and
runnable single-shot, with no Postgres dependency.

Usage:
    PYTHONPATH=src python scripts/eval_seven_day.py
"""

from __future__ import annotations

import asyncio
import sys
import uuid
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from attreq_api.models.wardrobe import WardrobeItem  # noqa: E402
from attreq_api.services.recommendation.algorithm import (  # noqa: E402
    filter_items_by_occasion,
    filter_items_by_weather,
)
from attreq_api.services.recommendation.composition import compose_daily_outfits  # noqa: E402

# Named-color vocab the legacy Lab bridge understands (services/ai/color_extraction.py).
_COLORS = [
    "black", "white", "blue", "red", "green", "brown", "beige", "gray",
    "navy", "maroon", "pink", "purple", "yellow", "orange", "tan", "cream",
]

_TOP_CATEGORIES = ["shirt", "t-shirt", "blouse", "sweater", "hoodie"]
_BOTTOM_CATEGORIES = ["jeans", "chinos", "skirt", "shorts", "dress pants"]
_FOOTWEAR_CATEGORIES = ["sneaker", "boot", "dress shoe", "sandal"]
_OUTERWEAR_CATEGORIES = ["jacket", "coat", "blazer"]
_FULLBODY_CATEGORIES = ["dress", "jumpsuit"]

# (tops, bottoms, footwear, outerwear, fullbody) — sums to the wardrobe size.
SIZE_CONFIG: dict[str, dict[str, int]] = {
    "small": {"tops": 5, "bottoms": 5, "footwear": 2, "outerwear": 2, "fullbody": 1},
    "medium": {"tops": 20, "bottoms": 20, "footwear": 8, "outerwear": 8, "fullbody": 4},
    "large": {"tops": 70, "bottoms": 70, "footwear": 25, "outerwear": 25, "fullbody": 10},
}

# 7-day mocked weather sequence, including a cold/rainy day (day index 2).
WEATHER_SEQUENCE: list[dict[str, Any]] = [
    {"temp": 22.0, "feels_like": 22.0, "condition": "Clear", "description": "clear", "humidity": 50, "wind_speed": 2.0, "icon": "01d"},
    {"temp": 26.0, "feels_like": 27.0, "condition": "Sunny", "description": "sunny", "humidity": 45, "wind_speed": 1.5, "icon": "01d"},
    {"temp": 12.0, "feels_like": 10.0, "condition": "Rain", "description": "light rain", "humidity": 80, "wind_speed": 4.0, "icon": "10d"},
    {"temp": 18.0, "feels_like": 18.0, "condition": "Cloudy", "description": "overcast", "humidity": 60, "wind_speed": 3.0, "icon": "03d"},
    {"temp": 9.0, "feels_like": 6.0, "condition": "Clear", "description": "cold and clear", "humidity": 55, "wind_speed": 5.0, "icon": "01d"},
    {"temp": 29.0, "feels_like": 31.0, "condition": "Clear", "description": "hot", "humidity": 40, "wind_speed": 1.0, "icon": "01d"},
    {"temp": 16.0, "feels_like": 15.0, "condition": "Clear", "description": "mild", "humidity": 50, "wind_speed": 2.0, "icon": "01d"},
]

OCCASION = "casual"
SIM_START_DATE = date(2026, 3, 1)


def _build_item(
    *,
    item_id: uuid.UUID,
    category: str,
    color: str,
    is_fullbody: bool,
    wear_count: int,
    last_worn: date | None,
    created_at: datetime,
    user_id: uuid.UUID,
) -> WardrobeItem:
    return WardrobeItem(
        id=item_id,
        user_id=user_id,
        original_image_url="/uploads/originals/synthetic.jpg",
        processed_image_url=None,
        thumbnail_url=None,
        category=category,
        color_primary=color,
        color_secondary=None,
        pattern="solid",
        season=["all"],
        occasion=["all"],
        detection_confidence=0.9,
        classification_source="fallback",
        processing_status="completed",
        status="active",
        wear_count=wear_count,
        last_worn=last_worn,
        purchase_price=None,
        brand=None,
        texture=None,
        silhouette=None,
        neckline=None,
        sleeve_length=None,
        statement_level=None,
        llm_formality=None,
        is_fullbody=is_fullbody,
        color_palette=None,
        color_extraction_source=None,
        attribute_confidence=None,
        schema_version=1,
        created_at=created_at,
        updated_at=created_at,
    )


def generate_synthetic_wardrobe(size: str, seed: int = 42) -> list[WardrobeItem]:
    """Seeded synthetic wardrobe: `size` in {"small", "medium", "large"}.

    ~25% of items are "grey inventory" (`wear_count=0`, never worn, created
    long ago — so cold-start's `is_recently_added` gate never fires for them,
    keeping cold-start and rediscovery mutually exclusive and deterministic
    for this eval: every `wear_count==0` item here takes the rediscovery
    path). The rest have a moderate wear_count and a recent `last_worn`.
    """
    import random

    # A local `random.Random(seed)` alone does NOT make this fully
    # deterministic across process runs if item ids come from `uuid.uuid4()`
    # — that's always cryptographically random regardless of any seed, and
    # `select_anchors`'s tie-break sorts by `str(item.id)`, so non-seeded ids
    # would make anchor selection (and everything downstream) vary run to
    # run. Every id here is derived from the SAME seeded `rng` instead.
    rng = random.Random(seed)
    config = SIZE_CONFIG[size]
    user_id = uuid.UUID(int=rng.getrandbits(128))
    old_created = datetime(2025, 1, 1)
    recent_worn = SIM_START_DATE - timedelta(days=5)

    items: list[WardrobeItem] = []

    def _make(categories: list[str], count: int, is_fullbody: bool) -> None:
        for i in range(count):
            category = categories[i % len(categories)]
            color = rng.choice(_COLORS)
            item_id = uuid.UUID(int=rng.getrandbits(128))
            grey = rng.random() < 0.25
            if grey:
                items.append(
                    _build_item(
                        item_id=item_id,
                        category=category,
                        color=color,
                        is_fullbody=is_fullbody,
                        wear_count=0,
                        last_worn=None,
                        created_at=old_created,
                        user_id=user_id,
                    )
                )
            else:
                items.append(
                    _build_item(
                        item_id=item_id,
                        category=category,
                        color=color,
                        is_fullbody=is_fullbody,
                        wear_count=rng.randint(1, 20),
                        last_worn=recent_worn,
                        created_at=old_created,
                        user_id=user_id,
                    )
                )

    _make(_TOP_CATEGORIES, config["tops"], is_fullbody=False)
    _make(_BOTTOM_CATEGORIES, config["bottoms"], is_fullbody=False)
    _make(_FOOTWEAR_CATEGORIES, config["footwear"], is_fullbody=False)
    _make(_OUTERWEAR_CATEGORIES, config["outerwear"], is_fullbody=False)
    _make(_FULLBODY_CATEGORIES, config["fullbody"], is_fullbody=True)

    return items


@dataclass
class SevenDayReport:
    size: str
    total_wardrobe_items: int
    has_footwear: bool
    has_outerwear: bool
    has_fullbody: bool
    has_grey_inventory: bool
    all_combos: list[frozenset] = field(default_factory=list)
    empty_explanation_count: int = 0
    footwear_missing_when_owned: int = 0
    outerwear_missing_on_cold_day: int = 0
    rediscovery_count: int = 0
    fullbody_no_phantom_bottom_seen: bool = False
    daily_counts: list[int] = field(default_factory=list)

    @property
    def no_repeated_combo(self) -> bool:
        return len(self.all_combos) == len(set(self.all_combos))

    @property
    def ok(self) -> bool:
        checks = [
            self.no_repeated_combo,
            self.empty_explanation_count == 0,
            not (self.has_footwear and self.footwear_missing_when_owned > 0),
            not (self.has_outerwear and self.outerwear_missing_on_cold_day > 0),
            not (self.has_grey_inventory) or self.rediscovery_count >= 1,
            not self.has_fullbody or self.fullbody_no_phantom_bottom_seen,
            all(c > 0 for c in self.daily_counts),
        ]
        return all(checks)


async def run_seven_day_sim(size: str, seed: int = 42, k: int = 3) -> SevenDayReport:
    items = generate_synthetic_wardrobe(size, seed=seed)
    report = SevenDayReport(
        size=size,
        total_wardrobe_items=len(items),
        has_footwear=any((i.category or "") in _FOOTWEAR_CATEGORIES for i in items),
        has_outerwear=any((i.category or "") in _OUTERWEAR_CATEGORIES for i in items),
        has_fullbody=any(i.is_fullbody for i in items),
        has_grey_inventory=any((i.wear_count or 0) == 0 for i in items),
    )

    shown_events: list[dict[str, Any]] = []

    for day_offset, weather in enumerate(WEATHER_SEQUENCE):
        today = SIM_START_DATE + timedelta(days=day_offset)

        weather_filtered = await filter_items_by_weather(items, weather)
        occasion_filtered = await filter_items_by_occasion(weather_filtered, OCCASION)
        if len(occasion_filtered) < 2:
            occasion_filtered = weather_filtered

        candidates = compose_daily_outfits(
            occasion_filtered,
            weather,
            OCCASION,
            worn_item_ids=set(),
            shown_events=shown_events,
            style_dna=None,
            k=k,
            today=today,
        )

        report.daily_counts.append(len(candidates))

        temp = weather.get("temp", 20.0)
        condition = (weather.get("condition") or "").lower()
        is_cold_or_rainy = temp < 15.0 or condition in {"rain", "snow"}

        for candidate in candidates:
            report.all_combos.append(candidate.combo_key)
            if not candidate.explanation:
                report.empty_explanation_count += 1
            if report.has_footwear and candidate.footwear_item is None:
                report.footwear_missing_when_owned += 1
            if report.has_outerwear and is_cold_or_rainy and candidate.outerwear_item is None:
                report.outerwear_missing_on_cold_day += 1
            if candidate.rediscovery:
                report.rediscovery_count += 1
            if candidate.fullbody_item is not None and candidate.bottom_item is None and candidate.top_item is None:
                report.fullbody_no_phantom_bottom_seen = True

            shown_events.append({"date": today, "item_ids": list(candidate.combo_key)})

    return report


def _print_report(report: SevenDayReport) -> None:
    status = "PASS" if report.ok else "FAIL"
    print(f"[{status}] size={report.size} wardrobe_items={report.total_wardrobe_items}")
    print(f"  daily outfit counts: {report.daily_counts}")
    print(f"  total combos shown: {len(report.all_combos)}  unique: {len(set(report.all_combos))}  no_repeated_combo={report.no_repeated_combo}")
    print(f"  empty explanations: {report.empty_explanation_count}")
    print(f"  footwear missing when owned: {report.footwear_missing_when_owned} (owned={report.has_footwear})")
    print(f"  outerwear missing on cold/rain day: {report.outerwear_missing_on_cold_day} (owned={report.has_outerwear})")
    print(f"  rediscovery outfits this week: {report.rediscovery_count} (grey_inventory_present={report.has_grey_inventory})")
    print(f"  fullbody-anchored outfit seen (no phantom bottom): {report.fullbody_no_phantom_bottom_seen} (owned={report.has_fullbody})")


async def main_async() -> bool:
    all_ok = True
    for size in ("small", "medium", "large"):
        report = await run_seven_day_sim(size)
        _print_report(report)
        all_ok = all_ok and report.ok
    return all_ok


def main() -> None:
    ok = asyncio.run(main_async())
    if not ok:
        print("\nRI-4 seven-day eval gate: FAILED")
        sys.exit(1)
    print("\nRI-4 seven-day eval gate: PASSED for all wardrobe sizes")


if __name__ == "__main__":
    main()
