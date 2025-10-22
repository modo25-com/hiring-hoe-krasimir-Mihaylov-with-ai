"""
Campaign Data Validation Function

This module provides validation for marketing campaign data from various sources.
It ensures data quality before the data enters the analytics pipeline.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


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
    
    Examples:
        >>> result = validate_campaign_data({
        ...     "campaign_id": "camp_123",
        ...     "source": "google_ads",
        ...     "date": "2024-10-15",
        ...     "spend": 1000.0,
        ...     "impressions": 50000,
        ...     "clicks": 1000
        ... })
        >>> result["valid"]
        True
        
        >>> result = validate_campaign_data({
        ...     "campaign_id": "camp_456",
        ...     "source": "facebook_ads",
        ...     "date": "2024-10-15",
        ...     "spend": 500.0,
        ...     "impressions": 0,
        ...     "clicks": 100
        ... })
        >>> result["valid"]
        False
        >>> "clicks cannot exceed impressions" in result["errors"][0].lower()
        True
    """
    # TODO: Implement validation logic here
    
    # Initialize result structure
    errors = []
    warnings = []
    campaign_id = campaign_data.get("campaign_id")
    
    # TODO: Validate required fields
    # Required: campaign_id, source, date, spend, impressions, clicks
    
    # TODO: Validate data types
    # spend, revenue should be float
    # impressions, clicks, conversions should be int
    # date should be valid YYYY-MM-DD format
    
    # TODO: Validate business rules
    # spend >= 0
    # clicks <= impressions
    # conversions <= clicks (if conversions present)
    # revenue >= 0 (if revenue present)
    # date not in future
    # date not more than 90 days old (warning)
    
    # TODO: Detect anomalies
    # impressions > 0 but clicks == 0 (warning - unusual but possible)
    # impressions == 0 but clicks > 0 (error - impossible)
    # spend > $100,000 (warning - unusual)
    # CTR > 50% (error - likely data quality issue)
    # conversions > 0 but revenue == 0 or missing (warning)
    
    # TODO: Add logging
    
    # Return validation result
    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "campaign_id": campaign_id,
        "validated_at": datetime.utcnow().isoformat()
    }


def validate_required_fields(campaign_data: dict) -> List[str]:
    """
    Validate that all required fields are present.
    
    Args:
        campaign_data: Campaign data dictionary
        
    Returns:
        List of error messages for missing required fields
    """
    # TODO: Implement this helper function
    errors = []
    required_fields = ["campaign_id", "source", "date", "spend", "impressions", "clicks"]
    
    # Check for missing fields
    
    return errors


def validate_data_types(campaign_data: dict) -> List[str]:
    """
    Validate that field data types are correct.
    
    Args:
        campaign_data: Campaign data dictionary
        
    Returns:
        List of error messages for incorrect data types
    """
    # TODO: Implement this helper function
    errors = []
    
    # Validate types for each field
    
    return errors


def validate_business_rules(campaign_data: dict) -> tuple[List[str], List[str]]:
    """
    Validate business logic rules.
    
    Args:
        campaign_data: Campaign data dictionary
        
    Returns:
        Tuple of (errors, warnings)
    """
    # TODO: Implement this helper function
    errors = []
    warnings = []
    
    # Validate business constraints
    
    return errors, warnings


def detect_anomalies(campaign_data: dict) -> tuple[List[str], List[str]]:
    """
    Detect anomalies that might indicate data quality issues.
    
    Args:
        campaign_data: Campaign data dictionary
        
    Returns:
        Tuple of (errors, warnings)
    """
    # TODO: Implement this helper function
    errors = []
    warnings = []
    
    # Check for suspicious patterns
    
    return errors, warnings


# Mock data for testing purposes
VALID_CAMPAIGN = {
    "campaign_id": "camp_123",
    "campaign_name": "Summer Sale 2024",
    "source": "google_ads",
    "date": "2024-10-15",
    "spend": 5000.00,
    "impressions": 100000,
    "clicks": 2500,
    "conversions": 50,
    "revenue": 7500.00,
    "currency": "USD"
}

INVALID_CAMPAIGN_MISSING_FIELDS = {
    "campaign_id": "camp_456",
    "source": "facebook_ads",
    # Missing date, spend, impressions, clicks
}

INVALID_CAMPAIGN_BAD_DATA = {
    "campaign_id": "camp_789",
    "source": "tiktok_ads",
    "date": "2024-10-15",
    "spend": 1000.00,
    "impressions": 0,  # 0 impressions
    "clicks": 500,  # but 500 clicks - impossible!
    "conversions": 10
}


if __name__ == "__main__":
    # Quick test of the validation function
    print("Testing validation function...\n")
    
    print("Test 1: Valid campaign")
    result = validate_campaign_data(VALID_CAMPAIGN)
    print(f"Result: {result}\n")
    
    print("Test 2: Missing required fields")
    result = validate_campaign_data(INVALID_CAMPAIGN_MISSING_FIELDS)
    print(f"Result: {result}\n")
    
    print("Test 3: Bad data (impossible metrics)")
    result = validate_campaign_data(INVALID_CAMPAIGN_BAD_DATA)
    print(f"Result: {result}\n")

