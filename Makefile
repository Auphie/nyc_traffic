PYTHON ?= python3
VENV_DIR ?= .env_duck
RUN_PYTHON := $(if $(wildcard $(VENV_DIR)/bin/python),$(VENV_DIR)/bin/python,$(PYTHON))
PYTHON_DIRS := build tests
DOWNLOAD_ARGS ?=
START_MONTH ?=
END_MONTH ?=

.PHONY: venv install check-env bootstrap download-tlc-full download-tlc discover-sources test lint lint-python lint-sql

venv:
	$(PYTHON) -m venv $(VENV_DIR)

install: venv
	$(VENV_DIR)/bin/pip install --upgrade pip
	$(VENV_DIR)/bin/pip install -r requirements.txt

check-env:
	$(RUN_PYTHON) -m build.check_environment

bootstrap:
	$(RUN_PYTHON) -m build.bootstrap

download-tlc-full:
	$(RUN_PYTHON) -m build.download_from_tlc_full $(if $(START_MONTH),--start-month $(START_MONTH)) $(if $(END_MONTH),--end-month $(END_MONTH)) $(DOWNLOAD_ARGS)

download-tlc:
	$(RUN_PYTHON) -m build.download_from_tlc_incremental $(DOWNLOAD_ARGS)

discover-sources:
	$(RUN_PYTHON) -m build.source_discovery

test:
	$(RUN_PYTHON) -m unittest discover -s tests -p 'test_*.py'

lint: lint-python lint-sql

lint-python:
	$(RUN_PYTHON) -m ruff check $(PYTHON_DIRS)

lint-sql:
	$(RUN_PYTHON) -m sqlfluff lint etl
