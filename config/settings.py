import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# --- Paths ---
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
DATA_DIR.mkdir(exist_ok=True)
DB_PATH = os.getenv("DB_PATH", str(DATA_DIR / "gold_sentiment.db"))
ASSETS_DIR = PROJECT_ROOT / "config" / "assets"

# --- API Keys ---
FRED_API_KEY = os.getenv("FRED_API_KEY", "")
ALPHA_VANTAGE_API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY", "")
REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID", "")
REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET", "")
REDDIT_USER_AGENT = os.getenv("REDDIT_USER_AGENT", "gold_sentiment_bot/1.0")

# --- Driver Weights (within each layer) ---
DRIVER_WEIGHTS = {
    "monetary_policy":   0.25,
    "us_dollar":         0.15,
    "inflation_expect":  0.15,
    "geopolitical_risk": 0.15,
    "investment_demand": 0.10,
    "spec_positioning":  0.10,
    "risk_appetite":     0.10,
}

# --- Layer Blend Weights ---
LAYER_WEIGHTS = {
    "sentiment": 0.40,
    "macro":     0.60,
}

# --- Normalization ---
ROLLING_WINDOW = 252  # trading days for percentile normalization
ZSCORE_WINDOW = 63    # ~3 months for z-score normalization

# --- Collector Settings ---
REQUEST_TIMEOUT = 30          # seconds
MAX_RETRIES = 3
RETRY_BACKOFF_FACTOR = 2.0

# --- Reddit ---
REDDIT_SUBREDDITS = ["Gold", "Silverbugs", "WallStreetBets", "investing", "economy"]
REDDIT_POST_LIMIT = 100

# --- GDELT ---
GDELT_BASE_URL = "https://api.gdeltproject.org/api/v2/doc/doc"
GDELT_TIMESPAN = "24h"

# --- Alpha Vantage ---
AV_BASE_URL = "https://www.alphavantage.co/query"
