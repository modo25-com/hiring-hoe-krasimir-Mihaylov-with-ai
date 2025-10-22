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
    """
    # Initialize result structure
    errors = []
    warnings = []
    campaign_id = campaign_data.get("campaign_id")

    # Validate required fields
    required_field_errors = validate_required_fields(campaign_data)
    errors.extend(required_field_errors)

    # Validate data types
    data_type_errors = validate_data_types(campaign_data)
    errors.extend(data_type_errors)

    # Validate business rules
    business_errors, business_warnings = validate_business_rules(campaign_data)
    errors.extend(business_errors)
    warnings.extend(business_warnings)

    # Detect anomalies
    anomaly_errors, anomaly_warnings = detect_anomalies(campaign_data)
    errors.extend(anomaly_errors)
    warnings.extend(anomaly_warnings)

    # Add logging
    if errors:
        logger.warning(f"Validation failed for campaign_id={campaign_id}: {len(errors)} error(s)")
    elif warnings:
        logger.info(f"Validation passed with warnings for campaign_id={campaign_id}: {len(warnings)} warning(s)")
    else:
        logger.info(f"Validation passed for campaign_id={campaign_id}")

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
    errors = []
    required_fields = ["campaign_id", "source", "date", "spend", "impressions", "clicks"]

    for field in required_fields:
        if field not in campaign_data:
            errors.append(f"Missing required field: '{field}'")

    return errors


def validate_data_types(campaign_data: dict) -> List[str]:
    """
    Validate that field data types are correct.

    Args:
        campaign_data: Campaign data dictionary

    Returns:
        List of error messages for incorrect data types
    """
    errors = []

    # Check spend (should be float or int)
    if "spend" in campaign_data:
        if not isinstance(campaign_data["spend"], (float, int)):
            errors.append(f"Field 'spend' must be a number (float or int), got {type(campaign_data['spend']).__name__}")

    # Check revenue (should be float or int)
    if "revenue" in campaign_data:
        if not isinstance(campaign_data["revenue"], (float, int)):
            errors.append(f"Field 'revenue' must be a number (float or int), got {type(campaign_data['revenue']).__name__}")

    # Check impressions (should be int)
    if "impressions" in campaign_data:
        if not isinstance(campaign_data["impressions"], int) or isinstance(campaign_data["impressions"], bool):
            errors.append(f"Field 'impressions' must be an integer, got {type(campaign_data['impressions']).__name__}")

    # Check clicks (should be int)
    if "clicks" in campaign_data:
        if not isinstance(campaign_data["clicks"], int) or isinstance(campaign_data["clicks"], bool):
            errors.append(f"Field 'clicks' must be an integer, got {type(campaign_data['clicks']).__name__}")

    # Check conversions (should be int)
    if "conversions" in campaign_data:
        if not isinstance(campaign_data["conversions"], int) or isinstance(campaign_data["conversions"], bool):
            errors.append(f"Field 'conversions' must be an integer, got {type(campaign_data['conversions']).__name__}")

    # Check date format (should be string in YYYY-MM-DD format)
    if "date" in campaign_data:
        if not isinstance(campaign_data["date"], str):
            errors.append(f"Field 'date' must be a string, got {type(campaign_data['date']).__name__}")
        else:
            try:
                datetime.strptime(campaign_data["date"], "%Y-%m-%d")
            except ValueError:
                errors.append(f"Field 'date' must be in YYYY-MM-DD format, got '{campaign_data['date']}'")

    # Check campaign_id (should be string)
    if "campaign_id" in campaign_data:
        if not isinstance(campaign_data["campaign_id"], str):
            errors.append(f"Field 'campaign_id' must be a string, got {type(campaign_data['campaign_id']).__name__}")

    # Check source (should be string)
    if "source" in campaign_data:
        if not isinstance(campaign_data["source"], str):
            errors.append(f"Field 'source' must be a string, got {type(campaign_data['source']).__name__}")

    # Check campaign_name (should be string if present)
    if "campaign_name" in campaign_data:
        if not isinstance(campaign_data["campaign_name"], str):
            errors.append(f"Field 'campaign_name' must be a string, got {type(campaign_data['campaign_name']).__name__}")

    # Check currency (should be string if present)
    if "currency" in campaign_data:
        if not isinstance(campaign_data["currency"], str):
            errors.append(f"Field 'currency' must be a string, got {type(campaign_data['currency']).__name__}")

    return errors


def validate_business_rules(campaign_data: dict) -> tuple[List[str], List[str]]:
    """
    Validate business logic rules.

    Args:
        campaign_data: Campaign data dictionary

    Returns:
        Tuple of (errors, warnings)
    """
    errors = []
    warnings = []

    # Check spend >= 0
    if "spend" in campaign_data and isinstance(campaign_data["spend"], (float, int)):
        if campaign_data["spend"] < 0:
            errors.append(f"Field 'spend' cannot be negative, got {campaign_data['spend']}")

    # Check revenue >= 0
    if "revenue" in campaign_data and isinstance(campaign_data["revenue"], (float, int)):
        if campaign_data["revenue"] < 0:
            errors.append(f"Field 'revenue' cannot be negative, got {campaign_data['revenue']}")

    # Check clicks <= impressions
    if ("clicks" in campaign_data and "impressions" in campaign_data and
        isinstance(campaign_data["clicks"], int) and isinstance(campaign_data["impressions"], int)):
        if campaign_data["clicks"] > campaign_data["impressions"]:
            errors.append(f"Field 'clicks' ({campaign_data['clicks']}) cannot exceed 'impressions' ({campaign_data['impressions']})")

    # Check conversions <= clicks (if conversions present)
    if ("conversions" in campaign_data and "clicks" in campaign_data and
        isinstance(campaign_data["conversions"], int) and isinstance(campaign_data["clicks"], int)):
        if campaign_data["conversions"] > campaign_data["clicks"]:
            errors.append(f"Field 'conversions' ({campaign_data['conversions']}) cannot exceed 'clicks' ({campaign_data['clicks']})")

    # Check date not in future
    if "date" in campaign_data and isinstance(campaign_data["date"], str):
        try:
            campaign_date = datetime.strptime(campaign_data["date"], "%Y-%m-%d")
            if campaign_date.date() > datetime.now().date():
                errors.append(f"Field 'date' cannot be in the future, got '{campaign_data['date']}'")

            # Check date not more than 90 days old (warning)
            days_old = (datetime.now() - campaign_date).days
            if days_old > 90:
                warnings.append(f"Field 'date' is {days_old} days old (more than 90 days)")
        except ValueError:
            # Date format error already caught in validate_data_types
            pass

    return errors, warnings


def detect_anomalies(campaign_data: dict) -> tuple[List[str], List[str]]:
    """
    Detect anomalies that might indicate data quality issues.

    Args:
        campaign_data: Campaign data dictionary

    Returns:
        Tuple of (errors, warnings)
    """
    errors = []
    warnings = []

    # impressions > 0 but clicks == 0 (warning - unusual but possible)
    if ("impressions" in campaign_data and "clicks" in campaign_data and
        isinstance(campaign_data["impressions"], int) and isinstance(campaign_data["clicks"], int)):
        if campaign_data["impressions"] > 0 and campaign_data["clicks"] == 0:
            warnings.append(f"Unusual: 'impressions' is {campaign_data['impressions']} but 'clicks' is 0")

    # impressions == 0 but clicks > 0 (error - impossible)
    if ("impressions" in campaign_data and "clicks" in campaign_data and
        isinstance(campaign_data["impressions"], int) and isinstance(campaign_data["clicks"], int)):
        if campaign_data["impressions"] == 0 and campaign_data["clicks"] > 0:
            errors.append(f"Impossible: 'impressions' is 0 but 'clicks' is {campaign_data['clicks']}")

    # spend > $100,000 (warning - unusual)
    if "spend" in campaign_data and isinstance(campaign_data["spend"], (float, int)):
        if campaign_data["spend"] > 100000:
            warnings.append(f"Unusually high spend: ${campaign_data['spend']:,.2f} (exceeds $100,000)")

    # CTR > 50% (error - likely data quality issue)
    if ("clicks" in campaign_data and "impressions" in campaign_data and
        isinstance(campaign_data["clicks"], int) and isinstance(campaign_data["impressions"], int)):
        if campaign_data["impressions"] > 0:
            ctr = (campaign_data["clicks"] / campaign_data["impressions"]) * 100
            if ctr > 50:
                errors.append(f"Impossibly high CTR: {ctr:.1f}% (clicks={campaign_data['clicks']}, impressions={campaign_data['impressions']})")

    # conversions > 0 but revenue == 0 or missing (warning)
    if "conversions" in campaign_data and isinstance(campaign_data["conversions"], int):
        if campaign_data["conversions"] > 0:
            if "revenue" not in campaign_data:
                warnings.append(f"'conversions' is {campaign_data['conversions']} but 'revenue' is missing")
            elif isinstance(campaign_data["revenue"], (float, int)) and campaign_data["revenue"] == 0:
                warnings.append(f"'conversions' is {campaign_data['conversions']} but 'revenue' is 0")

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

