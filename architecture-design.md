# Ask Bosco Marketing Analytics Platform - Simplified Architecture

## Executive Summary

This design uses a **minimal, serverless-first stack** leveraging managed services to reduce operational overhead. The core stack is: **Airbyte (open-source) → Snowflake (columnar warehouse) → dbt (open-source) → Python (FastAPI) → React**, optimized for heavy aggregation workloads.

**Philosophy:** Maximize managed services, minimize operational complexity, prefer open-source where available, optimize for analytical query performance.

**Key Decision:** Using **Snowflake** as the primary data warehouse instead of PostgreSQL due to:
- Columnar storage optimized for aggregations (10-100x faster than row-based)
- Automatic query optimization and caching
- Separation of storage and compute (scale independently)
- Built-in time travel and data versioning
- Pay-per-use with auto-suspend (no idle costs)

---

## Simplified Technology Stack

### Core Stack (5 technologies)
1. **Airbyte** (open-source) - Data ingestion from 100+ sources
2. **Snowflake** (managed, columnar) - Primary data warehouse optimized for analytics
3. **dbt** (open-source) - SQL-based transformations
4. **Python + FastAPI** (open-source) - Backend API services
5. **React** (open-source) - Frontend dashboards

### Supporting Services
- **Message Queue:** AWS SQS / GCP Pub/Sub (for async processing)
- **Object Storage:** AWS S3 / GCP Cloud Storage (raw data landing zone)
- **Cache:** Redis (managed) - Query result caching
- **Serverless Compute:** AWS Lambda / Cloud Functions (data quality checks)
- **ML Platform:** Snowflake ML / AWS SageMaker (built-in or external)

---

## Proposed Architecture: Columnar Warehouse + Serverless

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          DATA INGESTION                                     │
│                                                                             │
│  ┌────────────────────────────────────────────────────────────┐            │
│  │                    AIRBYTE (Self-hosted)                    │            │
│  │                                                             │            │
│  │  • 350+ pre-built connectors (Google Ads, Facebook, etc.)  │            │
│  │  • Open-source, community-supported                        │            │
│  │  • Built-in scheduling, retry logic, incremental sync      │            │
│  │  • Native Snowflake connector                              │            │
│  │                                                             │            │
│  │  Sources → Airbyte → Snowflake (RAW schema)                │            │
│  └─────────────────────────┬───────────────────────────────────┘            │
└────────────────────────────┼────────────────────────────────────────────────┘
                             ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          DATA WAREHOUSE: SNOWFLAKE                          │
│                                                                             │
│  ┌──────────────────────────────────────────────────────────────┐          │
│  │                   SNOWFLAKE (Columnar Storage)               │          │
│  │                                                              │          │
│  │  Schema: RAW                                                │          │
│  │  • raw.google_ads (JSON/VARIANT columns)                    │          │
│  │  • raw.facebook_ads                                         │          │
│  │  • raw.shopify_orders                                       │          │
│  │  • Auto-clustering by date + tenant_id                      │          │
│  │                                                              │          │
│  │         ↓ (dbt transformation)                              │          │
│  │                                                              │          │
│  │  Schema: STAGING                                            │          │
│  │  • stg_google_ads (validated, typed)                        │          │
│  │  • stg_facebook_ads                                         │          │
│  │  • Data quality tests via dbt tests                         │          │
│  │                                                              │          │
│  │         ↓ (dbt transformation)                              │          │
│  │                                                              │          │
│  │  Schema: ANALYTICS                                          │          │
│  │  • fct_campaign_performance (fact table)                    │          │
│  │  • dim_campaigns (dimension)                                │          │
│  │  • dim_ad_platforms (dimension)                             │          │
│  │  • Materialized views for common aggregations               │          │
│  │                                                              │          │
│  │         ↓ (dbt transformation)                              │          │
│  │                                                              │          │
│  │  Schema: METRICS                                            │          │
│  │  • daily_campaign_summary                                   │          │
│  │  • weekly_performance_rollups                               │          │
│  │  • Platform-specific metrics unified                        │          │
│  │                                                              │          │
│  │  Features:                                                  │          │
│  │  • Columnar storage (optimized for aggregations)            │          │
│  │  • Result cache (identical queries = instant)               │          │
│  │  • Time travel (query historical data up to 90 days)        │          │
│  │  • Zero-copy cloning (dev/staging environments)             │          │
│  │  • Automatic query optimization                             │          │
│  │  • Auto-suspend after 5 min idle (no waste)                 │          │
│  └──────────────────────────────────────────────────────────────┘          │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                             ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                      TRANSFORMATION LAYER: DBT                              │
│                                                                             │
│  ┌──────────────────────────────────────────────────────────────┐          │
│  │                    dbt Core (Open-Source)                     │          │
│  │                                                               │          │
│  │  models/                                                      │          │
│  │  ├── staging/                                                 │          │
│  │  │   ├── stg_google_ads.sql                                  │          │
│  │  │   └── stg_facebook_ads.sql                                │          │
│  │  ├── intermediate/                                            │          │
│  │  │   └── int_unified_campaigns.sql                           │          │
│  │  └── marts/                                                   │          │
│  │      ├── fct_campaign_performance.sql                        │          │
│  │      └── daily_campaign_summary.sql                          │          │
│  │                                                               │          │
│  │  • SQL-only transformations (no Python needed)                │          │
│  │  • Built-in data quality tests                               │          │
│  │  • Automatic lineage tracking                                │          │
│  │  • Incremental models (process only new data)                │          │
│  │  • Documentation generation                                  │          │
│  │  • Runs on schedule (Prefect/dbt Cloud)                      │          │
│  └──────────────────────────────────────────────────────────────┘          │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                             ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          AI/ML LAYER                                        │
│                                                                             │
│  ┌────────────────────────────────────────────────────────┐                │
│  │     AWS SageMaker / Vertex AI / Azure ML               │                │
│  │                                                         │                │
│  │  Training:                                             │                │
│  │  • Jupyter notebooks for experimentation               │                │
│  │  • Managed training jobs (spot instances)             │                │
│  │  • Model registry with versioning                     │                │
│  │                                                         │                │
│  │  Inference:                                            │                │
│  │  • Serverless endpoints (auto-scaling)                 │                │
│  │  • Batch transform for bulk predictions                │                │
│  │                                                         │                │
│  │  Models:                                               │                │
│  │  • Budget optimizer (spend allocation)                 │                │
│  │  • Anomaly detection (campaign issues)                 │                │
│  │  • Forecasting (future performance)                    │                │
│  │  • Attribution (multi-touch)                           │                │
│  └────────────────────────────────────────────────────────┘                │
│                                                                             │
│  Feature Store: PostgreSQL tables (simple approach)                        │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                             ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          API & SERVING LAYER                                │
│                                                                             │
│  ┌────────────────────────────────────────────────────────┐                │
│  │              FastAPI (Python Backend)                   │                │
│  │              Deployed on ECS / Cloud Run / App Service  │                │
│  │                                                         │                │
│  │  Endpoints:                                            │                │
│  │  • GET /campaigns - List campaigns with filters        │                │
│  │  • GET /metrics - Time-series metrics                  │                │
│  │  • GET /insights - ML-powered recommendations          │                │
│  │  • POST /alerts - Configure alerts                     │                │
│  │                                                         │                │
│  │  Features:                                             │                │
│  │  • Auto-generated OpenAPI docs                         │                │
│  │  • JWT authentication                                  │                │
│  │  • Query optimization (SQLAlchemy)                     │                │
│  │  • Response caching (Redis)                            │                │
│  │  • Rate limiting                                       │                │
│  └────────────────────────────────────────────────────────┘                │
│                                                                             │
│  ┌────────────────────────────────────────────────────────┐                │
│  │              React Frontend                             │                │
│  │              (Static hosting: S3 + CloudFront / CDN)    │                │
│  │                                                         │                │
│  │  • Dashboard with charts (Recharts/Chart.js)           │                │
│  │  • Real-time updates (WebSocket or polling)            │                │
│  │  • Campaign management UI                              │                │
│  └────────────────────────────────────────────────────────┘                │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                             ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                     OBSERVABILITY & ORCHESTRATION                           │
│                                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │  CloudWatch  │  │   Prefect    │  │  PostgreSQL  │  │   Sentry     │  │
│  │  / Stackdriver│  │ (open-source)│  │   (Lineage)  │  │(error track) │  │
│  │              │  │              │  │              │  │              │  │
│  │ • Logs       │  │ • Workflow   │  │ • Audit logs │  │ • Exception  │  │
│  │ • Metrics    │  │   DAGs       │  │ • History    │  │   tracking   │  │
│  │ • Alarms     │  │ • Scheduling │  │   tables     │  │ • APM        │  │
│  │ • Dashboards │  │ • Retry logic│  │              │  │              │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Detailed Component Breakdown

### 1. DATA INGESTION: Airbyte (Open-Source)

**Why Airbyte:**
- ✅ 350+ pre-built connectors (all major marketing platforms)
- ✅ Open-source with Apache 2.0 license
- ✅ Active community (venture-backed company)
- ✅ Built-in features: scheduling, incremental sync, error handling
- ✅ Can self-host (Docker/Kubernetes) or use Airbyte Cloud

**Setup:**
```
Airbyte OSS on ECS Fargate / Cloud Run
  ↓
Writes to → PostgreSQL (raw schema) OR S3 (raw files)
  ↓
Triggers → SQS/Pub/Sub message for processing
```

**Scaling:**
- Run 10-20 connectors per Airbyte instance
- Each instance: 2-4 vCPU, 8-16 GB RAM
- Auto-scale based on number of active syncs
- For 100 sources: ~5-10 instances = $500-1000/month

**Alternatives Considered:**
- Fivetran (not open-source, expensive)
- Meltano (open-source, but less mature)
- Custom connectors (too much maintenance)

---

### 2. PROCESSING: Python Serverless Functions

**Technology:** AWS Lambda / GCP Cloud Functions / Azure Functions

**Function Architecture:**

#### Function 1: Validation
```python
# lambda_validation.py
from pydantic import BaseModel, validator
from great_expectations import DataContext

def handler(event, context):
    # Get raw data from event (SQS/Pub/Sub)
    raw_data = parse_event(event)

    # Schema validation with Pydantic
    validated = CampaignDataModel(**raw_data)

    # Data quality checks with Great Expectations
    ge_results = run_expectations(validated)

    if ge_results.success:
        # Write to PostgreSQL validated table
        save_to_db(validated)
        # Send to transformation queue
        send_to_queue('transformation', validated)
    else:
        # Log to error table & alert
        log_validation_error(ge_results)
```

#### Function 2: Transformation
```python
# lambda_transformation.py
import pandas as pd
from sqlalchemy import create_engine

def handler(event, context):
    data = parse_event(event)

    # Load from validated table
    df = load_data(data['campaign_id'])

    # Normalize metrics
    df['unified_ctr'] = df['clicks'] / df['impressions']
    df['unified_cpc'] = df['cost'] / df['clicks']
    df['roas'] = df['revenue'] / df['cost']

    # Aggregate by time period
    daily_agg = df.groupby('date').agg({
        'cost': 'sum',
        'revenue': 'sum',
        'clicks': 'sum'
    })

    # Write to metrics table
    save_metrics(daily_agg)
```

#### Function 3: Enrichment
```python
# lambda_enrichment.py
def handler(event, context):
    data = parse_event(event)

    # External API calls (cached)
    geo_data = get_geo_enrichment(data['location'])
    currency_rate = get_exchange_rate(data['currency'])

    # Join with customer data
    customer = get_customer_profile(data['customer_id'])

    # Write enriched data
    save_enriched(data, geo_data, currency_rate, customer)
```

**Scaling:**
- Serverless auto-scaling (0 to 1000s of concurrent executions)
- Cost: ~$0.20 per 1M requests + compute time
- For 50K API calls/day: ~$100-200/month

**Alternative:** Single FastAPI service with background workers (Celery) if you prefer one long-running service over serverless functions.

---

### 3. STORAGE: PostgreSQL + TimescaleDB + S3

**Primary Database: PostgreSQL 15 + TimescaleDB Extension**

**Why PostgreSQL + TimescaleDB:**
- ✅ Open-source, battle-tested
- ✅ TimescaleDB: purpose-built for time-series (marketing metrics)
- ✅ Automatic partitioning (hypertables)
- ✅ Continuous aggregations (pre-computed rollups)
- ✅ Native compression (90% reduction)
- ✅ SQL interface (familiar for team)
- ✅ JSONB for semi-structured data
- ✅ Full-text search built-in
- ✅ Excellent query performance with proper indexing

**Schema Design:**
```sql
-- Raw data from Airbyte
CREATE SCHEMA raw;
CREATE TABLE raw.facebook_ads (...);
CREATE TABLE raw.google_ads (...);

-- Normalized data
CREATE SCHEMA normalized;

-- TimescaleDB hypertable for metrics
CREATE TABLE normalized.campaign_metrics (
    time TIMESTAMPTZ NOT NULL,
    tenant_id UUID NOT NULL,
    campaign_id VARCHAR(255),
    source VARCHAR(50),
    impressions BIGINT,
    clicks BIGINT,
    cost NUMERIC(12,2),
    revenue NUMERIC(12,2),
    -- ... other metrics
    PRIMARY KEY (time, tenant_id, campaign_id)
);

-- Convert to hypertable (automatic partitioning)
SELECT create_hypertable('normalized.campaign_metrics', 'time');

-- Continuous aggregation (materialized view that auto-updates)
CREATE MATERIALIZED VIEW daily_campaign_summary
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 day', time) AS day,
    tenant_id,
    campaign_id,
    SUM(cost) as total_cost,
    SUM(revenue) as total_revenue,
    SUM(clicks) as total_clicks
FROM normalized.campaign_metrics
GROUP BY day, tenant_id, campaign_id;

-- Enable compression (after 7 days)
ALTER TABLE normalized.campaign_metrics
SET (timescaledb.compress,
     timescaledb.compress_segmentby = 'tenant_id,campaign_id');

SELECT add_compression_policy('normalized.campaign_metrics',
                              INTERVAL '7 days');

-- Features table (for ML)
CREATE TABLE features.campaign_features (
    feature_timestamp TIMESTAMPTZ,
    campaign_id VARCHAR(255),
    feature_vector JSONB,
    -- Store as JSON for flexibility
    PRIMARY KEY (feature_timestamp, campaign_id)
);

-- Audit/lineage
CREATE TABLE audit.data_lineage (
    id UUID PRIMARY KEY,
    source_table TEXT,
    dest_table TEXT,
    transformation TEXT,
    executed_at TIMESTAMPTZ,
    record_count BIGINT
);
```

**Hosted Options:**
- AWS RDS PostgreSQL with TimescaleDB (managed)
- Timescale Cloud (fully managed TimescaleDB)
- Azure Database for PostgreSQL
- GCP Cloud SQL with TimescaleDB

**Scaling:**
- Start: db.r6g.xlarge (4 vCPU, 32 GB) ~ $500/month
- Scale: Read replicas for analytics queries
- At 1TB: db.r6g.2xlarge ~ $1000/month
- Storage: $0.115/GB/month for 1TB = $115/month

**Cold Storage: S3/Cloud Storage**
- Archive raw data after 90 days
- Parquet format with Snappy compression
- S3 lifecycle: Standard (30d) → IA (60d) → Glacier (1yr+)
- Cost: ~$23/TB/month (Standard), $12.50/TB (IA), $4/TB (Glacier)

---

### 4. AI/ML: Cloud Provider ML Platform

**Technology:** AWS SageMaker / GCP Vertex AI / Azure ML

**Why Managed ML:**
- ✅ No infrastructure management
- ✅ Built-in model registry & versioning
- ✅ Auto-scaling inference endpoints
- ✅ Spot instances for training (70% cheaper)
- ✅ Integration with notebooks (Jupyter)

**ML Workflow:**

1. **Feature Engineering** (Python + SQL)
```python
# features.py
def create_features(campaign_id, lookback_days=30):
    query = f"""
    SELECT
        campaign_id,
        AVG(cost) as avg_cost,
        AVG(revenue) as avg_revenue,
        STDDEV(cost) as cost_volatility,
        AVG(clicks / NULLIF(impressions, 0)) as avg_ctr,
        -- Lag features
        LAG(revenue, 1) OVER (ORDER BY time) as prev_day_revenue,
        -- Rolling windows
        AVG(revenue) OVER (ORDER BY time ROWS BETWEEN 7 PRECEDING AND CURRENT ROW) as revenue_7d_avg
    FROM normalized.campaign_metrics
    WHERE campaign_id = '{campaign_id}'
      AND time >= NOW() - INTERVAL '{lookback_days} days'
    """
    return pd.read_sql(query, db_engine)
```

2. **Training** (Scheduled weekly)
```python
# train.py (runs on SageMaker)
import sagemaker
from sklearn.ensemble import RandomForestRegressor

# Load features from PostgreSQL
X_train, y_train = load_training_data()

# Train model
model = RandomForestRegressor(n_estimators=100)
model.fit(X_train, y_train)

# Register model
model_uri = save_model(model, 's3://models/budget-optimizer/v1.2')
register_model(model_uri, name='budget-optimizer', version='1.2')
```

3. **Inference** (Serverless endpoint)
```python
# predict.py (called from FastAPI)
import boto3

sagemaker_runtime = boto3.client('sagemaker-runtime')

def predict_optimal_budget(campaign_id):
    features = create_features(campaign_id)

    response = sagemaker_runtime.invoke_endpoint(
        EndpointName='budget-optimizer',
        Body=json.dumps(features),
        ContentType='application/json'
    )

    prediction = json.loads(response['Body'].read())
    return prediction['optimal_budget']
```

**Models to Implement:**

1. **Budget Optimizer:** Predict optimal budget allocation across campaigns
2. **Anomaly Detector:** Detect unusual campaign performance (isolation forest)
3. **Forecaster:** Predict next 7-day metrics (Prophet or LSTM)
4. **Attribution:** Multi-touch attribution model (Markov chain or Shapley value)

**Cost:**
- Training: $2-5 per training job (spot instances)
- Inference: Serverless endpoint ~$0.05/hour idle + $0.064/hour per instance under load
- Estimated: $500-1500/month depending on usage

---

### 5. API & SERVING: FastAPI + React

**Backend: FastAPI (Python)**

**Why FastAPI:**
- ✅ Open-source
- ✅ High performance (async support)
- ✅ Auto-generated OpenAPI docs
- ✅ Type hints with Pydantic
- ✅ Easy integration with PostgreSQL (SQLAlchemy)

**Example API:**
```python
# main.py
from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
import redis

app = FastAPI(title="Ask Bosco API")
cache = redis.Redis(host='redis.example.com')

@app.get("/campaigns")
async def list_campaigns(
    tenant_id: str,
    date_from: date,
    date_to: date,
    db: Session = Depends(get_db)
):
    # Check cache first
    cache_key = f"campaigns:{tenant_id}:{date_from}:{date_to}"
    cached = cache.get(cache_key)
    if cached:
        return json.loads(cached)

    # Query TimescaleDB
    query = """
    SELECT * FROM daily_campaign_summary
    WHERE tenant_id = :tenant_id
      AND day BETWEEN :date_from AND :date_to
    ORDER BY day DESC
    """
    results = db.execute(query, {...}).fetchall()

    # Cache for 5 minutes
    cache.setex(cache_key, 300, json.dumps(results))

    return results

@app.get("/insights/{campaign_id}")
async def get_insights(campaign_id: str):
    # Call ML model
    prediction = predict_optimal_budget(campaign_id)
    anomalies = detect_anomalies(campaign_id)

    return {
        "campaign_id": campaign_id,
        "recommended_budget": prediction,
        "anomalies": anomalies
    }
```

**Deployment:**
- ECS Fargate / Cloud Run / App Service
- Container: Python 3.11 + FastAPI + dependencies
- Auto-scaling: 2-10 instances based on CPU/request count
- Cost: ~$100-300/month

**Frontend: React**

- Static site hosted on S3 + CloudFront / Netlify / Vercel
- Charts: Recharts or Chart.js
- State management: React Query (for API caching)
- Real-time: WebSocket connection to FastAPI or polling
- Cost: ~$20-50/month (mostly CDN)

---

### 6. OBSERVABILITY: Native Cloud Tools + Sentry

**Logging & Metrics: CloudWatch / Cloud Logging**
- All Lambda logs automatically collected
- Custom metrics: Lambda duration, errors, DB query time
- Alarms: Lambda errors > 5%, DB connections > 80%, API latency p99 > 500ms
- Cost: ~$50-100/month

**Error Tracking: Sentry (Open-Source)**
- Capture exceptions from FastAPI and React
- Alerting to Slack/email
- Cost: Free tier (5K errors/month) or $26/month

**Orchestration: Prefect (Open-Source)**

**Why Prefect:**
- ✅ Open-source (Apache 2.0)
- ✅ Modern, Python-native
- ✅ Hybrid execution (cloud + on-prem)
- ✅ Better UX than Airflow
- ✅ Native async support

```python
# flows/daily_ingestion.py
from prefect import flow, task

@task(retries=3, retry_delay_seconds=60)
def trigger_airbyte_sync(source_id):
    # Trigger Airbyte connector via API
    airbyte_client.trigger_sync(source_id)

@task
def validate_data(table_name):
    # Run Great Expectations suite
    results = ge_context.run_checkpoint(f"{table_name}_checkpoint")
    if not results.success:
        raise ValueError(f"Validation failed for {table_name}")

@task
def retrain_model():
    # Trigger SageMaker training job
    sagemaker.create_training_job(...)

@flow(name="daily-pipeline")
def daily_pipeline():
    # Ingest from all sources
    for source in sources:
        trigger_airbyte_sync(source)

    # Validate
    validate_data("campaign_metrics")

    # Weekly model retraining
    if datetime.today().weekday() == 0:  # Monday
        retrain_model()
```

**Deployment:**
- Self-host Prefect server (small EC2/Compute Engine instance)
- Or use Prefect Cloud (free tier: 20K task runs/month)
- Cost: $0-50/month

**Data Lineage: PostgreSQL Audit Tables**
- Simple approach: audit tables in PostgreSQL
- Log every transformation with source → destination mapping
- Query lineage with recursive CTEs

```sql
-- Example lineage query
WITH RECURSIVE lineage AS (
    SELECT * FROM audit.data_lineage WHERE dest_table = 'campaign_metrics'
    UNION ALL
    SELECT dl.* FROM audit.data_lineage dl
    JOIN lineage l ON dl.dest_table = l.source_table
)
SELECT * FROM lineage;
```

---

## Complete Tech Stack Summary

| Function | Technology | Type | Cost/Month |
|----------|-----------|------|------------|
| **Ingestion** | Airbyte OSS | Open-source (self-hosted) | $500 |
| **Queue** | AWS SQS / Pub/Sub | Managed | $50 |
| **Processing** | Lambda / Cloud Functions | Serverless | $200 |
| **Database** | PostgreSQL + TimescaleDB | Managed (RDS/Cloud SQL) | $650 |
| **Cache** | Redis | Managed (ElastiCache) | $100 |
| **Storage** | S3 / Cloud Storage | Managed | $50 |
| **ML** | SageMaker / Vertex AI | Managed | $1000 |
| **API** | FastAPI on ECS/Cloud Run | Containerized | $200 |
| **Frontend** | React on S3 + CloudFront | Static hosting | $30 |
| **Orchestration** | Prefect OSS | Open-source (self-hosted) | $50 |
| **Monitoring** | CloudWatch / Cloud Logging | Managed | $100 |
| **Error Tracking** | Sentry | SaaS (free tier) | $0 |
| **TOTAL** | | | **~$2,930/month** |

**At 50 clients:** $59/client/month → Healthy margins

---

## Requirements Mapping

| Requirement | Solution | How It's Addressed |
|-------------|----------|-------------------|
| **100+ diverse sources** | Airbyte (350+ connectors) | Pre-built connectors; open-source community |
| **50K+ API calls/day** | Serverless Lambda + SQS | Auto-scales to demand; queue buffers spikes |
| **1TB+ monthly data** | TimescaleDB compression + S3 | 90% compression; archive to S3 after 90 days |
| **Unified metrics** | Transformation functions | SQL + Python for metric normalization |
| **AI/ML support** | SageMaker/Vertex AI | Managed training & inference; model registry |
| **Real-time dashboards** | TimescaleDB continuous aggs + Redis cache | Pre-computed rollups; sub-second queries |
| **Data quality** | Great Expectations + validation functions | Automated checks; alerting on failures |
| **99.9% availability** | Multi-AZ managed services | RDS Multi-AZ; Lambda redundancy; CloudFront CDN |
| **Cost efficiency** | Serverless + managed services | Pay-per-use; no idle costs; auto-scaling |
| **Audit & lineage** | PostgreSQL audit tables | Track all transformations; query with SQL |

---

## Data Flow Example

**End-to-End: Google Ads Data → Dashboard**

1. **Ingestion (Every 6 hours)**
   - Airbyte connector polls Google Ads API
   - Writes raw JSON to `raw.google_ads` table in PostgreSQL
   - Sends message to SQS: `{"source": "google_ads", "campaign_ids": [...]}`

2. **Validation (Triggered by SQS)**
   - Lambda function reads message
   - Loads data from `raw.google_ads`
   - Validates with Pydantic schema
   - Runs Great Expectations suite (nulls, ranges, uniqueness)
   - If valid: writes to `normalized.campaign_metrics`
   - If invalid: writes to `errors.validation_failures` + alerts Slack

3. **Transformation (Triggered after validation)**
   - Lambda function calculates unified metrics
   - SQL: `unified_ctr = clicks / impressions`
   - Inserts into TimescaleDB hypertable
   - Continuous aggregation auto-updates `daily_campaign_summary`

4. **Enrichment (Optional, triggered separately)**
   - Lambda joins with customer table
   - Calls external API for currency conversion
   - Updates `normalized.campaign_metrics` with enriched fields

5. **ML Inference (Nightly batch job)**
   - Prefect flow triggers SageMaker batch transform
   - Reads features from PostgreSQL
   - Scores all campaigns for anomalies
   - Writes predictions to `ml.predictions` table

6. **Serving (Real-time)**
   - User opens dashboard (React app from CloudFront)
   - React calls FastAPI: `GET /campaigns?date_from=2025-10-01`
   - FastAPI checks Redis cache → miss
   - Queries TimescaleDB continuous aggregate (fast!)
   - Returns JSON, caches in Redis (TTL 5 min)
   - React renders charts with Recharts

7. **Real-time Update (Optional)**
   - WebSocket connection from React to FastAPI
   - When new data arrives, FastAPI publishes to Redis Pub/Sub
   - React receives message and updates dashboard without refresh

**Total Latency:** Ingestion → Dashboard: ~15 minutes (configurable)

---

## Alternative Architectures

### Alternative 1: Single Monolith (Even Simpler)

**Stack:** Just PostgreSQL + FastAPI + React

**Changes:**
- Remove: Airbyte (write custom connectors), SQS (use PostgreSQL queues), Lambda (background workers in FastAPI)
- All processing in FastAPI with Celery workers

**Pros:**
- ✅ Simplest possible architecture
- ✅ Single codebase, easier debugging
- ✅ Lowest cost (~$1000/month)

**Cons:**
- ❌ Harder to scale processing independently
- ❌ Custom connector maintenance burden
- ❌ Single point of failure (mitigated with replicas)

**When to choose:** Very early stage (< 10 sources, < 10 clients)

---

### Alternative 2: All-Serverless (No Long-Running Services)

**Stack:** Lambda + DynamoDB + S3 + API Gateway

**Changes:**
- Remove: PostgreSQL → DynamoDB + S3 (Athena for queries)
- Remove: FastAPI containers → API Gateway + Lambda
- Remove: Prefect → Step Functions

**Pros:**
- ✅ True zero-ops (fully serverless)
- ✅ Infinite scaling
- ✅ Pay only for requests

**Cons:**
- ❌ DynamoDB not great for complex analytics queries
- ❌ Athena has higher latency (seconds vs milliseconds)
- ❌ More expensive at high query volume

**When to choose:** Extreme unpredictability in traffic; team wants zero infrastructure

---

### Alternative 3: Data Lakehouse (BigQuery/Snowflake)

**Stack:** Airbyte → BigQuery/Snowflake → dbt → FastAPI

**Changes:**
- Replace PostgreSQL with BigQuery or Snowflake
- Use dbt for all transformations (SQL only)

**Pros:**
- ✅ Best-in-class query performance
- ✅ Automatic scaling
- ✅ Time travel and versioning built-in
- ✅ dbt has great ecosystem

**Cons:**
- ❌ Higher costs at scale ($3K-5K/month for 1TB queries)
- ❌ Vendor lock-in
- ❌ Not open-source

**When to choose:** Large team already using BigQuery/Snowflake; budget allows; want best query performance

---

## Recommended: Proposed Simplified Stack

For Ask Bosco, I recommend the **simplified serverless stack** (main design above):

**Why:**
1. ✅ **Minimal tech stack:** 5 core technologies (Airbyte, PostgreSQL, Python, Redis, React)
2. ✅ **Open-source first:** Airbyte, PostgreSQL, TimescaleDB, Prefect, Sentry all open-source
3. ✅ **Serverless where possible:** Lambda for processing, SageMaker for ML
4. ✅ **Managed services:** No infrastructure management (RDS, ElastiCache, S3)
5. ✅ **Cost-efficient:** ~$3K/month at initial scale vs $8K in original design
6. ✅ **Proven at scale:** PostgreSQL handles multi-TB deployments, TimescaleDB built for time-series
7. ✅ **Easy to hire for:** Python/PostgreSQL/React are mainstream skills

**Growth Path:**
- 0-10 clients: Single PostgreSQL instance
- 10-50 clients: Add read replicas + Redis cache
- 50-200 clients: Partition by tenant, add more Lambda concurrency
- 200+ clients: Consider splitting into separate DB instances per client tier

---

## Implementation Roadmap

### Phase 1: MVP (Weeks 1-4)
- Deploy Airbyte with 5 key sources (Google Ads, Facebook, GA4, Shopify, TikTok)
- Set up PostgreSQL with TimescaleDB on RDS
- Build validation + transformation Lambda functions
- Create basic FastAPI with 3 endpoints
- Deploy simple React dashboard
- **Goal:** 5 pilot customers

### Phase 2: Production (Weeks 5-8)
- Add 20 more Airbyte connectors
- Implement Great Expectations data quality
- Deploy Prefect for orchestration
- Add Redis caching
- Build out full dashboard with charts
- Implement authentication (JWT)
- **Goal:** 15 paying customers

### Phase 3: Intelligence (Weeks 9-12)
- Train first ML model (anomaly detection)
- Deploy SageMaker inference endpoint
- Add ML insights to API
- Build alerting system (email/Slack)
- Implement data lineage tracking
- **Goal:** 30 customers with ML features

### Phase 4: Scale (Months 4-6)
- Add remaining connectors to reach 100+
- Optimize TimescaleDB (partitioning, compression)
- Implement multi-tenancy isolation
- Build customer-facing analytics API
- Add more ML models (forecasting, attribution)
- **Goal:** 50+ customers, proven scalability

---

## Cost Breakdown at Different Scales

### Startup (10 clients, 5K API calls/day, 100 GB/month)
| Component | Cost |
|-----------|------|
| Airbyte (1 instance) | $100 |
| RDS db.t4g.large | $150 |
| Lambda (low volume) | $20 |
| S3 | $5 |
| SageMaker (minimal) | $200 |
| Other (Redis, monitoring, etc.) | $100 |
| **Total** | **$575/month** |
| **Per client** | **$58/month** |

### Growth (50 clients, 25K API calls/day, 500 GB/month)
| Component | Cost |
|-----------|------|
| Airbyte (3 instances) | $300 |
| RDS db.r6g.large | $400 |
| Lambda | $100 |
| S3 | $20 |
| SageMaker | $600 |
| Redis | $100 |
| Other | $150 |
| **Total** | **$1,670/month** |
| **Per client** | **$33/month** |

### Scale (200 clients, 100K API calls/day, 2 TB/month)
| Component | Cost |
|-----------|------|
| Airbyte (10 instances) | $800 |
| RDS db.r6g.2xlarge + replicas | $2,000 |
| Lambda | $500 |
| S3 | $100 |
| SageMaker | $2,500 |
| Redis | $300 |
| Other | $500 |
| **Total** | **$6,700/month** |
| **Per client** | **$34/month** |

**Note:** Costs improve per-client with scale due to shared infrastructure.

---

## Conclusion

This simplified architecture provides:

1. **Minimal Tech Stack:** 5 core technologies + managed cloud services
2. **Open-Source First:** All core components are open-source
3. **Serverless Where Possible:** Lambda for processing, auto-scaling everywhere
4. **Cost-Efficient:** Start at $575/month, scale to $6.7K at 200 clients
5. **Low Operational Overhead:** Managed services eliminate infrastructure management
6. **Proven Technologies:** PostgreSQL and Python are battle-tested at scale
7. **Growth Path:** Clear scaling strategy from 10 → 1000+ clients

The architecture meets all requirements while prioritizing simplicity and maintainability.
