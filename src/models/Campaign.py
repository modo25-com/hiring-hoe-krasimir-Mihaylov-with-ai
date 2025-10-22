"""Campaign model for marketing analytics platform."""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Campaign:
    """Represents a marketing campaign from various sources."""
    
    id: str
    name: str
    source: str  # e.g., 'google_ads', 'facebook_ads', 'tiktok_ads'
    date: datetime
    spend: float
    impressions: int
    clicks: int
    conversions: int
    revenue: Optional[float] = None
    currency: str = "USD"
    created_at: datetime = None
    updated_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.updated_at is None:
            self.updated_at = datetime.utcnow()
    
    @property
    def ctr(self) -> float:
        """Calculate Click-Through Rate."""
        if self.impressions == 0:
            return 0.0
        return (self.clicks / self.impressions) * 100
    
    @property
    def conversion_rate(self) -> float:
        """Calculate Conversion Rate."""
        if self.clicks == 0:
            return 0.0
        return (self.conversions / self.clicks) * 100
    
    @property
    def roas(self) -> Optional[float]:
        """Calculate Return on Ad Spend."""
        if self.spend == 0 or self.revenue is None:
            return None
        return self.revenue / self.spend
    
    @property
    def cpc(self) -> float:
        """Calculate Cost Per Click."""
        if self.clicks == 0:
            return 0.0
        return self.spend / self.clicks
    
    @property
    def cpa(self) -> float:
        """Calculate Cost Per Acquisition."""
        if self.conversions == 0:
            return 0.0
        return self.spend / self.conversions

