"""API endpoints for commodity sentiment index data."""

import json
import sqlite3
import threading
from datetime import date
from typing import Optional

from fastapi import APIRouter, Query

from config.settings import DB_PATH
from config.asset_registry import get_asset_config, list_assets, get_asset_ids

router = APIRouter()

# Track pipeline status
_pipeline_status = {"running": False, "last_error": None, "last_result": None}


def _get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _rows_to_dicts(rows: list[sqlite3.Row]) -> list[dict]:
    return [dict(r) for r in rows]


@router.get("/assets")
def assets_list():
    """List all available assets."""
    return {"data": list_assets()}


@router.get("/composite/latest")
def composite_latest(asset: str = Query("gold")):
    """Latest day's composite score with full breakdown."""
    conn = _get_conn()
    try:
        row = conn.execute(
            "SELECT * FROM daily_composite WHERE asset = ? ORDER BY date DESC LIMIT 1",
            (asset,),
        ).fetchone()
        if not row:
            return {"data": None}
        result = dict(row)
        if result.get("driver_breakdown"):
            result["driver_breakdown"] = json.loads(result["driver_breakdown"])
        return {"data": result}
    finally:
        conn.close()


@router.get("/composite/history")
def composite_history(
    asset: str = Query("gold"),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
):
    """Historical composite scores."""
    conn = _get_conn()
    try:
        query = "SELECT * FROM daily_composite WHERE asset = ?"
        params: list = [asset]
        if start_date:
            query += " AND date >= ?"
            params.append(start_date)
        if end_date:
            query += " AND date <= ?"
            params.append(end_date)
        query += " ORDER BY date"
        rows = conn.execute(query, params).fetchall()
        data = []
        for r in rows:
            d = dict(r)
            if d.get("driver_breakdown"):
                d["driver_breakdown"] = json.loads(d["driver_breakdown"])
            data.append(d)
        return {"data": data}
    finally:
        conn.close()


@router.get("/drivers/latest")
def drivers_latest(asset: str = Query("gold")):
    """Latest driver scores (sentiment + macro per driver)."""
    conn = _get_conn()
    try:
        date_row = conn.execute(
            "SELECT MAX(date) as max_date FROM driver_scores WHERE asset = ?",
            (asset,),
        ).fetchone()
        if not date_row or not date_row["max_date"]:
            return {"data": [], "date": None}
        latest_date = date_row["max_date"]
        rows = conn.execute(
            "SELECT * FROM driver_scores WHERE date = ? AND asset = ? ORDER BY driver",
            (latest_date, asset),
        ).fetchall()
        return {"data": _rows_to_dicts(rows), "date": latest_date}
    finally:
        conn.close()


@router.get("/drivers/history")
def drivers_history(
    asset: str = Query("gold"),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
):
    """Historical driver scores."""
    conn = _get_conn()
    try:
        query = "SELECT * FROM driver_scores WHERE asset = ?"
        params: list = [asset]
        if start_date:
            query += " AND date >= ?"
            params.append(start_date)
        if end_date:
            query += " AND date <= ?"
            params.append(end_date)
        query += " ORDER BY date, driver"
        rows = conn.execute(query, params).fetchall()
        return {"data": _rows_to_dicts(rows)}
    finally:
        conn.close()


@router.get("/signals")
def signals(
    asset: str = Query("gold"),
    driver: Optional[str] = Query(None),
    layer: Optional[str] = Query(None),
    source: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
):
    """Raw signals with filtering and pagination."""
    conn = _get_conn()
    try:
        where = "WHERE asset = ?"
        params: list = [asset]
        if driver:
            where += " AND driver = ?"
            params.append(driver)
        if layer:
            where += " AND layer = ?"
            params.append(layer)
        if source:
            where += " AND source = ?"
            params.append(source)
        if start_date:
            where += " AND date >= ?"
            params.append(start_date)
        if end_date:
            where += " AND date <= ?"
            params.append(end_date)

        # Count total
        count_row = conn.execute(
            f"SELECT COUNT(*) as total FROM raw_signals {where}", params
        ).fetchone()
        total = count_row["total"]

        # Fetch page
        offset = (page - 1) * page_size
        rows = conn.execute(
            f"SELECT * FROM raw_signals {where} ORDER BY date DESC, driver, source "
            f"LIMIT ? OFFSET ?",
            params + [page_size, offset],
        ).fetchall()

        return {
            "data": _rows_to_dicts(rows),
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size if total > 0 else 0,
        }
    finally:
        conn.close()


@router.post("/pipeline/run")
def pipeline_run(
    asset: str = Query("gold"),
    target_date: Optional[str] = Query(None),
):
    """Trigger the pipeline for a given date and asset (default: today, gold)."""
    if _pipeline_status["running"]:
        return {"status": "already_running"}

    td = date.fromisoformat(target_date) if target_date else date.today()

    def _run():
        _pipeline_status["running"] = True
        _pipeline_status["last_error"] = None
        try:
            from main import run_pipeline
            result = run_pipeline(td, asset=asset)
            _pipeline_status["last_result"] = {
                "date": result["date"],
                "asset": result["asset"],
                "composite_score": result["composite"]["composite_score"],
                "label": result["composite"]["label"],
            }
        except Exception as e:
            _pipeline_status["last_error"] = str(e)
        finally:
            _pipeline_status["running"] = False

    threading.Thread(target=_run, daemon=True).start()
    return {"status": "started", "date": td.isoformat(), "asset": asset}


@router.get("/pipeline/status")
def pipeline_status():
    """Check pipeline run status."""
    return _pipeline_status


@router.get("/config")
def config(asset: str = Query("gold")):
    """Driver weights, layer weights, driver names for a specific asset."""
    try:
        asset_config = get_asset_config(asset)
        return {
            "driver_weights": asset_config.get("driver_weights", {}),
            "layer_weights": asset_config.get("layer_weights", {}),
            "driver_names": asset_config.get("driver_names", []),
            "display_name": asset_config.get("display_name", asset),
            "category": asset_config.get("category", "other"),
        }
    except ValueError:
        return {
            "driver_weights": {},
            "layer_weights": {},
            "driver_names": [],
            "display_name": asset,
            "category": "other",
        }


@router.get("/stats")
def stats(asset: str = Query("gold")):
    """Summary statistics for a specific asset."""
    conn = _get_conn()
    try:
        composite_stats = conn.execute(
            "SELECT COUNT(*) as total_dates, MIN(date) as min_date, "
            "MAX(date) as max_date FROM daily_composite WHERE asset = ?",
            (asset,),
        ).fetchone()
        signal_count = conn.execute(
            "SELECT COUNT(*) as count FROM raw_signals WHERE asset = ?",
            (asset,),
        ).fetchone()

        # Get distinct sources and drivers for filter dropdowns
        sources = conn.execute(
            "SELECT DISTINCT source FROM raw_signals WHERE asset = ? ORDER BY source",
            (asset,),
        ).fetchall()
        drivers = conn.execute(
            "SELECT DISTINCT driver FROM raw_signals WHERE asset = ? ORDER BY driver",
            (asset,),
        ).fetchall()
        layers = conn.execute(
            "SELECT DISTINCT layer FROM raw_signals WHERE asset = ? ORDER BY layer",
            (asset,),
        ).fetchall()

        return {
            "total_dates": composite_stats["total_dates"],
            "min_date": composite_stats["min_date"],
            "max_date": composite_stats["max_date"],
            "signal_count": signal_count["count"],
            "sources": [r["source"] for r in sources],
            "drivers": [r["driver"] for r in drivers],
            "layers": [r["layer"] for r in layers],
        }
    finally:
        conn.close()
