"""GDELT news tone collector — driver-specific keyword queries."""

import logging
from datetime import date
from typing import Dict, List, Optional

from collectors.base import BaseCollector
from config.settings import GDELT_BASE_URL, GDELT_TIMESPAN

logger = logging.getLogger(__name__)


class GdeltCollector(BaseCollector):
    name = "gdelt"

    def _query_tone(self, keywords: List[str], timespan: str = GDELT_TIMESPAN
                     ) -> Optional[float]:
        """Query GDELT for average tone on a set of keywords.

        Returns the average tone score (roughly -10 to +10 scale).
        """
        query = " OR ".join(f'"{kw}"' for kw in keywords[:5])  # GDELT limits query length
        params = {
            "query": query,
            "mode": "tonechart",
            "timespan": timespan,
            "format": "json",
        }
        try:
            resp = self._request(GDELT_BASE_URL, params=params)
            data = resp.json()
            if not data:
                return None
            # tonechart returns list of {date, tone} or similar structure
            if isinstance(data, list):
                tones = [item.get("tone", 0) for item in data
                         if isinstance(item, dict) and "tone" in item]
                if tones:
                    return sum(tones) / len(tones)
            elif isinstance(data, dict):
                # Alternative response format
                if "tonechart" in data:
                    entries = data["tonechart"]
                    tones = [e.get("tone", 0) for e in entries if "tone" in e]
                    if tones:
                        return sum(tones) / len(tones)
            return None
        except Exception as e:
            logger.error("GDELT tone query failed for '%s': %s",
                         query[:50], e)
            return None

    def _query_article_count(self, keywords: List[str],
                              timespan: str = GDELT_TIMESPAN) -> Optional[int]:
        """Query GDELT for article volume on keywords."""
        query = " OR ".join(f'"{kw}"' for kw in keywords[:5])
        params = {
            "query": query,
            "mode": "artlist",
            "timespan": timespan,
            "format": "json",
            "maxrecords": "1",
        }
        try:
            resp = self._request(GDELT_BASE_URL, params=params)
            data = resp.json()
            if isinstance(data, dict):
                return data.get("totalresults", 0)
            return None
        except Exception as e:
            logger.error("GDELT article count failed: %s", e)
            return None

    def collect(self, target_date: date, asset_config: dict,
                drivers: Optional[List[str]] = None
                ) -> Dict[str, List[dict]]:
        results: Dict[str, List[dict]] = {}
        all_keywords = asset_config.get("keywords", {})

        for driver, keywords in all_keywords.items():
            if drivers and driver not in drivers:
                continue
            # Skip positioning — not a text-based signal
            if driver == "spec_positioning":
                continue

            tone = self._query_tone(keywords)
            if tone is not None:
                signals = [{
                    "source": "gdelt",
                    "series_name": f"{driver}_tone",
                    "raw_value": tone,
                    "metadata": {
                        "keywords": keywords[:5],
                        "timespan": GDELT_TIMESPAN,
                        "invert": False,
                    },
                }]

                # Also get article volume as a secondary signal
                count = self._query_article_count(keywords)
                if count is not None:
                    signals.append({
                        "source": "gdelt",
                        "series_name": f"{driver}_volume",
                        "raw_value": float(count),
                        "metadata": {
                            "keywords": keywords[:5],
                            "invert": False,
                        },
                    })

                results[driver] = signals
                logger.info("GDELT %s: tone=%.2f, articles=%s",
                            driver, tone, count)

        return results
