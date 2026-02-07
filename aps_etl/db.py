"""Database helpers for APS ETL."""

from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime
from typing import Any

from sqlalchemy import Engine, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.orm import Session, sessionmaker

from aps_etl.models import APSDiscovery, APSDocument, APSQuery, APSQueryRun, APSQueryState


def create_session_factory(engine: Engine) -> sessionmaker[Session]:
    """Create a session factory for the given engine."""

    return sessionmaker(bind=engine, expire_on_commit=False, future=True)


def upsert_document(session: Session, accession_number: str, values: dict[str, Any]) -> None:
    """Upsert an APS document, preserving existing non-null fields when stubbing."""

    normalized = accession_number.lower()
    payload = {"accession_number": accession_number, "accession_number_lower": normalized, **values}
    if session.bind is None:
        raise RuntimeError("Session is not bound to an engine.")

    dialect_name = session.bind.dialect.name
    if dialect_name == "postgresql":
        stmt_pg = pg_insert(APSDocument).values(**payload)
        update_values = {
            "url": stmt_pg.excluded.url,
            "is_package": stmt_pg.excluded.is_package,
            "is_stub": stmt_pg.excluded.is_stub,
            "document_date": stmt_pg.excluded.document_date,
            "date_added_timestamp": stmt_pg.excluded.date_added_timestamp,
            "document_type": stmt_pg.excluded.document_type,
            "docket_number": stmt_pg.excluded.docket_number,
            "title": stmt_pg.excluded.title,
            "raw_metadata_json": stmt_pg.excluded.raw_metadata_json,
            "last_seen_at": stmt_pg.excluded.last_seen_at,
            "last_modified_at": stmt_pg.excluded.last_modified_at,
        }
        session.execute(
            stmt_pg.on_conflict_do_update(index_elements=["accession_number"], set_=update_values)
        )
        return

    stmt_sqlite = sqlite_insert(APSDocument).values(**payload)
    update_values = {
        "url": stmt_sqlite.excluded.url,
        "is_package": stmt_sqlite.excluded.is_package,
        "is_stub": stmt_sqlite.excluded.is_stub,
        "document_date": stmt_sqlite.excluded.document_date,
        "date_added_timestamp": stmt_sqlite.excluded.date_added_timestamp,
        "document_type": stmt_sqlite.excluded.document_type,
        "docket_number": stmt_sqlite.excluded.docket_number,
        "title": stmt_sqlite.excluded.title,
        "raw_metadata_json": stmt_sqlite.excluded.raw_metadata_json,
        "last_seen_at": stmt_sqlite.excluded.last_seen_at,
        "last_modified_at": stmt_sqlite.excluded.last_modified_at,
    }
    session.execute(
        stmt_sqlite.on_conflict_do_update(index_elements=["accession_number"], set_=update_values)
    )


def upsert_query(session: Session, query_id: str, values: dict[str, Any]) -> None:
    """Upsert a query definition."""

    if session.bind is None:
        raise RuntimeError("Session is not bound to an engine.")
    payload = {"query_id": query_id, **values}
    dialect_name = session.bind.dialect.name
    if dialect_name == "postgresql":
        stmt_pg = pg_insert(APSQuery).values(**payload)
        update_values = {
            "name": stmt_pg.excluded.name,
            "definition_json": stmt_pg.excluded.definition_json,
            "enabled": stmt_pg.excluded.enabled,
            "updated_at": datetime.utcnow(),
        }
        session.execute(
            stmt_pg.on_conflict_do_update(index_elements=["query_id"], set_=update_values)
        )
        return

    stmt_sqlite = sqlite_insert(APSQuery).values(**payload)
    update_values = {
        "name": stmt_sqlite.excluded.name,
        "definition_json": stmt_sqlite.excluded.definition_json,
        "enabled": stmt_sqlite.excluded.enabled,
        "updated_at": datetime.utcnow(),
    }
    session.execute(
        stmt_sqlite.on_conflict_do_update(index_elements=["query_id"], set_=update_values)
    )


def get_or_create_query_state(
    session: Session, query_id: str, defaults: dict[str, Any]
) -> APSQueryState:
    """Fetch or create query state."""

    state = session.scalar(select(APSQueryState).where(APSQueryState.query_id == query_id))
    if state is not None:
        return state
    state = APSQueryState(query_id=query_id, **defaults)
    session.add(state)
    session.flush()
    return state


def insert_discoveries(session: Session, discoveries: Iterable[APSDiscovery]) -> None:
    """Insert discovery rows."""

    session.add_all(list(discoveries))


def insert_query_run(session: Session, query_run: APSQueryRun) -> None:
    """Insert a query run."""

    session.add(query_run)
    session.flush()
