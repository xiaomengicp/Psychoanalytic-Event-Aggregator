# Psychoanalytic Events Aggregator

An automated event aggregation system that collects psychoanalytic events from multiple sources and displays them in a searchable, filterable interface.

![Events Preview](https://img.shields.io/badge/Events-Aggregator-purple)

## Features

- 🔄 **Automated Scraping**: Daily collection from multiple sources
- 🌐 **Multi-Source Support**: Websites and email newsletters
- 🔍 **Search & Filter**: By date, format, type, organization
- 📊 **Completeness Scoring**: Shows data quality for each event
- 📱 **Responsive Design**: Works on mobile and desktop
- 🖼️ **Iframe Ready**: Embeddable in Ghost blog or other sites

## Project Structure

```
├── backend/              # Python scraping infrastructure
│   ├── scrapers/         # Website and email scrapers
│   ├── parsers/          # Event extraction logic
│   ├── models/           # Data models (Pydantic)
│   ├── storage/          # JSON file storage
│   └── utils/            # Validation, merging
├── frontend/             # React + Tailwind frontend
│   └── src/
│       ├── components/   # UI components
│       └── hooks/        # Data fetching
├── data/                 # Event data (JSON)
└── .github/workflows/    # GitHub Actions automation
```

## Quick Start

### Backend (Python 3.11+)

```bash
cd backend
pip install -r requirements.txt

# Run scrapers
python scrape_all.py

# Dry run (no data save)
python scrape_all.py --dry-run
```

### Frontend (Node 18+)

```bash
cd frontend
npm install
npm run dev
```

## Adding New Sources

### Website Source (Generic Scraper)

Add to `data/sources.json`:

```json
{
  "id": "new-source",
  "name": "Organization Name",
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
      "description": ".event-description"
    }
  }
}
```

### Custom Scraper

1. Create `backend/scrapers/custom/your_source.py`
2. Extend `BaseScraper` class
3. Implement `scrape()` method
4. Add to `CUSTOM_SCRAPERS` in `scrape_all.py`
5. Update `sources.json` with `"custom_parser": "YourScraperClass"`

## Deployment

### GitHub Actions (Automatic)

The included workflow runs daily at 6 AM UTC:
- Scrapes all enabled sources
- Commits updated `events.json`
- Deploys frontend to GitHub Pages

### Manual Deployment

```bash
# Build frontend
cd frontend
npm run build

# Output in dist/ folder
```

## Embedding in Ghost Blog

```html
<iframe 
  src="https://your-username.github.io/Psychoanalytic-Event-Aggregator/" 
  width="100%" 
  height="800px"
  frameborder="0"
></iframe>
```

## Gmail Newsletter Setup

1. Create Google Cloud project
2. Enable Gmail API
3. Create OAuth credentials
4. Store as GitHub Secrets:
   - `GMAIL_CREDENTIALS`: OAuth JSON
   - `GMAIL_TOKEN`: Refresh token

## Tech Stack

- **Backend**: Python, BeautifulSoup, Pydantic, dateutil
- **Frontend**: React, Vite, Tailwind CSS
- **Hosting**: GitHub Pages (free)
- **Automation**: GitHub Actions (free)

## License

MIT
