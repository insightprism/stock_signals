"""Per-driver sub-index computation for both sentiment and macro layers."""

import logging
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

from processors.normalizer import normalize_signal

logger = logging.getLogger(__name__)

# Normalization config per source+series pattern
NORM_CONFIG = {
    # FRED series — use rolling percentile
    "fred": {"method": "percentile"},
    # yfinance close prices — use rolling percentile
    "yfinance": {"method": "percentile"},
    # yfinance volume — use z-score sigmoid
    "yfinance_volume": {"method": "zscore"},
    # CFTC COT — use z-score sigmoid
    "cftc_cot": {"method": "zscore"},
    # GDELT tone — use linear rescale (typically -10 to +10)
    "gdelt": {"method": "linear", "src_min": -10.0, "src_max": 10.0},
    # Alpha Vantage sentiment — use linear rescale (-1 to +1)
    "alphavantage": {"method": "linear", "src_min": -1.0, "src_max": 1.0},
    # VADER sentiment — use linear rescale (-1 to +1)
    "reddit_vader": {"method": "linear", "src_min": -1.0, "src_max": 1.0},
    # Google Trends — use linear rescale (0 to 100)
    "google_trends": {"method": "linear", "src_min": 0.0, "src_max": 100.0},
}


def get_norm_config(source: str, series_name: str = "") -> dict:
    """Get normalization config for a given source/series combination."""
    # Check for volume-specific config
    if source == "yfinance" and "volume" in series_name.lower():
        return NORM_CONFIG["yfinance_volume"]
    return NORM_CONFIG.get(source, {"method": "percentile"})


def compute_driver_score(signals: List[dict],
                          history_lookup: Optional[dict] = None) -> float:
    """Compute a single driver's score from its signals.

    Each signal is normalized to 0-100, then averaged.
    Signals with invert=True in metadata are inverted during normalization.

    Args:
        signals: List of signal dicts with source, series_name, raw_value, metadata
        history_lookup: Dict mapping (source, series_name) to pd.Series of historical values

    Returns:
        Driver score 0-100
    """
    if not signals:
        return 50.0  # neutral when no data

    scores = []
    for sig in signals:
        source = sig["source"]
        series_name = sig.get("series_name", "")
        raw_value = sig["raw_value"]
        metadata = sig.get("metadata", {})
        invert = metadata.get("invert", False)

        norm_cfg = get_norm_config(source, series_name)
        method = norm_cfg["method"]

        history = None
        if history_lookup and (source, series_name) in history_lookup:
            history = history_lookup[(source, series_name)]

        kwargs = {"method": method, "current_value": raw_value,
                  "history": history, "invert": invert}
        if method == "linear":
            kwargs["src_min"] = norm_cfg.get("src_min", -1.0)
            kwargs["src_max"] = norm_cfg.get("src_max", 1.0)

        score = normalize_signal(**kwargs)
        scores.append(score)

        logger.debug("  %s/%s: raw=%.4f → norm=%.1f (method=%s, invert=%s)",
                      source, series_name, raw_value, score, method, invert)

    return float(np.mean(scores))


def compute_all_driver_scores(
    signals_by_driver: Dict[str, List[dict]],
    history_lookup: Optional[dict] = None,
) -> Dict[str, float]:
    """Compute scores for all drivers.

    Args:
        signals_by_driver: Dict mapping driver name to list of signal dicts
        history_lookup: Dict mapping (source, series_name) to historical pd.Series

    Returns:
        Dict mapping driver name to score (0-100)
    """
    scores = {}
    for driver, signals in signals_by_driver.items():
        score = compute_driver_score(signals, history_lookup)
        scores[driver] = score
        logger.info("Driver %s: %.1f (from %d signals)",
                     driver, score, len(signals))
    return scores
