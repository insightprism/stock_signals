"""Google Trends collector via pytrends."""

import logging
import time
from datetime import date, timedelta
from typing import Dict, List, Optional

from collectors.base import BaseCollector

logger = logging.getLogger(__name__)


class GoogleTrendsCollector(BaseCollector):
    name = "google_trends"

    def __init__(self):
        super().__init__()
        self._pytrends = None

    def _get_pytrends(self):
        """Lazy-init pytrends."""
        if self._pytrends is not None:
            return self._pytrends
        try:
            from pytrends.request import TrendReq
            self._pytrends = TrendReq(hl="en-US", tz=360)
            return self._pytrends
        except Exception as e:
            logger.error("pytrends init failed: %s", e)
            return None

    def _fetch_interest(self, keywords: List[str],
                         timeframe: str = "now 7-d") -> Optional[float]:
        """Fetch average search interest for keywords.

        Returns 0-100 where 100 = peak popularity.
        """
        pt = self._get_pytrends()
        if pt is None:
            return None
        try:
            # pytrends accepts max 5 keywords per request
            kw_batch = keywords[:5]
            pt.build_payload(kw_batch, cat=0, timeframe=timeframe, geo="US")
            df = pt.interest_over_time()
            if df.empty:
                return None
            # Average across keywords and time
            cols = [c for c in df.columns if c != "isPartial"]
            if not cols:
                return None
            avg = df[cols].mean().mean()
            return float(avg)
        except Exception as e:
            logger.error("pytrends fetch failed for %s: %s", keywords, e)
            return None

    def collect(self, target_date: date, asset_config: dict,
                drivers: Optional[List[str]] = None
                ) -> Dict[str, List[dict]]:
        results: Dict[str, List[dict]] = {}
        trends_queries = asset_config.get("trends_queries", {})

        for driver, keywords in trends_queries.items():
            if drivers and driver not in drivers:
                continue

            interest = self._fetch_interest(keywords)
            if interest is not None:
                results[driver] = [{
                    "source": "google_trends",
                    "series_name": f"{driver}_search_interest",
                    "raw_value": interest,
                    "metadata": {
                        "keywords": keywords,
                        "invert": False,
                    },
                }]
                logger.info("Google Trends %s: interest=%.1f", driver, interest)

            # Rate limit: ~10 requests per minute
            time.sleep(6)

        return results
