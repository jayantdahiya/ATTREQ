"""Thin pytest wrapper around `scripts/eval_seven_day.py::run_seven_day_sim` —
one parametrized case per synthetic wardrobe size, so `pytest -k seven_day`
catches a regression the same run as the rest of the suite (the script
itself is the authoritative, human-readable gate; see the verification
block in the milestone plan)."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from eval_seven_day import run_seven_day_sim  # noqa: E402


@pytest.mark.asyncio
@pytest.mark.parametrize("size", ["small", "medium", "large"])
async def test_seven_day_gate_passes_for_wardrobe_size(size):
    report = await run_seven_day_sim(size)

    assert report.no_repeated_combo, f"repeated combo for size={size}: {report.all_combos}"
    assert report.empty_explanation_count == 0
    assert all(count > 0 for count in report.daily_counts)
    if report.has_footwear:
        assert report.footwear_missing_when_owned == 0
    if report.has_outerwear:
        assert report.outerwear_missing_on_cold_day == 0
    if report.has_grey_inventory:
        assert report.rediscovery_count >= 1
    if report.has_fullbody:
        assert report.fullbody_no_phantom_bottom_seen
    assert report.ok
