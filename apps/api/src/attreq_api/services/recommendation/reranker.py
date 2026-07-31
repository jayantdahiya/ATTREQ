"""LLM re-ranker (RI-6) — feature-flagged, strict-JSON, soft-fail-only.

Reorders an already-scored candidate pool for DISPLAY ORDER + a one-sentence
rationale per outfit; it never re-derives or overrides the heuristic scores
(`services/recommendation/composition.py` remains the sole source of
`total`). Disabled by default (`RERANKER_ENABLED=false`) — when disabled,
`rerank()` returns immediately without importing or calling
`classifier_factory.get_classifier()` at all, matching the milestone's own
exit criterion: "flag off = zero LLM calls" (see `tests/test_reranker.py`).

Call budget:
- Default (`RERANKER_BOTH_ORDER=false`): exactly ONE `get_classifier()` call
  — all candidates sent in heuristic order, asking for a ranked list of
  pair-keys + one-sentence rationale each, strict JSON.
- Optional (`RERANKER_BOTH_ORDER=true`): a SECOND call with the candidates in
  reversed order (position-bias check). Agreement on #1 uses call-1's
  ranking + rationales; disagreement is a TIE -> heuristic order, though
  call-1's rationale for the heuristic-#1 item is still surfaced if it
  validated.

This is 2 calls/rec at most, never O(pairs) — literal pairwise-per-pair
scoring is rejected as violating the milestone's own "not per-pair" rule.

Item-ID grounding is honestly limited to "`rationales` keys subset of the
candidate pair-keys" — full free-text NER against the wardrobe (verifying no
sentence mentions an unowned item) is out of scope for this milestone.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from attreq_api.config.settings import settings

logger = logging.getLogger(__name__)

RerankResult = tuple[list[dict[str, Any]], dict[str, str] | None]


def _pair_key(candidate: dict[str, Any]) -> str:
    """`f"{top_item_id}:{bottom_item_id}"`, both `str(uuid)` (or the literal
    string "None" for a fullbody-anchored candidate) — matches how
    `algorithm.py::_candidate_to_payload` emits ids."""
    return f"{candidate.get('top_item_id')}:{candidate.get('bottom_item_id')}"


def _build_prompt(candidates: list[dict[str, Any]], context: dict[str, Any]) -> str:
    items_desc = []
    for candidate in candidates:
        top = candidate.get("top_item") or {}
        bottom = candidate.get("bottom_item") or {}
        items_desc.append(
            {
                "pair_key": _pair_key(candidate),
                "top": {"category": top.get("category"), "color": top.get("color_primary")},
                "bottom": {
                    "category": bottom.get("category"),
                    "color": bottom.get("color_primary"),
                },
                "scores": candidate.get("scores", {}),
            }
        )

    return (
        "You are ranking already-scored outfit suggestions for a wardrobe app. "
        "Improve the DISPLAY ORDER and give a one-sentence rationale for each, "
        "using only the categories/colors/scores given — never invent an item "
        "that isn't listed.\n\n"
        f"Context: {json.dumps(context, default=str)}\n\n"
        f"Candidates: {json.dumps(items_desc, default=str)}\n\n"
        "Respond with ONLY this strict JSON shape, nothing else:\n"
        '{"ranking": ["<pair_key>", ...], "rationales": {"<pair_key>": "<one sentence>"}}\n'
        "`ranking` MUST be a permutation of exactly the pair_key values given "
        "above (same count, no duplicates, no new keys). `rationales` keys "
        "MUST be a subset of those same pair_key values."
    )


def _validate(
    parsed: Any, expected_keys: set[str]
) -> tuple[list[str], dict[str, str]] | None:
    """Strict-JSON contract check: (a) `parsed` is a dict, (b) `ranking` is
    exactly a permutation of `expected_keys`, (c) `rationales` keys are a
    subset of `expected_keys`. Returns `None` on any violation."""
    if not isinstance(parsed, dict):
        return None

    ranking = parsed.get("ranking")
    rationales = parsed.get("rationales")

    if not isinstance(ranking, list) or len(ranking) != len(expected_keys):
        return None
    if set(ranking) != expected_keys:
        return None
    if not isinstance(rationales, dict) or not set(rationales.keys()) <= expected_keys:
        return None

    return ranking, {str(k): str(v) for k, v in rationales.items()}


async def _call_once(prompt: str) -> dict[str, Any] | None:
    """One `get_classifier().analyze_text()` call. Returns `None` (never
    raises) on any exception or non-dict response."""
    try:
        from attreq_api.services.ai.classifier_factory import get_classifier

        classifier = get_classifier()
        result = await classifier.analyze_text(prompt)
        return result if isinstance(result, dict) else None
    except Exception as e:
        logger.warning(f"Reranker LLM call failed: {e}")
        return None


async def rerank(candidates: list[dict[str, Any]], context: dict[str, Any]) -> RerankResult:
    """Return `(reordered candidates, {pair_key: rationale})`, or
    `(candidates, None)` on disabled/empty/any failure/malformed response.
    Never raises, never mutates the input list's dicts, never re-derives
    scores — display order + rationale text only.
    """
    if not settings.reranker_enabled or not candidates:
        return candidates, None

    expected_keys = {_pair_key(c) for c in candidates}
    by_key = {_pair_key(c): c for c in candidates}
    prompt = _build_prompt(candidates, context)

    parsed = await _call_once(prompt)
    validated = _validate(parsed, expected_keys) if parsed is not None else None
    if validated is None:
        # One bare retry (identical prompt) on parse/schema failure.
        parsed = await _call_once(prompt)
        validated = _validate(parsed, expected_keys) if parsed is not None else None
    if validated is None:
        return candidates, None

    ranking, rationales = validated

    if settings.reranker_both_order:
        reversed_candidates = list(reversed(candidates))
        reversed_prompt = _build_prompt(reversed_candidates, context)
        parsed2 = await _call_once(reversed_prompt)
        validated2 = _validate(parsed2, expected_keys) if parsed2 is not None else None

        heuristic_first_key = _pair_key(candidates[0])
        surfaced_rationale = (
            {heuristic_first_key: rationales[heuristic_first_key]}
            if heuristic_first_key in rationales
            else None
        )

        if validated2 is None:
            # Second call failed/malformed — can't confirm agreement, treat
            # as a tie: fall back to heuristic order, still surface call-1's
            # rationale for the heuristic-#1 item if it validated.
            return candidates, surfaced_rationale

        ranking2, _rationales2 = validated2
        if ranking[0] != ranking2[0]:
            # Disagreement on #1 -> tie -> heuristic order.
            return candidates, surfaced_rationale
        # Agreement on #1 — use call-1's ranking + rationales.

    reordered = [by_key[key] for key in ranking]
    return reordered, rationales
