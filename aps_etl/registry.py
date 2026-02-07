"""Query registry placeholders for APS ETL."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass


@dataclass(frozen=True)
class QuerySpec:
    """Definition of a query registered for APS ETL."""

    name: str
    sql: str
    parameters: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, object]:
        """Serialize the query specification for persistence."""

        return {
            "name": self.name,
            "sql": self.sql,
            "parameters": list(self.parameters),
        }


@dataclass(frozen=True)
class DateRangeFilter:
    """Canonical date range filter definition."""

    field: str
    ge: str
    le: str

    def to_aps_filter(self) -> dict[str, str]:
        """Serialize to APS filter object for date ranges."""

        return {
            "field": self.field,
            "value": f"({self.field} ge '{self.ge}' and {self.field} le '{self.le}')",
        }


def compile_date_range_filter(field: str, ge: str, le: str) -> dict[str, str]:
    """Compile a date range filter into the APS filter wire format."""

    return DateRangeFilter(field=field, ge=ge, le=le).to_aps_filter()


class QueryRegistry:
    """Registry holding all APS queries."""

    def __init__(self, queries: Iterable[QuerySpec] | None = None) -> None:
        self._queries: list[QuerySpec] = list(queries or [])

    @property
    def queries(self) -> tuple[QuerySpec, ...]:
        """Return the registered queries."""

        return tuple(self._queries)

    def register(self, query: QuerySpec) -> None:
        """Register a new query."""

        self._queries.append(query)

    def validate(self) -> list[str]:
        """Validate registered queries and return a list of issues."""

        issues: list[str] = []
        seen: set[str] = set()
        for query in self._queries:
            if not query.name:
                issues.append("Query name is required.")
            if query.name in seen:
                issues.append(f"Duplicate query name: {query.name}.")
            seen.add(query.name)
            if not query.sql:
                issues.append(f"Query '{query.name}' is missing SQL.")
        return issues

    def to_dict(self) -> dict[str, list[dict[str, object]]]:
        """Serialize all query specs."""

        return {"queries": [query.to_dict() for query in self._queries]}
