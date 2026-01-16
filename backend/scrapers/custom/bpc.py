"""Custom scraper for British Psychoanalytic Council (BPC)."""

import logging
from typing import List, Dict, Any

from ..base import BaseScraper
from ...parsers.event_parser import EventParser

logger = logging.getLogger(__name__)


class BPCScraper(BaseScraper):
    """Scraper for bpc.org.uk events."""

    EVENTS_URL = "https://www.bpc.org.uk/events/"

    def __init__(self, source_config: Dict[str, Any]):
        super().__init__(source_config)
        self.parser = EventParser()
        self.base_url = self.config.get('config', {}).get('url', self.EVENTS_URL)

    def scrape(self) -> List[Dict[str, Any]]:
        """Scrape events from BPC website."""
        html = self.fetch_url(self.base_url)
        if not html:
            return []

        soup = self.parse_html(html)
        events = []

        # BPC uses a standard events listing format
        event_containers = (
            soup.select('.event-listing') or
            soup.select('.event-item') or
            soup.select('article.post') or
            soup.select('.events-grid .event') or
            soup.select('[class*="event"]')
        )

        logger.info(f"BPC: Found {len(event_containers)} potential events")

        source_info = {
            'name': 'British Psychoanalytic Council',
            'url': self.base_url,
            'type': 'website',
        }

        for container in event_containers:
            try:
                event = self._parse_event(container, source_info)
                if event:
                    events.append(event)
            except Exception as e:
                logger.warning(f"BPC: Failed to parse event: {e}")
                continue

        logger.info(f"BPC: Successfully parsed {len(events)} events")
        return events

    def _parse_event(self, element, source_info: Dict) -> Dict[str, Any]:
        """Parse a single event element."""
        event = self.parser.parse_event_from_html(element, source_info)
        
        if not event:
            return None

        # BPC-specific adjustments
        event['organizer'] = {
            'name': 'British Psychoanalytic Council',
            'url': 'https://www.bpc.org.uk',
        }

        # Default location assumption for BPC events
        if not event.get('location', {}).get('country'):
            event['location'] = event.get('location', {})
            event['location']['country'] = 'United Kingdom'

        # Look for event detail link
        link = element.select_one('a[href]')
        if link and link.has_attr('href'):
            event_url = self.make_absolute_url(link['href'], self.base_url)
            if not event.get('registration', {}).get('url'):
                event['registration'] = {'url': event_url}

        # Generate ID
        event['id'] = self._generate_id(event)
        
        return event

    def _generate_id(self, event: Dict) -> str:
        """Generate unique event ID."""
        import hashlib
        unique_str = f"bpc:{event.get('title', '')}:{event.get('start_date', '')}"
        return hashlib.sha256(unique_str.encode()).hexdigest()[:16]
