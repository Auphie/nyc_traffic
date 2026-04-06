PYTHON ?= python3
VENV_DIR ?= .env_duck
RUN_PYTHON := $(if $(wildcard $(VENV_DIR)/bin/python),$(VENV_DIR)/bin/python,$(PYTHON))
RUN_DBT := $(if $(wildcard $(VENV_DIR)/bin/dbt),$(VENV_DIR)/bin/dbt,dbt)
RUN_STREAMLIT := $(if $(wildcard $(VENV_DIR)/bin/streamlit),$(VENV_DIR)/bin/streamlit,streamlit)
RUN_AIRFLOW := $(if $(wildcard $(VENV_DIR)/bin/airflow),$(VENV_DIR)/bin/airflow,airflow)
PYTHON_DIRS := airflow build tests streamlit
DOWNLOAD_ARGS ?=
START_MONTH ?=
END_MONTH ?=
DBT_PROJECT_DIR ?= etl/dbt
DBT_PROFILES_DIR ?= .env_duck
BUILD_DUCKDB_PATH ?= $(CURDIR)/state/build/nyc_tlc.duckdb
PROD_DUCKDB_PATH ?= $(CURDIR)/state/prod/nyc_tlc.duckdb
DBT_DUCKDB_PATH ?= $(BUILD_DUCKDB_PATH)
TLC_DATA_DIR ?= $(CURDIR)/data
DBT_ARGS ?=
STREAMLIT_PORT ?= 8501
AIRFLOW_HOME ?= $(CURDIR)/airflow/.local
AIRFLOW_VERSION ?= 3.1.2
AIRFLOW_ENV = AIRFLOW_HOME="$(AIRFLOW_HOME)" AIRFLOW__CORE__DAGS_FOLDER="$(CURDIR)/airflow/dags" AIRFLOW__CORE__LOAD_EXAMPLES=False

.PHONY: venv install install-airflow-deps airflow-install airflow-standalone airflow-list-dags airflow-trigger-pipeline check-env bootstrap download-tlc-full download-tlc discover-sources test lint lint-python lint-sql dbt-debug dbt-seed dbt-run dbt-test swap-duckdb streamlit-run ensure-state-dirs

venv:
	$(PYTHON) -m venv $(VENV_DIR)

install: venv
	$(VENV_DIR)/bin/pip install --upgrade pip
	$(VENV_DIR)/bin/pip install -r requirements.txt
	$(MAKE) install-airflow-deps

install-airflow-deps: venv
	AIRFLOW_VERSION="$(AIRFLOW_VERSION)"; \
	PYTHON_VERSION="$$( $(VENV_DIR)/bin/python -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")' )"; \
	CONSTRAINT_URL="https://raw.githubusercontent.com/apache/airflow/constraints-$${AIRFLOW_VERSION}/constraints-$${PYTHON_VERSION}.txt"; \
	$(VENV_DIR)/bin/pip install "apache-airflow==$${AIRFLOW_VERSION}" "apache-airflow-providers-standard" --constraint "$${CONSTRAINT_URL}"
	$(VENV_DIR)/bin/pip install \
		"click>=8.3,<9" \
		"protobuf>=6,<7" \
		"opentelemetry-proto>=1.40,<2" \
		"opentelemetry-exporter-otlp>=1.40,<2" \
		"opentelemetry-exporter-otlp-proto-common>=1.40,<2" \
		"opentelemetry-exporter-otlp-proto-grpc>=1.40,<2" \
		"opentelemetry-exporter-otlp-proto-http>=1.40,<2"

airflow-install: install-airflow-deps

airflow-standalone: ensure-state-dirs
	$(AIRFLOW_ENV) $(RUN_AIRFLOW) standalone

airflow-list-dags:
	$(AIRFLOW_ENV) $(RUN_AIRFLOW) dags list

airflow-trigger-pipeline:
	$(AIRFLOW_ENV) $(RUN_AIRFLOW) dags trigger nyc_tlc_local_pipeline

check-env:
	$(RUN_PYTHON) -m build.check_environment

bootstrap: ensure-state-dirs
	$(RUN_PYTHON) -m build.bootstrap

download-tlc-full:
	$(RUN_PYTHON) -m build.download_from_tlc_full $(if $(START_MONTH),--start-month $(START_MONTH)) $(if $(END_MONTH),--end-month $(END_MONTH)) $(DOWNLOAD_ARGS)

download-tlc:
	$(RUN_PYTHON) -m build.download_from_tlc_incremental $(DOWNLOAD_ARGS)

discover-sources:
	$(RUN_PYTHON) -m build.source_discovery $(DOWNLOAD_ARGS)

test:
	$(RUN_PYTHON) -m unittest discover -s tests -p 'test_*.py'

lint: lint-python lint-sql

lint-python:
	$(RUN_PYTHON) -m ruff check $(PYTHON_DIRS)

lint-sql: ensure-state-dirs
	$(RUN_PYTHON) -m sqlfluff lint etl

dbt-debug: ensure-state-dirs
	DBT_DUCKDB_PATH="$(DBT_DUCKDB_PATH)" TLC_DATA_DIR="$(TLC_DATA_DIR)" $(RUN_DBT) debug --project-dir $(DBT_PROJECT_DIR) --profiles-dir $(DBT_PROFILES_DIR) $(DBT_ARGS)

dbt-seed: ensure-state-dirs
	DBT_DUCKDB_PATH="$(DBT_DUCKDB_PATH)" TLC_DATA_DIR="$(TLC_DATA_DIR)" $(RUN_DBT) seed --project-dir $(DBT_PROJECT_DIR) --profiles-dir $(DBT_PROFILES_DIR) $(DBT_ARGS)

dbt-run: ensure-state-dirs
	DBT_DUCKDB_PATH="$(DBT_DUCKDB_PATH)" TLC_DATA_DIR="$(TLC_DATA_DIR)" $(RUN_DBT) run --project-dir $(DBT_PROJECT_DIR) --profiles-dir $(DBT_PROFILES_DIR) $(DBT_ARGS)

dbt-test: ensure-state-dirs
	DBT_DUCKDB_PATH="$(DBT_DUCKDB_PATH)" TLC_DATA_DIR="$(TLC_DATA_DIR)" $(RUN_DBT) test --project-dir $(DBT_PROJECT_DIR) --profiles-dir $(DBT_PROFILES_DIR) $(DBT_ARGS)

swap-duckdb: ensure-state-dirs
	DBT_DUCKDB_PATH="$(BUILD_DUCKDB_PATH)" PROD_DUCKDB_PATH="$(PROD_DUCKDB_PATH)" $(RUN_PYTHON) -m build.swap_duckdb

streamlit-run: ensure-state-dirs
	PROD_DUCKDB_PATH="$(PROD_DUCKDB_PATH)" $(RUN_STREAMLIT) run streamlit/app.py --server.port $(STREAMLIT_PORT)

ensure-state-dirs:
	mkdir -p "$(dir $(BUILD_DUCKDB_PATH))" "$(dir $(PROD_DUCKDB_PATH))"
