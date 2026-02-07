"""Query registry and canonical query compilation."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import jsonschema
import yaml  # type: ignore[import-untyped]


@dataclass(frozen=True)
class Libraries:
    """Library inclusion configuration."""

    legacy: bool
    main: bool


@dataclass(frozen=True)
class SortSpec:
    """Sorting configuration."""

    field: str
    direction: str


@dataclass(frozen=True)
class Filter:
    """Canonical filter."""

    field: str
    operator: str | None
    value: str | list[str]


@dataclass(frozen=True)
class QueryDefinition:
    """Canonical query definition."""

    query_id: str
    name: str
    q: str
    filters_and: tuple[Filter, ...]
    filters_or: tuple[Filter, ...]
    libraries: Libraries
    sort: SortSpec
    content: bool
    safety_buffer_days: int
    wire_format: str | None
    enabled: bool

    def to_definition_payload(self) -> dict[str, Any]:
        """Serialize the definition for persistence."""

        return {
            "query_id": self.query_id,
            "name": self.name,
            "q": self.q,
            "filters_and": [filter_to_payload(filter_) for filter_ in self.filters_and],
            "filters_or": [filter_to_payload(filter_) for filter_ in self.filters_or],
            "libraries": {"legacy": self.libraries.legacy, "main": self.libraries.main},
            "sort": {"field": self.sort.field, "dir": self.sort.direction},
            "content": self.content,
            "safety_buffer_days": self.safety_buffer_days,
            "wire_format": self.wire_format,
            "enabled": self.enabled,
        }


def filter_to_payload(filter_: Filter) -> dict[str, Any]:
    """Serialize a filter for persistence."""

    payload: dict[str, Any] = {"field": filter_.field, "value": filter_.value}
    if filter_.operator is not None:
        payload["operator"] = filter_.operator
    return payload


def compile_date_range_filter(field: str, ge: str, le: str) -> Filter:
    """Compile a date range filter into the APS canonical filter."""

    value = f"({field} ge '{ge}' and {field} le '{le}')"
    return Filter(field=field, operator=None, value=value)


def load_registry_schema(schema_path: Path) -> dict[str, Any]:
    """Load registry JSON schema."""

    return yaml.safe_load(schema_path.read_text(encoding="utf-8"))


def load_registry_payload(registry_path: Path, schema_path: Path) -> dict[str, Any]:
    """Load and validate registry payload."""

    payload = yaml.safe_load(registry_path.read_text(encoding="utf-8")) or {}
    schema = load_registry_schema(schema_path)
    jsonschema.validate(instance=payload, schema=schema)
    return payload


def load_registry(
    registry_path: Path, schema_path: Path, *, allow_disabled: bool = True
) -> list[QueryDefinition]:
    """Load registry YAML and return canonical query definitions."""

    payload = load_registry_payload(registry_path, schema_path)

    defaults = payload.get("defaults", {})
    default_libraries = defaults.get("libraries", {})
    default_sort = defaults.get("sort", {})
    default_content = defaults.get("content", False)
    default_safety_buffer = defaults.get("safety_buffer_days", 3)
    default_wire_format = defaults.get("wire_format")

    queries: list[QueryDefinition] = []
    for query in payload.get("queries", []):
        libraries = query.get("libraries", default_libraries)
        sort = query.get("sort", default_sort)
        enabled = query.get("enabled", True)
        if not allow_disabled and not enabled:
            continue
        query_id = query.get("query_id") or query["name"]
        filters_and = compile_filters(query.get("filters_and", []))
        filters_or = compile_filters(query.get("filters_or", []))
        queries.append(
            QueryDefinition(
                query_id=query_id,
                name=query["name"],
                q=query.get("q", ""),
                filters_and=tuple(filters_and),
                filters_or=tuple(filters_or),
                libraries=Libraries(
                    legacy=bool(libraries.get("legacy", True)),
                    main=bool(libraries.get("main", True)),
                ),
                sort=SortSpec(
                    field=sort.get("field", "DateAddedTimestamp"),
                    direction=sort.get("dir", "DESC"),
                ),
                content=bool(query.get("content", default_content)),
                safety_buffer_days=int(query.get("safety_buffer_days", default_safety_buffer)),
                wire_format=query.get("wire_format", default_wire_format),
                enabled=enabled,
            )
        )
    return queries


def registry_version(registry_path: Path, schema_path: Path) -> str:
    """Return the registry schema version."""

    payload = load_registry_payload(registry_path, schema_path)
    return str(payload.get("version", "1"))


def compile_filters(filters: list[dict[str, Any]]) -> list[Filter]:
    """Compile registry filters into canonical filters."""

    compiled: list[Filter] = []
    for filter_item in filters:
        filter_type = filter_item.get("type", "text")
        field = filter_item["field"]
        if filter_type == "date_range":
            compiled.append(
                compile_date_range_filter(
                    field=field,
                    ge=filter_item["ge"],
                    le=filter_item["le"],
                )
            )
        else:
            compiled.append(
                Filter(
                    field=field,
                    operator=filter_item["operator"],
                    value=filter_item["value"],
                )
            )
    return compiled
