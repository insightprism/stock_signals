"""Final composite index = weighted blend of sentiment and macro layers."""

import logging
from typing import Dict, Optional

from config.settings import LAYER_WEIGHTS

logger = logging.getLogger(__name__)

# Composite score labels
LABELS = [
    (0,  20, "Strongly Bearish"),
    (20, 35, "Bearish"),
    (35, 45, "Slightly Bearish"),
    (45, 55, "Neutral"),
    (55, 65, "Slightly Bullish"),
    (65, 80, "Bullish"),
    (80, 101, "Strongly Bullish"),
]


def score_to_label(score: float) -> str:
    """Convert a 0-100 composite score to a human-readable label."""
    for lo, hi, label in LABELS:
        if lo <= score < hi:
            return label
    return "Neutral"


def build_composite(layer_scores: Dict[str, float],
                     weights: Optional[Dict[str, float]] = None) -> Dict:
    """Blend sentiment and macro layers into final composite.

    Args:
        layer_scores: Dict with 'sentiment' and 'macro' keys, each 0-100
        weights: Optional custom layer weights

    Returns:
        Dict with composite_score, label, sentiment_layer, macro_layer
    """
    if weights is None:
        weights = LAYER_WEIGHTS

    sentiment = layer_scores.get("sentiment")
    macro = layer_scores.get("macro")

    # Handle missing layers
    if sentiment is not None and macro is not None:
        w_sent = weights["sentiment"]
        w_macro = weights["macro"]
        composite = sentiment * w_sent + macro * w_macro
    elif macro is not None:
        composite = macro
        logger.warning("Sentiment layer missing — using macro only")
    elif sentiment is not None:
        composite = sentiment
        logger.warning("Macro layer missing — using sentiment only")
    else:
        composite = 50.0
        logger.warning("Both layers missing — returning neutral 50")

    composite = max(0.0, min(100.0, composite))
    label = score_to_label(composite)

    logger.info("COMPOSITE: %.1f (%s) | Sentiment=%.1f Macro=%.1f",
                composite,
                label,
                sentiment if sentiment is not None else -1,
                macro if macro is not None else -1)

    return {
        "composite_score": round(composite, 2),
        "label": label,
        "sentiment_layer": round(sentiment, 2) if sentiment is not None else None,
        "macro_layer": round(macro, 2) if macro is not None else None,
    }
