PYTHON ?= python3
VENV_DIR ?= .env_duck
RUN_PYTHON := $(if $(wildcard $(VENV_DIR)/bin/python),$(VENV_DIR)/bin/python,$(PYTHON))
RUN_DBT := $(if $(wildcard $(VENV_DIR)/bin/dbt),$(VENV_DIR)/bin/dbt,dbt)
RUN_STREAMLIT := $(if $(wildcard $(VENV_DIR)/bin/streamlit),$(VENV_DIR)/bin/streamlit,streamlit)
PYTHON_DIRS := build tests streamlit
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

.PHONY: venv install check-env bootstrap download-tlc-full download-tlc discover-sources test lint lint-python lint-sql dbt-debug dbt-seed dbt-run dbt-test swap-duckdb streamlit-run ensure-state-dirs

venv:
	$(PYTHON) -m venv $(VENV_DIR)

install: venv
	$(VENV_DIR)/bin/pip install --upgrade pip
	$(VENV_DIR)/bin/pip install -r requirements.txt

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
