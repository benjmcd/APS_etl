"""SQLAlchemy models for APS ETL Milestone 1."""

from __future__ import annotations

import enum
from datetime import date, datetime
from typing import Any

from sqlalchemy import (
    JSON,
    Boolean,
    Date,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    Text,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Base class for all ORM models."""


class QueryRunStatus(enum.StrEnum):
    """Status for APS query runs."""

    SUCCESS = "success"
    PARTIAL = "partial"
    FAILED = "failed"


JsonValue = dict[str, Any] | list[Any]
JsonValueOrNone = JsonValue | None


class APSQuery(Base):
    """Registered APS query definitions."""

    __tablename__ = "aps_query"

    query_id: Mapped[str] = mapped_column(Text, primary_key=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    definition_json: Mapped[JsonValue] = mapped_column(JSON, nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    state: Mapped[APSQueryState] = relationship(back_populates="query", uselist=False)
    runs: Mapped[list[APSQueryRun]] = relationship(back_populates="query")


class APSQueryState(Base):
    """Per-query state for incremental runs and wire-format detection."""

    __tablename__ = "aps_query_state"

    query_id: Mapped[str] = mapped_column(
        Text, ForeignKey("aps_query.query_id", ondelete="CASCADE"), primary_key=True
    )
    last_seen_date: Mapped[date] = mapped_column(Date, nullable=False)
    safety_buffer_days: Mapped[int] = mapped_column(Integer, nullable=False, default=3)
    wire_format: Mapped[str | None] = mapped_column(Text, nullable=True)
    wire_format_verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    query: Mapped[APSQuery] = relationship(back_populates="state")


class APSQueryRun(Base):
    """Execution metadata for a query run."""

    __tablename__ = "aps_query_run"

    run_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    query_id: Mapped[str] = mapped_column(
        Text, ForeignKey("aps_query.query_id", ondelete="CASCADE"), nullable=False
    )
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[QueryRunStatus] = mapped_column(Enum(QueryRunStatus), nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text)
    wire_format: Mapped[str] = mapped_column(Text, nullable=False)
    request_fingerprint: Mapped[str] = mapped_column(Text, nullable=False)
    schema_version: Mapped[str] = mapped_column(Text, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)

    query: Mapped[APSQuery] = relationship(back_populates="runs")
    discoveries: Mapped[list[APSDiscovery]] = relationship(back_populates="run")


class APSDocument(Base):
    """APS document metadata."""

    __tablename__ = "aps_document"

    accession_number: Mapped[str] = mapped_column(Text, primary_key=True)
    accession_number_lower: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    url: Mapped[str | None] = mapped_column(Text)
    is_package: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_stub: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    document_date: Mapped[date | None] = mapped_column(Date)
    date_added_timestamp: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    document_type: Mapped[JsonValueOrNone] = mapped_column(JSON)
    docket_number: Mapped[JsonValueOrNone] = mapped_column(JSON)
    title: Mapped[str | None] = mapped_column(Text)
    raw_metadata_json: Mapped[JsonValueOrNone] = mapped_column(JSON)
    first_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    last_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    last_modified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    discoveries: Mapped[list[APSDiscovery]] = relationship(back_populates="document")


class APSDiscovery(Base):
    """Search result discovery rows."""

    __tablename__ = "aps_discovery"

    run_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("aps_query_run.run_id", ondelete="CASCADE"), primary_key=True
    )
    accession_number: Mapped[str] = mapped_column(
        Text, ForeignKey("aps_document.accession_number", ondelete="CASCADE"), primary_key=True
    )
    skip_value: Mapped[int] = mapped_column(Integer, nullable=False)
    page_number: Mapped[int] = mapped_column(Integer, nullable=False)
    search_score: Mapped[float | None] = mapped_column(Float)
    highlights_json: Mapped[JsonValueOrNone] = mapped_column(JSON)
    semantic_search_json: Mapped[JsonValueOrNone] = mapped_column(JSON)
    discovered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    run: Mapped[APSQueryRun] = relationship(back_populates="discoveries")
    document: Mapped[APSDocument] = relationship(back_populates="discoveries")
