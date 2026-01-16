#!/usr/bin/env python3
"""Script to run ONLY the Gmail scraper."""

import sys
import os
import logging
import json

# Add parent dir to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.storage.json_storage import JSONStorage
from backend.utils.validator import EventValidator
from backend.utils.merger import EventMerger
from backend.scrapers.gmail_scraper import GmailNewsletterScraper

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    # Change to project root
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.chdir(project_root)
    
    storage = JSONStorage('data')
    sources = storage.load_sources()
    
    # Filter only newsletter sources
    newsletter_sources = [s for s in sources if s.get('type') == 'newsletter' and s.get('enabled', True)]
    
    if not newsletter_sources:
        print("No newsletter sources configured!")
        return
        
    print(f"Running Gmail scraper for {len(newsletter_sources)} sources...")
    
    try:
        scraper = GmailNewsletterScraper(newsletter_sources)
        events = scraper.scrape()
        print(f"Extracted {len(events)} total raw events")
        
        # Validate
        validator = EventValidator()
        valid_events = []
        for event in events:
            is_valid, errors = validator.validate(event)
            if is_valid:
                valid_events.append(event)
            else:
                logger.warning(f"Invalid event: {errors}")
                
        print(f"Valid events: {len(valid_events)}")
        
        # Save
        if valid_events:
            merger = EventMerger()
            existing_events = storage.load_events()
            merged = merger.deduplicate(existing_events + valid_events)
            storage.save_events(merged)
            print(f"Saved {len(merged)} total events")
            
    except Exception as e:
        logger.error(f"Error: {e}")

if __name__ == '__main__':
    main()
