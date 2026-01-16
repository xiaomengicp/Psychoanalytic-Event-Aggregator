"""Newsletter parser for extracting events from email content."""

import re
import logging
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup

from .event_parser import EventParser

logger = logging.getLogger(__name__)


class NewsletterParser:
    """Parse events from email newsletters."""

    def __init__(self):
        self.event_parser = EventParser()

    def parse_newsletter(
        self,
        email_content: str,
        source_info: Dict[str, str]
    ) -> List[Dict[str, Any]]:
        """
        Extract events from newsletter email content.

        Args:
            email_content: Raw email content (HTML or plain text)
            source_info: Dict with source name, email address

        Returns:
            List of event dictionaries
        """
        events = []

        # Parse HTML content
        soup = BeautifulSoup(email_content, 'html.parser')

        # Strategy 1: Look for explicit event sections
        event_sections = soup.select('.event, [class*="event"], .calendar-item')

        # Strategy 2: Look for table rows or list items with dates
        if not event_sections:
            event_sections = self._find_date_containing_elements(soup)

        # Parse each potential event section
        for section in event_sections:
            if self._is_likely_event(section):
                event = self.event_parser.parse_event_from_html(section, {
                    'url': source_info.get('email', ''),
                    'name': source_info.get('name', 'Newsletter'),
                    'type': 'newsletter',
                })
                if event:
                    event['source']['type'] = 'newsletter'
                    events.append(event)

        logger.info(f"Extracted {len(events)} events from newsletter")
        return events

    def _find_date_containing_elements(self, soup: BeautifulSoup) -> List:
        """Find elements that likely contain event information."""
        elements = []

        # Check list items
        for li in soup.select('li'):
            if self._contains_date(li.get_text()):
                elements.append(li)

        # Check table rows
        for tr in soup.select('tr'):
            if self._contains_date(tr.get_text()):
                elements.append(tr)

        # Check divs with reasonable content
        for div in soup.select('div'):
            text = div.get_text()
            if self._contains_date(text) and 50 < len(text) < 1000:
                # Avoid too large or too small divs
                elements.append(div)

        return elements

    def _contains_date(self, text: str) -> bool:
        """Quick check if text contains date patterns."""
        date_indicators = [
            r'\d{1,2}/\d{1,2}/\d{2,4}',
            r'\d{4}-\d{2}-\d{2}',
            r'January|February|March|April|May|June|July|August|September|October|November|December',
            r'Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec',
            r'Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday',
            r'Mon|Tue|Wed|Thu|Fri|Sat|Sun',
        ]
        return any(re.search(pattern, text, re.IGNORECASE) for pattern in date_indicators)

    def _is_likely_event(self, element) -> bool:
        """Check if element is likely to contain event information."""
        text = element.get_text()

        # Must contain a date
        if not self._contains_date(text):
            return False

        # Should have reasonable length
        if len(text) < 20:
            return False

        # Should not be just navigation or footer
        nav_keywords = ['unsubscribe', 'privacy policy', 'terms of service', 'copyright']
        if any(kw in text.lower() for kw in nav_keywords):
            return False

        return True

    def parse_plain_text_newsletter(
        self,
        text: str,
        source_info: Dict[str, str]
    ) -> List[Dict[str, Any]]:
        """
        Parse events from plain text email.

        Args:
            text: Plain text email content
            source_info: Source information

        Returns:
            List of event dictionaries
        """
        events = []

        # Split into potential event blocks
        # Look for date patterns as block separators
        date_pattern = r'(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}'

        # Find all dates
        matches = list(re.finditer(date_pattern, text, re.IGNORECASE))

        for i, match in enumerate(matches):
            # Extract block from this date to next date (or end)
            start = match.start()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(text)

            block = text[start:end].strip()

            if len(block) > 30:  # Minimum content
                # Create minimal event
                lines = block.split('\n')
                title = None

                # Find title (usually first non-date line or second line)
                for line in lines:
                    line = line.strip()
                    if line and not re.match(date_pattern, line, re.IGNORECASE):
                        title = line[:200]
                        break

                if title:
                    events.append({
                        'title': title,
                        'description': block,
                        'start_date': match.group(),
                        'source': {
                            'type': 'newsletter',
                            'url': source_info.get('email', ''),
                            'name': source_info.get('name', 'Newsletter'),
                        }
                    })

        return events
