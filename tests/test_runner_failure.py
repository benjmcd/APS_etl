from __future__ import annotations

from datetime import datetime

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from aps_etl.client import APSClient
from aps_etl.models import APSQueryRun, Base, QueryRunStatus
from aps_etl.registry import Libraries, QueryDefinition, SortSpec
from aps_etl.runner import run_query


def test_query_run_persists_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)

    query = QueryDefinition(
        query_id="failure-query",
        name="Failure Query",
        q="NuScale",
        filters_and=(),
        filters_or=(),
        libraries=Libraries(legacy=True, main=True),
        sort=SortSpec(field="DateAddedTimestamp", direction="DESC"),
        content=False,
        safety_buffer_days=3,
        wire_format="A",
        enabled=True,
    )
    client = APSClient(
        base_url="https://adams-api.nrc.gov",
        api_key="test-key",
        timeout_s=1.0,
        retry_max_attempts=1,
        retry_min_wait_s=0.1,
        retry_max_wait_s=0.2,
    )

    def _raise_search(_: dict[str, object]) -> dict[str, object]:
        raise RuntimeError("boom")

    monkeypatch.setattr(client, "search", _raise_search)

    with Session(engine) as session:
        with pytest.raises(RuntimeError, match="boom"):
            run_query(
                session=session,
                client=client,
                query=query,
                schema_version="1",
                max_pages=1,
            )

    with Session(engine) as session:
        run_row = session.scalar(select(APSQueryRun).where(APSQueryRun.query_id == "failure-query"))

    assert run_row is not None
    assert run_row.status == QueryRunStatus.FAILED
    assert run_row.error_message == "boom"
    assert isinstance(run_row.ended_at, datetime)
