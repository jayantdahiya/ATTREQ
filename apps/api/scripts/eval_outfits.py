#!/usr/bin/env python
"""RI-1 outfit-quality eval harness — the RI-3/4/5 scorer regression gate.

Generates top x bottom pairs from a seeded synthetic wardrobe, renders a CSV
labeling sheet for a human (founder/beta-user) to fill in good/bad judgments, and
reports the current scorer's AUC against those labels.

Deliberately out of scope (see RI-1 plan / milestone doc): no change to scoring
weights or the recommendation algorithm itself — `score_pair` is a read-only,
minimal wrapper around the existing scoring functions so RI-3/4/5 can swap scorers
without rewriting this harness.

RI-5 Task 5.5 (`--weights fitted`) is the exception to that "no scoring-weight
change" rule: it does not change any weights itself (that's
`scripts/fit_scoring_weights.py`'s job), it only evaluates — pulling real
preference pairs from `recommendation_events` (or a seeded synthetic set if
none exist yet), fitting weights on a train split, and reporting
user-conditioned holdout AUC for the fitted weights vs. the hand-tuned
baseline (`FALLBACK_WEIGHTS`). Advisory only: it prints the comparison and
never exits nonzero on a loss.

Usage:
    python scripts/eval_outfits.py --generate --out tests/fixtures/eval/outfit_pairs_unlabeled.csv
    python scripts/eval_outfits.py --score tests/fixtures/eval/outfit_labels.csv
    python scripts/eval_outfits.py --compare legacy,branched
    python scripts/eval_outfits.py --weights fitted --metric user_auc
"""

from __future__ import annotations

import argparse
import asyncio
import json
import random
import sys
import uuid
from pathlib import Path
from typing import Any

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from _legacy_scorers import legacy_color_harmony_score  # noqa: E402

from attreq_api.models.wardrobe import WardrobeItem  # noqa: E402
from attreq_api.services.recommendation.algorithm import (  # noqa: E402
    calculate_color_harmony_score,
    calculate_formality_score,
)
from attreq_api.services.recommendation.weight_fitting import (  # noqa: E402
    FALLBACK_WEIGHTS,
    PreferencePair,
    build_feature_matrix,
    compute_holdout_user_auc,
    count_decision_batches,
    detect_component_keys,
    extract_preference_pairs,
    fit_weights,
    grouped_train_holdout_split,
)

# Only these fields are meaningful to the two scorer functions; anything else in a
# wardrobe-item dict (e.g. a synthetic `id`) must be stripped before constructing a
# transient (never-persisted) WardrobeItem for scoring.
_SCORER_FIELDS = {"category", "color_primary", "pattern", "occasion"}

DEFAULT_LABELS_CSV = Path(__file__).resolve().parent.parent / "tests" / "fixtures" / "eval" / "outfit_labels.csv"


def _to_wardrobe_item(item: dict[str, Any]) -> WardrobeItem:
    """Build a transient (never added to a session) WardrobeItem for scoring only."""
    fields = {k: v for k, v in item.items() if k in _SCORER_FIELDS}
    return WardrobeItem(**fields)


def score_pair(top: dict[str, Any], bottom: dict[str, Any]) -> float:
    """Minimal, stable scoring surface over the existing algorithm functions.

    RI-3: this now IS the "branched" arm — `calculate_color_harmony_score`
    was rewired in `algorithm.py` to the CIELAB three-branch max
    (`services/recommendation/color_harmony.py`), so this function picks it up
    automatically with no code change here. See `score_pair_legacy` below for
    the frozen pre-RI-3 arm, and `--compare legacy,branched` for a head-to-head.
    """
    top_item = _to_wardrobe_item(top)
    bottom_item = _to_wardrobe_item(bottom)

    color_score = calculate_color_harmony_score(top_item, bottom_item)
    formality_score = calculate_formality_score([top_item, bottom_item])

    return (color_score * 0.5) + (formality_score * 0.5)


def score_pair_legacy(top: dict[str, Any], bottom: dict[str, Any]) -> float:
    """RI-3 "legacy" arm — the frozen pre-RI-3 named-color-table scorer
    (`scripts/_legacy_scorers.py`), blended with the (unchanged) formality
    score the same way `score_pair` always has been, so the only variable
    between the two arms is the color-harmony logic itself.
    """
    top_item = _to_wardrobe_item(top)
    bottom_item = _to_wardrobe_item(bottom)

    color_score = legacy_color_harmony_score(top.get("color_primary"), bottom.get("color_primary"))
    formality_score = calculate_formality_score([top_item, bottom_item])

    return (color_score * 0.5) + (formality_score * 0.5)


def generate_synthetic_wardrobe(seed: int = 42) -> list[dict[str, Any]]:
    """Seeded synthetic wardrobe covering the attribute space the scorer reads.

    Not real user data — a fixed set of tops/bottoms spanning categories, color
    families (neutral/warm/cool), and formality/occasion tags, so `generate_pairs`
    can sample a representative mix.
    """
    tops = [
        {"id": "top-tshirt-white", "category": "t-shirt", "color_primary": "white", "pattern": "solid", "occasion": ["casual"]},
        {"id": "top-tshirt-red", "category": "t-shirt", "color_primary": "red", "pattern": "solid", "occasion": ["casual"]},
        {"id": "top-hoodie-gray", "category": "hoodie", "color_primary": "gray", "pattern": "solid", "occasion": ["casual"]},
        {"id": "top-blouse-blue", "category": "blouse", "color_primary": "blue", "pattern": "solid", "occasion": ["business"]},
        {"id": "top-dressshirt-white", "category": "dress shirt", "color_primary": "white", "pattern": "solid", "occasion": ["formal"]},
        {"id": "top-dressshirt-black", "category": "dress shirt", "color_primary": "black", "pattern": "solid", "occasion": ["formal"]},
        {"id": "top-blazer-navy", "category": "blazer", "color_primary": "blue", "pattern": "solid", "occasion": ["formal"]},
        {"id": "top-tshirt-yellow", "category": "t-shirt", "color_primary": "yellow", "pattern": "printed", "occasion": ["casual"]},
        {"id": "top-athletic-green", "category": "athletic wear", "color_primary": "green", "pattern": "solid", "occasion": ["casual"]},
        {"id": "top-tshirt-purple", "category": "t-shirt", "color_primary": "purple", "pattern": "solid", "occasion": ["casual"]},
    ]
    bottoms = [
        {"id": "bottom-jeans-blue", "category": "jeans", "color_primary": "blue", "pattern": "solid", "occasion": ["casual"]},
        {"id": "bottom-jeans-black", "category": "jeans", "color_primary": "black", "pattern": "solid", "occasion": ["casual"]},
        {"id": "bottom-shorts-beige", "category": "shorts", "color_primary": "beige", "pattern": "solid", "occasion": ["casual"]},
        {"id": "bottom-chinos-tan", "category": "chinos", "color_primary": "tan", "pattern": "solid", "occasion": ["business"]},
        {"id": "bottom-dresspants-black", "category": "dress pants", "color_primary": "black", "pattern": "solid", "occasion": ["formal"]},
        {"id": "bottom-dresspants-gray", "category": "dress pants", "color_primary": "gray", "pattern": "solid", "occasion": ["formal"]},
        {"id": "bottom-skirt-red", "category": "skirt", "color_primary": "red", "pattern": "solid", "occasion": ["business"]},
        {"id": "bottom-sweatpants-gray", "category": "sweatpants", "color_primary": "gray", "pattern": "solid", "occasion": ["casual"]},
        {"id": "bottom-jeans-green", "category": "jeans", "color_primary": "green", "pattern": "solid", "occasion": ["casual"]},
        {"id": "bottom-chinos-navy", "category": "chinos", "color_primary": "blue", "pattern": "solid", "occasion": ["business"]},
    ]

    rng = random.Random(seed)
    rng.shuffle(tops)
    rng.shuffle(bottoms)

    return tops + bottoms


def generate_pairs(wardrobe: list[dict[str, Any]], n: int = 100, seed: int = 42) -> list[dict[str, Any]]:
    """Sample n top x bottom pairs (with replacement) from the synthetic wardrobe."""
    tops = [item for item in wardrobe if item["id"].startswith("top-")]
    bottoms = [item for item in wardrobe if item["id"].startswith("bottom-")]

    rng = random.Random(seed)
    pairs = []
    for i in range(n):
        top = rng.choice(tops)
        bottom = rng.choice(bottoms)
        pairs.append(
            {
                "pair_id": f"pair-{i:04d}",
                "top_item_json": json.dumps(top),
                "bottom_item_json": json.dumps(bottom),
            }
        )
    return pairs


def render_labeling_sheet(pairs: list[dict[str, Any]], out_path: Path) -> None:
    """Write a CSV labeling sheet with an empty `label` column for a human to fill in.

    label semantics: 1 = good outfit, 0 = bad outfit. Leave blank to skip a pair.
    """
    df = pd.DataFrame(pairs)
    df["label"] = ""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_path, index=False)
    print(f"Wrote {len(df)} unlabeled pairs to {out_path}")


def ingest_labels(csv_path: Path) -> pd.DataFrame:
    """Load a labeled CSV (pair_id, top_item_json, bottom_item_json, label)."""
    df = pd.read_csv(csv_path)
    required = {"pair_id", "top_item_json", "bottom_item_json", "label"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Labeled CSV missing required columns: {missing}")

    df = df.dropna(subset=["label"])
    df["label"] = df["label"].astype(int)
    return df


def score_against_scorer(labeled_df: pd.DataFrame) -> float:
    """Compute the current scorer's AUC against human (or founder) labels.

    Raises if only one class is present — `roc_auc_score` requires both.
    """
    from sklearn.metrics import roc_auc_score

    scores = []
    labels = []
    for _, row in labeled_df.iterrows():
        top = json.loads(row["top_item_json"])
        bottom = json.loads(row["bottom_item_json"])
        scores.append(score_pair(top, bottom))
        labels.append(int(row["label"]))

    if len(set(labels)) < 2:
        raise ValueError(
            "Labeled data must contain both classes (0 and 1) for AUC to be defined; "
            f"got only: {set(labels)}"
        )

    return roc_auc_score(labels, scores)


def _auc_for(labeled_df: pd.DataFrame, scorer) -> float:
    from sklearn.metrics import roc_auc_score

    scores, labels = [], []
    for _, row in labeled_df.iterrows():
        top = json.loads(row["top_item_json"])
        bottom = json.loads(row["bottom_item_json"])
        scores.append(scorer(top, bottom))
        labels.append(int(row["label"]))

    if len(set(labels)) < 2:
        raise ValueError(
            "Labeled data must contain both classes (0 and 1) for AUC to be defined; "
            f"got only: {set(labels)}"
        )
    return roc_auc_score(labels, scores)


def compare_scorers(labeled_df: pd.DataFrame) -> dict[str, float]:
    """RI-3 (C-Eval): report both arms' AUC. ADVISORY ONLY — the blocking gate
    for RI-3 is the deterministic branch-selection unit tests
    (`tests/test_color_harmony.py`), not this comparison. The labeled set here
    is a ~120-pair hand-authored fixture (`tests/fixtures/eval/outfit_labels.csv`,
    RI-1), not the >=100 independently-human-labeled set the milestone doc
    originally envisioned — a real blocking AUC gate is deferred to RI-1's
    follow-up work. This function never raises/exits nonzero on a regression,
    only prints a warning (see `main()`).
    """
    return {
        "legacy": _auc_for(labeled_df, score_pair_legacy),
        "branched": _auc_for(labeled_df, score_pair),
    }


def generate_synthetic_preference_pairs(
    n_users: int = 30, batches_per_user: int = 20, seed: int = 42
) -> list[PreferencePair]:
    """Seeded synthetic preference pairs, shaped like `weight_fitting.PreferencePair`,
    used only as a bootstrap/local-dev fallback for `--weights fitted` when the
    DB has no real `recommendation_events` yet (a fresh/ephemeral database, or
    before RI-1 telemetry has accumulated any accept/reject signal).

    Each synthetic user has the same latent preference structure: the chosen
    (positive) outfit is planted with a small but ALWAYS-positive margin on
    `color_harmony`/`style_dna`, while `formality`/`behaviour` are pure noise
    (independent uniform draws on both sides, uncorrelated with which side
    won) — i.e. the first two components carry 100% of the taste signal and
    the other two carry none. `FALLBACK_WEIGHTS` (the hand-tuned baseline)
    still spreads real weight across the noisy formality/behaviour components
    (0.20 each) alongside the signal ones, so on a good fraction of pairs
    that noise is large enough to outvote the deliberately small signal
    margin and flip the baseline's ranking — while a correct fit learns to
    concentrate weight on `color_harmony`/`style_dna` and keeps ranking
    almost every pair correctly. Distinct `recommendation_id`s per batch and
    `user_id`s per synthetic user keep the grouped split and macro-averaged
    AUC meaningful, same as real data.

    NOT a substitute for the real-data run the milestone doc asks to be
    recorded by hand once RI-1 telemetry exists.
    """
    rng = random.Random(seed)

    def _seeded_uuid() -> uuid.UUID:
        # `uuid.uuid4()` draws from `os.urandom` and ignores `random.Random`
        # entirely, so using it here would silently break the "seeded" claim
        # (the grouped train/holdout split shuffles by these IDs — a
        # non-reproducible ID means a non-reproducible split, and thus a
        # non-reproducible AUC comparison, on every "same seed" re-run).
        return uuid.UUID(int=rng.getrandbits(128), version=4)

    pairs: list[PreferencePair] = []
    for _ in range(n_users):
        user_id = _seeded_uuid()
        for _ in range(batches_per_user):
            recommendation_id = _seeded_uuid()
            # Small, always-positive signal margin (never a large gap).
            pos_color = rng.uniform(0.5, 0.7)
            neg_color = pos_color - rng.uniform(0.05, 0.2)
            pos_style = rng.uniform(0.5, 0.7)
            neg_style = pos_style - rng.uniform(0.05, 0.2)
            pos = {
                "color_harmony": pos_color,
                "formality": rng.uniform(0.0, 1.0),
                "style_dna": pos_style,
                "behaviour": rng.uniform(0.0, 1.0),
            }
            neg = {
                "color_harmony": neg_color,
                "formality": rng.uniform(0.0, 1.0),
                "style_dna": neg_style,
                "behaviour": rng.uniform(0.0, 1.0),
            }
            pairs.append(
                PreferencePair(
                    components_pos=pos,
                    components_neg=neg,
                    user_id=user_id,
                    recommendation_id=recommendation_id,
                )
            )
    return pairs


def evaluate_fitted_vs_baseline(
    pairs: list[PreferencePair], holdout_frac: float = 0.2, seed: int = 42
) -> dict[str, Any]:
    """RI-5 Task 5.5 — pure (no DB) fit-and-compare core.

    Splits `pairs` train/holdout GROUPED by `recommendation_id` (no batch
    leakage — finalized RI-5 plan Correction 8), fits Bradley-Terry weights
    on the train split, then reports user-conditioned holdout AUC
    (`compute_holdout_user_auc`) for BOTH the fitted weights and the
    hand-tuned baseline (`FALLBACK_WEIGHTS`, restricted+renormalized to the
    detected component keys) on the identical holdout set, so the comparison
    is fair. Advisory only — callers decide what to do with the result, this
    function never raises on a "loss".
    """
    component_keys = detect_component_keys(pairs)
    train_pairs, holdout_pairs = grouped_train_holdout_split(pairs, holdout_frac=holdout_frac, seed=seed)

    x, y = build_feature_matrix(train_pairs, component_keys)
    fitted_weights = fit_weights(x, y, component_keys)

    restricted_baseline = {k: FALLBACK_WEIGHTS.get(k, 0.0) for k in component_keys}
    total = sum(restricted_baseline.values()) or 1.0
    baseline_weights = {k: v / total for k, v in restricted_baseline.items()}

    fitted_auc = compute_holdout_user_auc(holdout_pairs, fitted_weights, component_keys)
    baseline_auc = compute_holdout_user_auc(holdout_pairs, baseline_weights, component_keys)

    return {
        "n_pairs_total": len(pairs),
        "n_train_pairs": len(train_pairs),
        "n_holdout_pairs": len(holdout_pairs),
        "n_decision_batches": count_decision_batches(pairs),
        "component_keys": component_keys,
        "fitted_weights": fitted_weights,
        "baseline_weights": baseline_weights,
        "fitted_user_auc": fitted_auc,
        "baseline_user_auc": baseline_auc,
        "fitted_beats_baseline": fitted_auc > baseline_auc,
    }


async def run_weights_fitted_eval(holdout_frac: float = 0.2, seed: int = 42) -> dict[str, Any]:
    """RI-5 Task 5.5 — the `--weights fitted` async entry point.

    Extracts pooled preference pairs from real `recommendation_events`
    (`weight_fitting.extract_preference_pairs`, DB-backed); if the database
    has none yet — e.g. a fresh/ephemeral eval environment before any real
    RI-1 telemetry exists — falls back to `generate_synthetic_preference_pairs`
    so the comparison still runs end to end (mirrors how
    `scripts/fit_scoring_weights.py` treats an empty-pairs result as a
    handled, non-crashing case, rather than reinventing that emptiness
    handling here). Delegates the actual fit + AUC comparison to the pure
    `evaluate_fitted_vs_baseline`.
    """
    from attreq_api.config.database import AsyncSessionLocal

    async with AsyncSessionLocal() as db:
        pairs = await extract_preference_pairs(db)

    used_synthetic = False
    if not pairs:
        used_synthetic = True
        pairs = generate_synthetic_preference_pairs(seed=seed)

    report = evaluate_fitted_vs_baseline(pairs, holdout_frac=holdout_frac, seed=seed)
    report["used_synthetic_pairs"] = used_synthetic
    return report


def _print_weights_fitted_report(report: dict[str, Any], metric: str) -> None:
    def _fmt_weights(weights: dict[str, float]) -> str:
        return ", ".join(f"{k}={v:.3f}" for k, v in weights.items())

    print("RI-5 Task 5.5 — fitted vs. hand-tuned baseline scoring weights (advisory eval gate)")
    if report["used_synthetic_pairs"]:
        print(
            "NOTE: no real recommendation_events found in the database — using a seeded "
            "synthetic preference-pair set as a bootstrap/local-dev fallback. Re-run against "
            "real telemetry once RI-1 events accumulate and record that run in the milestone doc."
        )
    print(
        f"Preference pairs: {report['n_pairs_total']} total "
        f"(train={report['n_train_pairs']}, holdout={report['n_holdout_pairs']}, "
        f"decision_batches={report['n_decision_batches']})"
    )
    print(f"Component keys: {report['component_keys']}")
    print(f"Fitted weights:   {_fmt_weights(report['fitted_weights'])}")
    print(f"Baseline weights: {_fmt_weights(report['baseline_weights'])}")
    print(f"Fitted   holdout {metric}: {report['fitted_user_auc']:.4f}")
    print(f"Baseline holdout {metric}: {report['baseline_user_auc']:.4f}")
    if report["fitted_beats_baseline"]:
        print(
            f"RESULT: fitted weights BEAT the hand-tuned baseline on holdout {metric} "
            "(advisory only — does not fail CI)."
        )
    else:
        print(
            f"RESULT: fitted weights did NOT beat the hand-tuned baseline on holdout {metric} "
            "(advisory only — does not fail CI)."
        )


def main() -> None:
    parser = argparse.ArgumentParser(description="RI-1/RI-3 outfit-quality eval harness")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--generate", action="store_true", help="Generate a fresh unlabeled pairs CSV for labeling"
    )
    group.add_argument(
        "--score", metavar="LABELED_CSV", help="Score the current scorer's AUC against a labeled CSV"
    )
    group.add_argument(
        "--compare",
        metavar="ARMS",
        help=(
            "RI-3: compare scorer arms against tests/fixtures/eval/outfit_labels.csv, "
            "e.g. --compare legacy,branched (order is cosmetic — both are always computed). "
            "Advisory only: prints a regression warning but never exits nonzero."
        ),
    )
    group.add_argument(
        "--weights",
        choices=["fitted"],
        default=None,
        help=(
            "RI-5 Task 5.5: fit Bradley-Terry scoring weights on held-out preference pairs "
            "(real recommendation_events, or a seeded synthetic set if none exist yet) and "
            "compare against the hand-tuned baseline (FALLBACK_WEIGHTS) via user-conditioned "
            "holdout AUC. Advisory only: prints the comparison, never exits nonzero on a loss."
        ),
    )
    parser.add_argument("--n", type=int, default=100, help="Number of pairs to generate (--generate only)")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument(
        "--out",
        type=Path,
        default=Path(__file__).resolve().parent.parent / "tests" / "fixtures" / "eval" / "outfit_pairs_unlabeled.csv",
        help="Output path for --generate",
    )
    parser.add_argument(
        "--metric",
        choices=["user_auc"],
        default="user_auc",
        help="Metric to report for --weights fitted (only user_auc is supported)",
    )
    parser.add_argument(
        "--holdout-frac",
        type=float,
        default=0.2,
        help="Holdout fraction (by recommendation_id) for --weights fitted",
    )
    args = parser.parse_args()

    if args.generate:
        wardrobe = generate_synthetic_wardrobe(seed=args.seed)
        pairs = generate_pairs(wardrobe, n=args.n, seed=args.seed)
        render_labeling_sheet(pairs, args.out)
        return

    if args.compare:
        labeled_df = ingest_labels(DEFAULT_LABELS_CSV)
        aucs = compare_scorers(labeled_df)
        print(f"Legacy (pre-RI-3 name-pair table)  AUC: {aucs['legacy']:.4f}")
        print(f"Branched (RI-3 CIELAB three-branch) AUC: {aucs['branched']:.4f}")
        if aucs["branched"] < aucs["legacy"]:
            print(
                "WARNING: branched AUC is lower than legacy on this hand-authored fixture "
                "(advisory only, not a blocking gate — see compare_scorers() docstring)."
            )
        return

    if args.weights == "fitted":
        report = asyncio.run(run_weights_fitted_eval(holdout_frac=args.holdout_frac, seed=args.seed))
        _print_weights_fitted_report(report, args.metric)
        return

    labeled_df = ingest_labels(Path(args.score))
    auc = score_against_scorer(labeled_df)
    print(f"Scorer AUC against {len(labeled_df)} labeled pairs: {auc:.4f}")


if __name__ == "__main__":
    main()
