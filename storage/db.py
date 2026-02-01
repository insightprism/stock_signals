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


def init_db(db_path: str = DB_PATH):
    schema_sql = SCHEMA_PATH.read_text()
    with db_session(db_path) as conn:
        conn.executescript(schema_sql)


def upsert_raw_signal(conn, date: str, driver: str, layer: str, source: str,
                       series_name: str, raw_value: float,
                       normalized_value: Optional[float] = None,
                       metadata: Optional[dict] = None):
    meta_json = json.dumps(metadata) if metadata else None
    conn.execute("""
        INSERT INTO raw_signals (date, driver, layer, source, series_name,
                                  raw_value, normalized_value, metadata)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(date, driver, layer, source, series_name)
        DO UPDATE SET raw_value=excluded.raw_value,
                      normalized_value=excluded.normalized_value,
                      metadata=excluded.metadata,
                      created_at=datetime('now')
    """, (date, driver, layer, source, series_name,
          raw_value, normalized_value, meta_json))


def upsert_driver_score(conn, date: str, driver: str,
                         sentiment_score: Optional[float] = None,
                         macro_score: Optional[float] = None):
    conn.execute("""
        INSERT INTO driver_scores (date, driver, sentiment_score, macro_score)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(date, driver)
        DO UPDATE SET sentiment_score=COALESCE(excluded.sentiment_score, driver_scores.sentiment_score),
                      macro_score=COALESCE(excluded.macro_score, driver_scores.macro_score),
                      created_at=datetime('now')
    """, (date, driver, sentiment_score, macro_score))


def upsert_layer_scores(conn, date: str,
                         sentiment_layer: Optional[float] = None,
                         macro_layer: Optional[float] = None):
    conn.execute("""
        INSERT INTO layer_scores (date, sentiment_layer_score, macro_layer_score)
        VALUES (?, ?, ?)
        ON CONFLICT(date)
        DO UPDATE SET sentiment_layer_score=COALESCE(excluded.sentiment_layer_score, layer_scores.sentiment_layer_score),
                      macro_layer_score=COALESCE(excluded.macro_layer_score, layer_scores.macro_layer_score),
                      created_at=datetime('now')
    """, (date, sentiment_layer, macro_layer))


def upsert_daily_composite(conn, date: str, composite_score: float,
                            label: str, sentiment_layer: float,
                            macro_layer: float, driver_breakdown: dict,
                            gold_price: Optional[float] = None,
                            gold_return: Optional[float] = None):
    conn.execute("""
        INSERT INTO daily_composite (date, composite_score, label,
                                      sentiment_layer, macro_layer,
                                      driver_breakdown, gold_price, gold_return)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(date)
        DO UPDATE SET composite_score=excluded.composite_score,
                      label=excluded.label,
                      sentiment_layer=excluded.sentiment_layer,
                      macro_layer=excluded.macro_layer,
                      driver_breakdown=excluded.driver_breakdown,
                      gold_price=excluded.gold_price,
                      gold_return=excluded.gold_return,
                      created_at=datetime('now')
    """, (date, composite_score, label, sentiment_layer, macro_layer,
          json.dumps(driver_breakdown), gold_price, gold_return))


def get_raw_signals(db_path: str = DB_PATH, driver: Optional[str] = None,
                     layer: Optional[str] = None,
                     start_date: Optional[str] = None,
                     end_date: Optional[str] = None) -> pd.DataFrame:
    query = "SELECT * FROM raw_signals WHERE 1=1"
    params = []
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


def get_driver_scores(db_path: str = DB_PATH,
                       start_date: Optional[str] = None,
                       end_date: Optional[str] = None) -> pd.DataFrame:
    query = "SELECT * FROM driver_scores WHERE 1=1"
    params = []
    if start_date:
        query += " AND date >= ?"
        params.append(start_date)
    if end_date:
        query += " AND date <= ?"
        params.append(end_date)
    query += " ORDER BY date, driver"
    with db_session(db_path) as conn:
        return pd.read_sql_query(query, conn, params=params)


def get_daily_composites(db_path: str = DB_PATH,
                          start_date: Optional[str] = None,
                          end_date: Optional[str] = None) -> pd.DataFrame:
    query = "SELECT * FROM daily_composite WHERE 1=1"
    params = []
    if start_date:
        query += " AND date >= ?"
        params.append(start_date)
    if end_date:
        query += " AND date <= ?"
        params.append(end_date)
    query += " ORDER BY date"
    with db_session(db_path) as conn:
        return pd.read_sql_query(query, conn, params=params)


def get_normalization_history(db_path: str = DB_PATH, driver: str = "",
                               source: str = "", series_name: str = "",
                               lookback_days: int = 252) -> pd.DataFrame:
    """Get historical raw values for rolling normalization."""
    query = """
        SELECT date, raw_value FROM raw_signals
        WHERE driver = ? AND source = ? AND series_name = ?
        ORDER BY date DESC LIMIT ?
    """
    with db_session(db_path) as conn:
        return pd.read_sql_query(query, conn,
                                  params=(driver, source, series_name, lookback_days))


def export_to_csv(db_path: str = DB_PATH, output_dir: Optional[str] = None):
    """Export all tables to CSV files."""
    out = Path(output_dir) if output_dir else Path(db_path).parent
    out.mkdir(parents=True, exist_ok=True)
    tables = ["raw_signals", "driver_scores", "layer_scores", "daily_composite"]
    with db_session(db_path) as conn:
        for table in tables:
            df = pd.read_sql_query(f"SELECT * FROM {table} ORDER BY date", conn)
            df.to_csv(out / f"{table}.csv", index=False)
