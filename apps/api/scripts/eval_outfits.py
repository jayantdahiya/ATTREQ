#!/usr/bin/env python
"""RI-1 outfit-quality eval harness — the RI-3/4/5 scorer regression gate.

Generates top x bottom pairs from a seeded synthetic wardrobe, renders a CSV
labeling sheet for a human (founder/beta-user) to fill in good/bad judgments, and
reports the current scorer's AUC against those labels.

Deliberately out of scope (see RI-1 plan / milestone doc): no change to scoring
weights or the recommendation algorithm itself — `score_pair` is a read-only,
minimal wrapper around the existing scoring functions so RI-3/4/5 can swap scorers
without rewriting this harness.

Usage:
    python scripts/eval_outfits.py --generate --out tests/fixtures/eval/outfit_pairs_unlabeled.csv
    python scripts/eval_outfits.py --score tests/fixtures/eval/outfit_labels.csv
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path
from typing import Any

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from attreq_api.models.wardrobe import WardrobeItem  # noqa: E402
from attreq_api.services.recommendation.algorithm import (  # noqa: E402
    calculate_color_harmony_score,
    calculate_formality_score,
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

    RI-3/4/5 can swap in a different scorer by changing only this function's body —
    the rest of the harness (generation, labeling sheet, AUC scoring) stays put.
    """
    top_item = _to_wardrobe_item(top)
    bottom_item = _to_wardrobe_item(bottom)

    color_score = calculate_color_harmony_score(top_item, bottom_item)
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


def main() -> None:
    parser = argparse.ArgumentParser(description="RI-1 outfit-quality eval harness")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--generate", action="store_true", help="Generate a fresh unlabeled pairs CSV for labeling"
    )
    group.add_argument(
        "--score", metavar="LABELED_CSV", help="Score the current scorer's AUC against a labeled CSV"
    )
    parser.add_argument("--n", type=int, default=100, help="Number of pairs to generate (--generate only)")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument(
        "--out",
        type=Path,
        default=Path(__file__).resolve().parent.parent / "tests" / "fixtures" / "eval" / "outfit_pairs_unlabeled.csv",
        help="Output path for --generate",
    )
    args = parser.parse_args()

    if args.generate:
        wardrobe = generate_synthetic_wardrobe(seed=args.seed)
        pairs = generate_pairs(wardrobe, n=args.n, seed=args.seed)
        render_labeling_sheet(pairs, args.out)
        return

    labeled_df = ingest_labels(Path(args.score))
    auc = score_against_scorer(labeled_df)
    print(f"Scorer AUC against {len(labeled_df)} labeled pairs: {auc:.4f}")


if __name__ == "__main__":
    main()
