"""Event deduplication and merging."""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import re

logger = logging.getLogger(__name__)


class EventMerger:
    """Identifies and merges duplicate events."""

    def __init__(self, similarity_threshold: float = 0.7):
        """
        Initialize merger.

        Args:
            similarity_threshold: Minimum similarity (0-1) to consider duplicates
        """
        self.similarity_threshold = similarity_threshold

    def deduplicate(self, events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Find and merge duplicate events.

        Args:
            events: List of event dictionaries

        Returns:
            Deduplicated list of events
        """
        if not events:
            return []

        unique_events: List[Dict[str, Any]] = []
        
        for event in events:
            duplicate_found = False
            
            for i, existing in enumerate(unique_events):
                if self._are_duplicates(event, existing):
                    # Merge into existing event
                    unique_events[i] = self.merge_events(existing, event)
                    duplicate_found = True
                    logger.debug(f"Merged duplicate: {event.get('title', 'Unknown')}")
                    break
            
            if not duplicate_found:
                unique_events.append(event)

        logger.info(f"Deduplicated {len(events)} events to {len(unique_events)}")
        return unique_events

    def _are_duplicates(self, event1: Dict[str, Any], event2: Dict[str, Any]) -> bool:
        """Check if two events are duplicates."""
        # Compare titles (fuzzy match)
        title1 = self._normalize_text(event1.get('title', ''))
        title2 = self._normalize_text(event2.get('title', ''))
        
        title_similarity = self._calculate_similarity(title1, title2)
        
        if title_similarity < self.similarity_threshold:
            return False

        # If titles are similar, check dates
        date1 = self._parse_date(event1.get('start_date'))
        date2 = self._parse_date(event2.get('start_date'))
        
        if date1 and date2:
            # Same day or within 1 day tolerance
            if abs((date1 - date2).days) > 1:
                return False

        return True

    def _normalize_text(self, text: str) -> str:
        """Normalize text for comparison."""
        if not text:
            return ""
        # Lowercase, remove extra whitespace, remove special chars
        text = text.lower().strip()
        text = re.sub(r'[^\w\s]', '', text)
        text = re.sub(r'\s+', ' ', text)
        return text

    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate Jaccard similarity between two texts."""
        if not text1 or not text2:
            return 0.0

        words1 = set(text1.split())
        words2 = set(text2.split())

        if not words1 and not words2:
            return 1.0
        if not words1 or not words2:
            return 0.0

        intersection = words1 & words2
        union = words1 | words2

        return len(intersection) / len(union)

    def _parse_date(self, date_value: Any) -> Optional[datetime]:
        """Parse date from various formats."""
        if not date_value:
            return None
        
        if isinstance(date_value, datetime):
            return date_value
        
        if isinstance(date_value, str):
            try:
                return datetime.fromisoformat(date_value.replace('Z', '+00:00'))
            except ValueError:
                return None
        
        return None

    def merge_events(
        self,
        event1: Dict[str, Any],
        event2: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Merge two events, preferring more complete data.

        Args:
            event1: First event
            event2: Second event

        Returns:
            Merged event
        """
        # Start with event1 as base
        merged = event1.copy()

        # Fields to merge (prefer non-empty values)
        simple_fields = ['description', 'timezone', 'event_type', 'format']
        
        for field in simple_fields:
            if not merged.get(field) and event2.get(field):
                merged[field] = event2[field]

        # Merge nested objects
        merged['location'] = self._merge_dicts(
            event1.get('location', {}),
            event2.get('location', {})
        )
        merged['organizer'] = self._merge_dicts(
            event1.get('organizer', {}),
            event2.get('organizer', {})
        )
        merged['registration'] = self._merge_dicts(
            event1.get('registration', {}),
            event2.get('registration', {})
        )

        # Merge tags
        tags1 = set(event1.get('tags', []))
        tags2 = set(event2.get('tags', []))
        merged['tags'] = list(tags1 | tags2)

        # Track sources (could store both sources if needed)
        # For now, keep the original source

        # Update timestamp
        merged['updated_at'] = datetime.utcnow().isoformat()

        return merged

    def _merge_dicts(self, dict1: Dict, dict2: Dict) -> Dict:
        """Merge two dictionaries, preferring non-empty values from dict2."""
        if not isinstance(dict1, dict):
            dict1 = {}
        if not isinstance(dict2, dict):
            dict2 = {}

        merged = dict1.copy()
        
        for key, value in dict2.items():
            if value and not merged.get(key):
                merged[key] = value

        return merged
