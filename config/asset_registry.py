"""Asset configuration registry - loads per-asset YAML configs."""

import logging
from pathlib import Path
from typing import Dict, List, Optional

import yaml

logger = logging.getLogger(__name__)

ASSETS_DIR = Path(__file__).parent / "assets"

_cache: Dict[str, dict] = {}

REQUIRED_FIELDS = [
    "asset_id", "display_name", "category", "futures_ticker",
    "driver_weights", "layer_weights", "driver_names", "keywords",
]


def _load_all() -> Dict[str, dict]:
    """Load all asset YAML files from config/assets/."""
    if _cache:
        return _cache
    if not ASSETS_DIR.exists():
        logger.warning("Assets directory not found: %s", ASSETS_DIR)
        return _cache
    for path in sorted(ASSETS_DIR.glob("*.yaml")):
        try:
            with open(path) as f:
                cfg = yaml.safe_load(f)
            if not cfg or "asset_id" not in cfg:
                logger.warning("Skipping invalid asset config: %s", path)
                continue
            # Validate required fields
            missing = [f for f in REQUIRED_FIELDS if f not in cfg]
            if missing:
                logger.warning("Asset %s missing fields: %s", path.stem, missing)
            _cache[cfg["asset_id"]] = cfg
            logger.info("Loaded asset config: %s (%s)", cfg["asset_id"], cfg["display_name"])
        except Exception as e:
            logger.error("Failed to load asset config %s: %s", path, e)
    return _cache


def get_asset_config(asset_id: str) -> dict:
    """Get configuration for a specific asset."""
    configs = _load_all()
    if asset_id not in configs:
        raise ValueError(f"Unknown asset: {asset_id}. Available: {list(configs.keys())}")
    return configs[asset_id]


def list_assets() -> List[dict]:
    """List all available assets with summary metadata."""
    configs = _load_all()
    return [
        {
            "asset_id": cfg["asset_id"],
            "display_name": cfg["display_name"],
            "category": cfg.get("category", "other"),
            "futures_ticker": cfg.get("futures_ticker", ""),
            "etf_ticker": cfg.get("etf_ticker", ""),
        }
        for cfg in configs.values()
    ]


def get_asset_ids() -> List[str]:
    """Get list of all available asset IDs."""
    return list(_load_all().keys())


def reload():
    """Clear cache and reload all configs."""
    _cache.clear()
    _load_all()
