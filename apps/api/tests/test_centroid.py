"""Real-DB tests for services/style_dna/scoring.py::update_style_dna_centroid (RI-6).

Verifies the online running-mean math against the UNNORMALIZED stored
vector (the deliberate correction over "normalize after every update" —
see the module docstring) and the `n_items` increment / positive-only-signal
guard.
"""

from __future__ import annotations

import uuid

import numpy as np
import pytest
from sqlalchemy import select

from attreq_api.models.user import User
from attreq_api.services.style_dna.scoring import update_style_dna_centroid


@pytest.mark.asyncio
async def test_update_style_dna_centroid_seeds_on_first_call(db_session, real_user):
    mutated = await update_style_dna_centroid(
        db_session, real_user.id, [1.0, 2.0, 3.0], signal="liked"
    )
    assert mutated is True

    result = await db_session.execute(select(User).where(User.id == real_user.id))
    user = result.scalar_one()

    assert user.style_dna_centroid["n_items"] == 1
    assert user.style_dna_centroid["vector"] == pytest.approx([1.0, 2.0, 3.0])
    assert "updated_at" in user.style_dna_centroid


@pytest.mark.asyncio
async def test_update_style_dna_centroid_running_mean_on_unnormalized_vector(db_session, real_user):
    await update_style_dna_centroid(db_session, real_user.id, [2.0, 0.0], signal="liked")
    await update_style_dna_centroid(db_session, real_user.id, [0.0, 4.0], signal="worn")

    result = await db_session.execute(select(User).where(User.id == real_user.id))
    user = result.scalar_one()

    # new_mean = (old_mean * n + item) / (n + 1) = ([2,0]*1 + [0,4]) / 2 = [1, 2]
    assert user.style_dna_centroid["vector"] == pytest.approx([1.0, 2.0])
    assert user.style_dna_centroid["n_items"] == 2

    # Deliberately NOT unit-norm — the stored vector is a raw running mean,
    # normalized only at scoring time (similarity.centroid_score).
    stored_norm = float(np.linalg.norm(user.style_dna_centroid["vector"]))
    assert stored_norm != pytest.approx(1.0)


@pytest.mark.asyncio
async def test_update_style_dna_centroid_three_updates_matches_hand_computed_mean(db_session, real_user):
    vectors = [[1.0, 0.0], [0.0, 1.0], [2.0, 2.0]]
    for vec in vectors:
        await update_style_dna_centroid(db_session, real_user.id, vec, signal="liked")

    result = await db_session.execute(select(User).where(User.id == real_user.id))
    user = result.scalar_one()

    expected = np.mean(np.asarray(vectors), axis=0)
    assert user.style_dna_centroid["vector"] == pytest.approx(expected.tolist())
    assert user.style_dna_centroid["n_items"] == 3


@pytest.mark.asyncio
async def test_update_style_dna_centroid_rejects_dislike_signal(db_session, real_user):
    mutated = await update_style_dna_centroid(
        db_session, real_user.id, [1.0, 2.0], signal="disliked"
    )
    assert mutated is False

    result = await db_session.execute(select(User).where(User.id == real_user.id))
    user = result.scalar_one()
    assert user.style_dna_centroid is None


@pytest.mark.asyncio
async def test_update_style_dna_centroid_no_op_when_vector_missing(db_session, real_user):
    mutated = await update_style_dna_centroid(db_session, real_user.id, None, signal="liked")
    assert mutated is False


@pytest.mark.asyncio
async def test_update_style_dna_centroid_returns_false_for_unknown_user(db_session):
    mutated = await update_style_dna_centroid(db_session, uuid.uuid4(), [1.0], signal="liked")
    assert mutated is False
