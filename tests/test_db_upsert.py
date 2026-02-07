from __future__ import annotations

from datetime import datetime

from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session

from aps_etl.db import upsert_document
from aps_etl.models import APSDiscovery, APSDocument, APSQueryRun, Base, QueryRunStatus


def test_upsert_preserves_enriched_fields() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        upsert_document(
            session,
            "ml123",
            {"is_stub": False, "url": "https://example.com/doc", "is_package": False},
        )
        upsert_document(
            session,
            "ML123",
            {"is_stub": True, "url": None, "is_package": False},
        )
        session.commit()

        document = session.scalar(select(APSDocument))

    assert document is not None
    assert document.is_stub is False
    assert document.url == "https://example.com/doc"


def test_upsert_canonicalizes_accession_casing() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        upsert_document(session, " abc-123 ", {"is_stub": True, "is_package": False})
        upsert_document(session, "ABC-123", {"is_stub": True, "is_package": False})
        session.commit()

        count = session.scalar(select(func.count()).select_from(APSDocument)) or 0
        document = session.scalar(select(APSDocument))

    assert count == 1
    assert document is not None
    assert document.accession_number == "ABC-123"
    assert document.accession_number_lower == "abc-123"


def test_upsert_preserves_existing_accession_casing_for_fk() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        session.add(
            APSDocument(
                accession_number="ml24018a111",
                accession_number_lower="ml24018a111",
                is_stub=True,
                is_package=False,
            )
        )
        session.add(
            APSQueryRun(
                query_id="seed-query",
                status=QueryRunStatus.SUCCESS,
                wire_format="A",
                request_fingerprint="fingerprint",
                schema_version="1",
                ended_at=datetime.utcnow(),
            )
        )
        session.commit()

        run_id = session.scalar(select(APSQueryRun.run_id)) or 0
        canonical_accession = upsert_document(
            session,
            "ML24018A111",
            {"is_stub": False, "url": "https://example.com", "is_package": False},
        )
        session.add(
            APSDiscovery(
                run_id=run_id,
                accession_number=canonical_accession,
                skip_value=0,
                page_number=1,
            )
        )
        session.commit()

        count = session.scalar(select(func.count()).select_from(APSDocument)) or 0
        document = session.scalar(select(APSDocument))

    assert count == 1
    assert document is not None
    assert document.accession_number == "ml24018a111"
