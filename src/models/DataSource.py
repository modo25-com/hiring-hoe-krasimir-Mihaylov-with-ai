"""Data source model for marketing analytics platform."""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class DataSource:
    """Represents a marketing data source (e.g., Google Ads, Facebook Ads)."""
    
    id: str
    name: str
    type: str  # e.g., 'google_ads', 'facebook_ads', 'tiktok_ads', 'shopify'
    api_key: str
    api_secret: Optional[str] = None
    account_id: Optional[str] = None
    is_active: bool = True
    last_sync: Optional[datetime] = None
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()
    
    def update_last_sync(self) -> None:
        """Update the last sync timestamp."""
        self.last_sync = datetime.utcnow()

