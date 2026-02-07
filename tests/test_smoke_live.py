from __future__ import annotations

import os
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from aps_etl.client import APSClient
from aps_etl.models import Base
from aps_etl.registry import Libraries, QueryDefinition, SortSpec
from aps_etl.runner import run_query


@pytest.mark.smoke_live
def test_smoke_live_run(tmp_path: Path) -> None:
    api_key = os.getenv("APS_PRIMARY_KEY")
    if not api_key:
        pytest.skip("APS_PRIMARY_KEY is not set.")

    db_path = tmp_path / "aps_live.db"
    database_url = f"sqlite+pysqlite:///{db_path}"
    engine = create_engine(database_url, future=True)
    Base.metadata.create_all(engine)

    query = QueryDefinition(
        query_id="smoke-live",
        name="Smoke Live",
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
        api_key=api_key,
        timeout_s=30.0,
        retry_max_attempts=3,
        retry_min_wait_s=0.5,
        retry_max_wait_s=5.0,
    )

    with Session(engine) as session:
        run_query(
            session=session,
            client=client,
            query=query,
            schema_version="1",
            max_pages=1,
        )
        session.commit()
