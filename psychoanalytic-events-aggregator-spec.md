# Psychoanalytic Events Aggregator - Technical Specification

## Project Overview

### Purpose
Build an automated event aggregation system that collects psychoanalytic events from multiple sources (websites and Gmail newsletters) and displays them in a searchable, filterable interface that can be embedded in a Ghost blog.

### Key Requirements
- **Automation**: Daily automated scraping and updates
- **Multiple Sources**: 
  - Psychoanalytic organization websites (configurable)
  - Gmail newsletters from psychoanalytic institutions
- **Data Quality**: Display all events but clearly indicate completeness of information
- **Extensibility**: Easy to add new sources via configuration
- **Embedding**: Must work when embedded in Ghost blog via iframe
- **Language**: English interface and content

### Future Expansion (Not in MVP)
- Paper awards and prizes
- Call for papers (CFPs) for conferences
- Other psychoanalytic opportunities

---

## System Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Data Collection Layer                     │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────────┐         ┌──────────────────┐          │
│  │  Website Scrapers│         │  Gmail API Client│          │
│  │                  │         │                  │          │
│  │  - Generic       │         │  - Newsletter    │          │
│  │  - Custom        │         │    parsing       │          │
│  └────────┬─────────┘         └────────┬─────────┘          │
│           │                            │                     │
│           └────────────┬───────────────┘                     │
│                        │                                     │
│                  ┌─────▼──────┐                              │
│                  │   Parser   │                              │
│                  │  (Regex +  │                              │
│                  │  dateutil) │                              │
│                  └─────┬──────┘                              │
└────────────────────────┼────────────────────────────────────┘
                         │
                    ┌────▼─────┐
                    │ Validator│
                    │ & Merger │
                    └────┬─────┘
                         │
┌────────────────────────▼────────────────────────────────────┐
│                    Data Storage Layer                        │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────────┐         ┌──────────────────┐          │
│  │   events.json    │         │  sources.json    │          │
│  │  (All events)    │         │ (Source configs) │          │
│  └──────────────────┘         └──────────────────┘          │
│                                                               │
│         Stored in GitHub Repository                          │
│         (Version controlled, accessible via raw URLs)        │
└─────────────────────────────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────┐
│                   Presentation Layer                         │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────────────────────────────────────────────┐   │
│  │         Static Web Application (React/Vue)           │   │
│  │                                                       │   │
│  │  - Fetches events.json on load                       │   │
│  │  - Client-side filtering and search                  │   │
│  │  - Responsive design for iframe embedding            │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                               │
│         Hosted on: GitHub Pages / Netlify / Vercel           │
└─────────────────────────────────────────────────────────────┘
                         │
                    Embedded in
                         │
                  ┌──────▼──────┐
                  │ Ghost Blog  │
                  │  via iframe │
                  └─────────────┘
```

### Technology Stack

**Backend (Python)**
- `requests` / `httpx` - HTTP requests
- `beautifulsoup4` - HTML parsing
- `lxml` - Fast HTML/XML processing
- `google-auth` / `google-api-python-client` - Gmail API
- `pydantic` - Data validation
- `python-dateutil` - Flexible date parsing
- `email` (stdlib) - Email parsing
- `re` (stdlib) - Pattern matching
- GitHub Actions - Automation

**Frontend**
- React or Vue.js (lightweight)
- Tailwind CSS for styling
- No backend required (purely static)

**Infrastructure**
- GitHub Repository (code + data storage)
- GitHub Actions (automated scraping)
- GitHub Pages / Netlify (static hosting)
- Gmail API (newsletter access)

---

## Data Model

### Event Schema

```json
{
  "id": "string (unique identifier, generated from url + date hash)",
  "title": "string",
  "description": "string (optional)",
  "event_type": "enum: ['conference', 'workshop', 'lecture', 'seminar', 'webinar', 'course', 'other']",
  "format": "enum: ['online', 'in-person', 'hybrid']",
  "start_date": "ISO 8601 datetime",
  "end_date": "ISO 8601 datetime (optional)",
  "timezone": "string (IANA timezone, e.g., 'America/New_York')",
  "location": {
    "venue": "string (optional)",
    "address": "string (optional)",
    "city": "string (optional)",
    "country": "string (optional)",
    "online_url": "string (optional, for online events)"
  },
  "organizer": {
    "name": "string",
    "url": "string (optional)",
    "email": "string (optional)"
  },
  "registration": {
    "url": "string (optional)",
    "deadline": "ISO 8601 datetime (optional)",
    "fee": "string (optional, e.g., 'Free', '$50', '€30 members / €50 non-members')"
  },
  "source": {
    "type": "enum: ['website', 'newsletter']",
    "url": "string",
    "name": "string (source organization name)",
    "scraped_at": "ISO 8601 datetime"
  },
  "completeness_score": "integer (0-100, indicates how complete the information is)",
  "missing_fields": "array of strings (list of important missing fields)",
  "tags": "array of strings (optional, e.g., ['Lacanian', 'Relational', 'Child Analysis'])",
  "created_at": "ISO 8601 datetime",
  "updated_at": "ISO 8601 datetime"
}
```

### Source Configuration Schema

```json
{
  "id": "string (unique identifier)",
  "name": "string (organization name)",
  "type": "enum: ['website', 'newsletter']",
  "enabled": "boolean",
  "config": {
    // For website sources
    "url": "string",
    "scraper_type": "enum: ['generic', 'custom']",
    "custom_parser": "string (optional, name of custom parser function)",
    "selectors": {
      "event_list": "string (CSS selector for event container)",
      "event_item": "string (CSS selector for individual events)",
      "title": "string (CSS selector)",
      "date": "string (CSS selector)",
      "description": "string (CSS selector)",
      "link": "string (CSS selector)"
    },
    
    // For newsletter sources
    "gmail_sender": "string (email address)",
    "gmail_subject_pattern": "string (regex pattern, optional)"
  },
  "scrape_frequency": "string (cron expression)",
  "last_scraped": "ISO 8601 datetime",
  "active": "boolean",
  "notes": "string (optional, for human reference)"
}
```

### Data Quality Scoring

Completeness score calculation:
```python
def calculate_completeness(event):
    score = 0
    weights = {
        'title': 20,
        'start_date': 20,
        'event_type': 10,
        'format': 10,
        'description': 10,
        'location': 10,
        'organizer.name': 10,
        'registration.url': 10
    }
    
    missing_fields = []
    for field, weight in weights.items():
        if has_field(event, field):
            score += weight
        else:
            missing_fields.append(field)
    
    return score, missing_fields
```

---

## Module Design

### 1. Website Scraper Module

#### Generic Scraper

Handles standard event listing pages using configurable CSS selectors.

```python
class GenericWebsiteScraper:
    def __init__(self, source_config):
        self.config = source_config
    
    def scrape(self) -> List[RawEvent]:
        """
        Scrapes events from website using configured selectors.
        Returns list of partially-structured event data.
        """
        pass
    
    def extract_event_data(self, html_element) -> RawEvent:
        """
        Extracts event data from HTML element using selectors.
        """
        pass
```

#### Custom Scrapers

For websites with unique structures, implement custom parsers:

```python
class APsAEventsScraper(BaseWebsiteScraper):
    """Custom scraper for American Psychoanalytic Association"""
    
    def scrape(self) -> List[RawEvent]:
        # Custom logic for APsaA website structure
        pass

class BPCEventsScraper(BaseWebsiteScraper):
    """Custom scraper for British Psychoanalytic Council"""
    pass
```

**Initial Custom Scrapers Needed:**
1. `PsychoanalyticInquiryScraper` - https://www.psychoanalyticinquiry.com/
2. `ChicagoPsychoanalyticSocietyScraper` - https://www.chicagogopsychoanalyticsociety.org/
3. `APsAScraper` - https://apsa.org/meetings-events/
4. `BPCScraper` - https://www.bpc.org.uk/events/

### 2. Gmail Newsletter Module

```python
class GmailNewsletterScraper:
    def __init__(self, credentials_path, source_configs):
        self.gmail_client = self._init_gmail_client(credentials_path)
        self.source_configs = source_configs
        self.newsletter_parser = NewsletterParser()
    
    def fetch_newsletters(self, days_back=7) -> List[Email]:
        """
        Fetches newsletters from configured senders within time window.
        """
        pass
    
    def extract_events_from_email(self, email) -> List[Event]:
        """
        Uses NewsletterParser to extract event information from email body.
        """
        pass
```

#### Gmail API Setup

1. Create Google Cloud Project
2. Enable Gmail API
3. Create OAuth 2.0 credentials
4. Store credentials securely (GitHub Secrets for automation)

#### Email Filtering

Query newsletters using Gmail API filters:
```python
query = f"from:{sender_email} after:{start_date} before:{end_date}"
```

### 3. Event Parser Module

Uses traditional parsing techniques to extract structured event data from HTML and text.

```python
import re
from datetime import datetime
from dateutil import parser as date_parser
from typing import Optional, Dict, Any

class EventParser:
    """Extracts structured event data from HTML snippets or text"""
    
    # Common date patterns
    DATE_PATTERNS = [
        r'\d{1,2}/\d{1,2}/\d{4}',  # MM/DD/YYYY or DD/MM/YYYY
        r'\d{4}-\d{2}-\d{2}',       # YYYY-MM-DD
        r'[A-Z][a-z]+ \d{1,2},? \d{4}',  # January 15, 2024
        r'\d{1,2} [A-Z][a-z]+ \d{4}',    # 15 January 2024
    ]
    
    # Format indicators
    FORMAT_KEYWORDS = {
        'online': ['online', 'virtual', 'webinar', 'zoom', 'via zoom', 'remote'],
        'in-person': ['in-person', 'in person', 'venue', 'location:', 'address:'],
        'hybrid': ['hybrid', 'both online and in-person']
    }
    
    def parse_event_from_html(self, html_element, source_context: Dict) -> Optional[Event]:
        """
        Extract event data from HTML element using selectors and patterns.
        
        Args:
            html_element: BeautifulSoup element containing event info
            source_context: Dict with source URL, organization name, etc.
        
        Returns:
            Event object or None if parsing fails
        """
        try:
            event_data = {
                'title': self._extract_title(html_element),
                'description': self._extract_description(html_element),
                'start_date': self._extract_date(html_element),
                'format': self._detect_format(html_element),
                'location': self._extract_location(html_element),
                'registration': self._extract_registration(html_element),
                'source': source_context
            }
            
            # Create Event object with validation
            return Event(**event_data)
            
        except Exception as e:
            logger.error(f"Failed to parse event: {e}")
            return None
    
    def _extract_title(self, element) -> str:
        """Extract event title from various possible locations"""
        # Try common title selectors
        for selector in ['h1', 'h2', 'h3', '.event-title', '.title', 'a']:
            title_elem = element.select_one(selector)
            if title_elem and title_elem.text.strip():
                return title_elem.text.strip()
        
        # Fallback: use first text content
        return element.get_text(strip=True)[:200]
    
    def _extract_date(self, element) -> Optional[datetime]:
        """Extract and parse event date"""
        text = element.get_text()
        
        # Try to find date-specific elements first
        date_elem = element.select_one('.date, .event-date, time[datetime]')
        if date_elem:
            # Try datetime attribute
            if date_elem.has_attr('datetime'):
                return date_parser.parse(date_elem['datetime'])
            text = date_elem.get_text()
        
        # Use dateutil's flexible parser
        try:
            return date_parser.parse(text, fuzzy=True)
        except:
            # Try regex patterns
            for pattern in self.DATE_PATTERNS:
                match = re.search(pattern, text)
                if match:
                    try:
                        return date_parser.parse(match.group())
                    except:
                        continue
        
        return None
    
    def _detect_format(self, element) -> str:
        """Detect if event is online, in-person, or hybrid"""
        text = element.get_text().lower()
        
        # Check for explicit format indicators
        if any(kw in text for kw in self.FORMAT_KEYWORDS['hybrid']):
            return 'hybrid'
        if any(kw in text for kw in self.FORMAT_KEYWORDS['online']):
            return 'online'
        if any(kw in text for kw in self.FORMAT_KEYWORDS['in-person']):
            return 'in-person'
        
        # Default based on presence of location info
        if element.select_one('.location, .venue, .address'):
            return 'in-person'
        
        return 'online'  # Default assumption
    
    def _extract_location(self, element) -> Dict[str, str]:
        """Extract location information"""
        location = {}
        
        # Look for location elements
        loc_elem = element.select_one('.location, .venue, .address')
        if loc_elem:
            text = loc_elem.get_text(strip=True)
            location['venue'] = text
            
            # Try to extract city/country
            # Simple pattern: "City, Country" or "City, State, Country"
            parts = [p.strip() for p in text.split(',')]
            if len(parts) >= 2:
                location['city'] = parts[0]
                location['country'] = parts[-1]
        
        # Check for online URL
        zoom_link = element.select_one('a[href*="zoom"], a[href*="meet"]')
        if zoom_link:
            location['online_url'] = zoom_link['href']
        
        return location
    
    def _extract_description(self, element) -> str:
        """Extract event description"""
        # Try common description selectors
        for selector in ['.description', '.event-description', 'p', '.content']:
            desc_elem = element.select_one(selector)
            if desc_elem:
                text = desc_elem.get_text(strip=True)
                if len(text) > 50:  # Ensure it's substantial
                    return text
        
        return ""
    
    def _extract_registration(self, element) -> Dict[str, str]:
        """Extract registration information"""
        registration = {}
        
        # Look for registration links
        reg_link = element.select_one('a[href*="register"], a[href*="registration"]')
        if reg_link:
            registration['url'] = reg_link['href']
        
        # Look for price/fee information
        text = element.get_text()
        
        # Common fee patterns
        fee_patterns = [
            r'\$\d+(?:\.\d{2})?',  # $50 or $50.00
            r'€\d+',                # €50
            r'£\d+',                # £50
            r'free',                # Free events
            r'no charge',
            r'complimentary'
        ]
        
        for pattern in fee_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                registration['fee'] = match.group()
                break
        
        return registration

class NewsletterParser:
    """Parse events from email newsletters"""
    
    def parse_newsletter(self, email_content: str, source_info: Dict) -> List[Event]:
        """
        Extract events from newsletter email content.
        
        Newsletters typically have patterns like:
        - Event lists with date/title/link
        - Calendar format
        - Structured HTML sections
        """
        events = []
        
        # Convert to BeautifulSoup for HTML emails
        soup = BeautifulSoup(email_content, 'html.parser')
        
        # Strategy 1: Look for event-specific sections
        event_sections = soup.select('.event, [class*="event"]')
        
        # Strategy 2: Look for list items with dates
        if not event_sections:
            event_sections = soup.select('li, tr')
        
        parser = EventParser()
        
        for section in event_sections:
            # Check if section contains date-like content
            if self._contains_date(section.get_text()):
                event = parser.parse_event_from_html(section, source_info)
                if event:
                    events.append(event)
        
        return events
    
    def _contains_date(self, text: str) -> bool:
        """Quick check if text contains date patterns"""
        date_indicators = [
            r'\d{1,2}/\d{1,2}',
            r'\d{4}-\d{2}',
            r'January|February|March|April|May|June|July|August|September|October|November|December',
            r'Mon|Tue|Wed|Thu|Fri|Sat|Sun'
        ]
        return any(re.search(pattern, text, re.IGNORECASE) for pattern in date_indicators)
```

**Key Features:**

1. **Flexible Date Parsing**: Uses `dateutil` library which handles many formats automatically
2. **Pattern Matching**: Regex for fees, formats, and specific fields
3. **Fallback Strategy**: Multiple attempts to extract each field
4. **HTML Structure Awareness**: Works with various HTML structures
5. **Zero External API Costs**: All processing happens locally

### 4. Data Validation & Merging Module

```python
class EventValidator:
    def validate(self, event: Event) -> Tuple[bool, List[str]]:
        """
        Validates event data.
        Returns (is_valid, list_of_errors)
        """
        pass
    
    def calculate_completeness(self, event: Event) -> Tuple[int, List[str]]:
        """
        Returns (completeness_score, missing_fields)
        """
        pass

class EventMerger:
    def deduplicate(self, events: List[Event]) -> List[Event]:
        """
        Identifies and merges duplicate events from different sources.
        Uses fuzzy matching on title + date.
        """
        pass
    
    def merge_duplicates(self, event1: Event, event2: Event) -> Event:
        """
        Merges two events, preferring more complete information.
        """
        pass
```

### 5. Storage Module

```python
class EventStorage:
    def __init__(self, repo_path):
        self.events_file = f"{repo_path}/data/events.json"
        self.sources_file = f"{repo_path}/data/sources.json"
    
    def load_events(self) -> List[Event]:
        """Load existing events from JSON"""
        pass
    
    def save_events(self, events: List[Event]):
        """Save events to JSON with pretty formatting"""
        pass
    
    def update_source_metadata(self, source_id, metadata):
        """Update last_scraped timestamp, etc."""
        pass
```

---

## Frontend Design

### Technology Choice: React

**Why React:**
- Component-based architecture suits event cards/filtering
- Large ecosystem for date handling, search, etc.
- Easy to bundle into single-file deployment
- Works well with Tailwind CSS

### Component Structure

```
App
├── Header
│   └── Logo + Title
├── FilterBar
│   ├── SearchInput
│   ├── DateRangeFilter
│   ├── FormatFilter (online/in-person/hybrid)
│   ├── TypeFilter (conference/workshop/etc)
│   └── OrganizationFilter
├── EventList
│   └── EventCard[]
│       ├── EventTitle
│       ├── EventMeta (date, location, format)
│       ├── CompletenessIndicator
│       ├── EventDescription
│       └── RegistrationButton
└── Footer
    └── Data source info + last updated
```

### Key Features

**1. Client-Side Filtering**
```javascript
const filteredEvents = events.filter(event => {
  // Text search
  if (searchQuery && !event.title.toLowerCase().includes(searchQuery.toLowerCase())) {
    return false;
  }
  
  // Date range
  if (startDate && new Date(event.start_date) < startDate) {
    return false;
  }
  
  // Format filter
  if (formatFilter.length && !formatFilter.includes(event.format)) {
    return false;
  }
  
  // ... other filters
  
  return true;
});
```

**2. Sorting Options**
- Date (upcoming first)
- Date (chronological)
- Relevance (if search query present)
- Organization name

**3. Completeness Indicator**

Visual indicator for data quality:
```jsx
function CompletenessIndicator({ score, missingFields }) {
  const color = score >= 80 ? 'green' : score >= 50 ? 'yellow' : 'red';
  
  return (
    <div className={`completeness-badge ${color}`}>
      <span>{score}% complete</span>
      {missingFields.length > 0 && (
        <Tooltip>
          Missing: {missingFields.join(', ')}
        </Tooltip>
      )}
    </div>
  );
}
```

**4. Responsive Design**

Must work in:
- Desktop (full width in Ghost blog)
- Mobile (responsive iframe)
- Iframe constraints

```css
/* Ensure no scroll issues in iframe */
body {
  margin: 0;
  overflow-y: auto;
  overflow-x: hidden;
}

/* Responsive breakpoints */
@media (max-width: 768px) {
  .filter-bar {
    flex-direction: column;
  }
}
```

### Data Loading

```javascript
useEffect(() => {
  async function loadEvents() {
    const response = await fetch('https://raw.githubusercontent.com/[username]/[repo]/main/data/events.json');
    const data = await response.json();
    setEvents(data);
    setLastUpdated(new Date()); // From response headers or metadata
  }
  
  loadEvents();
}, []);
```

---

## Automation & Deployment

### GitHub Actions Workflow

Create `.github/workflows/scrape-events.yml`:

```yaml
name: Scrape Psychoanalytic Events

on:
  schedule:
    # Run daily at 6 AM UTC
    - cron: '0 6 * * *'
  workflow_dispatch: # Allow manual triggers

jobs:
  scrape:
    runs-on: ubuntu-latest
    
    steps:
      - name: Checkout repository
        uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
      
      - name: Run scrapers
        env:
          GMAIL_CREDENTIALS: ${{ secrets.GMAIL_CREDENTIALS }}
          GMAIL_TOKEN: ${{ secrets.GMAIL_TOKEN }}
        run: |
          python scrape_all.py
      
      - name: Commit and push if changed
        run: |
          git config --global user.name 'GitHub Actions Bot'
          git config --global user.email 'actions@github.com'
          git add data/events.json data/sources.json
          git diff --quiet && git diff --staged --quiet || (git commit -m "Update events data - $(date)" && git push)
```

### Secrets Configuration

Store in GitHub repository secrets:
- `GMAIL_CREDENTIALS` - Gmail API OAuth credentials (JSON)
- `GMAIL_TOKEN` - Gmail API refresh token (generated on first run)

### Error Handling & Notifications

```python
import logging
from typing import List

logger = logging.getLogger(__name__)

class ScraperOrchestrator:
    def run_all_scrapers(self) -> dict:
        """
        Runs all configured scrapers and returns summary.
        """
        results = {
            'total_sources': 0,
            'successful': 0,
            'failed': 0,
            'new_events': 0,
            'errors': []
        }
        
        for source in self.load_sources():
            try:
                events = self.scrape_source(source)
                results['successful'] += 1
                results['new_events'] += len(events)
            except Exception as e:
                logger.error(f"Failed to scrape {source['name']}: {e}")
                results['failed'] += 1
                results['errors'].append({
                    'source': source['name'],
                    'error': str(e)
                })
        
        # Optionally send email/Slack notification if errors
        if results['failed'] > 0:
            self.notify_admin(results)
        
        return results
```

---

## Frontend Deployment

### Option 1: GitHub Pages (Recommended)

**Pros:**
- Free
- Automatic deployment on push
- CDN-backed
- Simple HTTPS

**Setup:**
1. Build React app to `/docs` folder
2. Enable GitHub Pages in repo settings
3. Point to `/docs` directory
4. Access via `https://[username].github.io/[repo-name]/`

### Option 2: Netlify

**Pros:**
- Better build tooling
- Form handling (if needed later)
- Deploy previews

**Setup:**
1. Connect GitHub repo to Netlify
2. Configure build command: `npm run build`
3. Set publish directory: `build/`
4. Custom domain support

### Option 3: Vercel

Similar to Netlify, optimized for React/Next.js.

---

## Ghost Integration

### Embedding the Frontend

Create a Ghost page with iframe:

```html
<div class="events-embed-container">
  <iframe 
    src="https://[your-deployment-url]/" 
    width="100%" 
    height="800px"
    frameborder="0"
    scrolling="yes"
    title="Psychoanalytic Events Calendar"
  ></iframe>
</div>

<style>
.events-embed-container {
  width: 100%;
  max-width: 1200px;
  margin: 0 auto;
}

.events-embed-container iframe {
  min-height: 600px;
}

@media (max-width: 768px) {
  .events-embed-container iframe {
    height: 1000px; /* More height for mobile */
  }
}
</style>
```

### Communication Between iframe and Ghost

If needed for analytics or deep linking:

```javascript
// In React app
window.parent.postMessage({
  type: 'event_clicked',
  eventId: event.id
}, '*');

// In Ghost (if tracking needed)
window.addEventListener('message', (event) => {
  if (event.data.type === 'event_clicked') {
    // Track in analytics
    gtag('event', 'event_click', {
      event_id: event.data.eventId
    });
  }
});
```

---

## Configuration Management

### sources.json Example

```json
[
  {
    "id": "apsa-events",
    "name": "American Psychoanalytic Association",
    "type": "website",
    "enabled": true,
    "config": {
      "url": "https://apsa.org/meetings-events/",
      "scraper_type": "custom",
      "custom_parser": "APsAScraper"
    },
    "scrape_frequency": "0 6 * * *",
    "last_scraped": null,
    "active": true
  },
  {
    "id": "bpc-events",
    "name": "British Psychoanalytic Council",
    "type": "website",
    "enabled": true,
    "config": {
      "url": "https://www.bpc.org.uk/events/",
      "scraper_type": "custom",
      "custom_parser": "BPCScraper"
    },
    "scrape_frequency": "0 6 * * *",
    "last_scraped": null,
    "active": true
  },
  {
    "id": "newsletter-ipa",
    "name": "IPA Newsletter",
    "type": "newsletter",
    "enabled": true,
    "config": {
      "gmail_sender": "newsletter@ipa.world",
      "gmail_subject_pattern": "IPA.*Events"
    },
    "scrape_frequency": "0 6 * * *",
    "last_scraped": null,
    "active": true
  }
]
```

### Adding New Sources

To add a new website source:

1. **If using generic scraper**: Add entry to `sources.json` with CSS selectors
2. **If needs custom scraper**: 
   - Create new scraper class in `scrapers/custom/`
   - Add entry to `sources.json` referencing custom parser
   - No code changes needed elsewhere

Example generic source:
```json
{
  "id": "new-organization",
  "name": "New Psychoanalytic Organization",
  "type": "website",
  "enabled": true,
  "config": {
    "url": "https://example.org/events",
    "scraper_type": "generic",
    "selectors": {
      "event_list": ".events-container",
      "event_item": ".event-card",
      "title": ".event-title",
      "date": ".event-date",
      "description": ".event-description",
      "link": "a.event-link"
    }
  },
  "scrape_frequency": "0 6 * * *",
  "active": true
}
```

---

## Testing Strategy

### Unit Tests

```python
# Test individual scrapers
def test_apsa_scraper():
    scraper = APsAScraper(test_config)
    events = scraper.scrape()
    assert len(events) > 0
    assert all(isinstance(e, Event) for e in events)

# Test event parser
def test_event_parser():
    parser = EventParser()
    html = '<div class="event"><h2>Test Event</h2><span class="date">January 15, 2024</span></div>'
    element = BeautifulSoup(html, 'html.parser').find('div')
    event = parser.parse_event_from_html(element, {'url': 'test', 'name': 'test'})
    assert event.title == "Test Event"
    assert event.start_date is not None

# Test date parsing
def test_date_parsing():
    parser = EventParser()
    test_cases = [
        ("January 15, 2024", datetime(2024, 1, 15)),
        ("15/01/2024", datetime(2024, 1, 15)),
        ("2024-01-15", datetime(2024, 1, 15)),
    ]
    for text, expected in test_cases:
        result = parser._extract_date(BeautifulSoup(f'<div>{text}</div>', 'html.parser'))
        assert result.date() == expected.date()

# Test deduplication
def test_event_merger():
    merger = EventMerger()
    duplicates = [event1, event2]  # Same event from different sources
    merged = merger.deduplicate(duplicates)
    assert len(merged) == 1
```

### Integration Tests

```python
def test_full_scraping_pipeline():
    """Test complete flow from scraping to storage"""
    orchestrator = ScraperOrchestrator()
    results = orchestrator.run_all_scrapers()
    
    # Verify data was saved
    storage = EventStorage()
    events = storage.load_events()
    assert len(events) > 0
```

### Frontend Tests

```javascript
// Test filtering
test('filters events by date range', () => {
  const { getByLabelText, getAllByRole } = render(<App />);
  
  // Select date range
  fireEvent.change(getByLabelText('Start Date'), { target: { value: '2024-01-01' } });
  
  const events = getAllByRole('article');
  // Assert all visible events are within range
});

// Test completeness indicator
test('shows completeness warning for incomplete events', () => {
  const { getByText } = render(<EventCard event={incompleteEvent} />);
  expect(getByText(/50% complete/)).toBeInTheDocument();
});
```

---

## Error Handling & Resilience

### Scraper Failures

```python
class ResilientScraper:
    def __init__(self, max_retries=3, timeout=30):
        self.max_retries = max_retries
        self.timeout = timeout
    
    def scrape_with_retry(self, url):
        for attempt in range(self.max_retries):
            try:
                response = requests.get(url, timeout=self.timeout)
                response.raise_for_status()
                return response.text
            except (requests.Timeout, requests.ConnectionError) as e:
                if attempt == self.max_retries - 1:
                    logger.error(f"Failed after {self.max_retries} attempts: {e}")
                    raise
                time.sleep(2 ** attempt)  # Exponential backoff
```

### Rate Limiting

```python
import time
from functools import wraps

def rate_limit(calls_per_minute=30):
    """Decorator to limit request rate for website scraping"""
    min_interval = 60.0 / calls_per_minute
    last_called = [0.0]
    
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            elapsed = time.time() - last_called[0]
            left_to_wait = min_interval - elapsed
            if left_to_wait > 0:
                time.sleep(left_to_wait)
            result = func(*args, **kwargs)
            last_called[0] = time.time()
            return result
        return wrapper
    return decorator

class RateLimitedScraper:
    @rate_limit(calls_per_minute=30)
    def fetch_url(self, url):
        """Fetch URL with rate limiting"""
        return requests.get(url, timeout=30)
```

### Data Corruption Prevention

```python
def atomic_save(filepath, data):
    """Save data atomically to prevent corruption"""
    temp_path = f"{filepath}.tmp"
    
    # Write to temp file
    with open(temp_path, 'w') as f:
        json.dump(data, f, indent=2)
    
    # Atomic rename
    os.replace(temp_path, filepath)
```

---

## Monitoring & Maintenance

### Logging

```python
import logging
from logging.handlers import RotatingFileHandler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        RotatingFileHandler('scraper.log', maxBytes=10485760, backupCount=5),
        logging.StreamHandler()
    ]
)
```

### Metrics to Track

- Number of events scraped per source
- Scraping success/failure rate
- Average completeness score
- Events added/updated/removed per run
- Parsing accuracy (manual spot checks)
- Response time for each source

### Admin Dashboard (Optional Future Enhancement)

Simple Flask app to view:
- Scraping status and logs
- Event statistics
- Source management
- Manual trigger scraping

---

## Security Considerations

### API Keys

- Gmail OAuth tokens stored in GitHub Secrets (never commit)
- Use environment variables in code
- Rotate periodically

### Gmail API

- Use OAuth 2.0 (not API keys)
- Limit scope to `gmail.readonly`
- Store refresh tokens securely

### Data Privacy

- No PII stored (events are public)
- No user tracking in frontend
- HTTPS only

### Rate Limiting

- Respect robots.txt
- Add delays between requests (2-3 seconds)
- Use appropriate User-Agent headers

```python
headers = {
    'User-Agent': 'PsychoanalyticEventsBot/1.0 (contact@yourdomain.com)'
}
```

### Web Scraping Ethics

- Only scrape publicly accessible event pages
- Honor robots.txt directives
- Implement reasonable rate limiting
- Cache responses to minimize repeat requests

---

## Project Structure

```
psychoanalytic-events-aggregator/
├── backend/
│   ├── scrapers/
│   │   ├── __init__.py
│   │   ├── base.py              # Base scraper class
│   │   ├── generic.py           # Generic website scraper
│   │   ├── custom/              # Custom scrapers
│   │   │   ├── apsa.py
│   │   │   ├── bpc.py
│   │   │   ├── chicago_psychoanalytic.py
│   │   │   └── psychoanalytic_inquiry.py
│   │   └── gmail_scraper.py
│   ├── parsers/
│   │   ├── __init__.py
│   │   ├── event_parser.py      # HTML/text event parser
│   │   └── newsletter_parser.py # Email-specific parser
│   ├── models/
│   │   ├── __init__.py
│   │   ├── event.py             # Event data model
│   │   └── source.py            # Source config model
│   ├── storage/
│   │   ├── __init__.py
│   │   └── json_storage.py
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── validator.py
│   │   ├── merger.py
│   │   └── date_utils.py
│   ├── scrape_all.py            # Main orchestration script
│   ├── requirements.txt
│   └── config.py
├── frontend/
│   ├── public/
│   │   └── index.html
│   ├── src/
│   │   ├── components/
│   │   │   ├── EventCard.jsx
│   │   │   ├── FilterBar.jsx
│   │   │   ├── EventList.jsx
│   │   │   └── CompletenessIndicator.jsx
│   │   ├── hooks/
│   │   │   └── useEvents.js
│   │   ├── utils/
│   │   │   └── filters.js
│   │   ├── App.jsx
│   │   └── index.js
│   ├── package.json
│   └── tailwind.config.js
├── data/
│   ├── events.json              # Generated events data
│   └── sources.json             # Source configurations
├── .github/
│   └── workflows/
│       └── scrape-events.yml    # GitHub Actions workflow
├── tests/
│   ├── test_scrapers.py
│   ├── test_parser.py
│   └── test_merger.py
├── docs/
│   └── SETUP.md                 # Setup instructions
├── .gitignore
├── README.md
└── LICENSE
```

---

## Implementation Roadmap

### Phase 1: MVP (Week 1-2)

**Backend:**
- [ ] Set up project structure
- [ ] Implement data models (Event, Source)
- [ ] Create base scraper class
- [ ] Implement 4 custom scrapers for initial websites
- [ ] Set up Claude API integration for parsing
- [ ] Implement JSON storage
- [ ] Create basic validation and deduplication

**Frontend:**
- [ ] Initialize React app with Tailwind
- [ ] Create EventCard component
- [ ] Implement basic filtering (date, format, type)
- [ ] Add search functionality
- [ ] Display completeness indicators

**Deployment:**
- [ ] Set up GitHub repository
- [ ] Configure GitHub Actions for daily scraping
- [ ] Deploy frontend to GitHub Pages/Netlify
- [ ] Test iframe embedding in Ghost

### Phase 2: Gmail Integration (Week 3)

- [ ] Set up Gmail API credentials
- [ ] Implement newsletter scraper
- [ ] Add email parsing with LLM
- [ ] Test with real newsletters
- [ ] Configure in GitHub Actions

### Phase 3: Polish & Optimization (Week 4)

- [ ] Improve scraper robustness (error handling, retries)
- [ ] Optimize LLM parsing (reduce API calls)
- [ ] Add more filter options
- [ ] Improve UI/UX based on testing
- [ ] Write documentation
- [ ] Add monitoring/logging

### Phase 4: Future Enhancements

- [ ] Add paper awards section
- [ ] Add CFP (Call for Papers) tracking
- [ ] Email subscription feature
- [ ] RSS feed
- [ ] iCal export
- [ ] Admin dashboard
- [ ] Source suggestion form

---

## Estimated Costs

### API Usage

**Gmail API:**
- Free (within quota: 1 billion quota units/day)
- Typical usage: <1000 units/day
- Well within free tier

### Hosting

**GitHub Pages:** Free

**GitHub Actions:**
- 2,000 minutes/month free (public repos)
- Scraping takes ~5-10 min/run
- 30 runs/month = 150-300 minutes
- **Free** - well within free tier

**Domain (Optional):**
- ~$12/year if custom domain desired

**Total Monthly Cost: $0** (or ~$1/month if using custom domain)

### Cost Comparison

**Traditional Approach (Current):**
- All free tier services
- No per-request charges
- Scalable within GitHub's generous limits

**LLM Approach (Avoided):**
- Would cost ~$70/month for Claude API
- 500 events/day × $0.003/1K tokens input × $0.015/1K tokens output
- Not necessary for structured website data

---

## Success Metrics

### Technical Metrics
- Uptime: 99%+ (GitHub Actions reliability)
- Scraping success rate: >95%
- Average event completeness score: >70%
- Page load time: <2s

### User Metrics (Future)
- Page views
- Events clicked
- Search queries
- Filter usage patterns

### Data Quality Metrics
- Events scraped per week
- Sources active/inactive
- Duplicate detection accuracy
- Date parsing accuracy

---

## FAQ for Developers

**Q: How do I add a new event source?**

A: Add entry to `data/sources.json`. If the website structure is standard, use `generic` scraper type with CSS selectors. If complex, create custom scraper in `backend/scrapers/custom/`.

**Q: How often does the data update?**

A: Daily at 6 AM UTC via GitHub Actions. Can be manually triggered anytime.

**Q: What if a scraper fails?**

A: Errors are logged. Other scrapers continue. Failed source will retry next scheduled run.

**Q: Can users submit events?**

A: Not in MVP. Could add Google Forms integration in future.

**Q: How are duplicates handled?**

A: Fuzzy matching on title + date. When found, merge and keep most complete data.

**Q: What if a website changes its structure?**

A: Update the CSS selectors in `sources.json` for generic scrapers, or update the custom scraper class. The modular design makes this straightforward.

**Q: How accurate is the date parsing?**

A: `python-dateutil` handles most common date formats automatically. For edge cases, we can add custom patterns to the parser.

**Q: How to test locally?**

A:
```bash
# Backend
cd backend
python scrape_all.py --dry-run

# Frontend
cd frontend
npm start
```

---

## Conclusion

This specification provides a complete blueprint for building a robust, automated psychoanalytic events aggregation system with **zero operational costs**. The architecture is:

- **Modular**: Easy to add new sources or extend functionality
- **Resilient**: Handles failures gracefully
- **Maintainable**: Clear separation of concerns
- **Cost-effective**: 100% free using GitHub's free tier
- **Scalable**: Can handle hundreds of sources
- **No External Dependencies**: No paid APIs required

The MVP focuses on core functionality (automated scraping, traditional parsing, clean presentation) while leaving room for future enhancements (awards, CFPs, user submissions).

Key strengths:
1. **Configuration-driven**: Adding sources requires no code changes
2. **Traditional parsing**: Reliable and free using BeautifulSoup + dateutil + regex
3. **Data quality transparency**: Users see completeness scores
4. **Zero-maintenance deployment**: GitHub Actions handles everything
5. **Zero ongoing costs**: All services within free tiers

The decision to use traditional parsing instead of LLM:
- Saves ~$70/month
- More predictable and debuggable
- Sufficient for structured website data
- Can always add LLM later for complex edge cases if needed

Next steps: Developer reads this spec, asks clarifying questions, and begins Phase 1 implementation.
