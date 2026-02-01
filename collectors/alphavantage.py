"""Alpha Vantage news sentiment collector."""

import logging
from datetime import date
from typing import Dict, List, Optional

from collectors.base import BaseCollector
from config.settings import ALPHA_VANTAGE_API_KEY, AV_BASE_URL

logger = logging.getLogger(__name__)


class AlphaVantageCollector(BaseCollector):
    name = "alphavantage"

    def __init__(self):
        super().__init__()
        if not ALPHA_VANTAGE_API_KEY:
            logger.warning("ALPHA_VANTAGE_API_KEY not set — collector unavailable")

    def _fetch_news_sentiment(self, keywords: List[str],
                                topics: Optional[str] = None
                                ) -> Optional[List[dict]]:
        """Fetch news sentiment from Alpha Vantage."""
        if not ALPHA_VANTAGE_API_KEY:
            return None

        params = {
            "function": "NEWS_SENTIMENT",
            "apikey": ALPHA_VANTAGE_API_KEY,
        }
        if topics:
            params["topics"] = topics

        # Use tickers param for asset-specific queries
        if self._av_ticker:
            params["tickers"] = self._av_ticker

        try:
            resp = self._request(AV_BASE_URL, params=params)
            data = resp.json()
            if "feed" not in data:
                logger.warning("AV response has no 'feed': %s",
                               list(data.keys()))
                return None
            return data["feed"]
        except Exception as e:
            logger.error("Alpha Vantage fetch failed: %s", e)
            return None

    def _compute_keyword_sentiment(self, articles: List[dict],
                                     keywords: List[str]) -> Optional[float]:
        """Compute average sentiment for articles matching keywords."""
        matching_sentiments = []
        kw_lower = [k.lower() for k in keywords]

        for article in articles:
            title = article.get("title", "").lower()
            summary = article.get("summary", "").lower()
            text = f"{title} {summary}"

            # Check if any keyword matches
            if any(kw in text for kw in kw_lower):
                score = float(article.get("overall_sentiment_score", 0))
                matching_sentiments.append(score)

        if not matching_sentiments:
            return None
        return sum(matching_sentiments) / len(matching_sentiments)

    # Map drivers to Alpha Vantage topic filters
    _TOPIC_MAP = {
        "monetary_policy": "economy_monetary",
        "inflation_expect": "economy_macro",
        "risk_appetite": "finance",
        "investment_demand": "finance",
    }

    def collect(self, target_date: date, asset_config: dict,
                drivers: Optional[List[str]] = None
                ) -> Dict[str, List[dict]]:
        results: Dict[str, List[dict]] = {}

        if not ALPHA_VANTAGE_API_KEY:
            return results

        self._av_ticker = asset_config.get("alphavantage_ticker", "FOREX:XAU")
        articles = self._fetch_news_sentiment([], topics="finance")
        if not articles:
            return results

        all_keywords = asset_config.get("keywords", {})
        for driver, keywords in all_keywords.items():
            if drivers and driver not in drivers:
                continue
            if driver == "spec_positioning":
                continue

            avg_sentiment = self._compute_keyword_sentiment(articles, keywords)
            if avg_sentiment is not None:
                results[driver] = [{
                    "source": "alphavantage",
                    "series_name": f"{driver}_news_sentiment",
                    "raw_value": avg_sentiment,
                    "metadata": {
                        "matched_articles": len([
                            a for a in articles
                            if any(k.lower() in
                                   f"{a.get('title', '')} {a.get('summary', '')}".lower()
                                   for k in keywords)
                        ]),
                        "invert": False,
                    },
                }]
                logger.info("AV %s: sentiment=%.3f", driver, avg_sentiment)

        return results
