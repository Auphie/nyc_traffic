from __future__ import annotations

from datetime import datetime
from pathlib import Path

from airflow.providers.standard.operators.bash import BashOperator

from airflow import DAG

PROJECT_ROOT = Path(__file__).resolve().parents[2]
BUILD_DUCKDB_PATH = PROJECT_ROOT / "state" / "build" / "nyc_tlc.duckdb"
PROD_DUCKDB_PATH = PROJECT_ROOT / "state" / "prod" / "nyc_tlc.duckdb"
TLC_DATA_DIR = PROJECT_ROOT / "data"
AIRFLOW_RUNTIME_DIR = PROJECT_ROOT / "airflow" / ".local" / "runtime"
DOWNLOAD_FALLBACK_FILE = AIRFLOW_RUNTIME_DIR / "download_fallback.log"

TASK_ENV = {
    "DBT_DUCKDB_PATH": str(BUILD_DUCKDB_PATH),
    "BUILD_DUCKDB_PATH": str(BUILD_DUCKDB_PATH),
    "PROD_DUCKDB_PATH": str(PROD_DUCKDB_PATH),
    "TLC_DATA_DIR": str(TLC_DATA_DIR),
    "AIRFLOW_RUNTIME_DIR": str(AIRFLOW_RUNTIME_DIR),
    "AIRFLOW_DOWNLOAD_FALLBACK_FILE": str(DOWNLOAD_FALLBACK_FILE),
}

DAG_DOC = """
# NYC TLC Local Pipeline

This DAG keeps orchestration thin and reuses the project's existing CLI surface:

1. attempt the incremental TLC download
2. if the month is not published yet, log the fallback message and continue
3. `make bootstrap`
4. `make dbt-seed`
5. `make dbt-run`
6. `make swap-duckdb`

dbt always writes to `state/build/nyc_tlc.duckdb`, while Streamlit and other
readers continue to point at `state/prod/nyc_tlc.duckdb`.
"""


with DAG(
    dag_id="nyc_tlc_local_pipeline",
    description="Thin Airflow DAG for the local DuckDB + dbt + Streamlit workflow.",
    start_date=datetime(2026, 1, 1),
    schedule=None,
    catchup=False,
    tags=["nyc-tlc", "duckdb", "dbt", "streamlit"],
    doc_md=DAG_DOC,
) as dag:
    incremental_download = BashOperator(
        task_id="incremental_download",
        bash_command=f"""
            cd {PROJECT_ROOT}
            mkdir -p "$AIRFLOW_RUNTIME_DIR"
            rm -f "$AIRFLOW_DOWNLOAD_FALLBACK_FILE"
            log_capture="$(mktemp)"
            if make download-tlc >"$log_capture" 2>&1; then
                cat "$log_capture"
                rm -f "$log_capture"
                exit 0
            fi
            status="$?"
            cat "$log_capture"
            if [ "$status" -eq 2 ]; then
                cp "$log_capture" "$AIRFLOW_DOWNLOAD_FALLBACK_FILE"
                rm -f "$log_capture"
                exit 0
            fi
            rm -f "$log_capture"
            exit "$status"
        """,
        env=TASK_ENV,
    )

    log_download_fallback = BashOperator(
        task_id="log_download_fallback",
        bash_command="""
            if [ -f "$AIRFLOW_DOWNLOAD_FALLBACK_FILE" ]; then
                echo "TLC incremental download fallback triggered."
                cat "$AIRFLOW_DOWNLOAD_FALLBACK_FILE"
                rm -f "$AIRFLOW_DOWNLOAD_FALLBACK_FILE"
            else
                echo "No fallback logging needed."
            fi
        """,
        env=TASK_ENV,
    )

    bootstrap_duckdb = BashOperator(
        task_id="bootstrap_duckdb",
        bash_command=f"cd {PROJECT_ROOT} && make bootstrap",
        env=TASK_ENV,
    )

    seed_taxi_zone_lookup = BashOperator(
        task_id="seed_taxi_zone_lookup",
        bash_command=f"cd {PROJECT_ROOT} && make dbt-seed",
        env=TASK_ENV,
    )

    build_dbt_models = BashOperator(
        task_id="build_dbt_models",
        bash_command=f"cd {PROJECT_ROOT} && make dbt-run",
        env=TASK_ENV,
    )

    promote_prod_duckdb = BashOperator(
        task_id="promote_prod_duckdb",
        bash_command=f"cd {PROJECT_ROOT} && make swap-duckdb",
        env=TASK_ENV,
    )

    (
        incremental_download
        >> log_download_fallback
        >> bootstrap_duckdb
        >> seed_taxi_zone_lookup
        >> build_dbt_models
        >> promote_prod_duckdb
    )
