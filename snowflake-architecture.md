# Ask Bosco Marketing Analytics Platform - Snowflake Architecture

## Executive Summary

This design uses a **columnar warehouse-first stack** optimized for heavy aggregation workloads. Core stack: **Airbyte → Snowflake → dbt → FastAPI → React**.

**Key Decision:** Using **Snowflake** as the primary data warehouse due to:
- ✅ Columnar storage optimized for aggregations (10-100x faster than row-based databases)
- ✅ Automatic query optimization and result caching
- ✅ Separation of storage and compute (scale independently)
- ✅ Built-in time travel and zero-copy cloning
- ✅ Pay-per-use with auto-suspend (no idle costs)
- ✅ Native support for semi-structured data (JSON, VARIANT)
- ✅ Handles petabyte-scale data

**Philosophy:** Minimize technology stack, use managed services, optimize for analytical queries.

---

## Technology Stack (5 Core Technologies)

1. **Airbyte** (open-source) - Data ingestion from 350+ sources
2. **Snowflake** (managed, columnar) - Primary data warehouse
3. **dbt** (open-source) - SQL-based transformations & data quality
4. **Python + FastAPI** (open-source) - Backend API
5. **React** (open-source) - Frontend dashboards

**Supporting Services:**
- Redis (managed) - Query result caching
- S3 / Cloud Storage - Snowflake external stage (landing zone)
- SageMaker / Snowflake ML - Machine learning
- Prefect (open-source) - Workflow orchestration

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          DATA INGESTION                                     │
│                                                                             │
│  100+ Marketing Data Sources:                                              │
│  Google Ads, Facebook Ads, TikTok, Shopify, GA4, LinkedIn, etc.            │
│                                 ↓                                           │
│  ┌────────────────────────────────────────────────────────────┐            │
│  │                  AIRBYTE (Open-Source)                      │            │
│  │                                                             │            │
│  │  • 350+ pre-built connectors                               │            │
│  │  • Incremental sync (CDC where available)                  │            │
│  │  • Built-in retry + error handling                         │            │
│  │  • Direct Snowflake destination                            │            │
│  │  • Self-hosted on Docker/K8s                               │            │
│  └────────────────────────┬───────────────────────────────────┘            │
└────────────────────────────┼────────────────────────────────────────────────┘
                             ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    DATA WAREHOUSE: SNOWFLAKE                                │
│                                                                             │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                         DATABASE: PROD                               │  │
│  │                                                                      │  │
│  │  SCHEMA: RAW  (Airbyte writes here directly)                        │  │
│  │  ├── raw.google_ads_campaigns                                       │  │
│  │  ├── raw.facebook_ads_insights                                      │  │
│  │  ├── raw.shopify_orders                                             │  │
│  │  └── ...100+ tables                                                 │  │
│  │                                                                      │  │
│  │  • Columns: VARIANT (JSON), _airbyte_emitted_at, _airbyte_data     │  │
│  │  • Clustered by: date, tenant_id                                    │  │
│  │  • Retention: 90 days (time travel)                                 │  │
│  │                                                                      │  │
│  ├──────────────────────────────────────────────────────────────────────┤  │
│  │                                                                      │  │
│  │  SCHEMA: STAGING  (dbt models - validated & typed)                  │  │
│  │  ├── stg_google_ads__campaigns                                      │  │
│  │  ├── stg_facebook_ads__campaigns                                    │  │
│  │  ├── stg_shopify__orders                                            │  │
│  │  └── ...                                                            │  │
│  │                                                                      │  │
│  │  • JSON flattened to columns                                        │  │
│  │  • Data types enforced                                              │  │
│  │  • dbt tests: unique, not_null, relationships                       │  │
│  │  • Incremental models (only process new data)                       │  │
│  │                                                                      │  │
│  ├──────────────────────────────────────────────────────────────────────┤  │
│  │                                                                      │  │
│  │  SCHEMA: ANALYTICS  (dimensional model)                             │  │
│  │  ├── fct_campaign_performance  (fact table)                         │  │
│  │  │   • date, campaign_id, impressions, clicks, cost, revenue        │  │
│  │  │   • Partitioned by date                                          │  │
│  │  │   • Clustered by tenant_id, campaign_id                          │  │
│  │  ├── dim_campaigns                                                  │  │
│  │  ├── dim_ad_platforms                                               │  │
│  │  └── dim_customers                                                  │  │
│  │                                                                      │  │
│  │  • Star schema for efficient joins                                  │  │
│  │  • SCD Type 2 for slowly changing dimensions                        │  │
│  │                                                                      │  │
│  ├──────────────────────────────────────────────────────────────────────┤  │
│  │                                                                      │  │
│  │  SCHEMA: METRICS  (pre-aggregated for dashboards)                   │  │
│  │  ├── daily_campaign_summary  (materialized)                         │  │
│  │  │   SELECT date, campaign_id, platform,                            │  │
│  │  │          SUM(cost), SUM(revenue), SUM(clicks),                   │  │
│  │  │          SUM(revenue)/SUM(cost) as ROAS                          │  │
│  │  │   FROM fct_campaign_performance                                  │  │
│  │  │   GROUP BY 1,2,3                                                 │  │
│  │  │                                                                  │  │
│  │  ├── weekly_performance_rollup                                      │  │
│  │  ├── monthly_attribution                                            │  │
│  │  └── real_time_dashboard_cache  (near real-time)                   │  │
│  │                                                                      │  │
│  │  • Materialized views (auto-refreshed)                              │  │
│  │  • Dynamic tables (incremental refresh)                             │  │
│  │                                                                      │  │
│  ├──────────────────────────────────────────────────────────────────────┤  │
│  │                                                                      │  │
│  │  SCHEMA: ML  (features & predictions)                               │  │
│  │  ├── ml.campaign_features                                           │  │
│  │  │   • Feature engineering via SQL                                  │  │
│  │  │   • Lag features, rolling windows, ratios                        │  │
│  │  ├── ml.anomaly_scores                                              │  │
│  │  ├── ml.forecast_predictions                                        │  │
│  │  └── ml.budget_recommendations                                      │  │
│  │                                                                      │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  SNOWFLAKE FEATURES LEVERAGED:                                              │
│  • Result Cache: Identical queries return instantly (24hr TTL)              │
│  • Automatic Clustering: No manual index management                         │
│  • Zero-Copy Clone: dev/staging from prod (no storage cost)                 │
│  • Time Travel: Query historical data, rollback mistakes                    │
│  • Auto-Suspend: Warehouse stops after 5 min idle                           │
│  • Auto-Resume: Starts on first query                                       │
│  • Elastic Scaling: Add clusters for concurrency                            │
│                                                                             │
│  VIRTUAL WAREHOUSES (compute):                                              │
│  • INGESTION_WH (XS): Airbyte loads        → $2/hr, auto-suspend            │
│  • TRANSFORMATION_WH (M): dbt runs          → $4/hr, auto-suspend            │
│  • ANALYTICS_WH (M): Dashboard queries      → $4/hr, auto-suspend            │
│  • ML_WH (L): Feature engineering/training  → $8/hr, auto-suspend            │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                             ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                      TRANSFORMATION: DBT                                    │
│                                                                             │
│  ┌──────────────────────────────────────────────────────────────┐          │
│  │                   dbt Core (Open-Source)                      │          │
│  │                                                               │          │
│  │  models/                                                      │          │
│  │  ├── staging/                                                 │          │
│  │  │   ├── _staging.yml  (tests, docs)                         │          │
│  │  │   ├── stg_google_ads__campaigns.sql                       │          │
│  │  │   └── stg_facebook_ads__campaigns.sql                     │          │
│  │  ├── intermediate/                                            │          │
│  │  │   └── int_unified_campaigns.sql                           │          │
│  │  └── marts/                                                   │          │
│  │      ├── marketing/                                           │          │
│  │      │   ├── fct_campaign_performance.sql                    │          │
│  │      │   ├── dim_campaigns.sql                               │          │
│  │      │   └── daily_campaign_summary.sql                      │          │
│  │      └── ml/                                                  │          │
│  │          └── campaign_features.sql                           │          │
│  │                                                               │          │
│  │  tests/                                                       │          │
│  │  ├── assert_positive_revenue.sql  (custom test)              │          │
│  │  └── assert_roas_reasonable.sql                              │          │
│  │                                                               │          │
│  │  CAPABILITIES:                                                │          │
│  │  • SQL-only transformations (declarative)                     │          │
│  │  • Automatic lineage DAG                                      │          │
│  │  • Incremental models (only process new rows)                 │          │
│  │  • Built-in tests (unique, not_null, relationships)           │          │
│  │  • Data quality framework                                     │          │
│  │  • Auto-generated documentation                               │          │
│  │  • Jinja templating for DRY SQL                               │          │
│  │  • Packages (dbt_utils, dbt_expectations)                     │          │
│  │                                                               │          │
│  │  EXECUTION:                                                   │          │
│  │  • Orchestrated by Prefect (scheduled runs)                   │          │
│  │  • On Airbyte sync complete                                   │          │
│  │  • Hourly incremental, daily full refresh                     │          │
│  └──────────────────────────────────────────────────────────────┘          │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                             ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          ML LAYER                                           │
│                                                                             │
│  OPTION 1: Snowflake ML (Recommended - Stay in Warehouse)                  │
│  ┌──────────────────────────────────────────────────────────────┐          │
│  │  Snowpark Python / Snowflake ML Functions                    │          │
│  │                                                               │          │
│  │  • Write Python UDFs in Snowflake (no data export)           │          │
│  │  • Built-in ML functions:                                    │          │
│  │    - FORECAST() for time-series                              │          │
│  │    - ANOMALY_DETECTION()                                     │          │
│  │    - CLASSIFICATION() / REGRESSION()                         │          │
│  │  • Scikit-learn, XGBoost run natively                        │          │
│  │  • Feature store = Snowflake tables                          │          │
│  │  • Model registry in Snowflake                               │          │
│  └──────────────────────────────────────────────────────────────┘          │
│                                                                             │
│  OPTION 2: External ML Platform (If advanced features needed)              │
│  ┌──────────────────────────────────────────────────────────────┐          │
│  │  AWS SageMaker / GCP Vertex AI                               │          │
│  │                                                               │          │
│  │  • Export features from Snowflake (Snowpark)                 │          │
│  │  • Train models externally                                   │          │
│  │  • Deploy inference endpoints                                │          │
│  │  • Write predictions back to Snowflake                       │          │
│  └──────────────────────────────────────────────────────────────┘          │
│                                                                             │
│  MODELS:                                                                    │
│  1. Anomaly Detection: Detect unusual campaign performance                 │
│  2. Forecasting: Predict next 7/30 day metrics                             │
│  3. Budget Optimizer: Optimal spend allocation across channels             │
│  4. Attribution: Multi-touch attribution modeling                          │
│  5. Lifetime Value: Customer LTV prediction                                │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                             ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          API & SERVING LAYER                                │
│                                                                             │
│  ┌────────────────────────────────────────────────────────────┐            │
│  │              FastAPI (Python Backend)                       │            │
│  │              Deployed on ECS / Cloud Run / App Service      │            │
│  │                                                             │            │
│  │  from snowflake.connector import connect                   │            │
│  │  import redis                                               │            │
│  │                                                             │            │
│  │  @app.get("/campaigns")                                    │            │
│  │  async def get_campaigns(tenant_id, date_from, date_to):   │            │
│  │      # Check Redis cache first                             │            │
│  │      cached = redis_client.get(cache_key)                  │            │
│  │      if cached: return cached                              │            │
│  │                                                             │            │
│  │      # Query Snowflake (leverages result cache)            │            │
│  │      query = """                                           │            │
│  │      SELECT * FROM metrics.daily_campaign_summary          │            │
│  │      WHERE tenant_id = ? AND date BETWEEN ? AND ?          │            │
│  │      """                                                    │            │
│  │      results = snowflake_cursor.execute(query).fetchall()  │            │
│  │                                                             │            │
│  │      # Cache in Redis (5 min TTL)                          │            │
│  │      redis_client.setex(cache_key, 300, results)           │            │
│  │      return results                                        │            │
│  │                                                             │            │
│  │  ENDPOINTS:                                                │            │
│  │  • GET /campaigns - List with filters                      │            │
│  │  • GET /metrics/aggregate - Custom aggregations            │            │
│  │  • GET /insights/{campaign_id} - ML predictions            │            │
│  │  • GET /attribution - Multi-touch attribution              │            │
│  │  • POST /alerts - Configure anomaly alerts                 │            │
│  │                                                             │            │
│  │  FEATURES:                                                 │            │
│  │  • Snowflake connector pooling                             │            │
│  │  • Two-tier caching (Snowflake + Redis)                    │            │
│  │  • JWT authentication                                      │            │
│  │  • Rate limiting per tenant                                │            │
│  │  • OpenAPI docs auto-generated                             │            │
│  └────────────────────────────────────────────────────────────┘            │
│                                                                             │
│  ┌────────────────────────────────────────────────────────────┐            │
│  │                   Redis Cache Layer                         │            │
│  │                                                             │            │
│  │  • Application-level caching (5-15 min TTL)                │            │
│  │  • Reduces Snowflake compute costs                         │            │
│  │  • Session storage                                         │            │
│  │  • Rate limiting counters                                  │            │
│  └────────────────────────────────────────────────────────────┘            │
│                                                                             │
│  ┌────────────────────────────────────────────────────────────┐            │
│  │              React Frontend (Static)                        │            │
│  │              S3 + CloudFront / Vercel / Netlify             │            │
│  │                                                             │            │
│  │  • Dashboard with Recharts / Chart.js                      │            │
│  │  • React Query for API caching                             │            │
│  │  • Real-time: polling (every 30s) or WebSocket             │            │
│  │  • Responsive design                                       │            │
│  └────────────────────────────────────────────────────────────┘            │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                             ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                  OBSERVABILITY & ORCHESTRATION                              │
│                                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │   Prefect    │  │  Snowflake   │  │   Sentry     │  │ CloudWatch   │  │
│  │(open-source) │  │  Query Tags  │  │(error track) │  │   (logs)     │  │
│  │              │  │  & Lineage   │  │              │  │              │  │
│  │ • Workflows  │  │              │  │ • FastAPI    │  │ • Lambda     │  │
│  │ • Scheduling │  │ • QUERY_TAG  │  │   errors     │  │ • Airbyte    │  │
│  │ • Retry      │  │ • QUERY_     │  │ • React      │  │ • Metrics    │  │
│  │   logic      │  │   HISTORY    │  │   errors     │  │ • Alarms     │  │
│  │ • Airbyte    │  │ • dbt logs   │  │              │  │              │  │
│  │   triggers   │  │   lineage    │  │              │  │              │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘  │
│                                                                             │
│  DATA QUALITY:                                                              │
│  • dbt tests (built-in + custom)                                            │
│  • Snowflake data quality functions                                         │
│  • Great Expectations (optional, for complex checks)                        │
│  • Anomaly detection on metric values                                       │
│                                                                             │
│  LINEAGE & AUDIT:                                                           │
│  • dbt automatic lineage DAG                                                │
│  • Snowflake QUERY_HISTORY table                                            │
│  • Snowflake ACCESS_HISTORY (who queried what)                              │
│  • Query tags for attribution                                               │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Why Snowflake for Heavy Aggregations?

### Columnar Storage Advantage

**Traditional Row-Based (PostgreSQL):**
```
Row 1: [date, campaign_id, impressions, clicks, cost, revenue, ...]
Row 2: [date, campaign_id, impressions, clicks, cost, revenue, ...]
...
```
- To SUM(cost), must read entire rows
- Poor cache utilization
- Slow for aggregations

**Columnar (Snowflake):**
```
cost column: [100.50, 250.00, 75.25, ...]
revenue column: [500.00, 1200.00, 300.00, ...]
```
- To SUM(cost), read only cost column
- 10-100x faster for aggregations
- Excellent compression (similar values together)
- Vectorized execution

### Real-World Performance Comparison

**Query:** "Sum of cost and revenue by campaign for last 30 days across 100 campaigns"

| Database | Query Time | Cost/Query |
|----------|-----------|------------|
| PostgreSQL (row-based) | 5-15 seconds | $0.001 |
| TimescaleDB (row-based with optimization) | 2-5 seconds | $0.001 |
| Snowflake (columnar) | 0.5-2 seconds | $0.01 |
| BigQuery (columnar) | 0.5-2 seconds | $0.02 |

For a marketing analytics platform with **thousands of aggregation queries per day**, columnar wins on:
- ✅ User experience (sub-second dashboards)
- ✅ Cost at scale (result caching reduces compute)
- ✅ Maintainability (no index tuning needed)

---

## Data Flow Example

**End-to-End: Google Ads → Dashboard (15 min latency)**

1. **Ingestion (every hour)**
   ```
   Airbyte → Snowflake RAW.google_ads_campaigns
   • Incremental sync (only new data)
   • VARIANT column for JSON
   • Takes 2-5 minutes
   ```

2. **Transformation (triggered after ingestion)**
   ```
   dbt run --select staging.stg_google_ads*
   • Flatten JSON to columns
   • Data type conversion
   • Run tests (not_null, unique)
   • Takes 1-2 minutes

   dbt run --select marts.fct_campaign_performance
   • Join staging tables
   • Calculate unified metrics
   • Takes 2-3 minutes

   dbt run --select metrics.daily_campaign_summary
   • Pre-aggregate for dashboards
   • Materialized view refresh
   • Takes 1-2 minutes
   ```

3. **Serving (real-time)**
   ```
   User opens dashboard → FastAPI
   • Check Redis cache → HIT (instant)
   • If MISS: Query Snowflake
   • Snowflake result cache → HIT (< 1 sec)
   • If MISS: Execute query (1-3 sec)
   • Cache in Redis for 5 min
   ```

**Total Pipeline Latency:** 6-12 minutes from source to dashboard

---

## Requirements Mapping

| Requirement | Solution | How Snowflake Addresses It |
|-------------|----------|---------------------------|
| **100+ diverse sources** | Airbyte → Snowflake | Native Snowflake destination; VARIANT handles any JSON |
| **50K+ API calls/day** | FastAPI + Redis + Snowflake | Two-tier cache; Snowflake result cache; sub-second queries |
| **1TB+ monthly data** | Snowflake storage | $23/TB/month storage; columnar compression (3-5x); time travel included |
| **Heavy aggregations** | Columnar storage | 10-100x faster than row-based; automatic query optimization |
| **Unified metrics** | dbt transformations | SQL-based, testable, version-controlled transformations |
| **AI/ML support** | Snowflake ML / SageMaker | Snowpark Python for in-warehouse ML; or export to external platform |
| **Real-time dashboards** | Materialized views + cache | Pre-aggregated metrics; result cache; < 2 sec queries |
| **Data quality** | dbt tests + Snowflake functions | 100+ built-in tests; custom SQL tests; anomaly detection |
| **99.9% availability** | Snowflake SLA | Multi-AZ replication; automatic failover; 99.99% SLA |
| **Cost efficiency** | Auto-suspend + result cache | Pay only for compute used; auto-suspend after 5 min idle; result cache reduces compute |
| **Audit & lineage** | dbt + Snowflake metadata | Automatic lineage DAG; QUERY_HISTORY; ACCESS_HISTORY; time travel |

---

## Cost Breakdown

### Snowflake Costs (at 50 clients, 1TB data, 50K queries/day)

**Storage:**
- 1TB active data: $23/month (Snowflake storage)
- 2TB historical (time travel 90d): $46/month
- **Total Storage: $69/month**

**Compute (Virtual Warehouses):**

| Warehouse | Size | $/hour | Hours/day | Days | Monthly Cost |
|-----------|------|--------|-----------|------|--------------|
| INGESTION_WH | XS | $2 | 2 hrs | 30 | $120 |
| TRANSFORMATION_WH | M | $4 | 1 hr | 30 | $120 |
| ANALYTICS_WH | M | $4 | 6 hrs* | 30 | $720 |
| ML_WH | L | $8 | 2 hrs | 4 | $64 |

*Auto-suspends between queries; result cache reduces actual compute

**Total Compute: ~$1,024/month**

**Snowflake Total: ~$1,100/month**

**Key Optimizations:**
- Result cache: Identical queries free (24hr TTL) → saves 40-60% compute
- Auto-suspend: No idle costs
- Warehouse scaling: Add clusters only during peak times

### Complete Stack Costs

| Component | Technology | Monthly Cost |
|-----------|-----------|--------------|
| **Ingestion** | Airbyte (3 instances on ECS) | $300 |
| **Warehouse** | Snowflake (storage + compute) | $1,100 |
| **Transformation** | dbt Core (runs on Prefect) | $0 (open-source) |
| **API** | FastAPI on ECS (2 containers) | $200 |
| **Cache** | Redis (ElastiCache) | $100 |
| **Frontend** | React on S3 + CloudFront | $30 |
| **ML** | Snowflake ML (included) or SageMaker | $500 |
| **Orchestration** | Prefect (self-hosted) | $50 |
| **Monitoring** | CloudWatch + Sentry | $100 |
| **TOTAL** | | **$2,380/month** |

**Per client (50 clients): $48/month**

**Scaling costs:**
- 100 clients, 2TB: ~$3,500/month ($35/client)
- 200 clients, 5TB: ~$6,000/month ($30/client)

Costs improve per-client due to:
- Shared Snowflake compute
- Result cache hit rate increases
- Fixed costs (Airbyte, API) amortized

---

## Alternative Architectures

### Alternative 1: PostgreSQL + TimescaleDB (Row-Based)

**Changes:**
- Replace Snowflake with PostgreSQL + TimescaleDB
- Use continuous aggregations instead of materialized views

**Pros:**
- ✅ Lower storage costs ($15/TB vs $23/TB)
- ✅ Open-source
- ✅ No vendor lock-in

**Cons:**
- ❌ Slower aggregation queries (5-10x)
- ❌ Manual partitioning and indexing required
- ❌ Doesn't scale as easily beyond 5-10TB
- ❌ No automatic query optimization
- ❌ More operational overhead

**When to choose:** Very cost-sensitive; < 1TB data; team has strong PostgreSQL expertise

---

### Alternative 2: BigQuery (Google Cloud)

**Changes:**
- Replace Snowflake with BigQuery
- Otherwise same architecture

**Pros:**
- ✅ Similar columnar performance
- ✅ Serverless (no warehouse management)
- ✅ Pay-per-query instead of per-hour

**Cons:**
- ❌ More expensive at high query volume ($5/TB scanned)
- ❌ No result cache (must use Redis heavily)
- ❌ No time travel (limited to 7 days)
- ❌ Steeper learning curve for SQL dialect

**When to choose:** Already on GCP; prefer pay-per-query; lower query volume

---

### Alternative 3: ClickHouse (Open-Source Columnar)

**Changes:**
- Replace Snowflake with ClickHouse
- Self-host or use ClickHouse Cloud

**Pros:**
- ✅ Open-source
- ✅ Fastest query performance (benchmarks beat Snowflake)
- ✅ Lower costs if self-hosted

**Cons:**
- ❌ More operational overhead (if self-hosted)
- ❌ Less mature ecosystem (no dbt native support)
- ❌ Manual replication and scaling
- ❌ Steeper learning curve

**When to choose:** Team has strong ops skills; want maximum performance; anti-vendor lock-in

---

## Recommended: Snowflake Architecture

For Ask Bosco's requirements, **Snowflake is the optimal choice** because:

1. ✅ **Optimized for aggregations:** 10-100x faster than row-based for analytical queries
2. ✅ **Minimal operations:** Fully managed, auto-scaling, auto-suspend
3. ✅ **Cost-effective at scale:** Result cache + auto-suspend = pay only for what you use
4. ✅ **Integrated ecosystem:** dbt, Airbyte, ML all have native Snowflake support
5. ✅ **Time travel:** Built-in data versioning and rollback (compliance, debugging)
6. ✅ **Handles growth:** Proven at petabyte scale
7. ✅ **Developer productivity:** No index tuning, no partitioning management

**When to reconsider:**
- If you need < $2K/month total costs → use PostgreSQL
- If you're anti-vendor lock-in → use ClickHouse
- If already on GCP with BigQuery credits → use BigQuery

---

## Implementation Roadmap

### Phase 1: MVP (Weeks 1-4)
- Set up Snowflake account (trial includes $400 credits)
- Deploy Airbyte with 5 key sources → Snowflake RAW schema
- Build 5 dbt models (staging → analytics → metrics)
- Deploy FastAPI with 3 endpoints querying Snowflake
- Build basic React dashboard with 3 charts
- **Deliverable:** 5 pilot customers on live dashboards

### Phase 2: Production (Weeks 5-8)
- Add 20 more Airbyte connectors
- Build out complete dbt project (30+ models)
- Implement dbt tests for data quality
- Deploy Redis caching layer
- Add authentication (JWT) and multi-tenancy
- Build out full dashboard with 10+ visualizations
- **Deliverable:** 15 paying customers, SLA monitoring

### Phase 3: Intelligence (Weeks 9-12)
- Implement Snowpark Python for ML
- Train anomaly detection model (Snowflake ML)
- Build forecasting model (Prophet or ARIMA)
- Create ML.predictions tables
- Add ML insights to API and dashboard
- Implement alerting system
- **Deliverable:** 30 customers with ML-powered insights

### Phase 4: Scale (Months 4-6)
- Add remaining connectors to reach 100+
- Optimize Snowflake warehouses (right-sizing)
- Implement advanced features:
  - Multi-touch attribution
  - Budget optimizer
  - Custom report builder
- Build customer-facing analytics API
- Implement data sharing (Snowflake Marketplace)
- **Deliverable:** 50+ customers, proven scalability, revenue-positive

---

## Example dbt Model

```sql
-- models/marts/marketing/daily_campaign_summary.sql
{{
  config(
    materialized='incremental',
    unique_key='unique_id',
    cluster_by=['date', 'tenant_id']
  )
}}

WITH campaign_performance AS (
  SELECT
    date,
    tenant_id,
    campaign_id,
    platform,
    SUM(impressions) AS impressions,
    SUM(clicks) AS clicks,
    SUM(cost) AS cost,
    SUM(revenue) AS revenue,
    SUM(conversions) AS conversions
  FROM {{ ref('fct_campaign_performance') }}
  {% if is_incremental() %}
    WHERE date > (SELECT MAX(date) FROM {{ this }})
  {% endif %}
  GROUP BY 1, 2, 3, 4
)

SELECT
  {{ dbt_utils.generate_surrogate_key(['date', 'tenant_id', 'campaign_id']) }} AS unique_id,
  date,
  tenant_id,
  campaign_id,
  platform,
  impressions,
  clicks,
  cost,
  revenue,
  conversions,

  -- Calculated metrics
  CASE WHEN impressions > 0
    THEN clicks / impressions
    ELSE 0
  END AS ctr,

  CASE WHEN clicks > 0
    THEN cost / clicks
    ELSE 0
  END AS cpc,

  CASE WHEN cost > 0
    THEN revenue / cost
    ELSE 0
  END AS roas,

  CASE WHEN clicks > 0
    THEN conversions / clicks
    ELSE 0
  END AS conversion_rate,

  CURRENT_TIMESTAMP() AS _dbt_updated_at

FROM campaign_performance
```

**dbt test:**
```yaml
# models/marts/marketing/_marketing.yml
models:
  - name: daily_campaign_summary
    description: "Daily aggregated campaign performance metrics"
    columns:
      - name: unique_id
        tests:
          - unique
          - not_null
      - name: cost
        tests:
          - dbt_expectations.expect_column_values_to_be_between:
              min_value: 0
              max_value: 1000000
      - name: roas
        tests:
          - dbt_expectations.expect_column_values_to_be_between:
              min_value: 0
              max_value: 100
```

---

## Conclusion

The **Snowflake-based architecture** provides:

1. **Optimal for Aggregations:** Columnar storage delivers 10-100x faster queries for analytics workloads
2. **Minimal Tech Stack:** 5 core technologies (Airbyte, Snowflake, dbt, FastAPI, React)
3. **Low Operational Overhead:** Fully managed warehouse with auto-scaling and auto-suspend
4. **Cost-Effective:** $2,380/month at initial scale ($48/client), scales efficiently
5. **Developer Productivity:** dbt for transformations, automatic query optimization, no index tuning
6. **Built for Scale:** Handles 1TB+ data with sub-second query performance
7. **Future-Proof:** Native ML support, data sharing, proven at petabyte scale

This architecture positions Ask Bosco to deliver fast, reliable analytics to customers while maintaining healthy margins and minimal operational burden.
