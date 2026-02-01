"""Base collector with retry logic and common interface."""

import logging
import time
from abc import ABC, abstractmethod
from datetime import date
from typing import Dict, List, Optional

import requests

from config.settings import MAX_RETRIES, REQUEST_TIMEOUT, RETRY_BACKOFF_FACTOR

logger = logging.getLogger(__name__)


class BaseCollector(ABC):
    """Abstract base class for all data collectors."""

    name: str = "base"

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "GoldSentimentIndex/1.0"
        })

    def _request(self, url: str, params: Optional[dict] = None,
                 method: str = "GET", **kwargs) -> requests.Response:
        """HTTP request with retry and exponential backoff."""
        last_exc = None
        for attempt in range(MAX_RETRIES):
            try:
                resp = self.session.request(
                    method, url, params=params,
                    timeout=REQUEST_TIMEOUT, **kwargs
                )
                resp.raise_for_status()
                return resp
            except requests.RequestException as e:
                last_exc = e
                wait = RETRY_BACKOFF_FACTOR ** attempt
                logger.warning(
                    "%s: attempt %d/%d failed: %s — retrying in %.1fs",
                    self.name, attempt + 1, MAX_RETRIES, e, wait
                )
                time.sleep(wait)
        logger.error("%s: all %d attempts failed", self.name, MAX_RETRIES)
        raise last_exc

    @abstractmethod
    def collect(self, target_date: date, asset_config: dict,
                drivers: Optional[List[str]] = None
                ) -> Dict[str, List[dict]]:
        """Collect data for the given date and asset.

        Args:
            target_date: Date to collect data for
            asset_config: Asset configuration dict from asset_registry
            drivers: Optional list of driver names to collect for

        Returns a dict keyed by driver name, each value is a list of signal dicts:
            {
                "source": str,
                "series_name": str,
                "raw_value": float,
                "metadata": dict (optional),
            }
        """
        ...
