"""Search-only runner for APS ETL Milestone 1."""

from __future__ import annotations

from collections.abc import Iterable
from datetime import date, datetime
from pathlib import Path
from typing import Any

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from aps_etl.canonical import request_fingerprint
from aps_etl.client import APSClient
from aps_etl.db import (
    create_session_factory,
    get_or_create_query_state,
    insert_discoveries,
    insert_query_run,
    upsert_document,
    upsert_query,
)
from aps_etl.models import APSDiscovery, APSQueryRun, QueryRunStatus
from aps_etl.registry import QueryDefinition, load_registry, registry_version
from aps_etl.serialization import serialize_query
from aps_etl.settings import Settings


def build_client(settings: Settings) -> APSClient:
    """Build an APS client."""

    return APSClient(
        base_url=settings.aps_base_url,
        api_key=settings.aps_primary_key,
        timeout_s=settings.request_timeout_s,
        retry_max_attempts=settings.retry_max_attempts,
        retry_min_wait_s=settings.retry_min_wait_s,
        retry_max_wait_s=settings.retry_max_wait_s,
    )


def load_queries(registry_path: Path, schema_path: Path) -> list[QueryDefinition]:
    """Load enabled queries from registry."""

    return load_registry(registry_path, schema_path, allow_disabled=False)


def run_all_queries(
    settings: Settings,
    *,
    registry_path: Path,
    schema_path: Path,
) -> None:
    """Run all enabled queries in the registry."""

    engine = create_engine(settings.database_url, future=True)
    session_factory = create_session_factory(engine)
    schema_version = registry_version(registry_path, schema_path)
    queries = load_queries(registry_path, schema_path)
    client = build_client(settings)

    with session_factory() as session:
        for query in queries:
            run_query(
                session=session,
                client=client,
                query=query,
                schema_version=schema_version,
                max_pages=settings.max_pages_per_window,
            )
        session.commit()


def run_query(
    *,
    session: Session,
    client: APSClient,
    query: QueryDefinition,
    schema_version: str,
    max_pages: int,
) -> None:
    """Run a single query with pagination."""

    upsert_query(
        session,
        query.query_id,
        {
            "name": query.name,
            "definition_json": query.to_definition_payload(),
            "enabled": query.enabled,
        },
    )
    state = get_or_create_query_state(
        session,
        query.query_id,
        {
            "last_seen_date": date.today(),
            "safety_buffer_days": query.safety_buffer_days,
            "wire_format": query.wire_format,
        },
    )
    wire_format = state.wire_format or client.probe_wire_format(query)
    state.wire_format = wire_format
    state.wire_format_verified_at = datetime.utcnow()

    base_payload = serialize_query(query, wire_format=wire_format, skip=0)
    fingerprint = request_fingerprint(
        method="POST",
        url=f"{client.base_url}/aps/api/search",
        wire_format=wire_format,
        body=base_payload,
    )
    query_run = APSQueryRun(
        query_id=query.query_id,
        status=QueryRunStatus.SUCCESS,
        wire_format=wire_format,
        request_fingerprint=fingerprint,
        schema_version=schema_version,
    )
    insert_query_run(session, query_run)
    try:
        skip = 0
        page_number = 0
        total_pages = 0
        while True:
            if total_pages >= max_pages:
                query_run.status = QueryRunStatus.PARTIAL
                query_run.notes = "Page cap reached for window."
                break
            payload = serialize_query(query, wire_format=wire_format, skip=skip)
            response = client.search(payload)
            results = response.get("results", [])
            if not results:
                break
            page_number += 1
            discoveries = build_discoveries(results, query_run.run_id, skip, page_number, session)
            insert_discoveries(session, discoveries)
            skip += len(results)
            total_pages += 1
    except Exception as exc:  # pragma: no cover - defensive status setting
        query_run.status = QueryRunStatus.FAILED
        query_run.error_message = str(exc)
        raise
    finally:
        query_run.ended_at = datetime.utcnow()


def build_discoveries(
    results: Iterable[dict[str, Any]],
    run_id: int,
    skip_value: int,
    page_number: int,
    session: Session,
) -> list[APSDiscovery]:
    """Create discovery rows and ensure document stubs exist."""

    discoveries: list[APSDiscovery] = []
    for result in results:
        document = result.get("document", {})
        accession = document.get("AccessionNumber")
        if not accession:
            continue
        is_package = str(document.get("IsPackage", "No")).lower() in {"yes", "true", "1"}
        upsert_document(
            session,
            accession,
            {
                "url": document.get("Url"),
                "is_package": is_package,
                "is_stub": True,
                "document_date": parse_date(document.get("DocumentDate")),
                "date_added_timestamp": parse_datetime(document.get("DateAddedTimestamp")),
                "document_type": normalize_json_value(document.get("DocumentType")),
                "docket_number": normalize_json_value(document.get("DocketNumber")),
                "title": document.get("DocumentTitle"),
                "raw_metadata_json": document,
                "last_seen_at": datetime.utcnow(),
            },
        )
        discoveries.append(
            APSDiscovery(
                run_id=run_id,
                accession_number=accession,
                skip_value=skip_value,
                page_number=page_number,
                search_score=result.get("score"),
                highlights_json=result.get("highlights"),
                semantic_search_json=result.get("semanticSearch"),
            )
        )
    return discoveries


def parse_date(value: str | None) -> date | None:
    """Parse a YYYY-MM-DD date."""

    if not value:
        return None
    return datetime.strptime(value, "%Y-%m-%d").date()


def parse_datetime(value: str | None) -> datetime | None:
    """Parse a YYYY-MM-DD HH:MM timestamp."""

    if not value:
        return None
    return datetime.strptime(value, "%Y-%m-%d %H:%M")


def normalize_json_value(value: Any) -> list[Any] | None:
    """Normalize values to list when appropriate."""

    if value is None:
        return None
    if isinstance(value, list):
        return value
    return [value]
