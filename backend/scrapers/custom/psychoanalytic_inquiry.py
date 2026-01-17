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
        # Try specific events page first
        events_url = "https://www.psychoanalyticinquiry.com/event-calendar/"
        html = self.fetch_url(events_url)
        
        if not html:
            # Fallback to base
            html = self.fetch_url(self.base_url)
            
        if not html:
            return []

        soup = self.parse_html(html)
        events = []

        # Target specific container verified in browser
        event_containers = soup.select('.post-card') or soup.select('article.post')
        
        if not event_containers:
            # Fallback to generic search
            event_containers = (
                soup.select('.event') or
                soup.select('.events .item') or
                soup.select('article.event') or
                soup.select('[class*="event"]') or
                soup.select('.calendar-item')
            )

        logger.info(f"Psychoanalytic Inquiry: Found {len(event_containers)} potential events")

        source_info = {
            'name': 'Psychoanalytic Inquiry',
            'url': events_url,
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
        # Specific selectors for Avada/Fusion builder
        selectors = {
            'title': 'h2.fusion-title-heading, .fusion-post-title, .entry-title',
            'date': '.fusion-text p, .updated, .published', # Date often in generic text block
            'description': '.fusion-text'
        }
        
        event = self.parser.parse_event_from_html(element, source_info, selectors=selectors)
        
        if not event:
            return None

        # Source-specific adjustments
        event['organizer'] = {
            'name': 'Psychoanalytic Inquiry',
            'url': 'https://www.psychoanalyticinquiry.com',
        }

        # Look for event link in title
        link = element.select_one('h2.fusion-title-heading a, .fusion-post-title a, a.fusion-read-more')
        if not link:
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
