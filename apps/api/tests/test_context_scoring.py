"""Tests for services/recommendation/context_scoring.py (RI-3)."""

from __future__ import annotations

import uuid
from datetime import datetime

import pytest

from attreq_api.services.recommendation.context_scoring import (
    OCCASION_WEIGHT,
    TIME_WEIGHT,
    WEATHER_WEIGHT,
    calculate_context_score,
    calculate_occasion_fit,
    calculate_time_score,
    calculate_weather_score,
)
from tests.conftest import build_wardrobe_item


def _item(**overrides):
    return build_wardrobe_item(user_id=uuid.uuid4(), **overrides)


def test_weights_are_0_55_0_35_0_10():
    assert OCCASION_WEIGHT == 0.55
    assert WEATHER_WEIGHT == 0.35
    assert TIME_WEIGHT == 0.10
    assert pytest.approx(1.0) == OCCASION_WEIGHT + WEATHER_WEIGHT + TIME_WEIGHT


def test_calculate_context_score_arithmetic_is_exact():
    top = _item(category="t-shirt", occasion=["casual"], season=["summer"])
    bottom = _item(category="jeans", occasion=["casual"], season=["summer"])
    weather = {"temp": 30.0, "condition": "Clear"}
    now = datetime(2026, 7, 22, 14, 0, 0)  # daytime

    total, detail = calculate_context_score([top, bottom], "casual", weather, now=now)

    expected_occasion = calculate_occasion_fit([top, bottom], "casual")
    expected_weather = calculate_weather_score([top, bottom], weather)
    expected_time = calculate_time_score("casual", now)

    assert detail == {
        "occasion_fit": expected_occasion,
        "weather_score": expected_weather,
        "time_score": expected_time,
    }
    expected_total = round(
        OCCASION_WEIGHT * expected_occasion
        + WEATHER_WEIGHT * expected_weather
        + TIME_WEIGHT * expected_time,
        4,
    )
    assert total == expected_total


def test_occasion_fit_is_neutral_0_5_when_no_item_has_occasion_tags():
    top = _item(category="t-shirt", occasion=None)
    bottom = _item(category="jeans", occasion=None)

    assert calculate_occasion_fit([top, bottom], "casual") == 0.5


def test_occasion_fit_is_neutral_0_5_for_empty_item_list():
    assert calculate_occasion_fit([], "casual") == 0.5


def test_occasion_fit_rewards_exact_occasion_match():
    top = _item(category="dress shirt", occasion=["formal"])
    bottom = _item(category="dress pants", occasion=["formal"])

    matched = calculate_occasion_fit([top, bottom], "formal")

    mismatched_bottom = _item(category="sweatpants", occasion=["athletic"])
    mismatched = calculate_occasion_fit([top, mismatched_bottom], "formal")

    assert matched > mismatched


def test_occasion_fit_gives_partial_credit_for_all_occasion_tag():
    item_all = _item(category="t-shirt", occasion=["all"])
    item_exact = _item(category="jeans", occasion=["casual"])

    fit = calculate_occasion_fit([item_all, item_exact], "casual")
    assert 0.5 < fit <= 1.0


def test_weather_score_full_credit_for_hot_temp_summer_tag():
    item = _item(season=["summer"])
    score = calculate_weather_score([item], {"temp": 30.0, "condition": "Clear"})
    assert score == 1.0


def test_weather_score_full_credit_for_cold_temp_winter_tag():
    item = _item(season=["winter"])
    score = calculate_weather_score([item], {"temp": 5.0, "condition": "Clear"})
    assert score == 1.0


def test_weather_score_partial_credit_for_all_season_tag():
    item = _item(season=["all"])
    score = calculate_weather_score([item], {"temp": 30.0, "condition": "Clear"})
    assert score == 0.7


def test_weather_score_mismatch_scores_lower_than_match():
    hot_item = _item(season=["summer"])
    cold_item = _item(season=["winter"])
    weather = {"temp": 30.0, "condition": "Clear"}

    match_score = calculate_weather_score([hot_item], weather)
    mismatch_score = calculate_weather_score([cold_item], weather)

    assert match_score > mismatch_score


def test_weather_score_neutral_0_5_for_empty_items():
    assert calculate_weather_score([], {"temp": 20.0}) == 0.5


def test_time_score_evening_occasion_favors_evening():
    evening = datetime(2026, 7, 22, 20, 0, 0)
    daytime = datetime(2026, 7, 22, 12, 0, 0)

    assert calculate_time_score("party", evening) > calculate_time_score("party", daytime)


def test_time_score_business_occasion_favors_daytime():
    evening = datetime(2026, 7, 22, 20, 0, 0)
    daytime = datetime(2026, 7, 22, 12, 0, 0)

    assert calculate_time_score("business", daytime) > calculate_time_score("business", evening)


def test_time_score_casual_is_weak_flat_signal():
    evening = datetime(2026, 7, 22, 20, 0, 0)
    daytime = datetime(2026, 7, 22, 12, 0, 0)

    assert calculate_time_score("casual", evening) == calculate_time_score("casual", daytime)
