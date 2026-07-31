"""Tests for services/recommendation/reranker.py (RI-6).

Every test mocks `classifier_factory.get_classifier()` — never a real LLM
call. The most important exit-criterion test in this file is
`test_reranker_disabled_never_calls_get_classifier`: "flag off = zero LLM
calls".
"""

from __future__ import annotations

import pytest

from attreq_api.config.settings import settings
from attreq_api.services.recommendation import reranker


def _candidate(top_id: str, bottom_id: str) -> dict:
    return {
        "top_item_id": top_id,
        "top_item": {"category": "shirt", "color_primary": "blue"},
        "bottom_item_id": bottom_id,
        "bottom_item": {"category": "jeans", "color_primary": "black"},
        "scores": {"total": 0.8},
    }


@pytest.fixture(autouse=True)
def _reset_reranker_flags(monkeypatch):
    monkeypatch.setattr(settings, "reranker_enabled", True)
    monkeypatch.setattr(settings, "reranker_both_order", False)


class _FakeClassifier:
    def __init__(self, responses):
        self._responses = list(responses)
        self.call_count = 0

    async def analyze_text(self, prompt):
        self.call_count += 1
        response = self._responses[min(self.call_count - 1, len(self._responses) - 1)]
        if isinstance(response, Exception):
            raise response
        return response


def _patch_classifier(monkeypatch, responses):
    fake = _FakeClassifier(responses)
    monkeypatch.setattr(
        "attreq_api.services.ai.classifier_factory.get_classifier", lambda: fake
    )
    return fake


@pytest.mark.asyncio
async def test_reranker_disabled_never_calls_get_classifier(monkeypatch):
    monkeypatch.setattr(settings, "reranker_enabled", False)

    called = {"count": 0}

    def fake_get_classifier():
        called["count"] += 1
        raise AssertionError("get_classifier must never be called when RERANKER_ENABLED=false")

    monkeypatch.setattr("attreq_api.services.ai.classifier_factory.get_classifier", fake_get_classifier)

    candidates = [_candidate("t1", "b1"), _candidate("t2", "b2")]
    reordered, rationales = await reranker.rerank(candidates, {"occasion": "casual"})

    assert reordered == candidates
    assert rationales is None
    assert called["count"] == 0


@pytest.mark.asyncio
async def test_rerank_empty_candidates_short_circuits(monkeypatch):
    def fake_get_classifier():
        raise AssertionError("must not be called for an empty candidate list")

    monkeypatch.setattr("attreq_api.services.ai.classifier_factory.get_classifier", fake_get_classifier)

    reordered, rationales = await reranker.rerank([], {"occasion": "casual"})
    assert reordered == []
    assert rationales is None


@pytest.mark.asyncio
async def test_rerank_valid_response_reorders_and_attaches_rationales(monkeypatch):
    c1, c2 = _candidate("t1", "b1"), _candidate("t2", "b2")
    key1, key2 = reranker._pair_key(c1), reranker._pair_key(c2)

    _patch_classifier(
        monkeypatch,
        [{"ranking": [key2, key1], "rationales": {key1: "Nice combo.", key2: "Great pick."}}],
    )

    reordered, rationales = await reranker.rerank([c1, c2], {"occasion": "casual"})

    assert reordered == [c2, c1]
    assert rationales == {key1: "Nice combo.", key2: "Great pick."}


@pytest.mark.asyncio
async def test_rerank_malformed_json_falls_back_after_one_retry(monkeypatch):
    c1, c2 = _candidate("t1", "b1"), _candidate("t2", "b2")
    fake = _patch_classifier(monkeypatch, [{"not": "the right shape"}, {"also": "wrong"}])

    reordered, rationales = await reranker.rerank([c1, c2], {"occasion": "casual"})

    assert reordered == [c1, c2]
    assert rationales is None
    assert fake.call_count == 2  # one call + one bare retry, then give up


@pytest.mark.asyncio
async def test_rerank_non_permutation_ranking_falls_back(monkeypatch):
    c1, c2 = _candidate("t1", "b1"), _candidate("t2", "b2")
    key1 = reranker._pair_key(c1)
    # Missing key2, and a duplicate of key1 — not a valid permutation.
    bad_response = {"ranking": [key1, key1], "rationales": {}}
    _patch_classifier(monkeypatch, [bad_response, bad_response])

    reordered, rationales = await reranker.rerank([c1, c2], {"occasion": "casual"})

    assert reordered == [c1, c2]
    assert rationales is None


@pytest.mark.asyncio
async def test_rerank_rationales_keys_not_subset_falls_back(monkeypatch):
    c1, c2 = _candidate("t1", "b1"), _candidate("t2", "b2")
    key1, key2 = reranker._pair_key(c1), reranker._pair_key(c2)
    bad_response = {"ranking": [key1, key2], "rationales": {"some:unknown:key": "nope"}}
    _patch_classifier(monkeypatch, [bad_response, bad_response])

    reordered, rationales = await reranker.rerank([c1, c2], {"occasion": "casual"})

    assert reordered == [c1, c2]
    assert rationales is None


@pytest.mark.asyncio
async def test_rerank_retry_succeeds_after_first_malformed_response(monkeypatch):
    c1, c2 = _candidate("t1", "b1"), _candidate("t2", "b2")
    key1, key2 = reranker._pair_key(c1), reranker._pair_key(c2)
    good_response = {"ranking": [key1, key2], "rationales": {key1: "ok"}}
    fake = _patch_classifier(monkeypatch, [{"garbage": True}, good_response])

    reordered, rationales = await reranker.rerank([c1, c2], {"occasion": "casual"})

    assert reordered == [c1, c2]
    assert rationales == {key1: "ok"}
    assert fake.call_count == 2


@pytest.mark.asyncio
async def test_rerank_exception_from_classifier_falls_back(monkeypatch):
    c1, c2 = _candidate("t1", "b1"), _candidate("t2", "b2")
    _patch_classifier(monkeypatch, [RuntimeError("LLM down"), RuntimeError("LLM down")])

    reordered, rationales = await reranker.rerank([c1, c2], {"occasion": "casual"})

    assert reordered == [c1, c2]
    assert rationales is None


@pytest.mark.asyncio
async def test_rerank_both_order_agreement_uses_call_one_ranking(monkeypatch):
    monkeypatch.setattr(settings, "reranker_both_order", True)
    c1, c2 = _candidate("t1", "b1"), _candidate("t2", "b2")
    key1, key2 = reranker._pair_key(c1), reranker._pair_key(c2)

    # Both calls agree #1 is key2.
    call1 = {"ranking": [key2, key1], "rationales": {key2: "best"}}
    call2 = {"ranking": [key2, key1], "rationales": {key2: "best (reversed order)"}}
    _patch_classifier(monkeypatch, [call1, call2])

    reordered, rationales = await reranker.rerank([c1, c2], {"occasion": "casual"})

    assert reordered == [c2, c1]
    assert rationales == {key2: "best"}


@pytest.mark.asyncio
async def test_rerank_both_order_disagreement_falls_back_to_heuristic_order(monkeypatch):
    monkeypatch.setattr(settings, "reranker_both_order", True)
    c1, c2 = _candidate("t1", "b1"), _candidate("t2", "b2")
    key1, key2 = reranker._pair_key(c1), reranker._pair_key(c2)

    call1 = {"ranking": [key2, key1], "rationales": {key1: "heuristic first item"}}
    call2 = {"ranking": [key1, key2], "rationales": {}}  # disagrees on #1
    _patch_classifier(monkeypatch, [call1, call2])

    reordered, rationales = await reranker.rerank([c1, c2], {"occasion": "casual"})

    # Tie -> heuristic order, but call-1's rationale for the heuristic-#1
    # item (c1 / key1) is still surfaced since it validated.
    assert reordered == [c1, c2]
    assert rationales == {key1: "heuristic first item"}


@pytest.mark.asyncio
async def test_rerank_both_order_second_call_failure_treated_as_tie(monkeypatch):
    monkeypatch.setattr(settings, "reranker_both_order", True)
    c1, c2 = _candidate("t1", "b1"), _candidate("t2", "b2")
    key1, key2 = reranker._pair_key(c1), reranker._pair_key(c2)

    call1 = {"ranking": [key2, key1], "rationales": {key1: "first item rationale"}}
    _patch_classifier(monkeypatch, [call1, RuntimeError("second call failed"), RuntimeError("retry also failed")])

    reordered, rationales = await reranker.rerank([c1, c2], {"occasion": "casual"})

    assert reordered == [c1, c2]
    assert rationales == {key1: "first item rationale"}


def test_pair_key_matches_algorithm_candidate_id_shape():
    candidate = _candidate("11111111-1111-1111-1111-111111111111", "22222222-2222-2222-2222-222222222222")
    assert (
        reranker._pair_key(candidate)
        == "11111111-1111-1111-1111-111111111111:22222222-2222-2222-2222-222222222222"
    )


def test_build_prompt_is_json_serializable():
    c1 = _candidate("t1", "b1")
    prompt = reranker._build_prompt([c1], {"occasion": "casual", "weather": {"temp": 20}})
    assert isinstance(prompt, str)
    assert reranker._pair_key(c1) in prompt
