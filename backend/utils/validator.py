"""Event validation and completeness scoring."""

import logging
import re
from typing import Tuple, List, Dict, Any
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class EventValidator:
    """Validates event data and calculates completeness."""

    REQUIRED_FIELDS = ['title', 'source']
    
    # Titles that indicate non-event items (navigation, buttons, garbage, etc.)
    INVALID_TITLE_PATTERNS = [
        # Navigation / buttons
        r'^read more$',
        r'^learn more$',
        r'^click here$',
        r'^register$',
        r'^sign up$',
        r'^view all$',
        r'^see more$',
        r'^more info$',
        r'^details$',
        r'^back$',
        r'^next$',
        r'^previous$',
        r'^home$',
        r'^menu$',
        r'^contact',
        r'^about',
        r'^subscribe',
        r'^newsletter',
        r'^follow us',
        r'^\d+$',  # Just numbers
        r'^[a-z]$',  # Single letter
        # Archive / past / navigation links
        r'^see past events',
        r'^see presentation',
        r'^past events',
        r'^view archive',
        r'^archive',
        r'^events$',  # Just "Events"
        r'^all events',
        r'^upcoming events',
        r'^event calendar',
        r'^add your event',
        # Marketing / promotional text  
        r'^virtual\s*\|',  # "Virtual | Free | ..."
        r'^free\s*\|',
        r'^promotion of',
        r'^please note',
        r'^disclaimer',
        # Multi-category text (navigation tabs)
        r'bpc event.*mi event',
        r'all events.*bpc event',
        # Very short or generic
        r'^.{1,4}$',  # Too short (4 chars or less)
        # Contains only format/fee info
        r'^(online|in-person|hybrid|free|virtual)(\s*\|\s*(online|in-person|hybrid|free|virtual|dle|c&c))*$',
    ]
    
    # Keywords that if present at START suggest garbage
    GARBAGE_START_KEYWORDS = [
        'see ', 'view ', 'browse ', 'all ', 'our ', 'your ',
        'please ', 'note:', 'disclaimer', 'promotion '
    ]
    
    COMPLETENESS_WEIGHTS = {
        'title': 20,
        'start_date': 20,
        'event_type': 10,
        'format': 10,
        'description': 10,
        'location': 10,
        'organizer': 10,
        'registration_url': 10,
    }

    def validate(self, event: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate event data.

        Args:
            event: Event dictionary

        Returns:
            Tuple of (is_valid, list of errors)
        """
        errors = []

        # Check required fields
        for field in self.REQUIRED_FIELDS:
            if not event.get(field):
                errors.append(f"Missing required field: {field}")

        # Validate title
        title = event.get('title', '')
        if title:
            if len(title) < 5:
                errors.append("Title is too short (< 5 chars)")
            elif len(title) > 500:
                errors.append("Title is too long (> 500 chars)")
            elif self._is_invalid_title(title):
                errors.append("Title looks like navigation/button text")
        
        # Date validation: if provided, should be reasonable
        # Allow events without dates, but reject clearly past events
        start_date = event.get('start_date')
        if start_date and not self._is_valid_date(start_date):
            errors.append("Invalid or too old start_date")

        # Validate dates format
        if event.get('start_date'):
            try:
                if isinstance(event['start_date'], str):
                    datetime.fromisoformat(event['start_date'].replace('Z', '+00:00'))
            except ValueError:
                errors.append("Invalid start_date format")

        if event.get('end_date'):
            try:
                if isinstance(event['end_date'], str):
                    datetime.fromisoformat(event['end_date'].replace('Z', '+00:00'))
            except ValueError:
                errors.append("Invalid end_date format")

        # Validate format
        valid_formats = ['online', 'in-person', 'hybrid']
        if event.get('format') and event['format'] not in valid_formats:
            errors.append(f"Invalid format: {event['format']}")

        # Validate event_type
        valid_types = ['conference', 'workshop', 'lecture', 'seminar', 'webinar', 'course', 'other']
        if event.get('event_type') and event['event_type'] not in valid_types:
            errors.append(f"Invalid event_type: {event['event_type']}")

        # Must have valid registration URL or event URL
        if not self._has_valid_url(event):
            errors.append("Missing valid registration/event URL")

        return len(errors) == 0, errors

    def _is_invalid_title(self, title: str) -> bool:
        """Check if title matches invalid patterns or is likely garbage."""
        title_lower = title.lower().strip()
        
        # Check regex patterns
        for pattern in self.INVALID_TITLE_PATTERNS:
            if re.match(pattern, title_lower, re.IGNORECASE):
                return True
        
        # Check garbage start keywords
        for keyword in self.GARBAGE_START_KEYWORDS:
            if title_lower.startswith(keyword):
                return True
        
        # Title is too long (likely scraped an entire paragraph)
        if len(title) > 200:
            return True
            
        return False

    def _is_valid_date(self, date_value: Any) -> bool:
        """Check if date is valid and not too far in the past.
        
        More lenient validation:
        - Events up to 30 days in the past are OK (for recently passed)
        - Events up to 3 years in the future are OK
        """
        if not date_value:
            return True  # No date is OK - we don't want to filter out events without dates
        
        try:
            if isinstance(date_value, str):
                dt = datetime.fromisoformat(date_value.replace('Z', '+00:00'))
            elif isinstance(date_value, datetime):
                dt = date_value
            else:
                return True  # Unknown format, allow it
            
            # Allow events up to 30 days in the past (for recently passed events)
            # and up to 3 years in the future
            now = datetime.now(dt.tzinfo) if dt.tzinfo else datetime.now()
            min_date = now - timedelta(days=30)
            max_date = now + timedelta(days=1095)  # ~3 years
            
            return min_date <= dt <= max_date
        except (ValueError, TypeError):
            return True  # If we can't parse, don't filter it out

    def _has_valid_url(self, event: Dict[str, Any]) -> bool:
        """Check if event has a valid URL."""
        # Check registration URL
        registration = event.get('registration', {})
        if isinstance(registration, dict):
            url = registration.get('url', '')
            if url and self._is_valid_url(url):
                return True
        
        # Check source URL as fallback
        source = event.get('source', {})
        if isinstance(source, dict):
            url = source.get('url', '')
            if url and self._is_valid_url(url):
                return True
        
        return False

    def _is_valid_url(self, url: str) -> bool:
        """Simple URL validation."""
        if not url or not isinstance(url, str):
            return False
        url = url.strip()
        # Must start with http/https and have reasonable length
        if not url.startswith(('http://', 'https://')):
            return False
        if len(url) < 10:
            return False
        # Basic URL pattern check
        return '.' in url

    def calculate_completeness(self, event: Dict[str, Any]) -> Tuple[int, List[str]]:
        """
        Calculate completeness score for an event.

        Args:
            event: Event dictionary

        Returns:
            Tuple of (score 0-100, list of missing fields)
        """
        score = 0
        missing_fields = []

        checks = {
            'title': bool(event.get('title')),
            'start_date': event.get('start_date') is not None,
            'event_type': event.get('event_type') and event['event_type'] != 'other',
            'format': event.get('format') is not None,
            'description': bool(event.get('description')),
            'location': self._has_location(event),
            'organizer': self._has_organizer(event),
            'registration_url': self._has_registration(event),
        }

        for field, has_value in checks.items():
            weight = self.COMPLETENESS_WEIGHTS.get(field, 0)
            if has_value:
                score += weight
            else:
                missing_fields.append(field)

        return score, missing_fields

    def _has_location(self, event: Dict[str, Any]) -> bool:
        """Check if event has meaningful location data."""
        location = event.get('location', {})
        if isinstance(location, dict):
            return bool(
                location.get('venue') or
                location.get('city') or
                location.get('online_url')
            )
        return False

    def _has_organizer(self, event: Dict[str, Any]) -> bool:
        """Check if event has organizer info."""
        organizer = event.get('organizer', {})
        if isinstance(organizer, dict):
            name = organizer.get('name', '')
            return bool(name) and name != 'Unknown'
        return False

    def _has_registration(self, event: Dict[str, Any]) -> bool:
        """Check if event has registration URL."""
        registration = event.get('registration', {})
        if isinstance(registration, dict):
            url = registration.get('url', '')
            return bool(url) and self._is_valid_url(url)
        return False
