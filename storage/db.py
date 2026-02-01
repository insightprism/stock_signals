"""SQLite database operations for gold sentiment index."""

import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Optional

import pandas as pd

from config.settings import DB_PATH

SCHEMA_PATH = Path(__file__).parent / "schema.sql"


def get_connection(db_path: str = DB_PATH) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.row_factory = sqlite3.Row
    return conn


@contextmanager
def db_session(db_path: str = DB_PATH):
    conn = get_connection(db_path)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def _migrate_add_asset_column(conn):
    """Add asset column to existing tables if missing (migration)."""
    tables_to_migrate = ["raw_signals", "driver_scores", "layer_scores", "daily_composite"]
    for table in tables_to_migrate:
        try:
            cols = [row[1] for row in conn.execute(f"PRAGMA table_info({table})").fetchall()]
            if "asset" not in cols and cols:
                conn.execute(f"ALTER TABLE {table} ADD COLUMN asset TEXT NOT NULL DEFAULT 'gold'")
        except Exception:
            pass  # table doesn't exist yet, schema will create it

    # Migrate gold_price/gold_return -> asset_price/asset_return in daily_composite
    try:
        cols = [row[1] for row in conn.execute("PRAGMA table_info(daily_composite)").fetchall()]
        if "gold_price" in cols and "asset_price" not in cols:
            conn.execute("ALTER TABLE daily_composite RENAME COLUMN gold_price TO asset_price")
            conn.execute("ALTER TABLE daily_composite RENAME COLUMN gold_return TO asset_return")
    except Exception:
        pass


def init_db(db_path: str = DB_PATH):
    with db_session(db_path) as conn:
        _migrate_add_asset_column(conn)
    # Re-open to apply new schema (creates tables if not exist)
    with db_session(db_path) as conn:
        schema_sql = SCHEMA_PATH.read_text()
        conn.executescript(schema_sql)


def upsert_raw_signal(conn, date: str, asset: str, driver: str, layer: str,
                       source: str, series_name: str, raw_value: float,
                       normalized_value: Optional[float] = None,
                       metadata: Optional[dict] = None):
    meta_json = json.dumps(metadata) if metadata else None
    conn.execute("""
        INSERT INTO raw_signals (date, asset, driver, layer, source, series_name,
                                  raw_value, normalized_value, metadata)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(date, asset, driver, layer, source, series_name)
        DO UPDATE SET raw_value=excluded.raw_value,
                      normalized_value=excluded.normalized_value,
                      metadata=excluded.metadata,
                      created_at=datetime('now')
    """, (date, asset, driver, layer, source, series_name,
          raw_value, normalized_value, meta_json))


def upsert_driver_score(conn, date: str, asset: str, driver: str,
                         sentiment_score: Optional[float] = None,
                         macro_score: Optional[float] = None):
    conn.execute("""
        INSERT INTO driver_scores (date, asset, driver, sentiment_score, macro_score)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(date, asset, driver)
        DO UPDATE SET sentiment_score=COALESCE(excluded.sentiment_score, driver_scores.sentiment_score),
                      macro_score=COALESCE(excluded.macro_score, driver_scores.macro_score),
                      created_at=datetime('now')
    """, (date, asset, driver, sentiment_score, macro_score))


def upsert_layer_scores(conn, date: str, asset: str,
                         sentiment_layer: Optional[float] = None,
                         macro_layer: Optional[float] = None):
    conn.execute("""
        INSERT INTO layer_scores (date, asset, sentiment_layer_score, macro_layer_score)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(date, asset)
        DO UPDATE SET sentiment_layer_score=COALESCE(excluded.sentiment_layer_score, layer_scores.sentiment_layer_score),
                      macro_layer_score=COALESCE(excluded.macro_layer_score, layer_scores.macro_layer_score),
                      created_at=datetime('now')
    """, (date, asset, sentiment_layer, macro_layer))


def upsert_daily_composite(conn, date: str, asset: str, composite_score: float,
                            label: str, sentiment_layer: float,
                            macro_layer: float, driver_breakdown: dict,
                            asset_price: Optional[float] = None,
                            asset_return: Optional[float] = None):
    conn.execute("""
        INSERT INTO daily_composite (date, asset, composite_score, label,
                                      sentiment_layer, macro_layer,
                                      driver_breakdown, asset_price, asset_return)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(date, asset)
        DO UPDATE SET composite_score=excluded.composite_score,
                      label=excluded.label,
                      sentiment_layer=excluded.sentiment_layer,
                      macro_layer=excluded.macro_layer,
                      driver_breakdown=excluded.driver_breakdown,
                      asset_price=excluded.asset_price,
                      asset_return=excluded.asset_return,
                      created_at=datetime('now')
    """, (date, asset, composite_score, label, sentiment_layer, macro_layer,
          json.dumps(driver_breakdown), asset_price, asset_return))


def get_raw_signals(db_path: str = DB_PATH, asset: Optional[str] = None,
                     driver: Optional[str] = None, layer: Optional[str] = None,
                     start_date: Optional[str] = None,
                     end_date: Optional[str] = None) -> pd.DataFrame:
    query = "SELECT * FROM raw_signals WHERE 1=1"
    params = []
    if asset:
        query += " AND asset = ?"
        params.append(asset)
    if driver:
        query += " AND driver = ?"
        params.append(driver)
    if layer:
        query += " AND layer = ?"
        params.append(layer)
    if start_date:
        query += " AND date >= ?"
        params.append(start_date)
    if end_date:
        query += " AND date <= ?"
        params.append(end_date)
    query += " ORDER BY date"
    with db_session(db_path) as conn:
        return pd.read_sql_query(query, conn, params=params)


def get_driver_scores(db_path: str = DB_PATH, asset: Optional[str] = None,
                       start_date: Optional[str] = None,
                       end_date: Optional[str] = None) -> pd.DataFrame:
    query = "SELECT * FROM driver_scores WHERE 1=1"
    params = []
    if asset:
        query += " AND asset = ?"
        params.append(asset)
    if start_date:
        query += " AND date >= ?"
        params.append(start_date)
    if end_date:
        query += " AND date <= ?"
        params.append(end_date)
    query += " ORDER BY date, driver"
    with db_session(db_path) as conn:
        return pd.read_sql_query(query, conn, params=params)


def get_daily_composites(db_path: str = DB_PATH, asset: Optional[str] = None,
                          start_date: Optional[str] = None,
                          end_date: Optional[str] = None) -> pd.DataFrame:
    query = "SELECT * FROM daily_composite WHERE 1=1"
    params = []
    if asset:
        query += " AND asset = ?"
        params.append(asset)
    if start_date:
        query += " AND date >= ?"
        params.append(start_date)
    if end_date:
        query += " AND date <= ?"
        params.append(end_date)
    query += " ORDER BY date"
    with db_session(db_path) as conn:
        return pd.read_sql_query(query, conn, params=params)


def get_normalization_history(db_path: str = DB_PATH, asset: str = "",
                               driver: str = "", source: str = "",
                               series_name: str = "",
                               lookback_days: int = 252) -> pd.DataFrame:
    """Get historical raw values for rolling normalization."""
    query = """
        SELECT date, raw_value FROM raw_signals
        WHERE asset = ? AND driver = ? AND source = ? AND series_name = ?
        ORDER BY date DESC LIMIT ?
    """
    with db_session(db_path) as conn:
        return pd.read_sql_query(query, conn,
                                  params=(asset, driver, source, series_name, lookback_days))


def export_to_csv(db_path: str = DB_PATH, output_dir: Optional[str] = None):
    """Export all tables to CSV files."""
    out = Path(output_dir) if output_dir else Path(db_path).parent
    out.mkdir(parents=True, exist_ok=True)
    tables = ["raw_signals", "driver_scores", "layer_scores", "daily_composite"]
    with db_session(db_path) as conn:
        for table in tables:
            df = pd.read_sql_query(f"SELECT * FROM {table} ORDER BY date", conn)
            df.to_csv(out / f"{table}.csv", index=False)
