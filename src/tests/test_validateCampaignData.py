"""
Unit tests for campaign data validation.

Run with: pytest src/tests/test_validateCampaignData.py -v
"""

import pytest
from datetime import datetime, timedelta
from src.functions.validateCampaignData import validate_campaign_data


# Test Fixtures - Various campaign data scenarios

@pytest.fixture
def valid_campaign():
    """A valid campaign with all required fields and reasonable metrics."""
    return {
        "campaign_id": "camp_valid_001",
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


@pytest.fixture
def campaign_missing_required_fields():
    """Campaign missing required fields."""
    return {
        "campaign_id": "camp_missing_001",
        "source": "facebook_ads",
        # Missing: date, spend, impressions, clicks
    }


@pytest.fixture
def valid_base_campaign():
    """A minimal valid campaign to use as a base for type testing."""
    return {
        "campaign_id": "camp_test",
        "source": "google_ads",
        "date": "2024-10-15",
        "spend": 1000.0,
        "impressions": 10000,
        "clicks": 500
    }


@pytest.fixture
def campaign_impossible_metrics():
    """Campaign with impossible metric combinations."""
    return {
        "campaign_id": "camp_impossible_001",
        "source": "google_ads",
        "date": "2024-10-15",
        "spend": 1000.00,
        "impressions": 0,  # 0 impressions
        "clicks": 500,  # but 500 clicks - impossible!
        "conversions": 10
    }


@pytest.fixture
def campaign_clicks_exceed_impressions():
    """Campaign where clicks exceed impressions."""
    return {
        "campaign_id": "camp_exceed_001",
        "source": "facebook_ads",
        "date": "2024-10-15",
        "spend": 2000.00,
        "impressions": 1000,
        "clicks": 1500,  # More clicks than impressions
        "conversions": 20
    }


@pytest.fixture
def campaign_conversions_exceed_clicks():
    """Campaign where conversions exceed clicks."""
    return {
        "campaign_id": "camp_conv_001",
        "source": "google_ads",
        "date": "2024-10-15",
        "spend": 3000.00,
        "impressions": 50000,
        "clicks": 100,
        "conversions": 150  # More conversions than clicks
    }


@pytest.fixture
def campaign_future_date():
    """Campaign with a date in the future."""
    future_date = (datetime.now() + timedelta(days=5)).strftime("%Y-%m-%d")
    return {
        "campaign_id": "camp_future_001",
        "source": "google_ads",
        "date": future_date,
        "spend": 1000.00,
        "impressions": 10000,
        "clicks": 200,
        "conversions": 5
    }


@pytest.fixture
def campaign_very_old_date():
    """Campaign with a date more than 90 days old (should trigger warning)."""
    old_date = (datetime.now() - timedelta(days=120)).strftime("%Y-%m-%d")
    return {
        "campaign_id": "camp_old_001",
        "source": "facebook_ads",
        "date": old_date,
        "spend": 500.00,
        "impressions": 5000,
        "clicks": 100,
        "conversions": 2
    }


@pytest.fixture
def campaign_high_spend():
    """Campaign with unusually high spend (should trigger warning)."""
    return {
        "campaign_id": "camp_highspend_001",
        "source": "google_ads",
        "date": "2024-10-15",
        "spend": 150000.00,  # $150k in one day - unusual
        "impressions": 500000,
        "clicks": 10000,
        "conversions": 200,
        "revenue": 300000.00
    }


@pytest.fixture
def campaign_high_ctr():
    """Campaign with impossibly high CTR (>50%)."""
    return {
        "campaign_id": "camp_highctr_001",
        "source": "tiktok_ads",
        "date": "2024-10-15",
        "spend": 1000.00,
        "impressions": 1000,
        "clicks": 600,  # 60% CTR - likely data quality issue
        "conversions": 30
    }


@pytest.fixture
def campaign_conversions_no_revenue():
    """Campaign with conversions but no revenue (should trigger warning)."""
    return {
        "campaign_id": "camp_norev_001",
        "source": "facebook_ads",
        "date": "2024-10-15",
        "spend": 2000.00,
        "impressions": 50000,
        "clicks": 1000,
        "conversions": 25
        # No revenue field
    }


@pytest.fixture
def campaign_impressions_no_clicks():
    """Campaign with impressions but zero clicks (unusual but possible)."""
    return {
        "campaign_id": "camp_noclicks_001",
        "source": "google_ads",
        "date": "2024-10-15",
        "spend": 500.00,
        "impressions": 10000,
        "clicks": 0,  # 0 clicks - unusual but possible
        "conversions": 0
    }


@pytest.fixture
def campaign_negative_values():
    """Campaign with negative values."""
    return {
        "campaign_id": "camp_negative_001",
        "source": "facebook_ads",
        "date": "2024-10-15",
        "spend": -500.00,  # Negative spend
        "impressions": 10000,
        "clicks": 200,
        "conversions": 5
    }


# Test Cases

def test_valid_campaign_passes_validation(valid_campaign):
    """Test that a valid campaign passes all validation."""
    result = validate_campaign_data(valid_campaign)
    
    assert result["valid"] is True
    assert len(result["errors"]) == 0
    assert result["campaign_id"] == "camp_valid_001"
    assert "validated_at" in result


def test_missing_required_fields_fails(campaign_missing_required_fields):
    """Test that missing required fields triggers errors."""
    result = validate_campaign_data(campaign_missing_required_fields)
    
    assert result["valid"] is False
    assert len(result["errors"]) > 0
    # Should have errors for missing date, spend, impressions, clicks


def test_impossible_metrics_fails(campaign_impossible_metrics):
    """Test that impossible metrics (0 impressions, 500 clicks) fail validation."""
    result = validate_campaign_data(campaign_impossible_metrics)
    
    assert result["valid"] is False
    assert len(result["errors"]) > 0
    # Should detect that clicks > 0 when impressions = 0


def test_clicks_exceed_impressions_fails(campaign_clicks_exceed_impressions):
    """Test that clicks exceeding impressions fails validation."""
    result = validate_campaign_data(campaign_clicks_exceed_impressions)
    
    assert result["valid"] is False
    assert len(result["errors"]) > 0


def test_conversions_exceed_clicks_fails(campaign_conversions_exceed_clicks):
    """Test that conversions exceeding clicks fails validation."""
    result = validate_campaign_data(campaign_conversions_exceed_clicks)
    
    assert result["valid"] is False
    assert len(result["errors"]) > 0


def test_future_date_fails(campaign_future_date):
    """Test that future dates fail validation."""
    result = validate_campaign_data(campaign_future_date)
    
    assert result["valid"] is False
    assert len(result["errors"]) > 0


def test_old_date_triggers_warning(campaign_very_old_date):
    """Test that very old dates trigger a warning but don't fail validation."""
    result = validate_campaign_data(campaign_very_old_date)
    
    # Should still be valid but with warnings
    assert len(result["warnings"]) > 0


def test_high_spend_triggers_warning(campaign_high_spend):
    """Test that unusually high spend triggers a warning."""
    result = validate_campaign_data(campaign_high_spend)
    
    # Should pass validation but include warning
    assert len(result["warnings"]) > 0


def test_high_ctr_fails(campaign_high_ctr):
    """Test that impossibly high CTR (>50%) fails validation."""
    result = validate_campaign_data(campaign_high_ctr)
    
    assert result["valid"] is False
    assert len(result["errors"]) > 0


def test_conversions_no_revenue_warning(campaign_conversions_no_revenue):
    """Test that conversions without revenue trigger a warning."""
    result = validate_campaign_data(campaign_conversions_no_revenue)
    
    # Should be valid but have a warning
    assert len(result["warnings"]) > 0


# Anomaly Detection Tests - Simple and Reusable Pattern

@pytest.mark.parametrize("impressions,clicks,should_fail,should_warn,description", [
    # impressions > 0 but clicks == 0 (warning - unusual but possible)
    (1000, 0, False, True, "impressions with zero clicks - unusual"),
    (10000, 0, False, True, "high impressions with zero clicks"),
    (1, 0, False, True, "low impressions with zero clicks"),

    # impressions == 0 but clicks > 0 (error - impossible)
    (0, 1, True, False, "zero impressions but 1 click - impossible"),
    (0, 100, True, False, "zero impressions but many clicks - impossible"),

    # Normal cases - no anomaly
    (1000, 500, False, False, "normal CTR"),
    (1000, 10, False, False, "low CTR"),
    (0, 0, False, False, "zero impressions and zero clicks"),
])
def test_impressions_clicks_anomalies(valid_base_campaign, impressions, clicks, should_fail, should_warn, description):
    """Test anomaly detection for impressions/clicks combinations."""
    campaign = valid_base_campaign.copy()
    campaign["impressions"] = impressions
    campaign["clicks"] = clicks

    result = validate_campaign_data(campaign)

    if should_fail:
        assert result["valid"] is False, f"Should fail for {description}"
        assert any(("impressions" in error.lower() and "clicks" in error.lower()) or
                   "impossible" in error.lower()
                   for error in result["errors"])
    else:
        # Check for impossible impressions/clicks errors specifically
        impossible_errors = [e for e in result["errors"]
                            if "impossible" in e.lower() or
                            (("impressions" in e.lower() and "0" in e) and "clicks" in e.lower())]
        assert len(impossible_errors) == 0, f"Should not fail for {description}"

    if should_warn:
        assert len(result["warnings"]) > 0, f"Should warn for {description}"
        assert any("impressions" in warning.lower() and "clicks" in warning.lower()
                   for warning in result["warnings"])


@pytest.mark.parametrize("spend_value,should_warn,description", [
    (100000, False, "exactly $100,000 - not unusual"),
    (100000.01, True, "just over $100,000"),
    (100001, True, "$100,001"),
    (150000, True, "$150,000"),
    (1000000, True, "$1,000,000"),
    (99999.99, False, "just under $100,000"),
    (50000, False, "$50,000"),
    (1000, False, "normal spend"),
])
def test_high_spend_anomaly(valid_base_campaign, spend_value, should_warn, description):
    """Test spend > $100,000 warning (unusual)."""
    campaign = valid_base_campaign.copy()
    campaign["spend"] = spend_value

    result = validate_campaign_data(campaign)

    if should_warn:
        assert len(result["warnings"]) > 0, f"Should warn for {description}"
        assert any("spend" in warning.lower() and ("high" in warning.lower() or "unusual" in warning.lower())
                   for warning in result["warnings"])
    else:
        # Should not have high spend warnings
        high_spend_warnings = [w for w in result["warnings"]
                              if "spend" in w.lower() and ("high" in w.lower() or "unusual" in w.lower())]
        assert len(high_spend_warnings) == 0, f"Should not warn for {description}"


@pytest.mark.parametrize("impressions,clicks,should_fail,description", [
    # CTR > 50% (error - likely data quality issue)
    (100, 51, True, "51% CTR - just over threshold"),
    (100, 60, True, "60% CTR"),
    (100, 100, True, "100% CTR - impossible"),
    (1000, 600, True, "60% CTR with high volume"),

    # Normal CTR ranges
    (100, 50, False, "exactly 50% CTR - threshold"),
    (100, 49, False, "49% CTR - just under threshold"),
    (100, 25, False, "25% CTR"),
    (1000, 50, False, "5% CTR - normal"),
    (1000, 1, False, "0.1% CTR - low but valid"),
])
def test_high_ctr_anomaly(valid_base_campaign, impressions, clicks, should_fail, description):
    """Test CTR > 50% error (likely data quality issue)."""
    campaign = valid_base_campaign.copy()
    campaign["impressions"] = impressions
    campaign["clicks"] = clicks

    result = validate_campaign_data(campaign)

    if should_fail:
        assert result["valid"] is False, f"Should fail for {description}"
        assert any("ctr" in error.lower() or ("clicks" in error.lower() and "impressions" in error.lower())
                   for error in result["errors"])
    else:
        # Should not have high CTR errors
        ctr_errors = [e for e in result["errors"]
                     if "ctr" in e.lower() or ("high" in e.lower() and "%" in e)]
        assert len(ctr_errors) == 0, f"Should not fail for {description}"


@pytest.mark.parametrize("conversions,revenue,should_warn,description", [
    # conversions > 0 but revenue == 0 or missing (warning)
    (10, 0, True, "conversions with zero revenue"),
    (1, 0, True, "1 conversion with zero revenue"),
    (100, 0, True, "many conversions with zero revenue"),
    (10, None, True, "conversions with missing revenue"),  # revenue not in dict

    # Normal cases
    (10, 100, False, "conversions with revenue"),
    (1, 0.01, False, "conversions with small revenue"),
    (0, 0, False, "no conversions, no revenue"),
    (0, None, False, "no conversions, missing revenue"),
])
def test_conversions_revenue_anomaly(valid_base_campaign, conversions, revenue, should_warn, description):
    """Test conversions > 0 but revenue == 0 or missing warning."""
    campaign = valid_base_campaign.copy()
    campaign["conversions"] = conversions

    if revenue is None:
        # Don't include revenue field at all
        campaign.pop("revenue", None)
    else:
        campaign["revenue"] = revenue

    result = validate_campaign_data(campaign)

    if should_warn:
        assert len(result["warnings"]) > 0, f"Should warn for {description}"
        assert any("conversions" in warning.lower() and "revenue" in warning.lower()
                   for warning in result["warnings"])
    else:
        # Should not have conversions/revenue warnings
        conv_revenue_warnings = [w for w in result["warnings"]
                                if "conversions" in w.lower() and "revenue" in w.lower()]
        assert len(conv_revenue_warnings) == 0, f"Should not warn for {description}"


# Business Rules Validation Tests - Simple and Reusable Pattern

@pytest.mark.parametrize("spend_value,should_fail,description", [
    (-1, True, "negative spend"),
    (-0.01, True, "small negative spend"),
    (-1000, True, "large negative spend"),
    (0, False, "zero spend"),
    (0.01, False, "small positive spend"),
    (1000, False, "normal spend"),
    (100000, False, "large spend"),
])
def test_spend_validation(valid_base_campaign, spend_value, should_fail, description):
    """Test spend >= 0 rule."""
    campaign = valid_base_campaign.copy()
    campaign["spend"] = spend_value

    result = validate_campaign_data(campaign)

    if should_fail:
        assert result["valid"] is False, f"Should fail for {description}"
        assert any("spend" in error.lower() and "negative" in error.lower()
                   for error in result["errors"])
    else:
        # Should not have spend-related errors
        spend_errors = [e for e in result["errors"] if "spend" in e.lower() and "negative" in e.lower()]
        assert len(spend_errors) == 0, f"Should accept {description}"


@pytest.mark.parametrize("revenue_value,should_fail,description", [
    (-1, True, "negative revenue"),
    (-0.01, True, "small negative revenue"),
    (-1000, True, "large negative revenue"),
    (0, False, "zero revenue"),
    (0.01, False, "small positive revenue"),
    (1000, False, "normal revenue"),
])
def test_revenue_validation(valid_base_campaign, revenue_value, should_fail, description):
    """Test revenue >= 0 rule (if revenue present)."""
    campaign = valid_base_campaign.copy()
    campaign["revenue"] = revenue_value

    result = validate_campaign_data(campaign)

    if should_fail:
        assert result["valid"] is False, f"Should fail for {description}"
        assert any("revenue" in error.lower() and "negative" in error.lower()
                   for error in result["errors"])
    else:
        # Should not have revenue-related errors
        revenue_errors = [e for e in result["errors"] if "revenue" in e.lower() and "negative" in e.lower()]
        assert len(revenue_errors) == 0, f"Should accept {description}"


@pytest.mark.parametrize("impressions,clicks,should_fail,description", [
    (1000, 1001, True, "clicks exceed impressions by 1"),
    (1000, 1500, True, "clicks exceed impressions by many"),
    (0, 100, True, "zero impressions but clicks exist"),
    (1000, 1000, False, "clicks equal impressions"),
    (1000, 999, False, "clicks less than impressions"),
    (1000, 0, False, "zero clicks"),
    (0, 0, False, "zero impressions and zero clicks"),
])
def test_clicks_impressions_validation(valid_base_campaign, impressions, clicks, should_fail, description):
    """Test clicks <= impressions rule."""
    campaign = valid_base_campaign.copy()
    campaign["impressions"] = impressions
    campaign["clicks"] = clicks

    result = validate_campaign_data(campaign)

    if should_fail:
        assert result["valid"] is False, f"Should fail when {description}"
        assert any(("clicks" in error.lower() and "impressions" in error.lower()) or
                   ("impressions" in error.lower() and "clicks" in error.lower())
                   for error in result["errors"])
    else:
        # Should not have clicks/impressions relationship errors
        relationship_errors = [e for e in result["errors"]
                              if "clicks" in e.lower() and "impressions" in e.lower()
                              and ("exceed" in e.lower() or "impossible" in e.lower())]
        assert len(relationship_errors) == 0, f"Should accept when {description}"


@pytest.mark.parametrize("clicks,conversions,should_fail,description", [
    (100, 101, True, "conversions exceed clicks by 1"),
    (100, 200, True, "conversions exceed clicks by many"),
    (0, 10, True, "zero clicks but conversions exist"),
    (100, 100, False, "conversions equal clicks"),
    (100, 99, False, "conversions less than clicks"),
    (100, 0, False, "zero conversions"),
    (0, 0, False, "zero clicks and zero conversions"),
])
def test_conversions_clicks_validation(valid_base_campaign, clicks, conversions, should_fail, description):
    """Test conversions <= clicks rule (if conversions present)."""
    campaign = valid_base_campaign.copy()
    campaign["clicks"] = clicks
    campaign["conversions"] = conversions

    result = validate_campaign_data(campaign)

    if should_fail:
        assert result["valid"] is False, f"Should fail when {description}"
        assert any("conversions" in error.lower() and "clicks" in error.lower()
                   for error in result["errors"])
    else:
        # Should not have conversions/clicks relationship errors
        relationship_errors = [e for e in result["errors"]
                              if "conversions" in e.lower() and "clicks" in e.lower()
                              and "exceed" in e.lower()]
        assert len(relationship_errors) == 0, f"Should accept when {description}"


@pytest.mark.parametrize("days_offset,should_fail,should_warn,description", [
    (1, True, False, "1 day in future"),
    (5, True, False, "5 days in future"),
    (365, True, False, "1 year in future"),
    (0, False, False, "today"),
    (-1, False, False, "1 day ago"),
    (-30, False, False, "30 days ago"),
    (-89, False, False, "89 days ago"),
    (-90, False, False, "exactly 90 days ago"),
    (-91, False, True, "91 days ago - should warn"),
    (-120, False, True, "120 days ago - should warn"),
    (-365, False, True, "1 year ago - should warn"),
])
def test_date_validation(valid_base_campaign, days_offset, should_fail, should_warn, description):
    """Test date not in future (error) and date not more than 90 days old (warning) rules."""
    from datetime import datetime, timedelta

    campaign = valid_base_campaign.copy()
    test_date = (datetime.now() + timedelta(days=days_offset)).strftime("%Y-%m-%d")
    campaign["date"] = test_date

    result = validate_campaign_data(campaign)

    if should_fail:
        assert result["valid"] is False, f"Should fail for date {description}"
        assert any("date" in error.lower() and "future" in error.lower()
                   for error in result["errors"])
    else:
        # Should not have future date errors
        future_errors = [e for e in result["errors"] if "date" in e.lower() and "future" in e.lower()]
        assert len(future_errors) == 0, f"Should not fail for date {description}"

    if should_warn:
        assert len(result["warnings"]) > 0, f"Should warn for date {description}"
        assert any("date" in warning.lower() and "days" in warning.lower()
                   for warning in result["warnings"])
    elif not should_fail:
        # Should not have old date warnings
        old_date_warnings = [w for w in result["warnings"] if "date" in w.lower() and "days" in w.lower()]
        assert len(old_date_warnings) == 0, f"Should not warn for date {description}"


# Data Type Validation Tests - Simple and Reusable Pattern

@pytest.mark.parametrize("field,invalid_value,description", [
    # Numeric fields that should be float or int
    ("spend", "1000.00", "string instead of number"),
    ("spend", None, "None value"),
    ("spend", [1000], "list instead of number"),
    ("revenue", "500.00", "string instead of number"),
    ("revenue", None, "None value"),

    # Integer-only fields
    ("impressions", "10000", "string instead of int"),
    ("impressions", 10000.5, "float instead of int"),
    ("impressions", None, "None value"),
    ("clicks", "500", "string instead of int"),
    ("clicks", 500.5, "float instead of int"),
    ("clicks", None, "None value"),
    ("conversions", "50", "string instead of int"),
    ("conversions", 50.5, "float instead of int"),
    ("conversions", None, "None value"),

    # String fields
    ("campaign_id", 123, "int instead of string"),
    ("campaign_id", None, "None value"),
    ("source", 456, "int instead of string"),
    ("source", None, "None value"),
    ("date", 20241015, "int instead of string"),
    ("date", None, "None value"),
])
def test_invalid_data_types(valid_base_campaign, field, invalid_value, description):
    """Test that invalid data types for any field cause validation to fail."""
    campaign = valid_base_campaign.copy()
    campaign[field] = invalid_value

    result = validate_campaign_data(campaign)

    assert result["valid"] is False, f"Should fail when {field} is {description}"
    assert len(result["errors"]) > 0
    assert any(field in error.lower() for error in result["errors"])


@pytest.mark.parametrize("date_value,description", [
    ("10/15/2024", "MM/DD/YYYY format"),
    ("15-10-2024", "DD-MM-YYYY format"),
    ("2024/10/15", "YYYY/MM/DD with slashes"),
    ("2024-10-15T00:00:00", "ISO format with time"),
    ("Oct 15, 2024", "human readable format"),
    ("2024-13-01", "invalid month"),
    ("2024-10-32", "invalid day"),
    ("not-a-date", "invalid string"),
    ("", "empty string"),
])
def test_invalid_date_formats(valid_base_campaign, date_value, description):
    """Test that invalid date formats cause validation to fail."""
    campaign = valid_base_campaign.copy()
    campaign["date"] = date_value

    result = validate_campaign_data(campaign)

    assert result["valid"] is False, f"Should fail for date: {description}"
    assert len(result["errors"]) > 0
    assert any("date" in error.lower() for error in result["errors"])


@pytest.mark.parametrize("field,valid_value", [
    # Both int and float should work for spend/revenue
    ("spend", 1000.0),
    ("spend", 1000),
    ("revenue", 500.0),
    ("revenue", 500),

    # Int fields must be exactly int
    ("impressions", 10000),
    ("clicks", 500),
    ("conversions", 50),

    # String fields
    ("campaign_id", "camp_123"),
    ("source", "google_ads"),
    ("date", "2024-10-15"),
])
def test_valid_data_types(valid_base_campaign, field, valid_value):
    """Test that valid data types are accepted."""
    campaign = valid_base_campaign.copy()
    campaign[field] = valid_value

    result = validate_campaign_data(campaign)

    # Should not have type errors for this field
    type_errors = [e for e in result["errors"] if field in e.lower() and "type" in e.lower() or "must be" in e.lower()]
    assert len(type_errors) == 0, f"Should accept valid {field} value: {valid_value}"


def test_validation_result_structure():
    """Test that validation result has the expected structure."""
    campaign = {
        "campaign_id": "camp_test",
        "source": "google_ads",
        "date": "2024-10-15",
        "spend": 100.0,
        "impressions": 1000,
        "clicks": 50
    }
    
    result = validate_campaign_data(campaign)
    
    # Check required fields in result
    assert "valid" in result
    assert "errors" in result
    assert "warnings" in result
    assert "campaign_id" in result
    assert "validated_at" in result
    
    # Check types
    assert isinstance(result["valid"], bool)
    assert isinstance(result["errors"], list)
    assert isinstance(result["warnings"], list)
    assert isinstance(result["validated_at"], str)


def test_docstring_example_valid_campaign():
    """Test the first docstring example - valid campaign should pass."""
    campaign = {
        "campaign_id": "camp_123",
        "source": "google_ads",
        "date": "2024-10-15",
        "spend": 1000.0,
        "impressions": 50000,
        "clicks": 1000
    }

    result = validate_campaign_data(campaign)

    assert result["valid"] is True


def test_docstring_example_invalid_campaign():
    """Test the second docstring example - impossible metrics should fail."""
    campaign = {
        "campaign_id": "camp_456",
        "source": "facebook_ads",
        "date": "2024-10-15",
        "spend": 500.0,
        "impressions": 0,
        "clicks": 100
    }

    result = validate_campaign_data(campaign)

    assert result["valid"] is False
    # Check that errors mention both impressions and clicks
    assert any("impressions" in error.lower() and "clicks" in error.lower()
               for error in result["errors"])



