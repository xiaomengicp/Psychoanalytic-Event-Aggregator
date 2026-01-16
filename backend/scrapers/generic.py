"""Generic website scraper using CSS selectors."""

import logging
from typing import List, Dict, Any
from datetime import datetime

from .base import BaseScraper
from ..parsers.event_parser import EventParser

logger = logging.getLogger(__name__)


class GenericWebsiteScraper(BaseScraper):
    """Scraper for websites using configurable CSS selectors."""

    def __init__(self, source_config: Dict[str, Any]):
        super().__init__(source_config)
        self.url = source_config.get('config', {}).get('url', '')
        self.selectors = source_config.get('config', {}).get('selectors', {})
        self.parser = EventParser()

    def scrape(self) -> List[Dict[str, Any]]:
        """Scrape events using configured selectors."""
        if not self.url:
            logger.error("No URL configured for generic scraper")
            return []

        html = self.fetch_url(self.url)
        if not html:
            return []

        soup = self.parse_html(html)
        events = []

        # Find event container
        container_selector = self.selectors.get('event_list', 'body')
        container = soup.select_one(container_selector) or soup

        # Find individual event items
        item_selector = self.selectors.get('event_item', '.event')
        event_items = container.select(item_selector)

        logger.info(f"Found {len(event_items)} potential events on {self.url}")

        # Parse each event
        source_info = self.get_source_info()
        selector_dict = {
            'title': self.selectors.get('title'),
            'date': self.selectors.get('date'),
            'description': self.selectors.get('description'),
        }

        for item in event_items:
            try:
                event = self.parser.parse_event_from_html(
                    item,
                    source_info,
                    selector_dict
                )
                if event:
                    # Get event link
                    link_selector = self.selectors.get('link', 'a')
                    link_elem = item.select_one(link_selector)
                    if link_elem and link_elem.has_attr('href'):
                        event_url = self.make_absolute_url(link_elem['href'], self.url)
                        if not event.get('registration', {}).get('url'):
                            event['registration'] = event.get('registration', {})
                            event['registration']['url'] = event_url

                    # Generate ID
                    event['id'] = self._generate_event_id(event)
                    events.append(event)
            except Exception as e:
                logger.warning(f"Failed to parse event item: {e}")
                continue

        logger.info(f"Successfully parsed {len(events)} events from {self.url}")
        return events

    def _generate_event_id(self, event: Dict[str, Any]) -> str:
        """Generate unique event ID."""
        import hashlib
        unique_str = f"{self.url}:{event.get('title', '')}:{event.get('start_date', '')}"
        return hashlib.sha256(unique_str.encode()).hexdigest()[:16]
