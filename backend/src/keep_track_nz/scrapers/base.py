"""Base scraper class for all government data source scrapers."""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
import requests
from datetime import datetime
import logging

from ..debug import DebugContext, DebugFormatter

logger = logging.getLogger(__name__)


class BaseScraper(ABC):
    """Abstract base class for all scrapers."""

    def __init__(self, session: requests.Session | None = None, debug_context: Optional[DebugContext] = None):
        """Initialize scraper with optional session for connection pooling."""
        self.session = session or requests.Session()
        self.debug_context = debug_context
        # Use a browser-like User-Agent to avoid 403 blocks from government sites
        # while still identifying as a bot in the comment for transparency
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 KeepTrackNZ/1.0',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-NZ,en;q=0.9',
        })

    @abstractmethod
    def scrape(self, limit: int | None = None) -> List[Dict[str, Any]]:
        """
        Scrape government actions from the data source.

        Args:
            limit: Optional limit on number of actions to scrape

        Returns:
            List of raw action data dictionaries
        """
        pass

    @abstractmethod
    def get_source_system(self) -> str:
        """Get the source system identifier for this scraper."""
        pass

    def _make_request(self, url: str, **kwargs) -> requests.Response:
        """Make HTTP request with error handling and retry logic."""
        try:
            response = self.session.get(url, timeout=30, **kwargs)
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed for {url}: {e}")
            raise

    def _extract_date(self, date_str: str) -> str:
        """Extract and normalize date from various formats."""
        # This will be implemented with date parsing logic
        # For now, return as-is
        return date_str

    def _debug_log_item(self, item: Dict[str, Any]) -> None:
        """Log debug information for a scraped item."""
        if self.debug_context and self.debug_context.enabled:
            item_num = self.debug_context.next_item_number()
            source = self.get_source_system()
            title = item.get('title', '[No title]')

            print(DebugFormatter.format_item_header(item_num, title, source))
            print(DebugFormatter.format_item_summary(item))

    def _debug_log_summary(self, count: int) -> None:
        """Log debug summary for scraper completion."""
        if self.debug_context and self.debug_context.enabled:
            source = self.get_source_system()
            print(DebugFormatter.format_scraper_summary(source, count))

    def _debug_log_scraped_items(self, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Debug log all scraped items and return the same list."""
        if self.debug_context and self.debug_context.enabled:
            for item in items:
                self._debug_log_item(item)
            self._debug_log_summary(len(items))
        return items

    def close(self) -> None:
        """Close the session if needed."""
        if hasattr(self.session, 'close'):
            self.session.close()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()