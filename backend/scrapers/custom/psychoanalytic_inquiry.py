"""Custom scraper for Psychoanalytic Inquiry."""

import logging
from typing import List, Dict, Any

from ..base import BaseScraper
from ...parsers.event_parser import EventParser

logger = logging.getLogger(__name__)


class PsychoanalyticInquiryScraper(BaseScraper):
    """Scraper for psychoanalyticinquiry.com events."""

    EVENTS_URL = "https://www.psychoanalyticinquiry.com/"

    def __init__(self, source_config: Dict[str, Any]):
        super().__init__(source_config)
        self.parser = EventParser()
        self.base_url = self.config.get('config', {}).get('url', self.EVENTS_URL)

    def scrape(self) -> List[Dict[str, Any]]:
        """Scrape events from Psychoanalytic Inquiry website."""
        html = self.fetch_url(self.base_url)
        if not html:
            return []

        soup = self.parse_html(html)
        events = []

        # Try various common event container selectors
        event_containers = (
            soup.select('.event') or
            soup.select('.events .item') or
            soup.select('article.event') or
            soup.select('[class*="event"]') or
            soup.select('.calendar-item')
        )

        # Also look for events page link and scrape it
        events_link = soup.select_one('a[href*="event"], a[href*="calendar"]')
        if events_link and events_link.has_attr('href'):
            events_page_url = self.make_absolute_url(events_link['href'], self.base_url)
            events_html = self.fetch_url(events_page_url)
            if events_html:
                events_soup = self.parse_html(events_html)
                additional = (
                    events_soup.select('.event') or
                    events_soup.select('[class*="event"]')
                )
                event_containers.extend(additional)

        logger.info(f"Psychoanalytic Inquiry: Found {len(event_containers)} potential events")

        source_info = {
            'name': 'Psychoanalytic Inquiry',
            'url': self.base_url,
            'type': 'website',
        }

        for container in event_containers:
            try:
                event = self._parse_event(container, source_info)
                if event:
                    events.append(event)
            except Exception as e:
                logger.warning(f"Psychoanalytic Inquiry: Failed to parse event: {e}")
                continue

        logger.info(f"Psychoanalytic Inquiry: Successfully parsed {len(events)} events")
        return events

    def _parse_event(self, element, source_info: Dict) -> Dict[str, Any]:
        """Parse a single event element."""
        event = self.parser.parse_event_from_html(element, source_info)
        
        if not event:
            return None

        # Source-specific adjustments
        event['organizer'] = {
            'name': 'Psychoanalytic Inquiry',
            'url': 'https://www.psychoanalyticinquiry.com',
        }

        # Look for event link
        link = element.select_one('a[href]')
        if link and link.has_attr('href'):
            event_url = self.make_absolute_url(link['href'], self.base_url)
            event['registration'] = event.get('registration', {})
            if not event['registration'].get('url'):
                event['registration']['url'] = event_url

        # Generate ID
        event['id'] = self._generate_id(event)
        
        return event

    def _generate_id(self, event: Dict) -> str:
        """Generate unique event ID."""
        import hashlib
        unique_str = f"psychoanalytic-inquiry:{event.get('title', '')}:{event.get('start_date', '')}"
        return hashlib.sha256(unique_str.encode()).hexdigest()[:16]
