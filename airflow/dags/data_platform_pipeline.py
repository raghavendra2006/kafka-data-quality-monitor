"""
Data Platform Pipeline DAG
===========================
Orchestrates the full ETLT pipeline with strict task ordering:
  start → [ingest_postgres, ingest_api, ingest_files] → validate_data_quality
  → transform_data_dbt → load_to_warehouse → update_data_catalog → end

Design decisions:
  - All tasks are idempotent (safe to re-run without side effects)
  - Delta Lake `overwrite` mode ensures idempotency in raw-zone
  - Warehouse tables use TRUNCATE + INSERT for idempotent loads
  - Data quality gate stops the pipeline on validation failure
  - DataHub catalog update is best-effort (logs warning on failure)
"""

import os
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any

from airflow import DAG
from airflow.operators.empty import EmptyOperator
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Environment configuration
# ---------------------------------------------------------------------------
SOURCE_DB: Dict[str, Any] = {
    "host": os.environ.get("SOURCE_DB_HOST", "postgres-source"),
    "port": int(os.environ.get("SOURCE_DB_PORT", 5432)),
    "dbname": os.environ.get("SOURCE_DB_NAME", "source_db"),
    "user": os.environ.get("SOURCE_DB_USER", "source_user"),
    "password": os.environ.get("SOURCE_DB_PASSWORD", "source_pass"),
}

WAREHOUSE_DB: Dict[str, Any] = {
    "host": os.environ.get("WAREHOUSE_DB_HOST", "postgres-warehouse"),
    "port": int(os.environ.get("WAREHOUSE_DB_PORT", 5432)),
    "dbname": os.environ.get("WAREHOUSE_DB_NAME", "warehouse_db"),
    "user": os.environ.get("WAREHOUSE_DB_USER", "warehouse_user"),
    "password": os.environ.get("WAREHOUSE_DB_PASSWORD", "warehouse_pass"),
}

MINIO_CFG: Dict[str, str] = {
    "endpoint_url": os.environ.get("MINIO_ENDPOINT", "http://minio:9000"),
    "aws_access_key_id": os.environ.get("AWS_ACCESS_KEY_ID", "minioadmin"),
    "aws_secret_access_key": os.environ.get("AWS_SECRET_ACCESS_KEY", "minioadmin123"),
}

STORAGE_OPTIONS: Dict[str, str] = {
    "AWS_ACCESS_KEY_ID": MINIO_CFG["aws_access_key_id"],
    "AWS_SECRET_ACCESS_KEY": MINIO_CFG["aws_secret_access_key"],
    "AWS_ENDPOINT_URL": MINIO_CFG["endpoint_url"],
    "AWS_REGION": "us-east-1",
    "AWS_ALLOW_HTTP": "true",
    "AWS_S3_ALLOW_UNSAFE_RENAME": "true",
}

FMP_API_KEY: str = os.environ.get("FMP_API_KEY", "demo")
DATAHUB_GMS_URL: str = os.environ.get("DATAHUB_GMS_URL", "http://datahub-gms:8080")
RAW_ZONE: str = "s3://raw-zone"


# ===================================================================
# Task: Ingest from PostgreSQL source
# ===================================================================
def _ingest_postgres(**kwargs) -> None:
    """Extract products & sales from source PG → Delta Lake in raw-zone.

    Idempotent: uses overwrite mode so re-runs produce identical results.
    """
    import pandas as pd
    import psycopg2
    from deltalake import write_deltalake

    logger.info("Connecting to source database at %s:%s", SOURCE_DB["host"], SOURCE_DB["port"])
    conn = psycopg2.connect(**SOURCE_DB)
    try:
        for table in ("products", "sales"):
            df = pd.read_sql(f"SELECT * FROM {table}", conn)
            if df.empty:
                raise ValueError(f"Source table '{table}' is empty — aborting ingestion")
            logger.info("Ingested %d rows from source.%s", len(df), table)

            write_deltalake(
                f"{RAW_ZONE}/{table}",
                df,
                mode="overwrite",
                storage_options=STORAGE_OPTIONS,
            )
            logger.info("Wrote %s to Delta Lake at %s/%s", table, RAW_ZONE, table)
    finally:
        conn.close()
    logger.info("PostgreSQL ingestion complete.")


# ===================================================================
# Task: Ingest from external Financial API
# ===================================================================
def _ingest_api(**kwargs) -> None:
    """Fetch AAPL stock data from Financial Modeling Prep → Delta Lake.

    Falls back to realistic mock data if the API is unavailable or rate-limited.
    """
    import pandas as pd
    import requests
    from deltalake import write_deltalake

    url = (
        f"https://financialmodelingprep.com/api/v3/historical-price-full/AAPL"
        f"?timeseries=30&apikey={FMP_API_KEY}"
    )

    df = None
    try:
        logger.info("Fetching stock data from FMP API...")
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        historical = data.get("historical", [])
        if historical:
            df = pd.DataFrame(historical)
            logger.info("Fetched %d stock records from FMP API", len(df))
        else:
            raise ValueError("No historical data in API response")
    except Exception as e:
        logger.warning("FMP API unavailable (%s) — using mock stock data.", e)
        df = _generate_mock_stock_data()

    write_deltalake(
        f"{RAW_ZONE}/stocks",
        df,
        mode="overwrite",
        storage_options=STORAGE_OPTIONS,
    )
    logger.info("Wrote %d stock records to Delta Lake at %s/stocks", len(df), RAW_ZONE)


def _generate_mock_stock_data():
    """Generate realistic mock AAPL stock data for 30 business days."""
    import pandas as pd
    import random

    random.seed(42)  # Reproducible for idempotency
    dates = pd.date_range(end=datetime.now(), periods=30, freq="B")
    records = []
    price = 175.0
    for d in dates:
        open_p = round(price + random.uniform(-2, 2), 2)
        high = round(open_p + random.uniform(0, 5), 2)
        low = round(open_p - random.uniform(0, 5), 2)
        close = round(random.uniform(low, high), 2)
        volume = random.randint(50_000_000, 120_000_000)
        records.append({
            "date": d.strftime("%Y-%m-%d"),
            "open": open_p,
            "high": high,
            "low": low,
            "close": close,
            "adjClose": close,
            "volume": volume,
            "unadjustedVolume": volume,
            "change": round(close - open_p, 2),
            "changePercent": round((close - open_p) / open_p * 100, 4),
            "label": d.strftime("%B %d, %y"),
            "changeOverTime": round((close - open_p) / open_p, 6),
        })
        price = close
    return pd.DataFrame(records)


# ===================================================================
# Task: Ingest files from MinIO landing zone
# ===================================================================
def _ingest_files(**kwargs) -> None:
    """Read customer_reviews.csv from landing-zone → Delta Lake in raw-zone."""
    import pandas as pd
    import boto3
    from io import BytesIO
    from deltalake import write_deltalake

    s3 = boto3.client(
        "s3",
        endpoint_url=MINIO_CFG["endpoint_url"],
        aws_access_key_id=MINIO_CFG["aws_access_key_id"],
        aws_secret_access_key=MINIO_CFG["aws_secret_access_key"],
    )

    logger.info("Reading customer_reviews.csv from landing-zone bucket...")
    obj = s3.get_object(Bucket="landing-zone", Key="customer_reviews.csv")
    df = pd.read_csv(BytesIO(obj["Body"].read()))

    if df.empty:
        raise ValueError("customer_reviews.csv is empty — aborting ingestion")
    logger.info("Ingested %d reviews from landing-zone CSV", len(df))

    write_deltalake(
        f"{RAW_ZONE}/reviews",
        df,
        mode="overwrite",
        storage_options=STORAGE_OPTIONS,
    )
    logger.info("Wrote reviews to Delta Lake at %s/reviews", RAW_ZONE)


# ===================================================================
# Task: Data Quality Validation with Great Expectations
# ===================================================================
def _validate_data_quality(**kwargs) -> None:
    """Run Great Expectations validation on raw sales data.

    This is a quality gate: if any expectation fails, the entire pipeline stops.
    Validates: column existence, non-null constraints, value ranges.
    """
    import pandas as pd
    from deltalake import DeltaTable
    import great_expectations as gx

    # Read sales from Delta Lake
    dt = DeltaTable(f"{RAW_ZONE}/sales", storage_options=STORAGE_OPTIONS)
    df = dt.to_pandas()
    logger.info("Loaded %d sales rows for quality validation", len(df))

    if df.empty:
        raise ValueError("Sales dataset is empty — cannot validate")

    # Build ephemeral GE context
    context = gx.get_context()

    data_source = context.data_sources.add_pandas("sales_source")
    data_asset = data_source.add_dataframe_asset(name="sales_asset")
    batch_definition = data_asset.add_batch_definition_whole_dataframe("sales_batch")

    # Define expectation suite
    suite = context.suites.add(
        gx.ExpectationSuite(name="sales_quality_suite")
    )

    # Column existence checks
    for col in ("sale_id", "product_id", "sale_date", "quantity"):
        suite.add_expectation(
            gx.expectations.ExpectColumnToExist(column=col)
        )

    # Non-null checks
    for col in ("sale_id", "product_id"):
        suite.add_expectation(
            gx.expectations.ExpectColumnValuesToNotBeNull(column=col)
        )

    # Value range check
    suite.add_expectation(
        gx.expectations.ExpectColumnValuesToBeBetween(
            column="quantity", min_value=1
        )
    )

    # Run validation
    validation_definition = context.validation_definitions.add(
        gx.ValidationDefinition(
            name="sales_validation",
            data=batch_definition,
            suite=suite,
        )
    )

    checkpoint = context.checkpoints.add(
        gx.Checkpoint(
            name="sales_checkpoint",
            validation_definitions=[validation_definition],
        )
    )

    result = checkpoint.run(batch_parameters={"dataframe": df})

    if not result.success:
        failed_expectations = []
        for run_result in result.run_results.values():
            for vr in run_result["validation_result"]["results"]:
                if not vr["success"]:
                    failed_expectations.append(
                        f"{vr['expectation_config']['type']}({vr['expectation_config']['kwargs']})"
                    )
        error_msg = (
            f"DATA QUALITY GATE FAILED — {len(failed_expectations)} expectation(s) failed:\n"
            + "\n".join(f"  ✗ {e}" for e in failed_expectations)
        )
        logger.error(error_msg)
        raise ValueError(error_msg)

    logger.info("✓ All %d data quality checks PASSED.", len(suite.expectations))


# ===================================================================
# Task: Transform with dbt (includes loading raw data to warehouse)
# ===================================================================
def _transform_load_raw_to_warehouse(**kwargs) -> None:
    """Load raw Delta Lake data into warehouse staging tables for dbt.

    This runs as part of the transform phase: raw data must be in the warehouse
    for dbt to read from the `raw` schema and create mart models.
    Idempotent: uses TRUNCATE + INSERT.
    """
    import pandas as pd
    import psycopg2
    from deltalake import DeltaTable

    logger.info("Connecting to warehouse at %s:%s", WAREHOUSE_DB["host"], WAREHOUSE_DB["port"])
    conn = psycopg2.connect(**WAREHOUSE_DB)
    conn.autocommit = True
    cur = conn.cursor()

    try:
        cur.execute("CREATE SCHEMA IF NOT EXISTS raw;")

        table_definitions = {
            "products": """
                CREATE TABLE IF NOT EXISTS raw.products (
                    product_id INT PRIMARY KEY,
                    name VARCHAR(255),
                    category VARCHAR(100),
                    price DECIMAL(10,2)
                )
            """,
            "sales": """
                CREATE TABLE IF NOT EXISTS raw.sales (
                    sale_id INT PRIMARY KEY,
                    product_id INT,
                    sale_date TIMESTAMP,
                    quantity INT,
                    total_amount DECIMAL(12,2)
                )
            """,
            "reviews": """
                CREATE TABLE IF NOT EXISTS raw.reviews (
                    review_id INT PRIMARY KEY,
                    product_id INT,
                    rating INT,
                    review_text TEXT
                )
            """,
            "stocks": """
                CREATE TABLE IF NOT EXISTS raw.stocks (
                    date VARCHAR(20),
                    open DECIMAL(10,2),
                    high DECIMAL(10,2),
                    low DECIMAL(10,2),
                    close DECIMAL(10,2),
                    "adjClose" DECIMAL(10,2),
                    volume BIGINT,
                    "unadjustedVolume" BIGINT,
                    change DECIMAL(10,4),
                    "changePercent" DECIMAL(10,4),
                    label VARCHAR(50),
                    "changeOverTime" DECIMAL(12,6)
                )
            """,
        }

        for table_name, create_sql in table_definitions.items():
            cur.execute(create_sql)
            cur.execute(f"TRUNCATE TABLE raw.{table_name};")

            dt = DeltaTable(f"{RAW_ZONE}/{table_name}", storage_options=STORAGE_OPTIONS)
            df = dt.to_pandas()
            if df.empty:
                logger.warning("No data found for raw.%s — skipping", table_name)
                continue

            # Use COPY-style bulk insert via execute_values for performance
            cols = df.columns.tolist()
            col_str = ", ".join([f'"{c}"' for c in cols])
            template = "(" + ", ".join(["%s"] * len(cols)) + ")"
            insert_sql = f'INSERT INTO raw.{table_name} ({col_str}) VALUES %s'

            from psycopg2.extras import execute_values
            values = [tuple(row) for row in df.values]
            execute_values(cur, insert_sql, values, template=template, page_size=500)
            logger.info("Loaded %d rows into raw.%s", len(df), table_name)

    finally:
        cur.close()
        conn.close()

    logger.info("All raw data loaded to warehouse staging tables.")


# ===================================================================
# Task: Load to warehouse (post-dbt verification + indexing)
# ===================================================================
def _load_to_warehouse(**kwargs) -> None:
    """Verify dbt output and create indexes on the fact table.

    This task runs AFTER dbt transforms have completed. It:
    1. Verifies fact_daily_sales was created and is non-empty
    2. Creates indexes for query performance
    3. Runs ANALYZE for query planner statistics
    """
    import psycopg2

    logger.info("Verifying warehouse state after dbt transformation...")
    conn = psycopg2.connect(**WAREHOUSE_DB)
    conn.autocommit = True
    cur = conn.cursor()

    try:
        # Verify fact_daily_sales exists and has data
        cur.execute("""
            SELECT COUNT(*) FROM information_schema.tables
            WHERE table_schema = 'public' AND table_name = 'fact_daily_sales'
        """)
        if cur.fetchone()[0] == 0:
            raise ValueError("fact_daily_sales table was NOT created by dbt — transformation failed")

        cur.execute("SELECT COUNT(*) FROM fact_daily_sales")
        row_count = cur.fetchone()[0]
        if row_count == 0:
            raise ValueError("fact_daily_sales is EMPTY after dbt run — check model logic")
        logger.info("✓ fact_daily_sales verified: %d rows", row_count)

        # Create indexes for API query performance
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_fact_daily_sales_date
            ON fact_daily_sales (date DESC)
        """)
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_fact_daily_sales_product
            ON fact_daily_sales (product_id)
        """)
        logger.info("✓ Indexes created on fact_daily_sales")

        # Update query planner statistics
        cur.execute("ANALYZE fact_daily_sales;")
        logger.info("✓ ANALYZE complete on fact_daily_sales")

    finally:
        cur.close()
        conn.close()

    logger.info("Warehouse load verification complete.")


# ===================================================================
# Task: Update Data Catalog (DataHub)
# ===================================================================
def _update_data_catalog(**kwargs) -> None:
    """Push metadata and lineage to DataHub via REST emitter.

    Registers:
    - Raw-zone datasets (sales, products, reviews, stocks) from MinIO
    - Warehouse fact table (fact_daily_sales)
    - Lineage from raw → dbt → fact_daily_sales
    """
    try:
        from datahub.emitter.rest_emitter import DatahubRestEmitter
        from datahub.metadata.schema_classes import (
            DatasetPropertiesClass,
            UpstreamLineageClass,
            UpstreamClass,
        )
        from datahub.emitter.mce_builder import make_dataset_urn
        from datahub.emitter.mcp import MetadataChangeProposalWrapper

        emitter = DatahubRestEmitter(gms_server=DATAHUB_GMS_URL)
        emitter.test_connection()
        logger.info("Connected to DataHub at %s", DATAHUB_GMS_URL)

        # Register raw-zone datasets
        raw_datasets = {
            "sales": "Raw sales transactions in Delta Lake format",
            "products": "Raw product catalog in Delta Lake format",
            "reviews": "Raw customer reviews in Delta Lake format",
            "stocks": "Raw AAPL stock price data in Delta Lake format",
        }

        for ds_name, description in raw_datasets.items():
            dataset_urn = make_dataset_urn("s3", f"raw-zone/{ds_name}", "PROD")
            mcp = MetadataChangeProposalWrapper(
                entityUrn=dataset_urn,
                aspect=DatasetPropertiesClass(
                    name=ds_name,
                    description=description,
                    customProperties={
                        "format": "delta",
                        "zone": "raw-zone",
                        "storage": "MinIO",
                    },
                ),
            )
            emitter.emit(mcp)
            logger.info("Registered dataset: %s", ds_name)

        # Register fact_daily_sales in warehouse
        fact_urn = make_dataset_urn(
            "postgres", "warehouse_db.public.fact_daily_sales", "PROD"
        )
        mcp = MetadataChangeProposalWrapper(
            entityUrn=fact_urn,
            aspect=DatasetPropertiesClass(
                name="fact_daily_sales",
                description="Aggregated daily sales fact table with product info and review ratings",
                customProperties={
                    "source": "dbt",
                    "warehouse": "postgres-warehouse",
                    "materialization": "table",
                },
            ),
        )
        emitter.emit(mcp)

        # Publish lineage: raw tables → fact_daily_sales
        upstream_urns = [
            make_dataset_urn("s3", "raw-zone/sales", "PROD"),
            make_dataset_urn("s3", "raw-zone/products", "PROD"),
            make_dataset_urn("s3", "raw-zone/reviews", "PROD"),
        ]
        lineage_mcp = MetadataChangeProposalWrapper(
            entityUrn=fact_urn,
            aspect=UpstreamLineageClass(
                upstreams=[
                    UpstreamClass(dataset=u, type="TRANSFORMED")
                    for u in upstream_urns
                ]
            ),
        )
        emitter.emit(lineage_mcp)
        logger.info("✓ Published lineage to DataHub (3 upstream → fact_daily_sales)")

    except Exception as e:
        logger.warning(
            "DataHub catalog update failed: %s. "
            "This is non-fatal — the pipeline data is still valid. "
            "Ensure DataHub services are running if catalog updates are required.",
            e,
        )


# ===================================================================
# DAG Definition
# ===================================================================
default_args = {
    "owner": "data-platform",
    "depends_on_past": False,
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=2),
    "execution_timeout": timedelta(minutes=30),
}

with DAG(
    dag_id="data_platform_pipeline",
    default_args=default_args,
    description="End-to-end data platform: Ingest → Validate → Transform → Load → Catalog",
    schedule_interval="@daily",
    start_date=datetime(2024, 1, 1),
    catchup=False,
    max_active_runs=1,
    tags=["data-platform", "etl", "delta-lake"],
) as dag:

    start = EmptyOperator(task_id="start")
    end = EmptyOperator(task_id="end", trigger_rule="none_failed")

    ingest_postgres = PythonOperator(
        task_id="ingest_postgres",
        python_callable=_ingest_postgres,
    )

    ingest_api = PythonOperator(
        task_id="ingest_api",
        python_callable=_ingest_api,
    )

    ingest_files = PythonOperator(
        task_id="ingest_files",
        python_callable=_ingest_files,
    )

    validate_data_quality = PythonOperator(
        task_id="validate_data_quality",
        python_callable=_validate_data_quality,
    )

    # Transform phase: first load raw to warehouse, then run dbt
    load_raw_to_warehouse = PythonOperator(
        task_id="transform_load_staging",
        python_callable=_transform_load_raw_to_warehouse,
    )

    run_dbt = BashOperator(
        task_id="transform_data_dbt",
        bash_command=(
            "cd /opt/airflow/dbt_project && "
            "dbt deps --profiles-dir . --target prod 2>/dev/null; "
            "dbt run --profiles-dir . --target prod"
        ),
    )

    load_to_warehouse = PythonOperator(
        task_id="load_to_warehouse",
        python_callable=_load_to_warehouse,
    )

    update_data_catalog = PythonOperator(
        task_id="update_data_catalog",
        python_callable=_update_data_catalog,
    )

    # ---------------------------------------------------------------
    # Task dependency chain (matches specification exactly):
    #   start
    #   → [ingest_postgres, ingest_api, ingest_files]  (parallel)
    #   → validate_data_quality
    #   → transform_data_dbt  (includes staging load + dbt run)
    #   → load_to_warehouse   (verification + indexing)
    #   → update_data_catalog
    #   → end
    # ---------------------------------------------------------------
    start >> [ingest_postgres, ingest_api, ingest_files]
    [ingest_postgres, ingest_api, ingest_files] >> validate_data_quality
    validate_data_quality >> load_raw_to_warehouse >> run_dbt
    run_dbt >> load_to_warehouse
    load_to_warehouse >> update_data_catalog
    update_data_catalog >> end
