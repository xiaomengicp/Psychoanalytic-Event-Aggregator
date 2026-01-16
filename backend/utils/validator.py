"""Event validation and completeness scoring."""

import logging
from typing import Tuple, List, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class EventValidator:
    """Validates event data and calculates completeness."""

    REQUIRED_FIELDS = ['title', 'source']
    
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
        if event.get('title') and len(event['title']) < 3:
            errors.append("Title is too short")

        # Validate dates
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

        return len(errors) == 0, errors

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
            return bool(registration.get('url'))
        return False
