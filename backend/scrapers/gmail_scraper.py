"""Gmail newsletter scraper for psychoanalytic events."""

import os
import base64
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from email import message_from_bytes

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from .base import BaseScraper
from ..parsers.newsletter_parser import NewsletterParser

logger = logging.getLogger(__name__)

# Gmail API scopes - read only
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']


class GmailNewsletterScraper(BaseScraper):
    """Scraper for Gmail newsletters containing psychoanalytic events."""

    def __init__(self, source_configs: List[Dict[str, Any]], credentials_path: str = None):
        """
        Initialize Gmail scraper.

        Args:
            source_configs: List of newsletter source configurations
            credentials_path: Path to OAuth credentials JSON
        """
        self.source_configs = source_configs
        self.credentials_path = credentials_path or os.getenv('GMAIL_CREDENTIALS_PATH', 'credentials.json')
        self.token_path = os.getenv('GMAIL_TOKEN_PATH', 'token.json')
        self.service = None
        self.parser = NewsletterParser()

    def _authenticate(self) -> bool:
        """Authenticate with Gmail API."""
        creds = None

        # Load existing token
        if os.path.exists(self.token_path):
            try:
                creds = Credentials.from_authorized_user_file(self.token_path, SCOPES)
            except Exception as e:
                logger.warning(f"Failed to load token: {e}")

        # Refresh or get new credentials
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                except Exception as e:
                    logger.error(f"Failed to refresh credentials: {e}")
                    creds = None

            if not creds:
                if not os.path.exists(self.credentials_path):
                    logger.error(f"Credentials file not found: {self.credentials_path}")
                    return False

                try:
                    flow = InstalledAppFlow.from_client_secrets_file(
                        self.credentials_path, SCOPES
                    )
                    creds = flow.run_local_server(port=0)
                except Exception as e:
                    logger.error(f"Failed to authenticate: {e}")
                    return False

            # Save credentials
            try:
                with open(self.token_path, 'w') as token:
                    token.write(creds.to_json())
            except Exception as e:
                logger.warning(f"Failed to save token: {e}")

        try:
            self.service = build('gmail', 'v1', credentials=creds)
            return True
        except Exception as e:
            logger.error(f"Failed to build Gmail service: {e}")
            return False

    def scrape(self) -> List[Dict[str, Any]]:
        """Scrape events from all configured newsletter sources."""
        if not self._authenticate():
            logger.error("Gmail authentication failed")
            return []

        all_events = []

        for source_config in self.source_configs:
            if not source_config.get('enabled', True):
                continue

            config = source_config.get('config', {})
            sender = config.get('gmail_sender')

            # Sender is optional if subject pattern is provided
            if not sender and not config.get('gmail_subject_pattern'):
                logger.warning(f"Skipping source {source_config.get('name')} - missing both sender and subject pattern")
                continue

            try:
                events = self._scrape_newsletter(
                    sender=sender,
                    subject_pattern=config.get('gmail_subject_pattern'),
                    source_name=source_config.get('name', 'Newsletter'),
                )
                all_events.extend(events)
                logger.info(f"Scraped {len(events)} events matching config for {source_config.get('name')}")
            except Exception as e:
                logger.error(f"Failed to scrape source {source_config.get('name')}: {e}")
                continue

        return all_events

    def _scrape_newsletter(
        self,
        sender: Optional[str] = None,
        subject_pattern: Optional[str] = None,
        source_name: str = 'Newsletter',
        days_back: int = 30
    ) -> List[Dict[str, Any]]:
        """Scrape events from a specific newsletter."""
        # Build query
        after_date = (datetime.now() - timedelta(days=days_back)).strftime('%Y/%m/%d')
        query_parts = [f'after:{after_date}']
        
        if sender:
            query_parts.append(f'from:{sender}')
        
        if subject_pattern:
            query_parts.append(f'subject:({subject_pattern})')
            
        query = ' '.join(query_parts)

        try:
            # Search for messages
            results = self.service.users().messages().list(
                userId='me',
                q=query,
                maxResults=10
            ).execute()

            messages = results.get('messages', [])
            logger.info(f"Found {len(messages)} newsletters from {sender}")

            events = []
            for msg in messages:
                msg_events = self._process_message(msg['id'], {
                    'name': source_name,
                    'email': sender,
                })
                events.extend(msg_events)

            return events

        except Exception as e:
            logger.error(f"Failed to fetch newsletters from {sender}: {e}")
            return []

    def _process_message(self, message_id: str, source_info: Dict) -> List[Dict[str, Any]]:
        """Process a single email message."""
        try:
            message = self.service.users().messages().get(
                userId='me',
                id=message_id,
                format='full'
            ).execute()

            # Get headers
            payload = message.get('payload', {})
            headers = payload.get('headers', [])
            # Case insensitive header search
            from_header = next((h['value'] for h in headers if h['name'].lower() == 'from'), source_info.get('email', 'Unknown'))
            subject_header = next((h['value'] for h in headers if h['name'].lower() == 'subject'), 'No Subject')
            
            # Get email content
            body = self._get_body(payload)

            if not body:
                return []

            # Parse events from email content
            events = self.parser.parse_newsletter(body, source_info)

            # Add message metadata
            for event in events:
                url_val = f"mailto:{from_header}" if 'mailto:' not in from_header and '@' in from_header else from_header
                if 'mailto:' not in url_val and 'http' not in url_val:
                     # Fallback for unknown sender to pass validation (will be filtered later if needed)
                     url_val = f"mailto:unknown@example.com" 
                
                event['source'] = {
                    'type': 'newsletter',
                    'url': url_val,
                    'name': source_info.get('name', 'Newsletter'),
                    'email_subject': subject_header,
                    'scraped_at': datetime.utcnow().isoformat(),
                }
                logger.debug(f"Event: {event.get('title')[:30]}... URL: {url_val}")

            return events

        except Exception as e:
            logger.error(f"Failed to process message {message_id}: {e}")
            return []

    def _get_body(self, payload: Dict) -> str:
        """Extract body content from email payload."""
        body = ""

        # Try to get HTML content first
        if payload.get('mimeType') == 'text/html':
            data = payload.get('body', {}).get('data', '')
            if data:
                body = base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')

        # Try parts
        parts = payload.get('parts', [])
        for part in parts:
            mime_type = part.get('mimeType', '')

            if mime_type == 'text/html':
                data = part.get('body', {}).get('data', '')
                if data:
                    body = base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
                    break

            elif mime_type == 'text/plain' and not body:
                data = part.get('body', {}).get('data', '')
                if data:
                    body = base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')

            # Handle multipart
            elif 'multipart' in mime_type:
                nested_body = self._get_body(part)
                if nested_body:
                    body = nested_body
                    break

        return body

    def close(self):
        """Clean up resources."""
        self.service = None
