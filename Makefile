.PHONY: help install install-lock test lint typecheck check build clean

PYTHON ?= python

help:
	@echo "Targets: install install-lock test lint typecheck check build clean"

install:
	$(PYTHON) -m pip install -e ".[dev]"

install-lock:
	$(PYTHON) -m pip install -r requirements-dev.lock.txt
	$(PYTHON) -m pip install -e . --no-deps

test:
	$(PYTHON) -m pytest

lint:
	$(PYTHON) -m ruff check src tests
	$(PYTHON) -m ruff format --check src tests

typecheck:
	$(PYTHON) -m mypy src

check: lint typecheck test

build:
	$(PYTHON) -m build

clean:
	rm -rf build dist .pytest_cache .mypy_cache .ruff_cache
