"""Market data collector via yfinance (DXY, VIX, GVZ, GLD, equity indices)."""

import logging
from datetime import date, timedelta
from typing import Dict, List, Optional

import pandas as pd
import yfinance as yf

from collectors.base import BaseCollector
from config.drivers import GOLD_FUTURES_TICKER, YFINANCE_TICKERS

logger = logging.getLogger(__name__)


class MarketCollector(BaseCollector):
    name = "market"

    def _fetch_ticker(self, symbol: str, start_date: date,
                       end_date: date) -> Optional[pd.DataFrame]:
        """Fetch OHLCV data for a single ticker."""
        try:
            ticker = yf.Ticker(symbol)
            df = ticker.history(
                start=start_date.isoformat(),
                end=(end_date + timedelta(days=1)).isoformat(),
            )
            if df.empty:
                logger.warning("No data for %s", symbol)
                return None
            return df
        except Exception as e:
            logger.error("yfinance %s failed: %s", symbol, e)
            return None

    def fetch_history(self, symbol: str,
                       lookback_days: int = 365) -> Optional[pd.DataFrame]:
        """Fetch historical data for normalization."""
        end = date.today()
        start = end - timedelta(days=lookback_days)
        return self._fetch_ticker(symbol, start, end)

    def collect(self, target_date: date, drivers: Optional[List[str]] = None
                ) -> Dict[str, List[dict]]:
        results: Dict[str, List[dict]] = {}
        start = target_date - timedelta(days=7)

        for driver, ticker_map in YFINANCE_TICKERS.items():
            if drivers and driver not in drivers:
                continue
            signals = []
            for symbol, info in ticker_map.items():
                df = self._fetch_ticker(symbol, start, target_date)
                if df is not None and not df.empty:
                    latest = df.iloc[-1]
                    use_volume = info.get("use_volume", False)

                    if use_volume:
                        # Volume-based signal
                        raw_value = float(latest.get("Volume", 0))
                        series_suffix = "_volume"
                    else:
                        raw_value = float(latest["Close"])
                        series_suffix = "_close"

                    signals.append({
                        "source": "yfinance",
                        "series_name": f"{symbol}{series_suffix}",
                        "raw_value": raw_value,
                        "metadata": {
                            "name": info["name"],
                            "invert": info["invert"],
                            "use_volume": use_volume,
                            "obs_date": str(df.index[-1].date()),
                        },
                    })
                    logger.info("yfinance %s (%s): %.2f on %s",
                                symbol, info["name"], raw_value,
                                df.index[-1].date())

                    # For ETFs, also capture price for flow analysis
                    if use_volume:
                        signals.append({
                            "source": "yfinance",
                            "series_name": f"{symbol}_close",
                            "raw_value": float(latest["Close"]),
                            "metadata": {
                                "name": f"{info['name']} Price",
                                "invert": False,
                                "obs_date": str(df.index[-1].date()),
                            },
                        })

            if signals:
                results[driver] = signals

        return results

    def get_gold_price(self, target_date: date) -> Optional[float]:
        """Get gold futures closing price for the given date."""
        df = self._fetch_ticker(GOLD_FUTURES_TICKER,
                                 target_date - timedelta(days=7),
                                 target_date)
        if df is not None and not df.empty:
            return float(df.iloc[-1]["Close"])
        return None

    def get_gold_return(self, target_date: date, days: int = 1) -> Optional[float]:
        """Get gold return over the specified number of days."""
        start = target_date - timedelta(days=days + 10)
        df = self._fetch_ticker(GOLD_FUTURES_TICKER, start, target_date)
        if df is not None and len(df) >= 2:
            return float((df.iloc[-1]["Close"] / df.iloc[-2]["Close"]) - 1)
        return None
