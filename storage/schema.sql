CREATE TABLE IF NOT EXISTS raw_signals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL,
    asset TEXT NOT NULL DEFAULT 'gold',
    driver TEXT NOT NULL,
    layer TEXT NOT NULL CHECK (layer IN ('sentiment', 'macro')),
    source TEXT NOT NULL,
    series_name TEXT,
    raw_value REAL,
    normalized_value REAL,
    metadata TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    UNIQUE(date, asset, driver, layer, source, series_name)
);

CREATE TABLE IF NOT EXISTS driver_scores (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL,
    asset TEXT NOT NULL DEFAULT 'gold',
    driver TEXT NOT NULL,
    sentiment_score REAL,
    macro_score REAL,
    created_at TEXT DEFAULT (datetime('now')),
    UNIQUE(date, asset, driver)
);

CREATE TABLE IF NOT EXISTS layer_scores (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL,
    asset TEXT NOT NULL DEFAULT 'gold',
    sentiment_layer_score REAL,
    macro_layer_score REAL,
    created_at TEXT DEFAULT (datetime('now')),
    UNIQUE(date, asset)
);

CREATE TABLE IF NOT EXISTS daily_composite (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL,
    asset TEXT NOT NULL DEFAULT 'gold',
    composite_score REAL NOT NULL,
    label TEXT,
    sentiment_layer REAL,
    macro_layer REAL,
    driver_breakdown TEXT,
    asset_price REAL,
    asset_return REAL,
    created_at TEXT DEFAULT (datetime('now')),
    UNIQUE(date, asset)
);

CREATE INDEX IF NOT EXISTS idx_raw_signals_date ON raw_signals(date);
CREATE INDEX IF NOT EXISTS idx_raw_signals_asset ON raw_signals(asset);
CREATE INDEX IF NOT EXISTS idx_raw_signals_driver ON raw_signals(driver, layer);
CREATE INDEX IF NOT EXISTS idx_driver_scores_date ON driver_scores(date);
CREATE INDEX IF NOT EXISTS idx_driver_scores_asset ON driver_scores(asset);
CREATE INDEX IF NOT EXISTS idx_daily_composite_date ON daily_composite(date);
CREATE INDEX IF NOT EXISTS idx_daily_composite_asset ON daily_composite(asset);
