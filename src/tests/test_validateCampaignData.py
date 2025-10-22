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
def campaign_wrong_types():
    """Campaign with incorrect data types."""
    return {
        "campaign_id": "camp_types_001",
        "source": "tiktok_ads",
        "date": "2024-10-15",
        "spend": "5000.00",  # Should be float, not string
        "impressions": 100000,
        "clicks": "2500",  # Should be int, not string
        "conversions": 50
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


def test_zero_clicks_triggers_warning(campaign_impressions_no_clicks):
    """Test that zero clicks with impressions triggers warning (unusual but valid)."""
    result = validate_campaign_data(campaign_impressions_no_clicks)
    
    # Should be valid but have warning
    assert result["valid"] is True
    assert len(result["warnings"]) > 0


def test_negative_spend_fails(campaign_negative_values):
    """Test that negative spend fails validation."""
    result = validate_campaign_data(campaign_negative_values)
    
    assert result["valid"] is False
    assert len(result["errors"]) > 0


def test_wrong_data_types_fails(campaign_wrong_types):
    """Test that incorrect data types fail validation."""
    result = validate_campaign_data(campaign_wrong_types)
    
    assert result["valid"] is False
    assert len(result["errors"]) > 0


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


# Additional test cases to implement (optional):
# - Test invalid date format (e.g., "10/15/2024" instead of "2024-10-15")
# - Test missing campaign_id
# - Test empty strings for required fields
# - Test None values
# - Test extremely large numbers
# - Test special characters in campaign_id

