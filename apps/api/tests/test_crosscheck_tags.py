"""Tests for scripts/crosscheck_tags.py's pure compare function (RI-6).

`check_disagreement` takes precomputed similarity scores (fabricated here,
never a real FashionCLIP model) — a genuine unit test of the compare logic,
fully decoupled from the model/Weaviate/DB parts of the script (which are
never exercised in CI or this sandbox; see the script's own docstring).
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from crosscheck_tags import check_disagreement  # noqa: E402


def test_agrees_when_top1_matches_stored_label():
    disagreement, reason = check_disagreement(
        stored_label="shirt", candidate_sims={"shirt": 0.31, "jacket": 0.20}
    )
    assert disagreement is False
    assert reason is None


def test_disagrees_when_margin_exceeded():
    disagreement, reason = check_disagreement(
        stored_label="shirt",
        candidate_sims={"shirt": 0.20, "jacket": 0.31},
        margin=0.05,
    )
    assert disagreement is True
    assert "shirt" in reason
    assert "jacket" in reason


def test_no_disagreement_when_within_margin():
    """top1 != stored, but the similarity gap doesn't exceed the margin —
    not confident enough to flag."""
    disagreement, reason = check_disagreement(
        stored_label="shirt",
        candidate_sims={"shirt": 0.30, "jacket": 0.33},
        margin=0.05,
    )
    assert disagreement is False
    assert reason is None


def test_disagreement_boundary_is_strictly_greater_than_margin():
    # Exactly at the margin -> not a disagreement (">", not ">=").
    disagreement, _ = check_disagreement(
        stored_label="shirt", candidate_sims={"shirt": 0.25, "jacket": 0.30}, margin=0.05
    )
    assert disagreement is False

    # Just over the margin -> disagreement.
    disagreement, _ = check_disagreement(
        stored_label="shirt", candidate_sims={"shirt": 0.2499, "jacket": 0.30}, margin=0.05
    )
    assert disagreement is True


def test_off_vocabulary_stored_label_treated_as_zero_similarity():
    """A stored label that isn't itself a candidate can't be scored — treated
    as similarity 0.0, so any real top-1 match flags it for review."""
    disagreement, reason = check_disagreement(
        stored_label="some-off-vocab-label",
        candidate_sims={"shirt": 0.28, "jacket": 0.15},
        margin=0.05,
    )
    assert disagreement is True
    assert "some-off-vocab-label" in reason


def test_none_stored_label_treated_as_zero_similarity():
    disagreement, reason = check_disagreement(
        stored_label=None, candidate_sims={"solid": 0.30}, margin=0.05
    )
    assert disagreement is True


def test_empty_candidate_sims_never_flags():
    disagreement, reason = check_disagreement(stored_label="shirt", candidate_sims={})
    assert disagreement is False
    assert reason is None


def test_case_insensitive_stored_label_match():
    disagreement, _ = check_disagreement(
        stored_label="SHIRT", candidate_sims={"shirt": 0.31, "jacket": 0.10}
    )
    assert disagreement is False
