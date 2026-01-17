#!/usr/bin/env python3
"""Script to clean existing events.json using strict validator rules."""

import sys
import os
import logging
import json

# Add parent dir to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.storage.json_storage import JSONStorage
from backend.utils.validator import EventValidator

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    # Change to project root
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.chdir(project_root)
    
    storage = JSONStorage('data')
    events = storage.load_events()
    
    if not events:
        print("No events found to clean.")
        return
        
    print(f"Loaded {len(events)} events. validation...")
    
    validator = EventValidator()
    valid_events = []
    removed_counts = {
        'missing_date': 0,
        'past_event': 0,
        'other': 0
    }
    
    for event in events:
        # Check start_date specifically for logging
        if not event.get('start_date'):
            removed_counts['missing_date'] += 1
            continue
            
        if not validator._is_valid_date(event.get('start_date')):
            removed_counts['past_event'] += 1
            continue

        is_valid, errors = validator.validate(event)
        if is_valid:
            valid_events.append(event)
        else:
            removed_counts['other'] += 1
            # logger.warning(f"Removing invalid event: {event.get('title')} - {errors}")

    print(f"Validation complete.")
    print(f"Kept: {len(valid_events)}")
    print(f"Removed: {len(events) - len(valid_events)}")
    print(f"  - Missing Date: {removed_counts['missing_date']}")
    print(f"  - Past/Invalid Date: {removed_counts['past_event']}")
    print(f"  - Other Validation Errors: {removed_counts['other']}")
    
    if len(valid_events) < len(events):
        storage.save_events(valid_events)
        print("Updated data/events.json with cleaned data.")
    else:
        print("No events removed.")

if __name__ == '__main__':
    main()
