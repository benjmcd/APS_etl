# APS ETL (Milestone 1)

This repository contains the APS ETL Milestone 1 implementation: a search-only runner with
canonical query registry support, SQLAlchemy models, and offline tests.

## Requirements

* Python 3.12
* Docker (for local Postgres 16)

## Required environment variables

* `APS_PRIMARY_KEY` (required)
* `APS_SECONDARY_KEY` (optional)
* `APS_BASE_URL` (default: `https://adams-api.nrc.gov`)
* `DATABASE_URL` (default: `postgresql+psycopg://aps:aps@localhost:5432/aps`)
* `VCR_RECORD_MODE` (default: `none`)
* `VCR_CASSETTE_DIR` (default: `tests/fixtures/cassettes`)

## Local Postgres (Docker)

```bash
docker run --name aps-postgres -e POSTGRES_PASSWORD=aps -e POSTGRES_USER=aps -e POSTGRES_DB=aps \
  -p 5432:5432 -d postgres:16
```

## Common commands

```bash
make install
make fmt
make lint
make type
make test
make test-integration
make smoke-offline
```

`make smoke-offline` replays VCR cassettes and does not require live NRC connectivity.
