"""Matplotlib dashboard charts for gold sentiment index."""

import json
import logging
from pathlib import Path
from typing import Optional

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
import pandas as pd

from config.drivers import DRIVER_NAMES
from config.settings import DATA_DIR

logger = logging.getLogger(__name__)

# Color scheme
COLORS = {
    "composite": "#FFD700",
    "sentiment": "#4ECDC4",
    "macro": "#FF6B6B",
    "gold_price": "#B8860B",
    "bullish": "#2ECC71",
    "bearish": "#E74C3C",
    "neutral": "#95A5A6",
}

DRIVER_COLORS = [
    "#E74C3C", "#3498DB", "#2ECC71", "#F39C12",
    "#9B59B6", "#1ABC9C", "#E67E22",
]


def plot_composite_history(df: pd.DataFrame,
                            output_path: Optional[str] = None):
    """Plot composite score over time with gold price overlay.

    Args:
        df: DataFrame from daily_composite table
        output_path: Path to save the figure; if None, shows interactively
    """
    if df.empty:
        logger.warning("No data to plot")
        return

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 8),
                                     gridspec_kw={"height_ratios": [3, 1]},
                                     sharex=True)
    fig.suptitle("Daily Gold Sentiment Index", fontsize=16, fontweight="bold")

    dates = pd.to_datetime(df["date"])

    # --- Top panel: Composite score + layers ---
    ax1.fill_between(dates, 0, 100, alpha=0.05, color="gray")
    ax1.axhspan(0, 35, alpha=0.08, color=COLORS["bearish"])
    ax1.axhspan(65, 100, alpha=0.08, color=COLORS["bullish"])
    ax1.axhline(50, color="gray", linewidth=0.5, linestyle="--", alpha=0.5)

    ax1.plot(dates, df["composite_score"], color=COLORS["composite"],
             linewidth=2.5, label="Composite", zorder=5)

    if "sentiment_layer" in df.columns:
        sent = df["sentiment_layer"]
        if sent.notna().any():
            ax1.plot(dates, sent, color=COLORS["sentiment"],
                     linewidth=1, alpha=0.7, label="Sentiment Layer")

    if "macro_layer" in df.columns:
        macro = df["macro_layer"]
        if macro.notna().any():
            ax1.plot(dates, macro, color=COLORS["macro"],
                     linewidth=1, alpha=0.7, label="Macro Layer")

    ax1.set_ylabel("Score (0-100)")
    ax1.set_ylim(-2, 102)
    ax1.legend(loc="upper left", framealpha=0.9)
    ax1.grid(axis="y", alpha=0.3)

    # Gold price on secondary axis
    if "gold_price" in df.columns and df["gold_price"].notna().any():
        ax1b = ax1.twinx()
        ax1b.plot(dates, df["gold_price"], color=COLORS["gold_price"],
                  linewidth=1.5, linestyle="--", alpha=0.6, label="Gold Price")
        ax1b.set_ylabel("Gold Price ($)", color=COLORS["gold_price"])
        ax1b.tick_params(axis="y", labelcolor=COLORS["gold_price"])
        ax1b.legend(loc="upper right", framealpha=0.9)

    # --- Bottom panel: Driver breakdown heatmap (latest day) ---
    if "driver_breakdown" in df.columns:
        try:
            latest = df.iloc[-1]
            breakdown = json.loads(latest["driver_breakdown"]) if isinstance(
                latest["driver_breakdown"], str) else latest["driver_breakdown"]

            driver_labels = {
                "monetary_policy": "Monetary\nPolicy",
                "us_dollar": "USD",
                "inflation_expect": "Inflation",
                "geopolitical_risk": "Geopolitical",
                "investment_demand": "Investment\nDemand",
                "spec_positioning": "Spec.\nPositioning",
                "risk_appetite": "Risk\nAppetite",
            }

            names = []
            sent_scores = []
            macro_scores = []
            for d in DRIVER_NAMES:
                if d in breakdown:
                    names.append(driver_labels.get(d, d))
                    info = breakdown[d]
                    sent_scores.append(info.get("sentiment", 50))
                    macro_scores.append(info.get("macro", 50))

            if names:
                x = np.arange(len(names))
                width = 0.35
                ax2.bar(x - width/2, sent_scores, width,
                        label="Sentiment", color=COLORS["sentiment"], alpha=0.8)
                ax2.bar(x + width/2, macro_scores, width,
                        label="Macro", color=COLORS["macro"], alpha=0.8)
                ax2.set_xticks(x)
                ax2.set_xticklabels(names, fontsize=8)
                ax2.set_ylabel("Score")
                ax2.set_ylim(0, 100)
                ax2.axhline(50, color="gray", linewidth=0.5, linestyle="--")
                ax2.legend(loc="upper right", fontsize=8)
                ax2.set_title("Driver Breakdown (Latest)", fontsize=10)
        except Exception as e:
            logger.warning("Could not parse driver breakdown: %s", e)
            ax2.text(0.5, 0.5, "No driver breakdown available",
                     ha="center", va="center", transform=ax2.transAxes)

    ax2.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
    fig.autofmt_xdate()
    plt.tight_layout()

    if output_path:
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(output_path, dpi=150, bbox_inches="tight")
        logger.info("Dashboard saved to %s", output_path)
        plt.close(fig)
    else:
        plt.show()


def plot_driver_history(raw_signals_df: pd.DataFrame,
                         driver: str,
                         output_path: Optional[str] = None):
    """Plot raw and normalized signals for a single driver over time."""
    if raw_signals_df.empty:
        return

    df = raw_signals_df[raw_signals_df["driver"] == driver].copy()
    if df.empty:
        logger.warning("No signals for driver %s", driver)
        return

    df["date"] = pd.to_datetime(df["date"])
    series_names = df["series_name"].unique()

    fig, axes = plt.subplots(len(series_names), 1,
                              figsize=(12, 3 * len(series_names)),
                              sharex=True)
    if len(series_names) == 1:
        axes = [axes]

    fig.suptitle(f"Driver: {driver}", fontsize=14, fontweight="bold")

    for ax, sn in zip(axes, series_names):
        sub = df[df["series_name"] == sn].sort_values("date")
        ax.plot(sub["date"], sub["normalized_value"], linewidth=1.5)
        ax.set_ylabel(sn, fontsize=9)
        ax.set_ylim(-5, 105)
        ax.axhline(50, color="gray", linewidth=0.5, linestyle="--")
        ax.grid(alpha=0.3)

    axes[-1].xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
    fig.autofmt_xdate()
    plt.tight_layout()

    if output_path:
        fig.savefig(output_path, dpi=150, bbox_inches="tight")
        plt.close(fig)
    else:
        plt.show()
