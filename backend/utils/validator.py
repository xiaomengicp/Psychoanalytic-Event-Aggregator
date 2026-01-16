"""Event validation and completeness scoring."""

import logging
import re
from typing import Tuple, List, Dict, Any
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class EventValidator:
    """Validates event data and calculates completeness."""

    REQUIRED_FIELDS = ['title', 'source']
    
    # Titles that indicate non-event items (navigation, buttons, etc.)
    INVALID_TITLE_PATTERNS = [
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
        
        # Must have a valid date (future or recent)
        if not self._is_valid_date(event.get('start_date')):
            errors.append("Missing or past start_date")

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
        """Check if title matches invalid patterns."""
        title_lower = title.lower().strip()
        for pattern in self.INVALID_TITLE_PATTERNS:
            if re.match(pattern, title_lower, re.IGNORECASE):
                return True
        return False

    def _is_valid_date(self, date_value: Any) -> bool:
        """Check if date is valid and not too far in the past."""
        if not date_value:
            return False
        
        try:
            if isinstance(date_value, str):
                dt = datetime.fromisoformat(date_value.replace('Z', '+00:00'))
            elif isinstance(date_value, datetime):
                dt = date_value
            else:
                return False
            
            # Allow events up to 7 days in the past (for recently passed events)
            # and up to 2 years in the future
            now = datetime.now(dt.tzinfo) if dt.tzinfo else datetime.now()
            min_date = now - timedelta(days=7)
            max_date = now + timedelta(days=730)
            
            return min_date <= dt <= max_date
        except (ValueError, TypeError):
            return False

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
