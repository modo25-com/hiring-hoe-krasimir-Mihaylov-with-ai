"""
Campaign Data Validation Function

This module provides validation for marketing campaign data from various sources.
It ensures data quality before the data enters the analytics pipeline.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field, field_validator, model_validator

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CampaignData(BaseModel):
    """Pydantic model for campaign data validation."""

    model_config = {"strict": True}  # Disable type coercion

    campaign_id: str
    source: str
    date: str
    spend: float = Field(ge=0)
    impressions: int = Field(ge=0)
    clicks: int = Field(ge=0)
    conversions: Optional[int] = Field(default=None, ge=0)
    revenue: Optional[float] = Field(default=None, ge=0)
    campaign_name: Optional[str] = None
    currency: Optional[str] = None

    @field_validator('date')
    @classmethod
    def validate_date_format(cls, v: str) -> str:
        """Validate date is in YYYY-MM-DD format and not in future."""
        try:
            date_obj = datetime.strptime(v, "%Y-%m-%d")
        except ValueError:
            raise ValueError(f"Field 'date' must be in YYYY-MM-DD format, got '{v}'")

        if date_obj.date() > datetime.now().date():
            raise ValueError(f"Field 'date' cannot be in the future, got '{v}'")

        return v

    @model_validator(mode='after')
    def validate_business_rules(self) -> 'CampaignData':
        """Validate business rules across multiple fields."""
        errors = []

        # clicks <= impressions
        if self.clicks > self.impressions:
            errors.append(f"Field 'clicks' ({self.clicks}) cannot exceed 'impressions' ({self.impressions})")

        # conversions <= clicks
        if self.conversions is not None and self.conversions > self.clicks:
            errors.append(f"Field 'conversions' ({self.conversions}) cannot exceed 'clicks' ({self.clicks})")

        # Impossible: impressions == 0 but clicks > 0
        if self.impressions == 0 and self.clicks > 0:
            errors.append(f"Impossible: 'impressions' is 0 but 'clicks' is {self.clicks}")

        # CTR > 50%
        if self.impressions > 0:
            ctr = (self.clicks / self.impressions) * 100
            if ctr > 50:
                errors.append(f"Impossibly high CTR: {ctr:.1f}% (clicks={self.clicks}, impressions={self.impressions})")

        if errors:
            raise ValueError("; ".join(errors))

        return self

    def get_warnings(self) -> List[str]:
        """Generate warnings for anomalies that don't fail validation."""
        warnings = []

        # Date more than 90 days old
        try:
            date_obj = datetime.strptime(self.date, "%Y-%m-%d")
            days_old = (datetime.now() - date_obj).days
            if days_old > 90:
                warnings.append(f"Field 'date' is {days_old} days old (more than 90 days)")
        except ValueError:
            pass

        # Impressions > 0 but clicks == 0
        if self.impressions > 0 and self.clicks == 0:
            warnings.append(f"Unusual: 'impressions' is {self.impressions} but 'clicks' is 0")

        # Spend > $100,000
        if self.spend > 100000:
            warnings.append(f"Unusually high spend: ${self.spend:,.2f} (exceeds $100,000)")

        # Conversions > 0 but revenue == 0 or missing
        if self.conversions is not None and self.conversions > 0:
            if self.revenue is None:
                warnings.append(f"'conversions' is {self.conversions} but 'revenue' is missing")
            elif self.revenue == 0:
                warnings.append(f"'conversions' is {self.conversions} but 'revenue' is 0")

        return warnings


def validate_campaign_data(campaign_data: dict) -> dict:
    """
    Validates marketing campaign data against business rules and data quality checks.

    This function validates:
    - Required fields are present
    - Data types are correct
    - Values are within acceptable ranges
    - Business logic constraints (e.g., clicks <= impressions)
    - Anomalies that might indicate data quality issues

    Args:
        campaign_data: Dictionary containing campaign metrics with the following structure:
            {
                "campaign_id": str,
                "campaign_name": str (optional),
                "source": str,  # e.g., 'google_ads', 'facebook_ads'
                "date": str,  # YYYY-MM-DD format
                "spend": float,
                "impressions": int,
                "clicks": int,
                "conversions": int (optional),
                "revenue": float (optional),
                "currency": str (optional)
            }

    Returns:
        Dictionary with validation results:
        {
            "valid": bool,  # Overall validation status
            "errors": List[str],  # List of error messages (validation failures)
            "warnings": List[str],  # List of warning messages (anomalies)
            "campaign_id": str or None,  # Campaign ID if present
            "validated_at": str  # ISO timestamp of validation
        }
    """
    campaign_id = campaign_data.get("campaign_id")
    errors = []
    warnings = []

    # Pre-check for None values in fields that should have a type (Pydantic Optional allows None)
    for field in ['revenue', 'conversions']:
        if field in campaign_data and campaign_data[field] is None:
            field_type = "an integer" if field == 'conversions' else "a number (float or int)"
            errors.append(f"Field '{field}' must be {field_type}, got NoneType")

    if errors:
        logger.warning(f"Validation failed for campaign_id={campaign_id}: {len(errors)} error(s)")
        return {
            "valid": False,
            "errors": errors,
            "warnings": warnings,
            "campaign_id": campaign_id,
            "validated_at": datetime.utcnow().isoformat()
        }

    try:
        # Validate using Pydantic model
        campaign = CampaignData(**campaign_data)

        # Get warnings (anomalies that don't fail validation)
        warnings = campaign.get_warnings()

        # Add logging
        if warnings:
            logger.info(f"Validation passed with warnings for campaign_id={campaign_id}: {len(warnings)} warning(s)")
        else:
            logger.info(f"Validation passed for campaign_id={campaign_id}")

    except Exception as e:
        # Parse Pydantic validation errors
        from pydantic import ValidationError

        if isinstance(e, ValidationError):
            for error in e.errors():
                field = error['loc'][0] if error['loc'] else 'unknown'
                msg = error['msg']
                error_type = error['type']
                field_value = campaign_data.get(field)

                # Format error messages to match our existing format
                if error_type == 'missing':
                    errors.append(f"Missing required field: '{field}'")
                elif error_type in ('int_type', 'float_type', 'string_type'):
                    # Special case: None for optional fields should still be caught if explicitly set
                    if field_value is None and field in ('revenue', 'conversions'):
                        errors.append(f"Field '{field}' must be {error_type.replace('_type', 'an integer' if 'int' in error_type else 'a number (float or int)')}, got {type(field_value).__name__}")
                    else:
                        errors.append(f"Field '{field}' must be {error_type.replace('_type', '')}, got {type(field_value).__name__}")
                elif 'greater_than_equal' in error_type:
                    errors.append(f"Field '{field}' cannot be negative, got {field_value}")
                elif error_type == 'value_error':
                    errors.append(msg)
                else:
                    errors.append(f"Field '{field}': {msg}")
        else:
            errors.append(str(e))

        # Add logging
        logger.warning(f"Validation failed for campaign_id={campaign_id}: {len(errors)} error(s)")

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "campaign_id": campaign_id,
        "validated_at": datetime.utcnow().isoformat()
    }

