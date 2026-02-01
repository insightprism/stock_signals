"""VADER-based sentiment analysis with financial keyword augmentation."""

import logging
from typing import List, Optional

logger = logging.getLogger(__name__)

_analyzer = None

# Financial terms that VADER may not handle well — custom lexicon additions
FINANCIAL_LEXICON = {
    # Bullish gold terms
    "rate cut": 2.0,
    "dovish": 1.5,
    "easing": 1.5,
    "inflation": 1.0,
    "safe haven": 2.0,
    "flight to safety": 2.0,
    "gold rally": 2.5,
    "bullion demand": 1.5,
    "central bank buying": 2.0,
    "de-dollarization": 1.5,
    "recession": 1.0,   # bullish for gold
    "crisis": 1.0,      # bullish for gold
    "geopolitical risk": 1.5,
    "war": 0.5,          # mildly bullish for gold

    # Bearish gold terms
    "rate hike": -2.0,
    "hawkish": -1.5,
    "tightening": -1.5,
    "strong dollar": -1.5,
    "dollar strength": -1.5,
    "risk on": -1.0,
    "gold selloff": -2.5,
    "gold crash": -3.0,
    "deflation": -1.0,
    "tapering": -1.5,
}


def _get_analyzer():
    """Lazy-init VADER analyzer with custom financial lexicon."""
    global _analyzer
    if _analyzer is not None:
        return _analyzer

    try:
        import nltk
        try:
            nltk.data.find("sentiment/vader_lexicon.zip")
        except LookupError:
            nltk.download("vader_lexicon", quiet=True)

        from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
        _analyzer = SentimentIntensityAnalyzer()

        # Augment with financial terms
        for term, score in FINANCIAL_LEXICON.items():
            _analyzer.lexicon[term] = score

        return _analyzer
    except Exception as e:
        logger.error("VADER init failed: %s", e)
        return None


def analyze_sentiment(text: str) -> Optional[float]:
    """Analyze sentiment of a single text.

    Returns compound score from -1 (most negative) to +1 (most positive).
    """
    analyzer = _get_analyzer()
    if analyzer is None:
        return None
    try:
        scores = analyzer.polarity_scores(text)
        return scores["compound"]
    except Exception as e:
        logger.error("Sentiment analysis error: %s", e)
        return None


def analyze_sentiment_batch(texts: List[str]) -> Optional[float]:
    """Analyze sentiment of multiple texts, return average compound score.

    Returns average compound score from -1 to +1.
    """
    if not texts:
        return None

    analyzer = _get_analyzer()
    if analyzer is None:
        return None

    scores = []
    for text in texts:
        try:
            result = analyzer.polarity_scores(text)
            scores.append(result["compound"])
        except Exception:
            continue

    if not scores:
        return None
    return sum(scores) / len(scores)
