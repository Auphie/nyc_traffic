PYTHON ?= python3
VENV_DIR ?= .env_duck

.PHONY: venv install check-env

venv:
	$(PYTHON) -m venv $(VENV_DIR)

install: venv
	$(VENV_DIR)/bin/pip install --upgrade pip
	$(VENV_DIR)/bin/pip install -r requirements.txt

check-env:
	$(PYTHON) build/check_environment.py

