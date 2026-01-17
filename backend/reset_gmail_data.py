#!/usr/bin/env python3
"""Script to remove newsletter events to allow fresh scrape."""

import sys
import os
import json

# Add parent dir to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.storage.json_storage import JSONStorage

def main():
    # Change to project root
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.chdir(project_root)
    
    storage = JSONStorage('data')
    events = storage.load_events()
    
    if not events:
        print("No events found.")
        return
        
    # Keep only non-newsletter events
    kept_events = [e for e in events if e.get('source', {}).get('type') != 'newsletter']
    
    print(f"Original count: {len(events)}")
    print(f"Kept count (websites): {len(kept_events)}")
    print(f"Removed count (newsletters): {len(events) - len(kept_events)}")
    
    storage.save_events(kept_events)
    print("Updated data/events.json")

if __name__ == '__main__':
    main()
