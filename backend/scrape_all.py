#!/usr/bin/env python3
"""Main orchestration script for scraping psychoanalytic events."""

import argparse
import logging
import sys
import os
from datetime import datetime
from typing import Dict, Any, List

# Add parent dir to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.storage.json_storage import JSONStorage
from backend.utils.validator import EventValidator
from backend.utils.merger import EventMerger
from backend.scrapers.generic import GenericWebsiteScraper

# Try to import Gmail scraper (optional - requires google libraries)
try:
    from backend.scrapers.gmail_scraper import GmailNewsletterScraper
    GMAIL_AVAILABLE = True
except ImportError:
    GMAIL_AVAILABLE = False
    GmailNewsletterScraper = None

# Custom scrapers
from backend.scrapers.custom.apsa import APsAScraper
from backend.scrapers.custom.bpc import BPCScraper
from backend.scrapers.custom.chicago_psychoanalytic import ChicagoPsychoanalyticScraper
from backend.scrapers.custom.psychoanalytic_inquiry import PsychoanalyticInquiryScraper

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('scraper.log', mode='a')
    ]
)
logger = logging.getLogger(__name__)

# Map custom parser names to classes
CUSTOM_SCRAPERS = {
    'APsAScraper': APsAScraper,
    'BPCScraper': BPCScraper,
    'ChicagoPsychoanalyticScraper': ChicagoPsychoanalyticScraper,
    'PsychoanalyticInquiryScraper': PsychoanalyticInquiryScraper,
}


class ScraperOrchestrator:
    """Orchestrates all scraping operations."""

    def __init__(self, data_dir: str = "data", dry_run: bool = False):
        self.storage = JSONStorage(data_dir)
        self.validator = EventValidator()
        self.merger = EventMerger()
        self.dry_run = dry_run
        self.results = {
            'total_sources': 0,
            'successful': 0,
            'failed': 0,
            'new_events': 0,
            'errors': []
        }

    def run(self) -> Dict[str, Any]:
        """Run all scrapers and update data."""
        logger.info("Starting scraping run...")
        sources = self.storage.load_sources()

        if not sources:
            logger.warning("No sources configured")
            return self.results

        all_events = []
        website_sources = [s for s in sources if s.get('type') == 'website' and s.get('enabled', True)]
        newsletter_sources = [s for s in sources if s.get('type') == 'newsletter' and s.get('enabled', True)]

        self.results['total_sources'] = len(website_sources) + len(newsletter_sources)

        # Scrape websites
        for source in website_sources:
            try:
                events = self._scrape_website(source)
                all_events.extend(events)
                self.storage.update_source_last_scraped(source['id'])
                self.results['successful'] += 1
            except Exception as e:
                logger.error(f"Failed to scrape {source.get('name')}: {e}")
                self.results['failed'] += 1
                self.results['errors'].append({
                    'source': source.get('name'),
                    'error': str(e)
                })

        # Scrape newsletters
        if newsletter_sources and GMAIL_AVAILABLE:
            try:
                gmail_scraper = GmailNewsletterScraper(newsletter_sources)
                events = gmail_scraper.scrape()
                all_events.extend(events)
                for source in newsletter_sources:
                    self.storage.update_source_last_scraped(source['id'])
                self.results['successful'] += len(newsletter_sources)
            except Exception as e:
                logger.error(f"Failed to scrape newsletters: {e}")
                self.results['failed'] += len(newsletter_sources)
                self.results['errors'].append({
                    'source': 'Gmail Newsletters',
                    'error': str(e)
                })
        elif newsletter_sources and not GMAIL_AVAILABLE:
            logger.warning("Gmail scraping skipped - google libraries not installed")

        # Process events
        logger.info(f"Collected {len(all_events)} raw events")

        # Validate events
        valid_events = []
        for event in all_events:
            is_valid, errors = self.validator.validate(event)
            if is_valid:
                # Calculate completeness
                score, missing = self.validator.calculate_completeness(event)
                event['completeness_score'] = score
                event['missing_fields'] = missing
                valid_events.append(event)
            else:
                logger.warning(f"Invalid event: {errors}")

        # Deduplicate
        unique_events = self.merger.deduplicate(valid_events)
        logger.info(f"After deduplication: {len(unique_events)} events")

        # Save
        if not self.dry_run:
            existing_events = self.storage.load_events()
            existing_count = len(existing_events)

            # Merge with existing
            merged = self.merger.deduplicate(existing_events + unique_events)
            self.storage.save_events(merged)

            self.results['new_events'] = len(merged) - existing_count
            logger.info(f"Saved {len(merged)} total events ({self.results['new_events']} new)")

            # Clean up old events
            removed = self.storage.remove_past_events(keep_days=7)
            if removed:
                logger.info(f"Removed {removed} past events")
        else:
            self.results['new_events'] = len(unique_events)
            logger.info(f"[DRY RUN] Would save {len(unique_events)} events")

        return self.results

    def _scrape_website(self, source: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Scrape a single website source."""
        config = source.get('config', {})
        scraper_type = config.get('scraper_type', 'generic')

        if scraper_type == 'custom':
            parser_name = config.get('custom_parser')
            if parser_name in CUSTOM_SCRAPERS:
                scraper_class = CUSTOM_SCRAPERS[parser_name]
                with scraper_class(source) as scraper:
                    return scraper.scrape()
            else:
                raise ValueError(f"Unknown custom parser: {parser_name}")
        else:
            with GenericWebsiteScraper(source) as scraper:
                return scraper.scrape()


def main():
    parser = argparse.ArgumentParser(description='Scrape psychoanalytic events')
    parser.add_argument('--dry-run', action='store_true', help='Run without saving data')
    parser.add_argument('--data-dir', default='data', help='Data directory path')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose logging')
    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Change to project root
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.chdir(project_root)

    orchestrator = ScraperOrchestrator(
        data_dir=args.data_dir,
        dry_run=args.dry_run
    )
    results = orchestrator.run()

    # Print summary
    print("\n=== Scraping Summary ===")
    print(f"Total sources: {results['total_sources']}")
    print(f"Successful: {results['successful']}")
    print(f"Failed: {results['failed']}")
    print(f"New events: {results['new_events']}")

    if results['errors']:
        print("\nErrors:")
        for err in results['errors']:
            print(f"  - {err['source']}: {err['error']}")

    # Exit with error code if all scrapers failed
    if results['successful'] == 0 and results['total_sources'] > 0:
        sys.exit(1)


if __name__ == '__main__':
    main()
