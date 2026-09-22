from dataclasses import dataclass
from typing import Optional

@dataclass
class Venue:
    venue_id: str
    name: str
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    postal_code: Optional[str] = None
    longitude: Optional[float] = None
    latitude: Optional[float] = None

@dataclass
class Attraction:
    attraction_id: str
    name: str
    segment: Optional[str] = None
    genre: Optional[str] = None
    subgenre: Optional[str] = None

@dataclass
class Event:
    event_id: str
    name: str
    date: Optional[str] = None
    venue_id: Optional[str] = None
    attraction_id: Optional[str] = None
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    segment: Optional[str] = None
    genre: Optional[str] = None
    subgenre: Optional[str] = None
    status: Optional[str] = None
    date_on_sale: Optional[str] = None
    
