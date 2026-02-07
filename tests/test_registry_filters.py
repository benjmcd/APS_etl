from aps_etl.registry import compile_date_range_filter


def test_compile_date_range_filter() -> None:
    compiled = compile_date_range_filter(
        field="DateAddedTimestamp",
        ge="2025-01-01",
        le="2025-01-31",
    )

    assert compiled.field == "DateAddedTimestamp"
    assert compiled.operator is None
    assert compiled.value == (
        "(DateAddedTimestamp ge '2025-01-01' and DateAddedTimestamp le '2025-01-31')"
    )
