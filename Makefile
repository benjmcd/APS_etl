.PHONY: install fmt lint type test test-integration smoke-offline smoke-live

install:
	python -m venv .venv
	. .venv/bin/activate && pip install -r requirements.txt

fmt:
	ruff format aps_etl tests

lint:
	ruff check aps_etl tests

type:
	mypy aps_etl tests

test:
	pytest -m "not integration and not smoke_offline and not smoke_live"

test-integration:
	pytest -m "integration"

smoke-offline:
	pytest -m "smoke_offline"

smoke-live:
	pytest -m "smoke_live"
