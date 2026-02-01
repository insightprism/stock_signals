"""Daily text summary report."""

import json
import logging
from datetime import date
from typing import Dict, Optional

from config.drivers import DRIVER_NAMES

logger = logging.getLogger(__name__)


def generate_daily_report(
    target_date: date,
    composite: Dict,
    sentiment_drivers: Dict[str, float],
    macro_drivers: Dict[str, float],
    gold_price: Optional[float] = None,
    gold_return: Optional[float] = None,
) -> str:
    """Generate a formatted daily report string."""

    lines = []
    lines.append("=" * 60)
    lines.append(f"  DAILY GOLD SENTIMENT INDEX — {target_date.isoformat()}")
    lines.append("=" * 60)
    lines.append("")

    # Composite score
    score = composite["composite_score"]
    label = composite["label"]
    bar = _score_bar(score)
    lines.append(f"  COMPOSITE SCORE:  {score:.1f} / 100  [{label}]")
    lines.append(f"  {bar}")
    lines.append("")

    # Gold price
    if gold_price is not None:
        ret_str = ""
        if gold_return is not None:
            ret_str = f"  ({gold_return:+.2%} daily)"
        lines.append(f"  Gold Price: ${gold_price:,.2f}{ret_str}")
        lines.append("")

    # Layer scores
    sent = composite.get("sentiment_layer")
    macro = composite.get("macro_layer")
    lines.append("  LAYER SCORES:")
    if sent is not None:
        lines.append(f"    Sentiment Layer (40%):  {sent:.1f}")
    else:
        lines.append("    Sentiment Layer (40%):  N/A")
    if macro is not None:
        lines.append(f"    Macro Layer     (60%):  {macro:.1f}")
    else:
        lines.append("    Macro Layer     (60%):  N/A")
    lines.append("")

    # Driver breakdown
    lines.append("  DRIVER BREAKDOWN:")
    lines.append(f"  {'Driver':<25} {'Sentiment':>10} {'Macro':>10}")
    lines.append(f"  {'-'*25} {'-'*10} {'-'*10}")

    driver_labels = {
        "monetary_policy": "Monetary Policy",
        "us_dollar": "US Dollar",
        "inflation_expect": "Inflation Expect.",
        "geopolitical_risk": "Geopolitical Risk",
        "investment_demand": "Investment Demand",
        "spec_positioning": "Spec. Positioning",
        "risk_appetite": "Risk Appetite",
    }

    for driver in DRIVER_NAMES:
        name = driver_labels.get(driver, driver)
        s_val = sentiment_drivers.get(driver)
        m_val = macro_drivers.get(driver)
        s_str = f"{s_val:.1f}" if s_val is not None else "N/A"
        m_str = f"{m_val:.1f}" if m_val is not None else "N/A"
        lines.append(f"  {name:<25} {s_str:>10} {m_str:>10}")

    lines.append("")
    lines.append("  Scale: 0 = Strongly Bearish | 50 = Neutral | 100 = Strongly Bullish")
    lines.append("=" * 60)

    report = "\n".join(lines)
    return report


def _score_bar(score: float, width: int = 40) -> str:
    """Create a text-based score bar."""
    filled = int(score / 100 * width)
    bar = "█" * filled + "░" * (width - filled)
    return f"  [{bar}] {score:.0f}"
