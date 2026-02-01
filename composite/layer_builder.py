"""Build sentiment and macro layer scores from driver sub-indices."""

import logging
from typing import Dict, Optional

from config.settings import DRIVER_WEIGHTS

logger = logging.getLogger(__name__)


def build_layer_score(driver_scores: Dict[str, float],
                       weights: Optional[Dict[str, float]] = None) -> float:
    """Compute a weighted average layer score from driver scores.

    Handles missing drivers by redistributing weights proportionally.

    Args:
        driver_scores: Dict mapping driver name to score (0-100)
        weights: Optional custom weights; defaults to DRIVER_WEIGHTS

    Returns:
        Layer score 0-100
    """
    if weights is None:
        weights = DRIVER_WEIGHTS

    # Filter to available drivers
    available = {d: s for d, s in driver_scores.items() if d in weights}

    if not available:
        logger.warning("No driver scores available for layer computation")
        return 50.0

    # Redistribute weights to available drivers
    total_weight = sum(weights[d] for d in available)
    if total_weight == 0:
        return 50.0

    weighted_sum = sum(
        driver_scores[d] * (weights[d] / total_weight)
        for d in available
    )

    logger.info("Layer score: %.1f (from %d drivers, weight coverage %.0f%%)",
                weighted_sum, len(available),
                total_weight * 100)

    return float(weighted_sum)


def build_both_layers(
    sentiment_driver_scores: Dict[str, float],
    macro_driver_scores: Dict[str, float],
) -> Dict[str, float]:
    """Build both layer scores.

    Returns:
        Dict with 'sentiment' and 'macro' layer scores
    """
    sentiment = build_layer_score(sentiment_driver_scores)
    macro = build_layer_score(macro_driver_scores)

    logger.info("Sentiment layer: %.1f | Macro layer: %.1f", sentiment, macro)

    return {
        "sentiment": sentiment,
        "macro": macro,
    }
