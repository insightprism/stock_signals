"""CFTC Commitments of Traders (COT) data collector."""

import logging
from datetime import date, timedelta
from typing import Dict, List, Optional

import pandas as pd

from collectors.base import BaseCollector
from processors.interpolator import interpolate_weekly_to_daily

logger = logging.getLogger(__name__)

# Direct CFTC CSV download for futures-only legacy reports
COT_FUTURES_URL = "https://www.cftc.gov/dea/newcot/deacom.txt"
# Historical annual files
COT_HIST_URL = "https://www.cftc.gov/files/dea/history/deacom{year}.zip"


class CotCollector(BaseCollector):
    name = "cot"

    def _parse_cot_csv(self, text: str) -> Optional[pd.DataFrame]:
        """Parse COT CSV text into a DataFrame filtered for gold."""
        try:
            from io import StringIO
            df = pd.read_csv(StringIO(text))
            # Filter for gold futures
            gold_mask = df["Market_and_Exchange_Names"].str.contains(
                "GOLD", case=False, na=False
            )
            gold_df = df[gold_mask].copy()
            if gold_df.empty:
                return None
            return gold_df
        except Exception as e:
            logger.error("COT CSV parse error: %s", e)
            return None

    def _compute_net_speculative(self, row: pd.Series) -> float:
        """Compute net speculative position (longs - shorts) for managed money."""
        # Legacy report columns
        long_col = None
        short_col = None
        for col in row.index:
            cl = col.lower().strip()
            if "noncommercial" in cl and "long" in cl and "spread" not in cl:
                long_col = col
            elif "noncommercial" in cl and "short" in cl and "spread" not in cl:
                short_col = col

        if long_col and short_col:
            return float(row[long_col]) - float(row[short_col])
        logger.warning("Could not find noncommercial long/short columns")
        return 0.0

    def _fetch_current_report(self) -> Optional[pd.DataFrame]:
        """Fetch the current weekly COT report."""
        try:
            resp = self._request(COT_FUTURES_URL)
            return self._parse_cot_csv(resp.text)
        except Exception as e:
            logger.error("COT current report fetch failed: %s", e)
            return None

    def _try_cot_reports_library(self, target_date: date) -> Optional[pd.DataFrame]:
        """Try using the cot-reports library as fallback."""
        try:
            import cot_reports as cot
            df = cot.cot_year(year=target_date.year, cot_report_type="legacy_fut")
            gold_mask = df["Market and Exchange Names"].str.contains(
                "GOLD", case=False, na=False
            )
            return df[gold_mask].copy() if gold_mask.any() else None
        except ImportError:
            logger.info("cot-reports library not available")
            return None
        except Exception as e:
            logger.error("cot-reports library failed: %s", e)
            return None

    def fetch_history(self, lookback_days: int = 365) -> Optional[pd.DataFrame]:
        """Fetch historical COT data for gold and compute net speculative positions."""
        df = self._try_cot_reports_library(date.today())
        if df is None:
            df = self._fetch_current_report()
        if df is None:
            return None

        # Find the date column
        date_col = None
        for col in df.columns:
            if "date" in col.lower():
                date_col = col
                break
        if date_col is None:
            return None

        records = []
        for _, row in df.iterrows():
            net = self._compute_net_speculative(row)
            records.append({"date": row[date_col], "value": net})

        if not records:
            return None

        result = pd.DataFrame(records)
        result["date"] = pd.to_datetime(result["date"])
        result = result.sort_values("date").drop_duplicates(subset=["date"])

        # Interpolate to daily
        if len(result) > 1:
            result = interpolate_weekly_to_daily(result, method="ffill")

        return result

    def collect(self, target_date: date, drivers: Optional[List[str]] = None
                ) -> Dict[str, List[dict]]:
        results: Dict[str, List[dict]] = {}

        if drivers and "spec_positioning" not in drivers:
            return results

        # Try library first, fall back to direct download
        gold_df = self._try_cot_reports_library(target_date)
        if gold_df is None:
            gold_df = self._fetch_current_report()

        if gold_df is None or gold_df.empty:
            logger.warning("No COT data available")
            return results

        # Get the most recent report row
        date_col = None
        for col in gold_df.columns:
            if "date" in col.lower():
                date_col = col
                break

        if date_col:
            gold_df[date_col] = pd.to_datetime(gold_df[date_col])
            gold_df = gold_df.sort_values(date_col, ascending=False)

        latest = gold_df.iloc[0]
        net_spec = self._compute_net_speculative(latest)

        report_date = str(latest[date_col].date()) if date_col else target_date.isoformat()

        results["spec_positioning"] = [{
            "source": "cftc_cot",
            "series_name": "net_noncommercial",
            "raw_value": net_spec,
            "metadata": {
                "report_date": report_date,
                "invert": False,
            },
        }]

        logger.info("COT net speculative (gold): %.0f as of %s",
                     net_spec, report_date)

        return results
