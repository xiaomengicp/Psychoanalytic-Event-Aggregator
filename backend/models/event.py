"""Event data model for psychoanalytic events."""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, computed_field
import hashlib


class Location(BaseModel):
    """Event location details."""
    venue: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    online_url: Optional[str] = None


class Organizer(BaseModel):
    """Event organizer details."""
    name: str
    url: Optional[str] = None
    email: Optional[str] = None


class Registration(BaseModel):
    """Event registration details."""
    url: Optional[str] = None
    deadline: Optional[datetime] = None
    fee: Optional[str] = None


class Source(BaseModel):
    """Source information for an event."""
    type: str = Field(description="'website' or 'newsletter'")
    url: str
    name: str
    scraped_at: datetime = Field(default_factory=datetime.utcnow)


class Event(BaseModel):
    """Main event data model."""
    id: Optional[str] = None
    title: str
    description: Optional[str] = None
    event_type: str = Field(
        default="other",
        description="conference, workshop, lecture, seminar, webinar, course, other"
    )
    format: str = Field(
        default="online",
        description="online, in-person, hybrid"
    )
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    timezone: Optional[str] = None
    location: Location = Field(default_factory=Location)
    organizer: Organizer = Field(default_factory=lambda: Organizer(name="Unknown"))
    registration: Registration = Field(default_factory=Registration)
    source: Source
    completeness_score: int = 0
    missing_fields: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    def model_post_init(self, __context: Any) -> None:
        """Generate ID and calculate completeness after initialization."""
        if not self.id:
            self.id = self._generate_id()
        self._calculate_completeness()

    def _generate_id(self) -> str:
        """Generate unique ID from URL and title."""
        unique_str = f"{self.source.url}:{self.title}"
        if self.start_date:
            unique_str += f":{self.start_date.isoformat()}"
        return hashlib.sha256(unique_str.encode()).hexdigest()[:16]

    def _calculate_completeness(self) -> None:
        """Calculate completeness score and identify missing fields."""
        weights = {
            'title': (20, lambda: bool(self.title)),
            'start_date': (20, lambda: self.start_date is not None),
            'event_type': (10, lambda: self.event_type != 'other'),
            'format': (10, lambda: self.format is not None),
            'description': (10, lambda: bool(self.description)),
            'location': (10, lambda: bool(self.location.city or self.location.venue or self.location.online_url)),
            'organizer.name': (10, lambda: self.organizer.name != 'Unknown'),
            'registration.url': (10, lambda: bool(self.registration.url)),
        }

        score = 0
        missing = []

        for field, (weight, check) in weights.items():
            if check():
                score += weight
            else:
                missing.append(field)

        self.completeness_score = score
        self.missing_fields = missing

    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary for JSON serialization."""
        data = self.model_dump(mode='json')
        # Convert datetime fields to ISO strings
        for field in ['start_date', 'end_date', 'created_at', 'updated_at']:
            if data.get(field):
                if isinstance(data[field], datetime):
                    data[field] = data[field].isoformat()
        if data.get('registration', {}).get('deadline'):
            if isinstance(data['registration']['deadline'], datetime):
                data['registration']['deadline'] = data['registration']['deadline'].isoformat()
        if data.get('source', {}).get('scraped_at'):
            if isinstance(data['source']['scraped_at'], datetime):
                data['source']['scraped_at'] = data['source']['scraped_at'].isoformat()
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Event':
        """Create Event from dictionary."""
        return cls.model_validate(data)


class RawEvent(BaseModel):
    """Partially parsed event data from scrapers."""
    title: Optional[str] = None
    description: Optional[str] = None
    date_text: Optional[str] = None
    time_text: Optional[str] = None
    location_text: Optional[str] = None
    url: Optional[str] = None
    html_content: Optional[str] = None
    source_url: str
    source_name: str
