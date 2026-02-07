from __future__ import annotations

from pathlib import Path

import pytest
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session

from aps_etl.models import APSDiscovery, APSDocument, APSQuery, APSQueryRun, Base
from aps_etl.runner import run_all_queries
from aps_etl.settings import Settings
from tests.helpers import build_vcr


@pytest.mark.integration
def test_runner_writes_discoveries_and_documents(tmp_path: Path) -> None:
    db_path = tmp_path / "aps.db"
    database_url = f"sqlite+pysqlite:///{db_path}"
    engine = create_engine(database_url, future=True)
    Base.metadata.create_all(engine)

    settings = Settings.model_validate(
        {"database_url": database_url, "aps_primary_key": "test-key"}
    )
    cassette_dir = Path("tests/fixtures/cassettes")
    cassette_path = cassette_dir / "search_runner.yaml"

    recorder = build_vcr(record_mode="none")
    recorder.cassette_library_dir = str(cassette_dir)

    with recorder.use_cassette(str(cassette_path)):
        run_all_queries(
            settings,
            registry_path=Path("queries.yaml"),
            schema_path=Path("registry_schema.json"),
        )

    with Session(engine) as session:
        document_count = session.scalar(select(func.count()).select_from(APSDocument)) or 0
        discovery_count = session.scalar(select(func.count()).select_from(APSDiscovery)) or 0
        run_count = session.scalar(select(func.count()).select_from(APSQueryRun)) or 0
        query_count = session.scalar(select(func.count()).select_from(APSQuery)) or 0

    assert document_count == 2
    assert discovery_count == 2
    assert run_count == 1
    assert query_count == 1


@pytest.mark.integration
def test_runner_is_idempotent_on_documents(tmp_path: Path) -> None:
    db_path = tmp_path / "aps.db"
    database_url = f"sqlite+pysqlite:///{db_path}"
    engine = create_engine(database_url, future=True)
    Base.metadata.create_all(engine)

    settings = Settings.model_validate(
        {"database_url": database_url, "aps_primary_key": "test-key"}
    )
    cassette_dir = Path("tests/fixtures/cassettes")
    cassette_path = cassette_dir / "search_runner.yaml"
    recorder = build_vcr(record_mode="none")
    recorder.cassette_library_dir = str(cassette_dir)

    with recorder.use_cassette(str(cassette_path)):
        run_all_queries(
            settings,
            registry_path=Path("queries.yaml"),
            schema_path=Path("registry_schema.json"),
        )
        run_all_queries(
            settings,
            registry_path=Path("queries.yaml"),
            schema_path=Path("registry_schema.json"),
        )

    with Session(engine) as session:
        document_count = session.scalar(select(func.count()).select_from(APSDocument)) or 0
        run_count = session.scalar(select(func.count()).select_from(APSQueryRun)) or 0

    assert document_count == 2
    assert run_count == 2
