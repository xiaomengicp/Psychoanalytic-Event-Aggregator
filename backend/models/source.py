"""Source configuration model."""

from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


class WebsiteSelectors(BaseModel):
    """CSS selectors for generic website scraping."""
    event_list: Optional[str] = None
    event_item: Optional[str] = None
    title: Optional[str] = None
    date: Optional[str] = None
    description: Optional[str] = None
    link: Optional[str] = None


class SourceConfig(BaseModel):
    """Configuration for a source."""
    # Website sources
    url: Optional[str] = None
    scraper_type: str = Field(default="generic", description="'generic' or 'custom'")
    custom_parser: Optional[str] = None
    selectors: Optional[WebsiteSelectors] = None

    # Newsletter sources
    gmail_sender: Optional[str] = None
    gmail_subject_pattern: Optional[str] = None


class Source(BaseModel):
    """Source definition for event scraping."""
    id: str
    name: str
    type: str = Field(description="'website' or 'newsletter'")
    enabled: bool = True
    config: SourceConfig
    scrape_frequency: str = Field(default="0 6 * * *", description="Cron expression")
    last_scraped: Optional[datetime] = None
    active: bool = True
    notes: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = self.model_dump(mode='json')
        if data.get('last_scraped') and isinstance(data['last_scraped'], datetime):
            data['last_scraped'] = data['last_scraped'].isoformat()
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Source':
        """Create Source from dictionary."""
        return cls.model_validate(data)


class SourceList(BaseModel):
    """List of sources."""
    sources: List[Source] = Field(default_factory=list)

    def get_enabled_sources(self) -> List[Source]:
        """Get only enabled and active sources."""
        return [s for s in self.sources if s.enabled and s.active]

    def get_website_sources(self) -> List[Source]:
        """Get website sources only."""
        return [s for s in self.get_enabled_sources() if s.type == "website"]

    def get_newsletter_sources(self) -> List[Source]:
        """Get newsletter sources only."""
        return [s for s in self.get_enabled_sources() if s.type == "newsletter"]
