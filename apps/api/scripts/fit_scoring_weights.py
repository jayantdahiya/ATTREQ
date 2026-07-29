#!/usr/bin/env python
"""RI-5 (Task 5.2) — fit aggregation weights on real accept/reject preference
pairs and publish them to the `scoring_weights` table.

Reads `recommendation_events` (RI-1), derives (chosen, skipped) preference
pairs per generation batch, fits Bradley-Terry logistic regression over
score-component differences (`services/recommendation/weight_fitting.py`),
and — subject to a publish guard — writes a new active `scoring_weights` row
that `weight_fitting.get_active_weights` serves on the next request. NEVER
runs in a request path; this script is the only caller of
`LogisticRegression.fit()` in the codebase.

Global fit: pooled across all users (anonymized — `user_id` is never a model
feature, only used for macro-averaging the holdout AUC and grouping the
per-user refit below). Refuses to publish if the train set falls below
`--min-global-pairs` (default 200) unless `--force`.

Per-user refit: for each user with >= `--min-user-decisions` (default 30)
distinct decision batches (`recommendation_id`s with a positive event — the
milestone's "30 decisions" is expressed in batches, not raw pairs), fits that
user's own pairs and shrinks toward the (freshly-fit) global weights via
`shrink_to_global` (lambda=20), then publishes under `scope=str(user_id)` if
it beats that user's prior scope-specific holdout AUC (or has none yet).

Usage:
    python scripts/fit_scoring_weights.py --dry-run
    python scripts/fit_scoring_weights.py --scope global
    python scripts/fit_scoring_weights.py --scope <uuid>
    python scripts/fit_scoring_weights.py --force   # bootstrap: first-ever fit,
                                                     # no baseline to compare against
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import sys
from pathlib import Path
from uuid import UUID

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

logger = logging.getLogger("fit_scoring_weights")


async def _fit_scope(
    db,
    *,
    pairs,
    component_keys: list[str],
    scope: str,
    holdout_frac: float,
    seed: int,
    min_pairs_floor: int | None,
    force: bool,
    dry_run: bool,
) -> dict:
    """Fit + evaluate + (maybe) publish one scope's weights. Returns a report dict."""
    from attreq_api.crud.scoring_weights import scoring_weights_crud
    from attreq_api.services.recommendation.weight_fitting import (
        FALLBACK_WEIGHTS,
        build_feature_matrix,
        compute_holdout_user_auc,
        fit_weights,
        grouped_train_holdout_split,
    )

    train_pairs, holdout_pairs = grouped_train_holdout_split(pairs, holdout_frac=holdout_frac, seed=seed)

    report: dict = {
        "scope": scope,
        "n_pairs_total": len(pairs),
        "n_train_pairs": len(train_pairs),
        "n_holdout_pairs": len(holdout_pairs),
        "component_keys": component_keys,
    }

    if min_pairs_floor is not None and len(train_pairs) < min_pairs_floor and not force:
        report["published"] = False
        report["refusal_reason"] = (
            f"train pairs ({len(train_pairs)}) below floor ({min_pairs_floor}); use --force to override"
        )
        return report

    x, y = build_feature_matrix(train_pairs, component_keys)
    fitted_weights = fit_weights(x, y, component_keys)
    new_auc = compute_holdout_user_auc(holdout_pairs, fitted_weights, component_keys)

    existing = await scoring_weights_crud.get_active(db, scope=scope)
    if existing is not None:
        baseline_weights = dict(existing.weights)
        baseline_auc = compute_holdout_user_auc(holdout_pairs, baseline_weights, component_keys)
        baseline_source = f"active scope={scope} row"
    else:
        baseline_weights = {k: FALLBACK_WEIGHTS.get(k, 0.0) for k in component_keys}
        total = sum(baseline_weights.values()) or 1.0
        baseline_weights = {k: v / total for k, v in baseline_weights.items()}
        baseline_auc = compute_holdout_user_auc(holdout_pairs, baseline_weights, component_keys)
        baseline_source = "FALLBACK_WEIGHTS (no prior active row)"

    report.update(
        {
            "fitted_weights": fitted_weights,
            "new_holdout_user_auc": new_auc,
            "baseline_holdout_user_auc": baseline_auc,
            "baseline_source": baseline_source,
        }
    )

    should_publish = force or new_auc > baseline_auc
    report["published"] = False

    if dry_run:
        report["dry_run"] = True
        report["would_publish"] = should_publish
        return report

    if should_publish:
        await scoring_weights_crud.publish(
            db,
            scope=scope,
            weights=fitted_weights,
            fitted_on_n_pairs=len(train_pairs),
            holdout_user_auc=new_auc,
        )
        report["published"] = True
    else:
        await scoring_weights_crud.record_refused(
            db,
            scope=scope,
            weights=fitted_weights,
            fitted_on_n_pairs=len(train_pairs),
            holdout_user_auc=new_auc,
        )
        report["refusal_reason"] = f"new AUC ({new_auc:.4f}) did not beat baseline ({baseline_auc:.4f})"

    return report


async def _run(args: argparse.Namespace) -> list[dict]:
    from attreq_api.config.database import AsyncSessionLocal
    from attreq_api.services.recommendation.weight_fitting import (
        detect_component_keys,
        extract_preference_pairs,
    )

    reports: list[dict] = []

    async with AsyncSessionLocal() as db:
        target_user_id: UUID | None = None
        if args.scope and args.scope != "global":
            target_user_id = UUID(args.scope)

        all_pairs = await extract_preference_pairs(db, user_id=target_user_id)
        if not all_pairs:
            logger.warning("No preference pairs found — nothing to fit.")
            return [{"scope": args.scope or "global", "n_pairs_total": 0, "published": False,
                      "refusal_reason": "no preference pairs available"}]

        component_keys = detect_component_keys(all_pairs)
        logger.info("Detected component keys: %s", component_keys)

        if target_user_id is not None:
            # Single-scope run: fit only this user, no global floor applies.
            report = await _fit_scope(
                db,
                pairs=all_pairs,
                component_keys=component_keys,
                scope=str(target_user_id),
                holdout_frac=args.holdout_frac,
                seed=args.seed,
                min_pairs_floor=None,
                force=args.force,
                dry_run=args.dry_run,
            )
            reports.append(report)
            return reports

        # Global fit first.
        global_report = await _fit_scope(
            db,
            pairs=all_pairs,
            component_keys=component_keys,
            scope="global",
            holdout_frac=args.holdout_frac,
            seed=args.seed,
            min_pairs_floor=args.min_global_pairs,
            force=args.force,
            dry_run=args.dry_run,
        )
        reports.append(global_report)

        if "fitted_weights" not in global_report:
            # Global floor refusal — per-user refits shrink toward a global
            # fit that was refused; skip them rather than shrinking toward
            # noise.
            logger.warning("Skipping per-user refits: global fit was not produced.")
            return reports

        global_weights = global_report["fitted_weights"]

        from attreq_api.crud.scoring_weights import scoring_weights_crud
        from attreq_api.services.recommendation.weight_fitting import (
            build_feature_matrix,
            compute_holdout_user_auc,
            count_decision_batches,
            fit_weights,
            grouped_train_holdout_split,
            shrink_to_global,
        )

        pairs_by_user: dict[UUID, list] = {}
        for pair in all_pairs:
            pairs_by_user.setdefault(pair.user_id, []).append(pair)

        for user_id, user_pairs in pairs_by_user.items():
            m = count_decision_batches(user_pairs)
            if m < args.min_user_decisions:
                continue

            train_pairs, holdout_pairs = grouped_train_holdout_split(
                user_pairs, holdout_frac=args.holdout_frac, seed=args.seed
            )
            if not train_pairs:
                continue

            x, y = build_feature_matrix(train_pairs, component_keys)
            user_fit = fit_weights(x, y, component_keys)
            shrunk = shrink_to_global(user_fit, global_weights, m=m, lam=20)
            new_auc = compute_holdout_user_auc(holdout_pairs, shrunk, component_keys)

            existing = await scoring_weights_crud.get_active(db, scope=str(user_id))
            if existing is not None:
                baseline_auc = compute_holdout_user_auc(holdout_pairs, dict(existing.weights), component_keys)
            else:
                baseline_auc = compute_holdout_user_auc(holdout_pairs, global_weights, component_keys)

            user_report = {
                "scope": str(user_id),
                "n_decision_batches": m,
                "n_train_pairs": len(train_pairs),
                "n_holdout_pairs": len(holdout_pairs),
                "shrunk_weights": shrunk,
                "new_holdout_user_auc": new_auc,
                "baseline_holdout_user_auc": baseline_auc,
                "published": False,
            }

            should_publish = args.force or new_auc > baseline_auc
            if args.dry_run:
                user_report["dry_run"] = True
                user_report["would_publish"] = should_publish
            elif should_publish:
                await scoring_weights_crud.publish(
                    db,
                    scope=str(user_id),
                    weights=shrunk,
                    fitted_on_n_pairs=len(train_pairs),
                    holdout_user_auc=new_auc,
                )
                user_report["published"] = True
            else:
                await scoring_weights_crud.record_refused(
                    db,
                    scope=str(user_id),
                    weights=shrunk,
                    fitted_on_n_pairs=len(train_pairs),
                    holdout_user_auc=new_auc,
                )
                user_report["refusal_reason"] = (
                    f"new AUC ({new_auc:.4f}) did not beat baseline ({baseline_auc:.4f})"
                )

            reports.append(user_report)

    return reports


def _print_report(report: dict) -> None:
    print(f"--- scope={report.get('scope')} ---")
    for key, value in report.items():
        if key == "scope":
            continue
        print(f"  {key}: {value}")


def main() -> None:
    parser = argparse.ArgumentParser(description="RI-5 scoring-weight fit + publish")
    parser.add_argument("--dry-run", action="store_true", help="Fit and report, write nothing")
    parser.add_argument(
        "--scope",
        default=None,
        help="'global' (default behavior) or a user UUID to fit only that user's pairs",
    )
    parser.add_argument("--holdout-frac", type=float, default=0.2)
    parser.add_argument(
        "--min-global-pairs",
        type=int,
        default=200,
        help="Refuse to publish the global fit below this many TRAIN pairs (unless --force)",
    )
    parser.add_argument(
        "--min-user-decisions",
        type=int,
        default=30,
        help="Minimum distinct decision batches for a per-user refit to run",
    )
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument(
        "--force",
        action="store_true",
        help="Override the global-floor and publish-guard refusals (loud log) — bootstrap fits only",
    )
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)
    reports = asyncio.run(_run(args))

    for report in reports:
        _print_report(report)

    if args.dry_run:
        sys.exit(0)

    any_published = any(r.get("published") for r in reports)
    sys.exit(0 if any_published else 1)


if __name__ == "__main__":
    main()
