"""Driver-to-keyword and driver-to-ticker mappings for gold sentiment analysis."""

# Keywords used by sentiment collectors (GDELT, Alpha Vantage, Reddit, Google Trends)
DRIVER_KEYWORDS = {
    "monetary_policy": [
        "federal reserve", "interest rate", "rate cut", "rate hike",
        "FOMC", "Powell", "monetary policy", "treasury yield",
        "real rates", "TIPS yield",
    ],
    "us_dollar": [
        "US dollar", "dollar index", "DXY", "dollar strength",
        "dollar weakness", "greenback", "forex USD",
    ],
    "inflation_expect": [
        "inflation", "CPI", "consumer prices", "cost of living",
        "inflation expectations", "breakeven inflation", "PCE",
    ],
    "geopolitical_risk": [
        "war", "sanctions", "geopolitical", "conflict", "trade war",
        "military", "nuclear", "invasion", "Middle East crisis",
    ],
    "investment_demand": [
        "buy gold", "gold ETF", "gold investment", "gold bullion",
        "gold demand", "central bank gold", "gold reserves",
    ],
    "spec_positioning": [
        "gold futures", "COMEX gold", "gold speculative",
        "gold long", "gold short", "gold positioning",
    ],
    "risk_appetite": [
        "stock market crash", "recession", "risk off", "market fear",
        "safe haven", "flight to safety", "bear market", "market selloff",
    ],
}

# Google Trends queries (max 5 terms per request)
DRIVER_TRENDS_QUERIES = {
    "monetary_policy":   ["federal reserve rate", "interest rate cut", "FOMC meeting"],
    "us_dollar":         ["US dollar index", "dollar strength"],
    "inflation_expect":  ["inflation rate", "CPI report", "cost of living"],
    "geopolitical_risk": ["geopolitical risk", "war conflict", "sanctions"],
    "investment_demand": ["buy gold", "gold price", "gold ETF"],
    "spec_positioning":  ["gold futures", "COMEX gold"],
    "risk_appetite":     ["stock market crash", "recession risk", "market fear"],
}

# FRED series for macro layer
FRED_SERIES = {
    "monetary_policy": {
        "DFII10":    {"name": "10Y TIPS Yield",        "invert": True},
        "FEDFUNDS":  {"name": "Fed Funds Rate",        "invert": True},
    },
    "inflation_expect": {
        "T10YIE":    {"name": "10Y Breakeven Inflation","invert": False},
        "T5YIFR":    {"name": "5Y5Y Forward Inflation", "invert": False},
    },
}

# yfinance tickers for macro layer
YFINANCE_TICKERS = {
    "us_dollar": {
        "DX-Y.NYB": {"name": "DXY (Dollar Index)", "invert": True},
    },
    "risk_appetite": {
        "^VIX":     {"name": "VIX",           "invert": True},
        "^GSPC":    {"name": "S&P 500",       "invert": False},
    },
    "investment_demand": {
        "GLD":      {"name": "GLD ETF",       "invert": False, "use_volume": True},
        "IAU":      {"name": "IAU ETF",       "invert": False, "use_volume": True},
        "^GVZ":     {"name": "Gold Volatility","invert": False},
    },
}

# CFTC COT report settings
COT_SETTINGS = {
    "spec_positioning": {
        "commodity": "GOLD",
        "report_type": "legacy_fut",
        "measure": "net_managed_money",  # long - short
        "invert": False,  # more longs = more bullish
    },
}

# Gold reference ticker
GOLD_FUTURES_TICKER = "GC=F"
GOLD_ETF_TICKER = "GLD"

# All driver names in canonical order
DRIVER_NAMES = [
    "monetary_policy",
    "us_dollar",
    "inflation_expect",
    "geopolitical_risk",
    "investment_demand",
    "spec_positioning",
    "risk_appetite",
]
