"""Historical replay backtester for the gold sentiment index."""

import logging
from datetime import date, timedelta
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

from config.settings import DATA_DIR, DB_PATH
from storage.db import get_daily_composites

logger = logging.getLogger(__name__)


class Backtester:
    """Simple backtester that tests a signal-based strategy on gold.

    Strategy: Go long gold when composite > upper_threshold,
              go flat (or short) when composite < lower_threshold.
    """

    def __init__(self, upper_threshold: float = 60.0,
                  lower_threshold: float = 40.0,
                  allow_short: bool = False):
        self.upper_threshold = upper_threshold
        self.lower_threshold = lower_threshold
        self.allow_short = allow_short

    def run(self, db_path: str = DB_PATH) -> Optional[pd.DataFrame]:
        """Run backtest on historical data.

        Returns DataFrame with daily P&L and cumulative returns.
        """
        df = get_daily_composites(db_path)
        if df.empty or len(df) < 5:
            logger.warning("Not enough data for backtesting")
            return None

        df = df.sort_values("date").reset_index(drop=True)
        df["gold_price"] = pd.to_numeric(df["gold_price"], errors="coerce")
        df["composite_score"] = pd.to_numeric(df["composite_score"], errors="coerce")
        df["gold_return"] = df["gold_price"].pct_change()

        # Generate position signal
        positions = []
        pos = 0  # 0 = flat, 1 = long, -1 = short
        for _, row in df.iterrows():
            score = row["composite_score"]
            if pd.isna(score):
                positions.append(pos)
                continue
            if score >= self.upper_threshold:
                pos = 1
            elif score <= self.lower_threshold:
                pos = -1 if self.allow_short else 0
            positions.append(pos)

        df["position"] = positions
        # Strategy return = position * next day's gold return
        df["strategy_return"] = df["position"].shift(1) * df["gold_return"]
        df["cumulative_gold"] = (1 + df["gold_return"].fillna(0)).cumprod()
        df["cumulative_strategy"] = (1 + df["strategy_return"].fillna(0)).cumprod()

        return df

    def summary(self, results: pd.DataFrame) -> Dict:
        """Compute backtest summary statistics."""
        if results is None or results.empty:
            return {}

        strat = results["strategy_return"].dropna()
        gold = results["gold_return"].dropna()

        def _sharpe(returns: pd.Series, ann_factor: float = 252) -> float:
            if returns.std() == 0:
                return 0.0
            return float(returns.mean() / returns.std() * np.sqrt(ann_factor))

        def _max_drawdown(cum_returns: pd.Series) -> float:
            peak = cum_returns.cummax()
            dd = (cum_returns - peak) / peak
            return float(dd.min())

        stats = {
            "total_days": len(results),
            "strategy_return_total": float(results["cumulative_strategy"].iloc[-1] - 1),
            "gold_return_total": float(results["cumulative_gold"].iloc[-1] - 1),
            "strategy_sharpe": _sharpe(strat),
            "gold_sharpe": _sharpe(gold),
            "strategy_max_dd": _max_drawdown(results["cumulative_strategy"]),
            "gold_max_dd": _max_drawdown(results["cumulative_gold"]),
            "long_days": int((results["position"] == 1).sum()),
            "flat_days": int((results["position"] == 0).sum()),
            "short_days": int((results["position"] == -1).sum()),
            "strategy_hit_rate": float((strat > 0).mean()) if len(strat) > 0 else 0,
        }

        return stats

    def print_report(self, db_path: str = DB_PATH):
        """Run backtest and print formatted report."""
        results = self.run(db_path)
        if results is None:
            print("Not enough data for backtesting.")
            return

        stats = self.summary(results)

        print("\n" + "=" * 50)
        print("  BACKTEST REPORT")
        print(f"  Thresholds: Long > {self.upper_threshold}, "
              f"{'Short' if self.allow_short else 'Flat'} < {self.lower_threshold}")
        print("=" * 50)
        print(f"  Total Days:           {stats['total_days']}")
        print(f"  Long / Flat / Short:  {stats['long_days']} / "
              f"{stats['flat_days']} / {stats['short_days']}")
        print(f"\n  {'Metric':<25} {'Strategy':>12} {'Buy & Hold':>12}")
        print(f"  {'-'*25} {'-'*12} {'-'*12}")
        print(f"  {'Total Return':<25} "
              f"{stats['strategy_return_total']:>11.2%} "
              f"{stats['gold_return_total']:>11.2%}")
        print(f"  {'Sharpe Ratio':<25} "
              f"{stats['strategy_sharpe']:>12.2f} "
              f"{stats['gold_sharpe']:>12.2f}")
        print(f"  {'Max Drawdown':<25} "
              f"{stats['strategy_max_dd']:>11.2%} "
              f"{stats['gold_max_dd']:>11.2%}")
        print(f"  {'Hit Rate':<25} "
              f"{stats['strategy_hit_rate']:>11.1%}")
        print("=" * 50)

        # Save results to CSV
        csv_path = DATA_DIR / "backtest_results.csv"
        results.to_csv(csv_path, index=False)
        logger.info("Backtest results saved to %s", csv_path)
