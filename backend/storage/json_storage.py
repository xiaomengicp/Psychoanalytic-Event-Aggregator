"""JSON file storage for events and sources."""

import json
import os
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class JSONStorage:
    """Handles JSON file storage with atomic writes."""

    def __init__(self, data_dir: str = "data"):
        """
        Initialize storage.

        Args:
            data_dir: Directory for data files
        """
        self.data_dir = data_dir
        self.events_file = os.path.join(data_dir, "events.json")
        self.sources_file = os.path.join(data_dir, "sources.json")
        
        # Ensure data directory exists
        os.makedirs(data_dir, exist_ok=True)

    def load_events(self) -> List[Dict[str, Any]]:
        """Load events from JSON file."""
        return self._load_json(self.events_file, default=[])

    def save_events(self, events: List[Dict[str, Any]]) -> None:
        """Save events to JSON file."""
        # Add metadata
        data = {
            "metadata": {
                "last_updated": datetime.utcnow().isoformat(),
                "count": len(events),
            },
            "events": events,
        }
        self._save_json(self.events_file, data)
        logger.info(f"Saved {len(events)} events to {self.events_file}")

    def load_sources(self) -> List[Dict[str, Any]]:
        """Load source configurations from JSON file."""
        return self._load_json(self.sources_file, default=[])

    def save_sources(self, sources: List[Dict[str, Any]]) -> None:
        """Save source configurations to JSON file."""
        self._save_json(self.sources_file, sources)
        logger.info(f"Saved {len(sources)} sources to {self.sources_file}")

    def update_source_last_scraped(
        self,
        source_id: str,
        scraped_at: Optional[datetime] = None
    ) -> None:
        """
        Update last_scraped timestamp for a source.

        Args:
            source_id: Source identifier
            scraped_at: Timestamp (defaults to now)
        """
        sources = self.load_sources()
        
        for source in sources:
            if source.get('id') == source_id:
                source['last_scraped'] = (scraped_at or datetime.utcnow()).isoformat()
                break
        
        self.save_sources(sources)

    def add_events(self, new_events: List[Dict[str, Any]]) -> int:
        """
        Add new events, merging with existing.

        Args:
            new_events: List of new events

        Returns:
            Number of events added
        """
        existing = self.load_events()
        existing_ids = {e.get('id') for e in existing if e.get('id')}
        
        added = 0
        for event in new_events:
            if event.get('id') not in existing_ids:
                existing.append(event)
                added += 1
            else:
                # Update existing event
                for i, e in enumerate(existing):
                    if e.get('id') == event.get('id'):
                        existing[i] = event
                        break
        
        self.save_events(existing)
        logger.info(f"Added {added} new events, updated {len(new_events) - added} existing")
        return added

    def remove_past_events(self, keep_days: int = 7) -> int:
        """
        Remove events that have passed.

        Args:
            keep_days: Keep events up to this many days in the past

        Returns:
            Number of events removed
        """
        events = self.load_events()
        cutoff = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Keep events without dates or with future dates
        filtered = []
        removed = 0
        
        for event in events:
            start_date = event.get('start_date')
            if not start_date:
                filtered.append(event)
                continue
            
            try:
                if isinstance(start_date, str):
                    event_date = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                else:
                    event_date = start_date
                
                # Keep if within keep_days
                days_ago = (cutoff - event_date.replace(tzinfo=None)).days
                if days_ago <= keep_days:
                    filtered.append(event)
                else:
                    removed += 1
            except (ValueError, TypeError):
                filtered.append(event)
        
        if removed > 0:
            self.save_events(filtered)
            logger.info(f"Removed {removed} past events")
        
        return removed

    def _load_json(self, filepath: str, default: Any = None) -> Any:
        """Load JSON file with error handling."""
        if not os.path.exists(filepath):
            return default if default is not None else {}
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # Handle both direct list and wrapper object
                if isinstance(data, dict) and 'events' in data:
                    return data['events']
                return data
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"Error loading {filepath}: {e}")
            return default if default is not None else {}

    def _save_json(self, filepath: str, data: Any) -> None:
        """Save JSON file atomically."""
        temp_path = f"{filepath}.tmp"
        
        try:
            with open(temp_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False, default=str)
            
            # Atomic rename
            os.replace(temp_path, filepath)
        except IOError as e:
            logger.error(f"Error saving {filepath}: {e}")
            # Clean up temp file if exists
            if os.path.exists(temp_path):
                os.remove(temp_path)
            raise
