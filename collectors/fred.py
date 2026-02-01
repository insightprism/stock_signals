"""FRED API collector for macro economic data (TIPS yields, breakevens, fed funds)."""

import logging
from datetime import date, timedelta
from typing import Dict, List, Optional

import pandas as pd

from collectors.base import BaseCollector
from config.settings import FRED_API_KEY

logger = logging.getLogger(__name__)

FRED_API_URL = "https://api.stlouisfed.org/fred/series/observations"


class FredCollector(BaseCollector):
    name = "fred"

    def __init__(self):
        super().__init__()
        if not FRED_API_KEY:
            logger.warning("FRED_API_KEY not set — FRED collector will be unavailable")

    def _fetch_series(self, series_id: str, start_date: date,
                       end_date: date) -> Optional[pd.DataFrame]:
        """Fetch a single FRED series."""
        if not FRED_API_KEY:
            return None
        params = {
            "series_id": series_id,
            "api_key": FRED_API_KEY,
            "file_type": "json",
            "observation_start": start_date.isoformat(),
            "observation_end": end_date.isoformat(),
            "sort_order": "desc",
        }
        try:
            resp = self._request(FRED_API_URL, params=params)
            data = resp.json()
            obs = data.get("observations", [])
            if not obs:
                return None
            rows = []
            for o in obs:
                if o["value"] != ".":
                    rows.append({"date": o["date"], "value": float(o["value"])})
            if not rows:
                return None
            return pd.DataFrame(rows)
        except Exception as e:
            logger.error("FRED fetch %s failed: %s", series_id, e)
            return None

    def fetch_history(self, series_id: str,
                       lookback_days: int = 365) -> Optional[pd.DataFrame]:
        """Fetch historical data for normalization."""
        end = date.today()
        start = end - timedelta(days=lookback_days)
        return self._fetch_series(series_id, start, end)

    def collect(self, target_date: date, asset_config: dict,
                drivers: Optional[List[str]] = None
                ) -> Dict[str, List[dict]]:
        results: Dict[str, List[dict]] = {}
        start = target_date - timedelta(days=7)
        fred_series = asset_config.get("fred_series", {})

        for driver, series_map in fred_series.items():
            if drivers and driver not in drivers:
                continue
            signals = []
            for series_id, info in series_map.items():
                df = self._fetch_series(series_id, start, target_date)
                if df is not None and not df.empty:
                    latest = df.iloc[0]  # most recent (desc sorted)
                    signals.append({
                        "source": "fred",
                        "series_name": series_id,
                        "raw_value": latest["value"],
                        "metadata": {
                            "name": info["name"],
                            "invert": info["invert"],
                            "obs_date": latest["date"],
                        },
                    })
                    logger.info("FRED %s (%s): %.4f on %s",
                                series_id, info["name"],
                                latest["value"], latest["date"])
            if signals:
                results[driver] = signals

        return results
