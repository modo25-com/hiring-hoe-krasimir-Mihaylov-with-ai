# Task 4: AI-Generated Code Review Challenge

## Background
Your mid-level engineer used ChatGPT to implement a data validation function for campaign data. The code runs and passes basic tests, but you suspect there may be subtle bugs, edge cases, or design issues that AI missed.

## Task: Review and Fix AI-Generated Code
You will review AI-generated code (with intentional bugs) and validate/improve it. This simulates the real VP Engineering skill: **reviewing and validating code that your team (or AI) produces**.

## Three-Phase Approach

### Phase 1: Generate Code with AI (10 minutes)
1. **Use AI to implement the validation function:**
   - Use Claude, ChatGPT, Cursor, or Copilot
   - Give it the requirements below
   - Have it generate code for `src/functions/validateCampaignData.py`
   - Document which AI tool and prompts you used

2. **Run the initial tests:**
   ```bash
   pytest src/tests/test_validateCampaignData.py -v
   ```

### Phase 2: Critical Code Review (15 minutes)
3. **Review the AI-generated code carefully:**
   - Identify bugs, edge cases, or design flaws
   - Look for subtle issues AI often makes:
     - Missing None/null checks
     - Off-by-one errors
     - Race conditions or state issues
     - Type confusion
     - Logic errors in complex conditions
     - Missing error handling

4. **Document issues found:**
   - Create `TASK4_REVIEW.md`
   - List all issues you found
   - Categorize by severity (Critical, High, Medium, Low)

### Phase 3: Fix and Improve (5 minutes)
5. **Fix the most critical issues:**
   - Implement fixes for at least the top 3 issues
   - Add comments explaining what you fixed and why
   - Re-run tests to validate fixes

## Validation Requirements

## Campaign Data Schema

A campaign data payload looks like this:

```python
{
    "campaign_id": "camp_123",
    "campaign_name": "Summer Sale 2024",
    "source": "google_ads",  # or "facebook_ads", "tiktok_ads", etc.
    "date": "2024-10-15",
    "spend": 5000.00,
    "impressions": 100000,
    "clicks": 2500,
    "conversions": 50,
    "revenue": 7500.00,
    "currency": "USD"
}
```

## Validation Rules

### Required Fields
- `campaign_id`, `source`, `date`, `spend`, `impressions`, `clicks`

### Data Types
- `campaign_id`: string
- `spend`, `revenue`: float (positive or zero)
- `impressions`, `clicks`, `conversions`: int (non-negative)
- `date`: string in YYYY-MM-DD format

### Business Rules
- `spend` must be >= 0
- `clicks` cannot exceed `impressions`
- `conversions` cannot exceed `clicks`
- `revenue` (if present) should be >= 0
- `date` cannot be in the future
- `date` should not be more than 90 days in the past (warning, not error)

### Anomaly Detection
- If `impressions` > 0 but `clicks` == 0, flag as warning (unusual but possible)
- If `impressions` == 0 but `clicks` > 0, flag as error (impossible)
- If `spend` > $100,000 in a single day, flag as warning (might be legitimate but unusual)
- If Click-Through Rate (CTR = clicks/impressions) > 50%, flag as error (likely data quality issue)
- If `conversions` > 0 but `revenue` == 0 or missing, flag as warning

## Expected Function Signature

```python
def validate_campaign_data(campaign_data: dict) -> dict:
    """
    Validates marketing campaign data.
    
    Args:
        campaign_data: Dictionary containing campaign metrics
        
    Returns:
        Dictionary with validation results:
        {
            "valid": bool,
            "errors": [list of error messages],
            "warnings": [list of warning messages],
            "campaign_id": str or None,
            "validated_at": str (ISO timestamp)
        }
    """
    pass
```

## Test Data Provided

Mock campaign data fixtures are provided in the test file with various scenarios:
- Valid campaigns (happy path)
- Missing required fields
- Invalid data types
- Business rule violations
- Anomalies and edge cases

## Evaluation Criteria (AI-Era Focus)

- **Bug Detection (35%):** Can you catch subtle bugs that AI introduced or missed?
- **Critical Thinking (25%):** Do you understand WHY the code is wrong (not just that it is)?
- **Prioritization (20%):** Can you distinguish critical bugs from minor issues?
- **Fixes (15%):** Can you implement correct fixes quickly?
- **Communication (5%):** Can you explain issues clearly in your review doc?

**We're NOT evaluating:**
- How fast you code from scratch (use AI for that!)
- Whether you memorize Python syntax
- Whether you use AI tools (we expect you to!)

**We ARE evaluating:**
- Can you be the "senior reviewer" for AI-generated code?
- Can you catch bugs AI doesn't see?
- Can you validate code your team (using AI) produces?

## Time
You should spend approximately 30 minutes total on this task.

## Running the Tests

```bash
# Install dependencies
pip install -r requirements.txt

# Run tests
pytest src/tests/test_validateCampaignData.py -v

# Run with coverage
pytest src/tests/test_validateCampaignData.py --cov=src/functions --cov-report=term
```

## What We're Looking For

This is an **AI-era assessment**. We're testing:

- **Validation skills:** Can you be the "senior engineer" reviewing AI output?
- **Bug detection:** Can you spot subtle issues AI introduces?
- **Critical thinking:** Do you understand WHY code is wrong?
- **Prioritization:** Can you focus on what matters vs. minor style issues?
- **Speed:** Can you use AI to move fast while maintaining quality?

**Great candidates will:**
- Find 5-7 real bugs in AI-generated code
- Explain clearly why each bug is problematic
- Prioritize which bugs to fix first
- Fix critical issues quickly (using AI or not)
- Show they can lead a team that uses AI tools

**Remember:** This is a VP Engineering role. We're not testing "can you implement from scratch in 30 minutes." We're testing "can you validate what your AI-assisted team produces."

## Bonus Context (If Time Permits)
Think about:
- How would you coach your mid-level engineer to use AI better?
- What guidelines would prevent these bugs in future AI-generated code?
- How do you balance AI productivity with code quality?

