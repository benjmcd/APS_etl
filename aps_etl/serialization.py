"""Serialization helpers for APS queries."""

from __future__ import annotations

from typing import Any

from aps_etl.registry import Filter, QueryDefinition


def serialize_query(query: QueryDefinition, wire_format: str, skip: int) -> dict[str, Any]:
    """Serialize a canonical query into APS wire format A or B."""

    if wire_format == "A":
        return {
            "q": query.q,
            "filters": [serialize_filter_a(filter_) for filter_ in query.filters_and],
            "anyFilters": [serialize_filter_a(filter_) for filter_ in query.filters_or],
            "legacyLibFilter": query.libraries.legacy,
            "mainLibFilter": query.libraries.main,
            "sort": query.sort.field,
            "sortDirection": 1 if query.sort.direction == "DESC" else 0,
            "skip": skip,
            "content": query.content,
        }
    if wire_format == "B":
        return {
            "q": query.q,
            "filters": [serialize_filter_b(filter_) for filter_ in query.filters_and],
            "anyFilters": [serialize_filter_b(filter_) for filter_ in query.filters_or],
            "legacyLibFilter": query.libraries.legacy,
            "mainLibFilter": query.libraries.main,
            "sort": query.sort.field,
            "sortDirection": query.sort.direction,
            "skip": skip,
            "content": query.content,
        }
    raise ValueError(f"Unsupported wire format: {wire_format}")


def serialize_filter_a(filter_: Filter) -> dict[str, Any]:
    """Serialize a filter using APS wire format A."""

    payload: dict[str, Any] = {"field": filter_.field, "value": filter_.value}
    if filter_.operator is not None:
        payload["operator"] = filter_.operator
    return payload


def serialize_filter_b(filter_: Filter) -> dict[str, Any]:
    """Serialize a filter using APS wire format B."""

    payload: dict[str, Any] = {"name": filter_.field, "value": filter_.value}
    if filter_.operator is not None:
        payload["operator"] = filter_.operator
    elif isinstance(filter_.value, str) and " ge " in filter_.value and " le " in filter_.value:
        payload["operator"] = "inRange"
        cleaned = filter_.value.strip("()")
        tokens = cleaned.split(" and ")
        values: dict[str, str] = {}
        for token in tokens:
            token = token.strip()
            if " ge " in token:
                values["ge"] = token.split(" ge ")[-1].strip().strip("'")
            elif " le " in token:
                values["le"] = token.split(" le ")[-1].strip().strip("'")
        payload["value"] = [values["ge"], values["le"]]
    return payload
