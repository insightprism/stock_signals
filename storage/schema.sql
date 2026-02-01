CREATE TABLE IF NOT EXISTS raw_signals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL,
    driver TEXT NOT NULL,
    layer TEXT NOT NULL CHECK (layer IN ('sentiment', 'macro')),
    source TEXT NOT NULL,
    series_name TEXT,
    raw_value REAL,
    normalized_value REAL,
    metadata TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    UNIQUE(date, driver, layer, source, series_name)
);

CREATE TABLE IF NOT EXISTS driver_scores (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL,
    driver TEXT NOT NULL,
    sentiment_score REAL,
    macro_score REAL,
    created_at TEXT DEFAULT (datetime('now')),
    UNIQUE(date, driver)
);

CREATE TABLE IF NOT EXISTS layer_scores (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL,
    sentiment_layer_score REAL,
    macro_layer_score REAL,
    created_at TEXT DEFAULT (datetime('now')),
    UNIQUE(date)
);

CREATE TABLE IF NOT EXISTS daily_composite (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL,
    composite_score REAL NOT NULL,
    label TEXT,
    sentiment_layer REAL,
    macro_layer REAL,
    driver_breakdown TEXT,
    gold_price REAL,
    gold_return REAL,
    created_at TEXT DEFAULT (datetime('now')),
    UNIQUE(date)
);

CREATE INDEX IF NOT EXISTS idx_raw_signals_date ON raw_signals(date);
CREATE INDEX IF NOT EXISTS idx_raw_signals_driver ON raw_signals(driver, layer);
CREATE INDEX IF NOT EXISTS idx_driver_scores_date ON driver_scores(date);
CREATE INDEX IF NOT EXISTS idx_daily_composite_date ON daily_composite(date);
