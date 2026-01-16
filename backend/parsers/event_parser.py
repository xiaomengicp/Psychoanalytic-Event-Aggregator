"""Event parser for extracting structured data from HTML and text."""

import re
import logging
from datetime import datetime
from typing import Optional, Dict, List, Any
from bs4 import BeautifulSoup, Tag
from dateutil import parser as date_parser

logger = logging.getLogger(__name__)


class EventParser:
    """Extracts structured event data from HTML snippets or text."""

    # Common date patterns
    DATE_PATTERNS = [
        r'\d{1,2}/\d{1,2}/\d{4}',           # MM/DD/YYYY or DD/MM/YYYY
        r'\d{4}-\d{2}-\d{2}',                # YYYY-MM-DD
        r'[A-Z][a-z]+ \d{1,2},? \d{4}',      # January 15, 2024
        r'\d{1,2} [A-Z][a-z]+ \d{4}',        # 15 January 2024
        r'[A-Z][a-z]+ \d{1,2}-\d{1,2},? \d{4}',  # January 15-17, 2024
    ]

    # Event type keywords
    EVENT_TYPE_KEYWORDS = {
        'conference': ['conference', 'congress', 'symposium', 'annual meeting'],
        'workshop': ['workshop', 'training', 'hands-on'],
        'lecture': ['lecture', 'talk', 'presentation', 'address'],
        'seminar': ['seminar', 'colloquium', 'discussion'],
        'webinar': ['webinar', 'online event', 'virtual event'],
        'course': ['course', 'program', 'certificate', 'training program'],
    }

    # Format indicators
    FORMAT_KEYWORDS = {
        'online': ['online', 'virtual', 'webinar', 'zoom', 'via zoom', 'remote', 'web-based'],
        'in-person': ['in-person', 'in person', 'venue', 'location:', 'address:', 'on-site'],
        'hybrid': ['hybrid', 'both online and in-person', 'in-person and online'],
    }

    def parse_event_from_html(
        self,
        html_element: Tag,
        source_context: Dict[str, str],
        selectors: Optional[Dict[str, str]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Extract event data from HTML element.

        Args:
            html_element: BeautifulSoup element containing event info
            source_context: Dict with source URL, organization name
            selectors: Optional CSS selectors for specific fields

        Returns:
            Event data dict or None if parsing fails
        """
        try:
            event_data = {
                'title': self._extract_title(html_element, selectors),
                'description': self._extract_description(html_element, selectors),
                'start_date': self._extract_date(html_element, selectors),
                'format': self._detect_format(html_element),
                'event_type': self._detect_event_type(html_element),
                'location': self._extract_location(html_element),
                'registration': self._extract_registration(html_element),
                'source': {
                    'type': 'website',
                    'url': source_context.get('url', ''),
                    'name': source_context.get('name', 'Unknown'),
                    'scraped_at': datetime.utcnow().isoformat(),
                },
            }

            # Must have title at minimum
            if not event_data['title']:
                logger.warning("No title found for event")
                return None

            return event_data

        except Exception as e:
            logger.error(f"Failed to parse event: {e}")
            return None

    def _extract_title(
        self,
        element: Tag,
        selectors: Optional[Dict[str, str]] = None
    ) -> Optional[str]:
        """Extract event title."""
        # Try custom selector first
        if selectors and selectors.get('title'):
            title_elem = element.select_one(selectors['title'])
            if title_elem:
                return title_elem.get_text(strip=True)

        # Try common title selectors
        for selector in ['h1', 'h2', 'h3', '.event-title', '.title', '[class*="title"]', 'a']:
            title_elem = element.select_one(selector)
            if title_elem and title_elem.get_text(strip=True):
                text = title_elem.get_text(strip=True)
                if len(text) > 5:  # Filter out very short text
                    return text[:500]  # Truncate very long titles

        # Fallback: first substantial text
        text = element.get_text(strip=True)
        if text:
            return text[:200]

        return None

    def _extract_description(
        self,
        element: Tag,
        selectors: Optional[Dict[str, str]] = None
    ) -> Optional[str]:
        """Extract event description."""
        # Try custom selector first
        if selectors and selectors.get('description'):
            desc_elem = element.select_one(selectors['description'])
            if desc_elem:
                return desc_elem.get_text(strip=True)

        # Try common description selectors
        for selector in ['.description', '.event-description', '.summary', 'p', '.content']:
            desc_elem = element.select_one(selector)
            if desc_elem:
                text = desc_elem.get_text(strip=True)
                if len(text) > 50:  # Ensure substantial content
                    return text[:2000]  # Truncate very long descriptions

        return None

    def _extract_date(
        self,
        element: Tag,
        selectors: Optional[Dict[str, str]] = None
    ) -> Optional[str]:
        """Extract and parse event date."""
        text = ""

        # Try custom selector first
        if selectors and selectors.get('date'):
            date_elem = element.select_one(selectors['date'])
            if date_elem:
                # Check datetime attribute
                if date_elem.has_attr('datetime'):
                    try:
                        return date_parser.parse(date_elem['datetime']).isoformat()
                    except Exception:
                        pass
                text = date_elem.get_text(strip=True)

        # Try common date selectors
        if not text:
            date_elem = element.select_one('.date, .event-date, time[datetime], [class*="date"]')
            if date_elem:
                if date_elem.has_attr('datetime'):
                    try:
                        return date_parser.parse(date_elem['datetime']).isoformat()
                    except Exception:
                        pass
                text = date_elem.get_text(strip=True)

        # Try to parse from element text
        if not text:
            text = element.get_text()

        # Use dateutil's flexible parser
        try:
            parsed = date_parser.parse(text, fuzzy=True)
            return parsed.isoformat()
        except Exception:
            pass

        # Try regex patterns
        for pattern in self.DATE_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    parsed = date_parser.parse(match.group())
                    return parsed.isoformat()
                except Exception:
                    continue

        return None

    def _detect_format(self, element: Tag) -> str:
        """Detect if event is online, in-person, or hybrid."""
        text = element.get_text().lower()

        if any(kw in text for kw in self.FORMAT_KEYWORDS['hybrid']):
            return 'hybrid'
        if any(kw in text for kw in self.FORMAT_KEYWORDS['online']):
            return 'online'
        if any(kw in text for kw in self.FORMAT_KEYWORDS['in-person']):
            return 'in-person'

        # Default based on presence of location
        if element.select_one('.location, .venue, .address, [class*="location"]'):
            return 'in-person'

        return 'online'

    def _detect_event_type(self, element: Tag) -> str:
        """Detect event type from content."""
        text = element.get_text().lower()

        for event_type, keywords in self.EVENT_TYPE_KEYWORDS.items():
            if any(kw in text for kw in keywords):
                return event_type

        return 'other'

    def _extract_location(self, element: Tag) -> Dict[str, Optional[str]]:
        """Extract location information."""
        location: Dict[str, Optional[str]] = {}

        # Look for location elements
        loc_elem = element.select_one('.location, .venue, .address, [class*="location"]')
        if loc_elem:
            text = loc_elem.get_text(strip=True)
            location['venue'] = text

            # Try to extract city/country from "City, Country" pattern
            parts = [p.strip() for p in text.split(',')]
            if len(parts) >= 2:
                location['city'] = parts[0]
                location['country'] = parts[-1]

        # Check for online URL
        for zoom_link in element.select('a[href*="zoom"], a[href*="meet.google"], a[href*="teams"]'):
            if zoom_link.has_attr('href'):
                location['online_url'] = zoom_link['href']
                break

        return location

    def _extract_registration(self, element: Tag) -> Dict[str, Optional[str]]:
        """Extract registration information."""
        registration: Dict[str, Optional[str]] = {}

        # Look for registration links
        for reg_link in element.select('a[href*="register"], a[href*="registration"], a[href*="signup"], a[href*="sign-up"]'):
            if reg_link.has_attr('href'):
                registration['url'] = reg_link['href']
                break

        # Look for price/fee information
        text = element.get_text()

        fee_patterns = [
            r'\$\d+(?:\.\d{2})?',      # $50 or $50.00
            r'€\d+(?:\.\d{2})?',       # €50
            r'£\d+(?:\.\d{2})?',       # £50
            r'\bfree\b',              # Free
            r'no charge',
            r'complimentary',
        ]

        for pattern in fee_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                registration['fee'] = match.group()
                break

        return registration

    def extract_event_url(self, element: Tag) -> Optional[str]:
        """Extract event detail URL."""
        # Try to find link in element
        link = element.select_one('a[href]')
        if link and link.has_attr('href'):
            return link['href']

        # Check if element itself is a link
        if element.name == 'a' and element.has_attr('href'):
            return element['href']

        return None
