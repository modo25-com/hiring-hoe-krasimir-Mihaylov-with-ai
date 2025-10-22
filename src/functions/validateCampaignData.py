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


def _check_type(data: dict, field: str, expected_type: type | tuple, type_name: str) -> Optional[str]:
    """Helper: validate single field type."""
    if field not in data:
        return None

    value = data[field]

    # Exclude bools when checking for int (Python quirk: isinstance(True, int) == True)
    if expected_type == int and isinstance(value, bool):
        return f"Field '{field}' must be {type_name}, got {type(value).__name__}"

    if not isinstance(value, expected_type):
        return f"Field '{field}' must be {type_name}, got {type(value).__name__}"

    return None


def _check_date_format(data: dict, field: str) -> Optional[str]:
    """Helper: validate date string format."""
    if field not in data:
        return None

    value = data[field]

    if not isinstance(value, str):
        return f"Field '{field}' must be a string, got {type(value).__name__}"

    try:
        datetime.strptime(value, "%Y-%m-%d")
        return None
    except ValueError:
        return f"Field '{field}' must be in YYYY-MM-DD format, got '{value}'"


def validate_data_types(campaign_data: dict) -> List[str]:
    """
    Validate that field data types are correct.

    Args:
        campaign_data: Campaign data dictionary

    Returns:
        List of error messages for incorrect data types
    """
    checks = [
        _check_type(campaign_data, "spend", (float, int), "a number (float or int)"),
        _check_type(campaign_data, "revenue", (float, int), "a number (float or int)"),
        _check_type(campaign_data, "impressions", int, "an integer"),
        _check_type(campaign_data, "clicks", int, "an integer"),
        _check_type(campaign_data, "conversions", int, "an integer"),
        _check_date_format(campaign_data, "date"),
        _check_type(campaign_data, "campaign_id", str, "a string"),
        _check_type(campaign_data, "source", str, "a string"),
        _check_type(campaign_data, "campaign_name", str, "a string"),
        _check_type(campaign_data, "currency", str, "a string"),
    ]

    return [error for error in checks if error is not None]


def _check_non_negative(data: dict, field: str) -> Optional[str]:
    """Helper: validate field >= 0."""
    if field not in data:
        return None

    value = data[field]
    if isinstance(value, (float, int)) and value < 0:
        return f"Field '{field}' cannot be negative, got {value}"

    return None


def _check_not_exceeds(data: dict, field: str, limit_field: str) -> Optional[str]:
    """Helper: validate field <= limit_field."""
    if field not in data or limit_field not in data:
        return None

    value = data[field]
    limit = data[limit_field]

    if isinstance(value, int) and isinstance(limit, int) and value > limit:
        return f"Field '{field}' ({value}) cannot exceed '{limit_field}' ({limit})"

    return None


def _check_date_rules(data: dict) -> tuple[Optional[str], Optional[str]]:
    """Helper: validate date not in future (error) and not too old (warning)."""
    if "date" not in data or not isinstance(data["date"], str):
        return None, None

    try:
        campaign_date = datetime.strptime(data["date"], "%Y-%m-%d")
        error = None
        warning = None

        if campaign_date.date() > datetime.now().date():
            error = f"Field 'date' cannot be in the future, got '{data['date']}'"

        days_old = (datetime.now() - campaign_date).days
        if days_old > 90:
            warning = f"Field 'date' is {days_old} days old (more than 90 days)"

        return error, warning
    except ValueError:
        return None, None  # Date format error already caught in validate_data_types


def validate_business_rules(campaign_data: dict) -> tuple[List[str], List[str]]:
    """
    Validate business logic rules.

    Args:
        campaign_data: Campaign data dictionary

    Returns:
        Tuple of (errors, warnings)
    """
    date_error, date_warning = _check_date_rules(campaign_data)

    error_checks = [
        _check_non_negative(campaign_data, "spend"),
        _check_non_negative(campaign_data, "revenue"),
        _check_not_exceeds(campaign_data, "clicks", "impressions"),
        _check_not_exceeds(campaign_data, "conversions", "clicks"),
        date_error,
    ]

    warning_checks = [
        date_warning,
    ]

    errors = [e for e in error_checks if e is not None]
    warnings = [w for w in warning_checks if w is not None]

    return errors, warnings


def _check_impressions_clicks_anomaly(data: dict) -> tuple[Optional[str], Optional[str]]:
    """Helper: detect impossible or unusual impressions/clicks combinations."""
    if ("impressions" not in data or "clicks" not in data or
        not isinstance(data["impressions"], int) or not isinstance(data["clicks"], int)):
        return None, None

    impressions = data["impressions"]
    clicks = data["clicks"]
    error = None
    warning = None

    if impressions == 0 and clicks > 0:
        error = f"Impossible: 'impressions' is 0 but 'clicks' is {clicks}"
    elif impressions > 0 and clicks == 0:
        warning = f"Unusual: 'impressions' is {impressions} but 'clicks' is 0"

    return error, warning


def _check_high_spend(data: dict, threshold: float = 100000) -> Optional[str]:
    """Helper: warn if spend exceeds threshold."""
    if "spend" not in data or not isinstance(data["spend"], (float, int)):
        return None

    if data["spend"] > threshold:
        return f"Unusually high spend: ${data['spend']:,.2f} (exceeds ${threshold:,.0f})"

    return None


def _check_high_ctr(data: dict, threshold: float = 50) -> Optional[str]:
    """Helper: error if CTR exceeds threshold."""
    if ("clicks" not in data or "impressions" not in data or
        not isinstance(data["clicks"], int) or not isinstance(data["impressions"], int)):
        return None

    impressions = data["impressions"]
    clicks = data["clicks"]

    if impressions > 0:
        ctr = (clicks / impressions) * 100
        if ctr > threshold:
            return f"Impossibly high CTR: {ctr:.1f}% (clicks={clicks}, impressions={impressions})"

    return None


def _check_conversions_without_revenue(data: dict) -> Optional[str]:
    """Helper: warn if conversions exist but revenue is missing or zero."""
    if "conversions" not in data or not isinstance(data["conversions"], int):
        return None

    if data["conversions"] > 0:
        if "revenue" not in data:
            return f"'conversions' is {data['conversions']} but 'revenue' is missing"
        elif isinstance(data["revenue"], (float, int)) and data["revenue"] == 0:
            return f"'conversions' is {data['conversions']} but 'revenue' is 0"

    return None


def detect_anomalies(campaign_data: dict) -> tuple[List[str], List[str]]:
    """
    Detect anomalies that might indicate data quality issues.

    Args:
        campaign_data: Campaign data dictionary

    Returns:
        Tuple of (errors, warnings)
    """
    impressions_clicks_error, impressions_clicks_warning = _check_impressions_clicks_anomaly(campaign_data)

    error_checks = [
        impressions_clicks_error,
        _check_high_ctr(campaign_data),
    ]

    warning_checks = [
        impressions_clicks_warning,
        _check_high_spend(campaign_data),
        _check_conversions_without_revenue(campaign_data),
    ]

    errors = [e for e in error_checks if e is not None]
    warnings = [w for w in warning_checks if w is not None]

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

