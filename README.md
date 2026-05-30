# 🚀 Real-Time Data Ingestion & Quality Monitoring Platform

A fully containerized, multi-service data platform that ingests data from multiple sources, validates it against a data quality framework, transforms it, catalogs lineage, and exposes curated data through a secure REST API.

![Architecture](https://img.shields.io/badge/Architecture-Microservices-blue)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker)
![Python](https://img.shields.io/badge/Python-3.11-3776AB?logo=python)
![License](https://img.shields.io/badge/License-MIT-green)

---

## 📋 Table of Contents

- [Architecture Overview](#architecture-overview)
- [Services](#services)
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Pipeline Overview](#pipeline-overview)
- [Data Quality](#data-quality)
- [API Documentation](#api-documentation)
- [Testing the API with JWT Tokens](#testing-the-api-with-jwt-tokens)
- [Database Backup](#database-backup)
- [Project Structure](#project-structure)
- [Configuration](#configuration)
- [Troubleshooting](#troubleshooting)

---

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Data Sources                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │
│  │ PostgreSQL   │  │ CSV Files    │  │ Financial    │              │
│  │ Source DB    │  │ (MinIO)      │  │ API (FMP)    │              │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘              │
│         └──────────────────┼─────────────────┘                      │
│                            ▼                                        │
│                   ┌────────────────┐                                │
│                   │ Apache Airflow │  ← Orchestration               │
│                   └────────┬───────┘                                │
│                            ▼                                        │
│              ┌─────────────────────────┐                           │
│              │ MinIO Data Lake         │                           │
│              │ ┌─────────┐ ┌────────┐ │                           │
│              │ │landing  │ │raw-zone│ │  ← Delta Lake Format      │
│              │ └─────────┘ └────┬───┘ │                           │
│              └──────────────────┼─────┘                           │
│                                 ▼                                  │
│              ┌──────────────────────────┐                          │
│              │ Great Expectations       │  ← Data Quality Gates   │
│              └──────────────┬───────────┘                          │
│                             ▼                                      │
│              ┌──────────────────────────┐                          │
│              │ dbt Transformations      │  ← Analytics Models     │
│              └──────────────┬───────────┘                          │
│                             ▼                                      │
│  ┌──────────────────┐  ┌──────────────────┐                       │
│  │ PostgreSQL       │  │ DataHub          │  ← Data Catalog       │
│  │ Warehouse        │  │ (Metadata +      │                       │
│  │ (fact_daily_sales)│ │  Lineage)        │                       │
│  └────────┬─────────┘  └──────────────────┘                       │
│           ▼                                                        │
│  ┌──────────────────┐                                              │
│  │ FastAPI Data API │  ← JWT + RBAC Security                      │
│  └──────────────────┘                                              │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 🧩 Services

| Service | Port | Description |
|---------|------|-------------|
| **postgres-source** | 5433 | Source PostgreSQL database with seed data |
| **postgres-warehouse** | 5434 | Destination data warehouse |
| **minio** | 9000 / 9001 | S3-compatible data lake (API / Console) |
| **airflow-webserver** | 8080 | Airflow UI for pipeline management |
| **airflow-scheduler** | — | DAG scheduler |
| **airflow-worker** | — | Celery task worker |
| **redis** | 6379 | Celery message broker |
| **datahub-gms** | 8081 | DataHub metadata service |
| **datahub-frontend** | 9002 | DataHub UI |
| **data-api** | 8000 | FastAPI data access API |

---

## 📦 Prerequisites

- **Docker** ≥ 24.0
- **Docker Compose** ≥ 2.20
- **8 GB RAM** minimum (DataHub requires significant resources)
- **10 GB disk space**

---

## ⚡ Quick Start

### 1. Clone the repository

```bash
git clone https://github.com/raghavendra2006/kafka-data-quality-monitor.git
cd kafka-data-quality-monitor
```

### 2. Configure environment

```bash
# The .env file is included with working defaults for local development
# For production, copy .env.example and set real secrets:
cp .env.example .env
# Edit .env with your values
```

### 3. Start the platform

```bash
docker-compose up -d --build
```

### 4. Wait for all services to be healthy

```bash
docker-compose ps
# All services should show "healthy" status within ~5 minutes
```

### 5. Access the services

| Service | URL | Credentials |
|---------|-----|-------------|
| Airflow UI | http://localhost:8080 | admin / admin |
| MinIO Console | http://localhost:9001 | minioadmin / minioadmin123 |
| DataHub UI | http://localhost:9002 | datahub / datahub |
| Data API Docs | http://localhost:8000/docs | JWT required |
| Data API Health | http://localhost:8000/health | No auth needed |

### 6. Trigger the pipeline

Open the Airflow UI → Find `data_platform_pipeline` → Click **Trigger DAG** (▶).

---

## 🔄 Pipeline Overview

The `data_platform_pipeline` DAG executes the following stages:

```
start
  ├── ingest_postgres    (Extract products & sales → Delta Lake)
  ├── ingest_api         (Fetch AAPL stock data → Delta Lake)
  └── ingest_files       (Read CSV reviews → Delta Lake)
        │
        ▼
validate_data_quality    (Great Expectations on raw sales)
        │
        ▼
transform_data_dbt       (Load raw → warehouse staging, then dbt run → fact_daily_sales)
        │
        ▼
load_to_warehouse        (Verify fact table, run ANALYZE)
        │
        ▼
update_data_catalog      (Push metadata & lineage to DataHub)
        │
        ▼
      end
```

---

## ✅ Data Quality

Great Expectations validates the raw sales data with these checks:

| Expectation | Column | Rule |
|-------------|--------|------|
| `expect_column_to_exist` | sale_id, product_id, sale_date, quantity | Column must exist |
| `expect_column_values_to_not_be_null` | sale_id, product_id | No NULL values |
| `expect_column_values_to_be_between` | quantity | Must be ≥ 1 |

If validation fails, the pipeline **stops** and subsequent tasks are skipped.

---

## 🔐 API Documentation

### Authentication

All API endpoints (except `/health` and `/auth/token`) require a JWT token in the `Authorization` header:

```
Authorization: Bearer <your_jwt_token>
```

### Roles

| Role | Access |
|------|--------|
| `analyst` | `GET /api/v1/sales/daily` |
| `admin` | `GET /api/v1/sales/daily` + `GET /api/v1/reviews/raw` |

### Endpoints

#### `GET /health`
Health check — no auth required.

#### `POST /auth/token`
Generate a JWT token for testing.

```bash
curl -X POST http://localhost:8000/auth/token \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "role": "analyst"}'
```

#### `GET /api/v1/sales/daily`
Daily sales summary (analyst + admin).

```bash
curl http://localhost:8000/api/v1/sales/daily \
  -H "Authorization: Bearer <token>"
```

#### `GET /api/v1/reviews/raw`
Raw review data (admin only).

```bash
curl http://localhost:8000/api/v1/reviews/raw \
  -H "Authorization: Bearer <token>"
```

---

## 🎟️ Testing the API with JWT Tokens

### Method 1: Using the `/auth/token` endpoint

```bash
# Get an analyst token
ANALYST_TOKEN=$(curl -s -X POST http://localhost:8000/auth/token \
  -H "Content-Type: application/json" \
  -d '{"username": "analyst1", "role": "analyst"}' | jq -r '.access_token')

# Get an admin token
ADMIN_TOKEN=$(curl -s -X POST http://localhost:8000/auth/token \
  -H "Content-Type: application/json" \
  -d '{"username": "admin1", "role": "admin"}' | jq -r '.access_token')

# Test: Analyst can access sales
curl -H "Authorization: Bearer $ANALYST_TOKEN" http://localhost:8000/api/v1/sales/daily

# Test: Analyst CANNOT access reviews (403 Forbidden)
curl -H "Authorization: Bearer $ANALYST_TOKEN" http://localhost:8000/api/v1/reviews/raw

# Test: Admin CAN access reviews (200 OK)
curl -H "Authorization: Bearer $ADMIN_TOKEN" http://localhost:8000/api/v1/reviews/raw

# Test: No token → 401 Unauthorized
curl http://localhost:8000/api/v1/sales/daily
```

### Method 2: Using the Python helper script

```bash
docker-compose exec data-api python generate_token.py --role analyst
docker-compose exec data-api python generate_token.py --role admin
```

### Method 3: Interactive API docs

Open http://localhost:8000/docs in your browser. Use the **Authorize** button with a Bearer token.

---

## 💾 Database Backup

Run a logical backup of the data warehouse:

```bash
docker-compose exec postgres-warehouse bash /backup.sh
```

Backups are saved to `./backups/` on the host with timestamped filenames:
```
backups/warehouse_backup_20240115_103000.sql
```

---

## 🧪 Running Tests

### Install test dependencies

```bash
pip install -r tests/requirements-test.txt
```

### Run the full test suite

```bash
pytest tests/ -v
```

### Run specific test categories

```bash
# Auth tests only
pytest tests/test_auth.py -v

# API endpoint tests only
pytest tests/test_api.py -v
```

Tests cover:
- JWT token creation, decoding, expiry, and signature validation
- RBAC role enforcement (analyst vs admin)
- API endpoint authentication (401/403 responses)
- Token generation round-trip
- Health check endpoint

---

## 📁 Project Structure

```
kafka-data-quality-monitor/
├── docker-compose.yml          # All service definitions
├── .env.example                # Environment variable template
├── .env                        # Local environment variables (git-ignored)
├── .gitignore
├── backup.sh                   # Warehouse backup script
├── README.md
│
├── seeds/                      # Data seeding
│   ├── source_db/
│   │   └── 01_init.sql         # Products & sales seed data
│   └── minio_files/
│       └── customer_reviews.csv
│
├── airflow/                    # Apache Airflow
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── dags/
│   │   └── data_platform_pipeline.py
│   └── plugins/
│
├── great_expectations/         # Data quality framework
│   ├── great_expectations.yml
│   └── expectations/
│       └── sales_suite.json
│
├── dbt_project/                # dbt transformations
│   ├── dbt_project.yml
│   ├── profiles.yml
│   └── models/
│       ├── staging/            # stg_sales, stg_products, stg_reviews
│       └── marts/              # fact_daily_sales
│
├── data_api/                   # FastAPI data access API
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── generate_token.py
│   └── app/
│       ├── main.py             # FastAPI application
│       ├── auth.py             # JWT + RBAC
│       ├── config.py           # Settings
│       ├── database.py         # Async SQLAlchemy
│       ├── models.py           # Pydantic schemas
│       └── routes/
│           ├── sales.py        # /api/v1/sales/daily
│           └── reviews.py      # /api/v1/reviews/raw
│
├── tests/                      # Unit & integration tests
│   ├── test_auth.py
│   └── test_api.py
│
└── backups/                    # Warehouse backups (git-ignored)
```

---

## ⚙️ Configuration

All configuration is managed through environment variables. See `.env.example` for the complete list.

| Variable | Description | Default |
|----------|-------------|---------|
| `SOURCE_DB_*` | Source PostgreSQL connection | source_user/source_pass |
| `WAREHOUSE_DB_*` | Warehouse PostgreSQL connection | warehouse_user/warehouse_pass |
| `MINIO_ROOT_USER/PASSWORD` | MinIO credentials | minioadmin/minioadmin123 |
| `AIRFLOW_FERNET_KEY` | Airflow encryption key | (generated) |
| `JWT_SECRET` | API JWT signing secret | (change in production!) |
| `FMP_API_KEY` | Financial Modeling Prep key | demo (mock fallback) |

---

## 🔧 Troubleshooting

### Services not starting?
```bash
# Check logs for a specific service
docker-compose logs -f airflow-webserver
docker-compose logs -f datahub-gms

# Restart everything
docker-compose down -v && docker-compose up -d --build
```

### Airflow DAG not visible?
- Wait 30 seconds for the scheduler to parse DAGs
- Check scheduler logs: `docker-compose logs airflow-scheduler`

### DataHub not responding?
- **Known Upstream Bug:** The official `v0.12.1` upgrade image has a known Java ANTLR runtime bug. If `datahub-gms` continuously fails to start because of a missing `datahubpolicyindex_v2` index, it is due to the `datahub-upgrade` container crashing.
- DataHub takes 2-3 minutes to start
- Check: `docker-compose logs datahub-gms`
- Elasticsearch needs time to initialize

### Pipeline fails at `ingest_api`?
- The FMP API key defaults to `demo` which has limited access
- Get a free key at https://financialmodelingprep.com/
- Set `FMP_API_KEY` in your `.env` file
- The pipeline uses mock data as fallback when the API is unavailable

### MinIO buckets not created?
```bash
# Manually trigger the setup
docker-compose run --rm minio-setup
```

---

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.
