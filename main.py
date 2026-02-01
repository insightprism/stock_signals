"""Pipeline orchestrator for the Daily Gold Sentiment Index."""

import argparse
import logging
import sys
from datetime import date, timedelta
from typing import Dict, List, Optional

import pandas as pd

from collectors.fred import FredCollector
from collectors.market import MarketCollector
from collectors.cot import CotCollector
from collectors.gdelt import GdeltCollector
from collectors.alphavantage import AlphaVantageCollector
from collectors.reddit import RedditCollector
from collectors.google_trends import GoogleTrendsCollector
from composite.driver_index import compute_all_driver_scores
from composite.layer_builder import build_both_layers, build_layer_score
from composite.composite_builder import build_composite
from config.drivers import DRIVER_NAMES
from config.settings import DATA_DIR, DB_PATH
from storage.db import (
    db_session, init_db, upsert_raw_signal, upsert_driver_score,
    upsert_layer_scores, upsert_daily_composite, get_daily_composites,
    get_raw_signals, export_to_csv,
)
from visualization.report import generate_daily_report
from visualization.dashboard import plot_composite_history

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def collect_macro_signals(target_date: date,
                           drivers: Optional[List[str]] = None
                           ) -> Dict[str, List[dict]]:
    """Collect all macro layer signals."""
    all_signals: Dict[str, List[dict]] = {}

    # FRED
    try:
        fred = FredCollector()
        fred_signals = fred.collect(target_date, drivers)
        for driver, sigs in fred_signals.items():
            all_signals.setdefault(driver, []).extend(sigs)
    except Exception as e:
        logger.error("FRED collection failed: %s", e)

    # Market data (yfinance)
    try:
        market = MarketCollector()
        market_signals = market.collect(target_date, drivers)
        for driver, sigs in market_signals.items():
            all_signals.setdefault(driver, []).extend(sigs)
    except Exception as e:
        logger.error("Market collection failed: %s", e)

    # COT
    try:
        cot = CotCollector()
        cot_signals = cot.collect(target_date, drivers)
        for driver, sigs in cot_signals.items():
            all_signals.setdefault(driver, []).extend(sigs)
    except Exception as e:
        logger.error("COT collection failed: %s", e)

    return all_signals


def collect_sentiment_signals(target_date: date,
                               drivers: Optional[List[str]] = None
                               ) -> Dict[str, List[dict]]:
    """Collect all sentiment layer signals."""
    all_signals: Dict[str, List[dict]] = {}

    # GDELT
    try:
        gdelt = GdeltCollector()
        gdelt_signals = gdelt.collect(target_date, drivers)
        for driver, sigs in gdelt_signals.items():
            all_signals.setdefault(driver, []).extend(sigs)
    except Exception as e:
        logger.error("GDELT collection failed: %s", e)

    # Alpha Vantage
    try:
        av = AlphaVantageCollector()
        av_signals = av.collect(target_date, drivers)
        for driver, sigs in av_signals.items():
            all_signals.setdefault(driver, []).extend(sigs)
    except Exception as e:
        logger.error("Alpha Vantage collection failed: %s", e)

    # Reddit
    try:
        reddit = RedditCollector()
        reddit_signals = reddit.collect(target_date, drivers)
        for driver, sigs in reddit_signals.items():
            all_signals.setdefault(driver, []).extend(sigs)
    except Exception as e:
        logger.error("Reddit collection failed: %s", e)

    # Google Trends
    try:
        gt = GoogleTrendsCollector()
        gt_signals = gt.collect(target_date, drivers)
        for driver, sigs in gt_signals.items():
            all_signals.setdefault(driver, []).extend(sigs)
    except Exception as e:
        logger.error("Google Trends collection failed: %s", e)

    return all_signals


def build_history_lookup(db_path: str = DB_PATH) -> dict:
    """Build a lookup table of historical raw values for normalization."""
    lookup = {}
    df = get_raw_signals(db_path)
    if df.empty:
        return lookup
    for (source, series_name), group in df.groupby(["source", "series_name"]):
        series = group.set_index("date")["raw_value"].sort_index()
        lookup[(source, series_name)] = series
    return lookup


def run_pipeline(target_date: date,
                  layers: str = "both",
                  skip_sentiment: bool = False,
                  skip_macro: bool = False) -> Dict:
    """Run the full pipeline for a single date.

    Args:
        target_date: Date to compute the index for
        layers: 'both', 'macro', or 'sentiment'
        skip_sentiment: Skip sentiment layer collection
        skip_macro: Skip macro layer collection

    Returns:
        Dict with composite results
    """
    logger.info("=" * 50)
    logger.info("Running pipeline for %s", target_date.isoformat())
    logger.info("=" * 50)

    # Initialize DB
    init_db()

    # Build history lookup for normalization
    history_lookup = build_history_lookup()

    macro_driver_scores = {}
    sentiment_driver_scores = {}

    # --- Macro Layer ---
    if not skip_macro and layers in ("both", "macro"):
        logger.info("--- Collecting Macro Signals ---")
        macro_signals = collect_macro_signals(target_date)

        # Store raw signals
        with db_session() as conn:
            for driver, sigs in macro_signals.items():
                for sig in sigs:
                    upsert_raw_signal(
                        conn, target_date.isoformat(), driver, "macro",
                        sig["source"], sig.get("series_name", ""),
                        sig["raw_value"], metadata=sig.get("metadata"),
                    )

        # Compute macro driver scores
        macro_driver_scores = compute_all_driver_scores(
            macro_signals, history_lookup
        )
        logger.info("Macro driver scores: %s", macro_driver_scores)

    # --- Sentiment Layer ---
    if not skip_sentiment and layers in ("both", "sentiment"):
        logger.info("--- Collecting Sentiment Signals ---")
        sentiment_signals = collect_sentiment_signals(target_date)

        # Store raw signals
        with db_session() as conn:
            for driver, sigs in sentiment_signals.items():
                for sig in sigs:
                    upsert_raw_signal(
                        conn, target_date.isoformat(), driver, "sentiment",
                        sig["source"], sig.get("series_name", ""),
                        sig["raw_value"], metadata=sig.get("metadata"),
                    )

        # Compute sentiment driver scores
        sentiment_driver_scores = compute_all_driver_scores(
            sentiment_signals, history_lookup
        )
        logger.info("Sentiment driver scores: %s", sentiment_driver_scores)

    # --- Store driver scores ---
    with db_session() as conn:
        all_drivers = set(list(macro_driver_scores.keys()) +
                          list(sentiment_driver_scores.keys()))
        for driver in all_drivers:
            upsert_driver_score(
                conn, target_date.isoformat(), driver,
                sentiment_score=sentiment_driver_scores.get(driver),
                macro_score=macro_driver_scores.get(driver),
            )

    # --- Build layer scores ---
    layer_scores = {}
    if macro_driver_scores:
        layer_scores["macro"] = build_layer_score(macro_driver_scores)
    if sentiment_driver_scores:
        layer_scores["sentiment"] = build_layer_score(sentiment_driver_scores)

    with db_session() as conn:
        upsert_layer_scores(
            conn, target_date.isoformat(),
            sentiment_layer=layer_scores.get("sentiment"),
            macro_layer=layer_scores.get("macro"),
        )

    # --- Build composite ---
    composite = build_composite(layer_scores)

    # Get gold price
    gold_price = None
    gold_return = None
    try:
        market = MarketCollector()
        gold_price = market.get_gold_price(target_date)
        gold_return = market.get_gold_return(target_date)
    except Exception as e:
        logger.warning("Could not fetch gold price: %s", e)

    # Driver breakdown for storage
    driver_breakdown = {}
    for driver in DRIVER_NAMES:
        driver_breakdown[driver] = {
            "sentiment": sentiment_driver_scores.get(driver),
            "macro": macro_driver_scores.get(driver),
        }

    with db_session() as conn:
        upsert_daily_composite(
            conn, target_date.isoformat(),
            composite["composite_score"],
            composite["label"],
            composite.get("sentiment_layer") or 0,
            composite.get("macro_layer") or 0,
            driver_breakdown,
            gold_price,
            gold_return,
        )

    # --- Generate report ---
    report = generate_daily_report(
        target_date, composite,
        sentiment_driver_scores, macro_driver_scores,
        gold_price, gold_return,
    )
    print(report)

    return {
        "date": target_date.isoformat(),
        "composite": composite,
        "sentiment_drivers": sentiment_driver_scores,
        "macro_drivers": macro_driver_scores,
        "gold_price": gold_price,
        "gold_return": gold_return,
    }


def run_backfill(start_date: date, end_date: date, **kwargs):
    """Run the pipeline for a range of dates."""
    from tqdm import tqdm

    current = start_date
    dates = []
    while current <= end_date:
        dates.append(current)
        current += timedelta(days=1)

    results = []
    for d in tqdm(dates, desc="Backfilling"):
        # Skip weekends
        if d.weekday() >= 5:
            continue
        try:
            result = run_pipeline(d, **kwargs)
            results.append(result)
        except Exception as e:
            logger.error("Pipeline failed for %s: %s", d, e)

    return results


def main():
    parser = argparse.ArgumentParser(
        description="Daily Gold Sentiment Index Pipeline"
    )
    parser.add_argument(
        "--date", type=str, default=None,
        help="Target date (YYYY-MM-DD). Default: today"
    )
    parser.add_argument(
        "--backfill-start", type=str, default=None,
        help="Start date for backfill (YYYY-MM-DD)"
    )
    parser.add_argument(
        "--backfill-end", type=str, default=None,
        help="End date for backfill (YYYY-MM-DD). Default: today"
    )
    parser.add_argument(
        "--layers", choices=["both", "macro", "sentiment"],
        default="both", help="Which layers to compute"
    )
    parser.add_argument(
        "--skip-sentiment", action="store_true",
        help="Skip sentiment layer (faster, macro only)"
    )
    parser.add_argument(
        "--skip-macro", action="store_true",
        help="Skip macro layer"
    )
    parser.add_argument(
        "--chart", action="store_true",
        help="Generate dashboard chart after pipeline run"
    )
    parser.add_argument(
        "--export-csv", action="store_true",
        help="Export all tables to CSV"
    )

    args = parser.parse_args()

    # Backfill mode
    if args.backfill_start:
        start = date.fromisoformat(args.backfill_start)
        end = date.fromisoformat(args.backfill_end) if args.backfill_end else date.today()
        run_backfill(start, end,
                     layers=args.layers,
                     skip_sentiment=args.skip_sentiment,
                     skip_macro=args.skip_macro)
    else:
        # Single date mode
        target = date.fromisoformat(args.date) if args.date else date.today()
        run_pipeline(target,
                     layers=args.layers,
                     skip_sentiment=args.skip_sentiment,
                     skip_macro=args.skip_macro)

    # Chart
    if args.chart:
        df = get_daily_composites()
        if not df.empty:
            chart_path = str(DATA_DIR / "dashboard.png")
            plot_composite_history(df, output_path=chart_path)
            print(f"\nDashboard saved to {chart_path}")

    # CSV export
    if args.export_csv:
        export_to_csv()
        print(f"\nCSV files exported to {DATA_DIR}")


if __name__ == "__main__":
    main()
