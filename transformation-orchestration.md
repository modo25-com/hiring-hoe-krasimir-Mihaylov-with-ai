# Transformation Orchestration - How dbt Runs Are Triggered

## Overview

After Airbyte ingests data into Snowflake's RAW schema, we need to trigger dbt transformations to process that data through STAGING → ANALYTICS → METRICS. Here are the recommended approaches:

---

## Recommended Approach: Prefect Workflows

### Architecture

```
Airbyte Sync Completes
    ↓
Airbyte Webhook → AWS API Gateway
    ↓
API Gateway → AWS Lambda
    ↓
Lambda → Prefect Cloud API (trigger flow)
    ↓
Prefect Flow Runs
    ↓ (orchestrates)
dbt runs on worker
    ↓
Updates Snowflake tables
```

### Implementation

#### 1. Prefect Flow Definition

```python
# flows/dbt_transform.py
from prefect import flow, task
from prefect.blocks.system import Secret
import subprocess
import requests
from datetime import datetime

@task(retries=2, retry_delay_seconds=60)
def check_airbyte_sync_status(connection_id: str):
    """Verify Airbyte sync completed successfully"""
    airbyte_url = Secret.load("airbyte-api-url").get()
    response = requests.get(
        f"{airbyte_url}/api/v1/connections/{connection_id}/status"
    )
    if response.json()["status"] != "succeeded":
        raise Exception(f"Airbyte sync failed: {response.json()}")
    return response.json()

@task(retries=2, retry_delay_seconds=60)
def run_dbt_models(
    models: str,
    target: str = "prod",
    full_refresh: bool = False
):
    """Execute dbt models"""
    cmd = [
        "dbt", "run",
        "--models", models,
        "--target", target,
        "--profiles-dir", "/opt/dbt"
    ]

    if full_refresh:
        cmd.append("--full-refresh")

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd="/opt/dbt/bosco_analytics"
    )

    if result.returncode != 0:
        raise Exception(f"dbt run failed: {result.stderr}")

    return {
        "stdout": result.stdout,
        "models_run": models,
        "timestamp": datetime.utcnow().isoformat()
    }

@task(retries=2, retry_delay_seconds=60)
def run_dbt_tests(models: str):
    """Run dbt tests on transformed data"""
    result = subprocess.run(
        ["dbt", "test", "--models", models],
        capture_output=True,
        text=True,
        cwd="/opt/dbt/bosco_analytics"
    )

    if result.returncode != 0:
        # Log but don't fail - send alert instead
        send_alert(f"dbt tests failed: {result.stderr}")

    return result.stdout

@task
def send_slack_notification(status: str, details: dict):
    """Notify team of transformation completion"""
    webhook_url = Secret.load("slack-webhook").get()
    requests.post(webhook_url, json={
        "text": f"dbt transformation {status}",
        "blocks": [{
            "type": "section",
            "text": {"type": "mrkdwn", "text": f"```{details}```"}
        }]
    })

@flow(name="dbt-transformation-flow")
def dbt_transformation_flow(
    source: str,
    connection_id: str = None,
    full_refresh: bool = False
):
    """
    Main dbt transformation flow triggered after Airbyte sync

    Args:
        source: Source name (e.g., 'google_ads', 'facebook_ads')
        connection_id: Airbyte connection ID (optional verification)
        full_refresh: Whether to do full refresh vs incremental
    """

    # 1. Verify Airbyte sync if connection_id provided
    if connection_id:
        check_airbyte_sync_status(connection_id)

    # 2. Run staging models for this source
    staging_result = run_dbt_models(
        models=f"staging.stg_{source}*",
        full_refresh=full_refresh
    )

    # 3. Run tests on staging
    run_dbt_tests(models=f"staging.stg_{source}*")

    # 4. Run downstream analytics models
    analytics_result = run_dbt_models(
        models="marts.fct_campaign_performance+",  # + means this model and all downstream
        full_refresh=False  # Analytics are always incremental
    )

    # 5. Refresh metrics (materialized views)
    metrics_result = run_dbt_models(
        models="metrics.*",
        full_refresh=False
    )

    # 6. Run final tests
    run_dbt_tests(models="marts.*")

    # 7. Notify success
    send_slack_notification("completed", {
        "source": source,
        "staging_models": staging_result["models_run"],
        "timestamp": staging_result["timestamp"]
    })

    return {
        "status": "success",
        "source": source,
        "staging": staging_result,
        "analytics": analytics_result,
        "metrics": metrics_result
    }


@flow(name="full-dbt-refresh")
def full_dbt_refresh():
    """
    Full refresh of all dbt models - scheduled daily at 2 AM
    """

    # Run all staging models
    run_dbt_models(models="staging.*", full_refresh=False)

    # Run all marts
    run_dbt_models(models="marts.*", full_refresh=False)

    # Run all metrics
    run_dbt_models(models="metrics.*", full_refresh=False)

    # Run all tests
    run_dbt_tests(models="all")

    send_slack_notification("completed", {"type": "full_refresh"})
```

#### 2. Airbyte Webhook Handler (AWS Lambda)

```python
# lambda/airbyte_webhook_handler.py
import json
import boto3
import os
from prefect import get_client

def lambda_handler(event, context):
    """
    Receives webhook from Airbyte when sync completes
    Triggers Prefect flow to run dbt transformations
    """

    # Parse Airbyte webhook payload
    body = json.loads(event['body'])

    connection_id = body.get('connectionId')
    status = body.get('status')
    source_name = body.get('sourceName')  # Custom field from Airbyte

    if status != 'succeeded':
        print(f"Airbyte sync failed for {source_name}, skipping transformation")
        return {
            'statusCode': 200,
            'body': json.dumps({'message': 'Sync failed, no transformation triggered'})
        }

    # Trigger Prefect flow
    prefect_api_url = os.environ['PREFECT_API_URL']
    prefect_api_key = os.environ['PREFECT_API_KEY']

    # Get Prefect client
    async with get_client() as client:
        # Trigger the dbt transformation flow
        deployment = await client.read_deployment_by_name(
            "dbt-transformation-flow/production"
        )

        flow_run = await client.create_flow_run_from_deployment(
            deployment.id,
            parameters={
                "source": source_name,
                "connection_id": connection_id,
                "full_refresh": False
            }
        )

        print(f"Triggered Prefect flow {flow_run.id} for source {source_name}")

    return {
        'statusCode': 200,
        'body': json.dumps({
            'message': 'Transformation triggered',
            'flow_run_id': str(flow_run.id)
        })
    }
```

#### 3. Airbyte Webhook Configuration

In Airbyte UI or API:

```json
{
  "connectionId": "abc-123",
  "name": "Google Ads → Snowflake",
  "webhook": {
    "url": "https://api.example.com/webhooks/airbyte",
    "method": "POST",
    "headers": {
      "X-API-Key": "secret-key"
    },
    "payload": {
      "connectionId": "{{connection.id}}",
      "status": "{{sync.status}}",
      "sourceName": "google_ads",
      "recordsSynced": "{{sync.recordsSynced}}",
      "bytesEmitted": "{{sync.bytesEmitted}}"
    }
  }
}
```

#### 4. Scheduled Full Refreshes (Prefect Deployment)

```python
# deploy.py
from prefect.deployments import Deployment
from prefect.server.schemas.schedules import CronSchedule
from flows.dbt_transform import full_dbt_refresh, dbt_transformation_flow

# Schedule 1: Full refresh daily at 2 AM UTC
full_refresh_deployment = Deployment.build_from_flow(
    flow=full_dbt_refresh,
    name="daily-full-refresh",
    schedule=CronSchedule(cron="0 2 * * *", timezone="UTC"),
    work_queue_name="dbt-transforms"
)

full_refresh_deployment.apply()

# Schedule 2: Event-driven (webhook) deployment
webhook_deployment = Deployment.build_from_flow(
    flow=dbt_transformation_flow,
    name="production",
    work_queue_name="dbt-transforms",
    parameters={
        "full_refresh": False
    }
)

webhook_deployment.apply()
```

---

## Alternative Approaches

### Option 2: Airbyte + dbt Cloud (Simpler, Managed)

**How it works:**
- Airbyte has native integration with dbt Cloud
- Configure dbt Cloud job to trigger after Airbyte sync
- No custom orchestration code needed

**Setup:**

1. **In dbt Cloud:**
   - Create job "Transform Google Ads"
   - Configure to run models: `staging.stg_google_ads* marts.fct_campaign_performance+ metrics.*`

2. **In Airbyte:**
   - Go to connection settings
   - Enable "dbt Cloud Integration"
   - Select dbt Cloud job ID
   - Choose trigger condition: "After sync succeeds"

**Pros:**
- ✅ Zero code orchestration
- ✅ Fully managed (dbt Cloud handles retries, logging, scheduling)
- ✅ Nice UI for viewing transformation runs

**Cons:**
- ❌ dbt Cloud costs $100-500/month (vs free dbt Core)
- ❌ Less flexibility for complex workflows
- ❌ Vendor lock-in to dbt Cloud

**Cost:**
- dbt Cloud Developer: $100/month (1 developer)
- dbt Cloud Team: $300/month (up to 8 developers)

---

### Option 3: Snowflake Tasks + Streams (Serverless, Native)

**How it works:**
- Snowflake STREAMS detect changes in RAW tables
- Snowflake TASKS run dbt models when stream has data
- All orchestration happens inside Snowflake

**Setup:**

```sql
-- 1. Create stream on RAW table to detect new data
CREATE OR REPLACE STREAM raw_google_ads_stream
ON TABLE raw.google_ads_campaigns;

-- 2. Create task to run dbt when stream has data
CREATE OR REPLACE TASK run_dbt_google_ads
  WAREHOUSE = transformation_wh
  SCHEDULE = '5 MINUTE'  -- Check every 5 minutes
WHEN
  SYSTEM$STREAM_HAS_DATA('raw_google_ads_stream')
AS
  CALL dbt_run_stored_proc('staging.stg_google_ads*');

-- 3. Create downstream task (runs after staging completes)
CREATE OR REPLACE TASK run_dbt_analytics
  WAREHOUSE = transformation_wh
  AFTER run_dbt_google_ads  -- DAG dependency
AS
  CALL dbt_run_stored_proc('marts.fct_campaign_performance+');

-- 4. Start tasks
ALTER TASK run_dbt_analytics RESUME;
ALTER TASK run_dbt_google_ads RESUME;
```

**dbt as Snowflake Stored Procedure:**

```sql
-- Wrapper to run dbt from Snowflake
CREATE OR REPLACE PROCEDURE dbt_run_stored_proc(models VARCHAR)
  RETURNS VARCHAR
  LANGUAGE PYTHON
  RUNTIME_VERSION = '3.8'
  PACKAGES = ('dbt-snowflake')
  HANDLER = 'run_dbt'
AS
$$
def run_dbt(session, models):
    import subprocess
    result = subprocess.run(
        ['dbt', 'run', '--models', models],
        capture_output=True
    )
    return result.stdout.decode()
$$;
```

**Pros:**
- ✅ Native Snowflake (no external orchestrator)
- ✅ Serverless (no Prefect infrastructure)
- ✅ Very low latency (runs as soon as data arrives)

**Cons:**
- ❌ Limited observability compared to Prefect
- ❌ Harder to debug failures
- ❌ dbt logs not easily accessible
- ❌ More complex setup

---

### Option 4: Simple Cron + Lambda (Cheapest)

**How it works:**
- CloudWatch Events trigger Lambda every hour
- Lambda checks if Airbyte synced new data
- If yes, run dbt via ECS Fargate task

**Setup:**

```python
# lambda/hourly_transform.py
import boto3
from datetime import datetime, timedelta

ecs = boto3.client('ecs')
snowflake = boto3.client('snowflake')  # hypothetical

def lambda_handler(event, context):
    # Check if any new data in last hour
    query = """
    SELECT COUNT(*)
    FROM raw.google_ads_campaigns
    WHERE _airbyte_emitted_at > DATEADD(hour, -1, CURRENT_TIMESTAMP())
    """

    result = execute_snowflake_query(query)

    if result['count'] > 0:
        # Trigger ECS task to run dbt
        ecs.run_task(
            cluster='dbt-cluster',
            taskDefinition='dbt-transform',
            launchType='FARGATE',
            overrides={
                'containerOverrides': [{
                    'name': 'dbt',
                    'command': ['dbt', 'run', '--models', 'staging.* marts.* metrics.*']
                }]
            }
        )
        return {'status': 'triggered'}
    else:
        return {'status': 'no_new_data'}
```

**Pros:**
- ✅ Very simple
- ✅ Cheap ($10-20/month)
- ✅ No additional orchestrator needed

**Cons:**
- ❌ Runs on schedule, not event-driven
- ❌ May run unnecessarily if no new data
- ❌ No retry logic
- ❌ Limited observability

---

## Recommended Architecture Decision

### For Ask Bosco: **Option 1 (Prefect) or Option 2 (dbt Cloud)**

**Choose Prefect if:**
- Want full control and flexibility
- Have DevOps resources to manage infrastructure
- Need complex workflows (e.g., ML training after transformations)
- Want to minimize costs ($50-100/month)

**Choose dbt Cloud if:**
- Want zero operational overhead
- Budget allows $300/month
- Team is small (< 5 people)
- Want best-in-class dbt experience

### My Recommendation: **Start with dbt Cloud, migrate to Prefect later**

**Phase 1 (Months 0-6):**
- Use dbt Cloud for simplicity
- Focus on building models, not orchestration
- Iterate quickly with nice UI

**Phase 2 (Months 6+):**
- When you hit 50+ customers, costs justify building own orchestration
- Migrate to Prefect + self-hosted dbt Core
- Save $200-300/month, gain flexibility

---

## Data Freshness Considerations

### Latency Requirements

| Use Case | Freshness Required | Strategy |
|----------|-------------------|----------|
| Executive dashboard | 1-4 hours | Hourly incremental dbt runs |
| Campaign monitoring | 15-30 minutes | High-frequency syncs + fast transforms |
| Real-time alerts | < 5 minutes | Stream directly to Redis, bypass warehouse |
| Historical reports | 24 hours | Daily batch refresh |

### Optimization for Low Latency

If you need < 15 min freshness:

```python
@flow(name="fast-transform-flow")
def fast_transform_for_dashboards(source: str):
    """
    Optimized for speed - only transform what dashboards need
    """

    # Only run models tagged 'dashboard'
    run_dbt_models(
        models="tag:dashboard",
        full_refresh=False
    )

    # Skip tests (run separately in background)

    # Warm Redis cache
    warm_dashboard_cache()
```

**dbt model:**
```sql
-- models/metrics/daily_campaign_summary.sql
{{
  config(
    materialized='incremental',
    tags=['dashboard', 'high_priority']
  )
}}

-- Only process last 2 days for speed
WHERE date >= CURRENT_DATE() - 2
```

---

## Monitoring & Alerting

### What to Monitor

```python
@task
def check_transform_health():
    """Monitor transformation pipeline health"""

    checks = {
        # 1. Data freshness
        "data_freshness": check_data_freshness(),

        # 2. dbt test failures
        "test_failures": get_dbt_test_failures(),

        # 3. Row count anomalies
        "row_counts": check_row_count_anomalies(),

        # 4. Transformation lag
        "transform_lag": check_transform_lag()
    }

    for check_name, result in checks.items():
        if not result['passing']:
            send_pagerduty_alert(check_name, result)

    return checks

def check_data_freshness():
    """Alert if data is stale"""
    query = """
    SELECT
        MAX(_airbyte_emitted_at) as last_sync,
        DATEDIFF('minute', MAX(_airbyte_emitted_at), CURRENT_TIMESTAMP()) as minutes_stale
    FROM raw.google_ads_campaigns
    """

    result = execute_query(query)

    return {
        'passing': result['minutes_stale'] < 120,  # Alert if > 2 hours stale
        'minutes_stale': result['minutes_stale']
    }
```

---

## Summary: Transformation Trigger Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    TRANSFORMATION PIPELINE                      │
└─────────────────────────────────────────────────────────────────┘

TRIGGER OPTIONS:

Option 1: Event-Driven (Airbyte Webhook → Prefect)
  Airbyte sync completes
    → Webhook to API Gateway
    → Lambda triggers Prefect flow
    → Prefect runs dbt
    → dbt transforms Snowflake
  Latency: 5-10 minutes
  Cost: $50-100/month
  Complexity: Medium

Option 2: Managed (Airbyte → dbt Cloud)
  Airbyte sync completes
    → dbt Cloud job auto-triggered
    → dbt Cloud runs transformations
  Latency: 10-15 minutes
  Cost: $300/month
  Complexity: Low

Option 3: Native (Snowflake Streams + Tasks)
  New data arrives in RAW
    → Stream detects changes
    → Snowflake Task runs dbt
  Latency: 5-10 minutes
  Cost: $20-50/month
  Complexity: High

Option 4: Schedule-Based (Cron + Lambda)
  Every hour
    → Lambda checks for new data
    → If found, trigger dbt run
  Latency: 30-60 minutes
  Cost: $10-20/month
  Complexity: Low

RECOMMENDATION:
  Start: dbt Cloud (fast to implement, fully managed)
  Scale: Migrate to Prefect (more control, lower cost)
```

---

## Next Steps

1. **Prototype with dbt Cloud** (Week 1-2)
   - Connect to Snowflake
   - Set up 3 test transformations
   - Configure Airbyte integration

2. **Add monitoring** (Week 3)
   - Data freshness checks
   - dbt test alerts

3. **Optimize for latency** (Month 2)
   - Incremental models
   - Partition large tables
   - Dashboard-specific materialized views

4. **Consider Prefect migration** (Month 6+)
   - When orchestration costs > $200/month
   - Or when you need custom workflows

Would you like me to elaborate on any of these options or show more detailed code examples?
