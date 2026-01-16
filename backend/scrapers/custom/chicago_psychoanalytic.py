"""Custom scraper for Chicago Psychoanalytic Society."""

import logging
from typing import List, Dict, Any

from ..base import BaseScraper
from ...parsers.event_parser import EventParser

logger = logging.getLogger(__name__)


class ChicagoPsychoanalyticScraper(BaseScraper):
    """Scraper for Chicago Psychoanalytic Society events."""

    EVENTS_URL = "https://www.chicagopsychoanalyticsociety.org/"

    def __init__(self, source_config: Dict[str, Any]):
        super().__init__(source_config)
        self.parser = EventParser()
        self.base_url = self.config.get('config', {}).get('url', self.EVENTS_URL)

    def scrape(self) -> List[Dict[str, Any]]:
        """Scrape events from Chicago Psychoanalytic Society website."""
        html = self.fetch_url(self.base_url)
        if not html:
            return []

        soup = self.parse_html(html)
        events = []

        # Look for events section - try multiple selectors
        event_containers = (
            soup.select('.event') or
            soup.select('.events-list li') or
            soup.select('[class*="calendar"] .item') or
            soup.select('article') or
            soup.select('.upcoming-events .event-item')
        )

        # Also try to find events in main content area
        if not event_containers:
            main_content = soup.select_one('main, #content, .content')
            if main_content:
                # Look for date patterns in text to find event-like content
                for section in main_content.select('section, div, article'):
                    text = section.get_text()
                    if self._looks_like_event(text):
                        event_containers.append(section)

        logger.info(f"Chicago: Found {len(event_containers)} potential events")

        source_info = {
            'name': 'Chicago Psychoanalytic Society',
            'url': self.base_url,
            'type': 'website',
        }

        for container in event_containers:
            try:
                event = self._parse_event(container, source_info)
                if event:
                    events.append(event)
            except Exception as e:
                logger.warning(f"Chicago: Failed to parse event: {e}")
                continue

        logger.info(f"Chicago: Successfully parsed {len(events)} events")
        return events

    def _looks_like_event(self, text: str) -> bool:
        """Check if text looks like event content."""
        import re
        # Has date pattern
        date_patterns = [
            r'\d{1,2}/\d{1,2}/\d{4}',
            r'January|February|March|April|May|June|July|August|September|October|November|December',
        ]
        has_date = any(re.search(p, text, re.IGNORECASE) for p in date_patterns)
        
        # Has event-related keywords
        event_keywords = ['register', 'rsvp', 'lecture', 'seminar', 'workshop', 'presentation']
        has_keyword = any(kw in text.lower() for kw in event_keywords)
        
        return has_date and has_keyword

    def _parse_event(self, element, source_info: Dict) -> Dict[str, Any]:
        """Parse a single event element."""
        event = self.parser.parse_event_from_html(element, source_info)
        
        if not event:
            return None

        # Chicago-specific adjustments
        event['organizer'] = {
            'name': 'Chicago Psychoanalytic Society',
            'url': 'https://www.chicagopsychoanalyticsociety.org',
        }

        event['location'] = event.get('location', {})
        if not event['location'].get('city'):
            event['location']['city'] = 'Chicago'
        if not event['location'].get('country'):
            event['location']['country'] = 'USA'

        # Generate ID
        event['id'] = self._generate_id(event)
        
        return event

    def _generate_id(self, event: Dict) -> str:
        """Generate unique event ID."""
        import hashlib
        unique_str = f"chicago:{event.get('title', '')}:{event.get('start_date', '')}"
        return hashlib.sha256(unique_str.encode()).hexdigest()[:16]
