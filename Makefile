PYTHON ?= python3
VENV_DIR ?= .env_duck

.PHONY: venv install check-env bootstrap test

venv:
	$(PYTHON) -m venv $(VENV_DIR)

install: venv
	$(VENV_DIR)/bin/pip install --upgrade pip
	$(VENV_DIR)/bin/pip install -r requirements.txt

check-env:
	$(PYTHON) -m build.check_environment

bootstrap:
	$(PYTHON) -m build.bootstrap

test:
	$(PYTHON) -m unittest discover -s tests -p 'test_*.py'
