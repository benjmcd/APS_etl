"""Create Milestone 1 tables.

Revision ID: 0001_milestone1
Revises:
Create Date: 2025-02-14 00:00:00.000000
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op


revision = "0001_milestone1"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "aps_query",
        sa.Column("query_id", sa.Text(), primary_key=True),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("definition_json", sa.JSON(), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_table(
        "aps_query_state",
        sa.Column(
            "query_id",
            sa.Text(),
            sa.ForeignKey("aps_query.query_id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("last_seen_date", sa.Date(), nullable=False),
        sa.Column("safety_buffer_days", sa.Integer(), nullable=False, server_default="3"),
        sa.Column("wire_format", sa.Text(), nullable=True),
        sa.Column("wire_format_verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_table(
        "aps_query_run",
        sa.Column("run_id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "query_id",
            sa.Text(),
            sa.ForeignKey("aps_query.query_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "status",
            sa.Enum("success", "partial", "failed", name="query_run_status"),
            nullable=False,
        ),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("wire_format", sa.Text(), nullable=False),
        sa.Column("request_fingerprint", sa.Text(), nullable=False),
        sa.Column("schema_version", sa.Text(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
    )
    op.create_table(
        "aps_document",
        sa.Column("accession_number", sa.Text(), primary_key=True),
        sa.Column("accession_number_lower", sa.Text(), nullable=False, unique=True),
        sa.Column("url", sa.Text(), nullable=True),
        sa.Column("is_package", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("is_stub", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("document_date", sa.Date(), nullable=True),
        sa.Column("date_added_timestamp", sa.DateTime(timezone=True), nullable=True),
        sa.Column("document_type", sa.JSON(), nullable=True),
        sa.Column("docket_number", sa.JSON(), nullable=True),
        sa.Column("title", sa.Text(), nullable=True),
        sa.Column("raw_metadata_json", sa.JSON(), nullable=True),
        sa.Column("first_seen_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("last_modified_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_table(
        "aps_discovery",
        sa.Column(
            "run_id",
            sa.Integer(),
            sa.ForeignKey("aps_query_run.run_id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "accession_number",
            sa.Text(),
            sa.ForeignKey("aps_document.accession_number", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("skip_value", sa.Integer(), nullable=False),
        sa.Column("page_number", sa.Integer(), nullable=False),
        sa.Column("search_score", sa.Float(), nullable=True),
        sa.Column("highlights_json", sa.JSON(), nullable=True),
        sa.Column("semantic_search_json", sa.JSON(), nullable=True),
        sa.Column("discovered_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("aps_discovery")
    op.drop_table("aps_document")
    op.drop_table("aps_query_run")
    op.drop_table("aps_query_state")
    op.drop_table("aps_query")
    op.execute("DROP TYPE IF EXISTS query_run_status")
