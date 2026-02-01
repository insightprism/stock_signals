"""Normalization methods: rolling percentile, linear rescale, z-score sigmoid."""

import numpy as np
import pandas as pd

from config.settings import ROLLING_WINDOW, ZSCORE_WINDOW


def rolling_percentile(current_value: float, history: pd.Series,
                        window: int = ROLLING_WINDOW,
                        invert: bool = False) -> float:
    """Rank current value as a percentile within a rolling window.

    Used for unbounded signals (TIPS yields, DXY, VIX, COT positions).
    Returns 0-100 where 100 = highest percentile.
    """
    values = history.dropna().tail(window)
    if len(values) == 0:
        return 50.0  # neutral if no history
    rank = (values < current_value).sum()
    pct = (rank / len(values)) * 100.0
    if invert:
        pct = 100.0 - pct
    return float(np.clip(pct, 0, 100))


def linear_rescale(value: float, src_min: float, src_max: float,
                    invert: bool = False) -> float:
    """Linear map from [src_min, src_max] → [0, 100].

    Used for bounded signals (VADER -1 to +1, Google Trends 0-100).
    """
    if src_max == src_min:
        return 50.0
    normed = (value - src_min) / (src_max - src_min) * 100.0
    if invert:
        normed = 100.0 - normed
    return float(np.clip(normed, 0, 100))


def zscore_sigmoid(current_value: float, history: pd.Series,
                    window: int = ZSCORE_WINDOW,
                    invert: bool = False) -> float:
    """Z-score over rolling window passed through sigmoid → 0-100.

    Used for shifting-range signals (COT net positions, ETF volume ratio).
    """
    values = history.dropna().tail(window)
    if len(values) < 2:
        return 50.0
    mean = values.mean()
    std = values.std()
    if std == 0:
        return 50.0
    z = (current_value - mean) / std
    sigmoid = 1.0 / (1.0 + np.exp(-z))
    score = sigmoid * 100.0
    if invert:
        score = 100.0 - score
    return float(np.clip(score, 0, 100))


def normalize_signal(method: str, current_value: float,
                      history: pd.Series = None,
                      invert: bool = False,
                      src_min: float = -1.0,
                      src_max: float = 1.0) -> float:
    """Dispatch to the appropriate normalization method."""
    if method == "percentile":
        if history is None:
            return 50.0
        return rolling_percentile(current_value, history, invert=invert)
    elif method == "linear":
        return linear_rescale(current_value, src_min, src_max, invert=invert)
    elif method == "zscore":
        if history is None:
            return 50.0
        return zscore_sigmoid(current_value, history, invert=invert)
    else:
        raise ValueError(f"Unknown normalization method: {method}")
