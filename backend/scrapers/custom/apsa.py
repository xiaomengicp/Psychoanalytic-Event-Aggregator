"""Custom scraper for American Psychoanalytic Association (APsA)."""

import logging
from typing import List, Dict, Any
from datetime import datetime

from ..base import BaseScraper
from ...parsers.event_parser import EventParser

logger = logging.getLogger(__name__)


class APsAScraper(BaseScraper):
    """Scraper for apsa.org meetings and events."""

    EVENTS_URL = "https://apsa.org/meetings-events/"

    def __init__(self, source_config: Dict[str, Any]):
        super().__init__(source_config)
        self.parser = EventParser()
        self.base_url = self.config.get('config', {}).get('url', self.EVENTS_URL)

    def scrape(self) -> List[Dict[str, Any]]:
        """Scrape events from APsA website."""
        html = self.fetch_url(self.base_url)
        if not html:
            return []

        soup = self.parse_html(html)
        events = []

        # APsA typically uses event cards or listing items
        # Try multiple possible selectors for event containers
        event_containers = (
            soup.select('.event-item') or
            soup.select('.event-card') or
            soup.select('article.event') or
            soup.select('.events-list .event') or
            soup.select('[class*="event"]')
        )

        logger.info(f"APsA: Found {len(event_containers)} potential events")

        source_info = {
            'name': 'American Psychoanalytic Association',
            'url': self.base_url,
            'type': 'website',
        }

        for container in event_containers:
            try:
                event = self._parse_event(container, source_info)
                if event:
                    events.append(event)
            except Exception as e:
                logger.warning(f"APsA: Failed to parse event: {e}")
                continue

        logger.info(f"APsA: Successfully parsed {len(events)} events")
        return events

    def _parse_event(self, element, source_info: Dict) -> Dict[str, Any]:
        """Parse a single event element."""
        event = self.parser.parse_event_from_html(element, source_info)
        
        if not event:
            return None

        # APsA-specific adjustments
        event['organizer'] = {
            'name': 'American Psychoanalytic Association',
            'url': 'https://apsa.org',
        }

        # Look for registration links
        reg_link = element.select_one('a[href*="register"], a.register-btn')
        if reg_link and reg_link.has_attr('href'):
            event['registration'] = event.get('registration', {})
            event['registration']['url'] = self.make_absolute_url(
                reg_link['href'], self.base_url
            )

        # Generate ID
        event['id'] = self._generate_id(event)
        
        return event

    def _generate_id(self, event: Dict) -> str:
        """Generate unique event ID."""
        import hashlib
        unique_str = f"apsa:{event.get('title', '')}:{event.get('start_date', '')}"
        return hashlib.sha256(unique_str.encode()).hexdigest()[:16]
