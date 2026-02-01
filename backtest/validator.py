"""Validation: correlation of composite index with gold returns."""

import logging
from typing import Dict, Optional

import numpy as np
import pandas as pd

from config.settings import DB_PATH
from storage.db import get_daily_composites

logger = logging.getLogger(__name__)


def compute_correlations(db_path: str = DB_PATH,
                          forward_days: list = None) -> Dict[str, float]:
    """Compute correlation between composite score and forward gold returns.

    Args:
        db_path: Path to SQLite database
        forward_days: List of forward return horizons (default: [1, 5, 10, 20])

    Returns:
        Dict mapping 'corr_{n}d' to Pearson correlation coefficient
    """
    if forward_days is None:
        forward_days = [1, 5, 10, 20]

    df = get_daily_composites(db_path)
    if df.empty or len(df) < 10:
        logger.warning("Not enough data for correlation analysis (have %d rows)", len(df))
        return {}

    df = df.sort_values("date").reset_index(drop=True)
    df["gold_price"] = pd.to_numeric(df["gold_price"], errors="coerce")
    df["composite_score"] = pd.to_numeric(df["composite_score"], errors="coerce")

    results = {}
    for n in forward_days:
        df[f"fwd_return_{n}d"] = df["gold_price"].pct_change(n).shift(-n)
        valid = df[["composite_score", f"fwd_return_{n}d"]].dropna()
        if len(valid) < 5:
            continue
        corr = valid["composite_score"].corr(valid[f"fwd_return_{n}d"])
        results[f"corr_{n}d"] = round(corr, 4)
        logger.info("Correlation (composite vs %dd fwd return): %.4f (n=%d)",
                     n, corr, len(valid))

    return results


def regime_analysis(db_path: str = DB_PATH,
                     n_quintiles: int = 5) -> Optional[pd.DataFrame]:
    """Analyze gold returns by composite score quintile.

    Groups days into quintiles based on composite score and computes
    average next-day returns for each group.
    """
    df = get_daily_composites(db_path)
    if df.empty or len(df) < 20:
        logger.warning("Not enough data for regime analysis")
        return None

    df = df.sort_values("date").reset_index(drop=True)
    df["gold_price"] = pd.to_numeric(df["gold_price"], errors="coerce")
    df["composite_score"] = pd.to_numeric(df["composite_score"], errors="coerce")
    df["next_day_return"] = df["gold_price"].pct_change().shift(-1)

    valid = df[["composite_score", "next_day_return"]].dropna()
    if len(valid) < n_quintiles * 2:
        return None

    valid["quintile"] = pd.qcut(valid["composite_score"], n_quintiles,
                                  labels=False, duplicates="drop") + 1

    regime_stats = valid.groupby("quintile").agg(
        count=("next_day_return", "count"),
        mean_return=("next_day_return", "mean"),
        median_return=("next_day_return", "median"),
        std_return=("next_day_return", "std"),
        hit_rate=("next_day_return", lambda x: (x > 0).mean()),
        avg_score=("composite_score", "mean"),
    ).round(6)

    logger.info("Regime analysis:\n%s", regime_stats.to_string())
    return regime_stats


def information_coefficient(db_path: str = DB_PATH) -> Optional[float]:
    """Compute the Information Coefficient (rank correlation).

    IC = Spearman rank correlation between composite score and next-day returns.
    """
    df = get_daily_composites(db_path)
    if df.empty or len(df) < 10:
        return None

    df = df.sort_values("date").reset_index(drop=True)
    df["gold_price"] = pd.to_numeric(df["gold_price"], errors="coerce")
    df["composite_score"] = pd.to_numeric(df["composite_score"], errors="coerce")
    df["next_day_return"] = df["gold_price"].pct_change().shift(-1)

    valid = df[["composite_score", "next_day_return"]].dropna()
    if len(valid) < 5:
        return None

    ic = valid["composite_score"].corr(valid["next_day_return"], method="spearman")
    logger.info("Information Coefficient (Spearman): %.4f", ic)
    return round(ic, 4)


def print_validation_report(db_path: str = DB_PATH):
    """Print a formatted validation summary."""
    print("\n" + "=" * 50)
    print("  VALIDATION REPORT")
    print("=" * 50)

    # Correlations
    corrs = compute_correlations(db_path)
    if corrs:
        print("\n  Composite Score vs Forward Gold Returns:")
        for key, val in corrs.items():
            horizon = key.replace("corr_", "").replace("d", "-day")
            print(f"    {horizon:>8} forward:  {val:+.4f}")
    else:
        print("\n  Insufficient data for correlation analysis")

    # IC
    ic = information_coefficient(db_path)
    if ic is not None:
        print(f"\n  Information Coefficient (Spearman): {ic:+.4f}")

    # Regime analysis
    regimes = regime_analysis(db_path)
    if regimes is not None:
        print("\n  Regime Analysis (Score Quintiles → Next-Day Returns):")
        print(f"  {'Q':>3} {'Avg Score':>10} {'Mean Ret':>10} {'Hit Rate':>10} {'Count':>6}")
        for q, row in regimes.iterrows():
            print(f"  {q:>3} {row['avg_score']:>10.1f} {row['mean_return']:>10.4%} "
                  f"{row['hit_rate']:>10.1%} {int(row['count']):>6}")

    print("\n" + "=" * 50)
