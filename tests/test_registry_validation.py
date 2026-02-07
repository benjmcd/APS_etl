from aps_etl.registry import QueryRegistry, QuerySpec


def test_registry_validation_flags_duplicates() -> None:
    registry = QueryRegistry(
        [
            QuerySpec(name="jobs", sql="SELECT * FROM jobs"),
            QuerySpec(name="jobs", sql="SELECT * FROM jobs"),
        ]
    )

    issues = registry.validate()

    assert "Duplicate query name: jobs." in issues


def test_registry_validation_flags_missing_sql() -> None:
    registry = QueryRegistry([QuerySpec(name="empty", sql="")])

    issues = registry.validate()

    assert "Query 'empty' is missing SQL." in issues
