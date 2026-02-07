"""Database model placeholders for APS ETL."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class APSRecord(BaseModel):
    """Example data record for APS ETL pipelines."""

    record_id: str = Field(..., description="Primary identifier from APS.")
    payload: dict[str, object] = Field(default_factory=dict)

    def to_serializable(self) -> dict[str, Any]:
        """Serialize the record payload."""

        return self.model_dump()
