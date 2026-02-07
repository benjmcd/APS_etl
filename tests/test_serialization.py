from aps_etl.registry import Filter, Libraries, QueryDefinition, SortSpec
from aps_etl.serialization import serialize_query


def test_wire_format_a_serialization() -> None:
    query = QueryDefinition(
        query_id="test",
        name="test",
        q="NuScale",
        filters_and=(Filter(field="DocumentType", operator="contains", value="Report"),),
        filters_or=(),
        libraries=Libraries(legacy=True, main=True),
        sort=SortSpec(field="DateAddedTimestamp", direction="DESC"),
        content=False,
        safety_buffer_days=3,
        wire_format=None,
        enabled=True,
    )

    payload = serialize_query(query, wire_format="A", skip=0)

    assert payload["filters"][0]["field"] == "DocumentType"
    assert payload["sortDirection"] == 1


def test_wire_format_b_serialization() -> None:
    query = QueryDefinition(
        query_id="test",
        name="test",
        q="NuScale",
        filters_and=(Filter(field="DocumentDate", operator="equals", value="2024-01-01"),),
        filters_or=(),
        libraries=Libraries(legacy=True, main=True),
        sort=SortSpec(field="DateAddedTimestamp", direction="DESC"),
        content=False,
        safety_buffer_days=3,
        wire_format=None,
        enabled=True,
    )

    payload = serialize_query(query, wire_format="B", skip=5)

    assert payload["filters"][0]["name"] == "DocumentDate"
    assert payload["sortDirection"] == "DESC"
    assert payload["skip"] == 5
