"""Base scraper class with retry logic and rate limiting."""

import time
import logging
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from functools import wraps

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


def rate_limit(calls_per_minute: int = 30):
    """Decorator to limit request rate."""
    min_interval = 60.0 / calls_per_minute
    last_called = [0.0]

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            elapsed = time.time() - last_called[0]
            left_to_wait = min_interval - elapsed
            if left_to_wait > 0:
                time.sleep(left_to_wait)
            result = func(*args, **kwargs)
            last_called[0] = time.time()
            return result
        return wrapper
    return decorator


class BaseScraper(ABC):
    """Abstract base class for all scrapers."""

    DEFAULT_HEADERS = {
        'User-Agent': 'PsychoanalyticEventsBot/1.0 (Educational event aggregator)',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
    }

    def __init__(
        self,
        source_config: Dict[str, Any],
        max_retries: int = 3,
        timeout: int = 30
    ):
        """
        Initialize scraper.

        Args:
            source_config: Configuration for this source
            max_retries: Maximum retry attempts
            timeout: Request timeout in seconds
        """
        self.config = source_config
        self.max_retries = max_retries
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update(self.DEFAULT_HEADERS)

    @abstractmethod
    def scrape(self) -> List[Dict[str, Any]]:
        """
        Scrape events from source.

        Returns:
            List of event dictionaries
        """
        pass

    @rate_limit(calls_per_minute=20)
    def fetch_url(self, url: str) -> Optional[str]:
        """
        Fetch URL with retry logic.

        Args:
            url: URL to fetch

        Returns:
            HTML content or None on failure
        """
        for attempt in range(self.max_retries):
            try:
                response = self.session.get(url, timeout=self.timeout)
                response.raise_for_status()
                return response.text
            except requests.Timeout:
                logger.warning(f"Timeout fetching {url} (attempt {attempt + 1})")
            except requests.ConnectionError as e:
                logger.warning(f"Connection error for {url}: {e} (attempt {attempt + 1})")
            except requests.HTTPError as e:
                logger.error(f"HTTP error for {url}: {e}")
                if e.response.status_code == 404:
                    return None
                # Don't retry 4xx errors except ratelimiting
                if 400 <= e.response.status_code < 500 and e.response.status_code != 429:
                    return None
            except Exception as e:
                logger.error(f"Unexpected error fetching {url}: {e}")
                return None

            # Exponential backoff
            if attempt < self.max_retries - 1:
                wait_time = 2 ** attempt
                logger.info(f"Retrying in {wait_time}s...")
                time.sleep(wait_time)

        logger.error(f"Failed to fetch {url} after {self.max_retries} attempts")
        return None

    def parse_html(self, html: str) -> BeautifulSoup:
        """Parse HTML content."""
        return BeautifulSoup(html, 'lxml')

    def get_source_info(self) -> Dict[str, str]:
        """Get source information for event tagging."""
        return {
            'name': self.config.get('name', 'Unknown'),
            'url': self.config.get('config', {}).get('url', ''),
            'type': self.config.get('type', 'website'),
        }

    def make_absolute_url(self, url: str, base_url: str) -> str:
        """Convert relative URL to absolute."""
        if not url:
            return ''
        if url.startswith('http'):
            return url
        if url.startswith('//'):
            return 'https:' + url
        if url.startswith('/'):
            # Get base domain
            from urllib.parse import urlparse
            parsed = urlparse(base_url)
            return f"{parsed.scheme}://{parsed.netloc}{url}"
        return base_url.rstrip('/') + '/' + url

    def close(self):
        """Clean up resources."""
        self.session.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False
