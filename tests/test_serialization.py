import pytest

from aps_etl.registry import QueryRegistry, QuerySpec


def test_registry_serialization() -> None:
    registry = QueryRegistry([QuerySpec(name="jobs", sql="SELECT * FROM jobs")])

    payload = registry.to_dict()

    assert payload == {
        "queries": [
            {
                "name": "jobs",
                "sql": "SELECT * FROM jobs",
                "parameters": [],
            }
        ]
    }


def test_record_serialization() -> None:
    pytest.importorskip("pydantic")
    from aps_etl.models import APSRecord

    record = APSRecord(record_id="123", payload={"status": "open"})

    assert record.to_serializable() == {
        "record_id": "123",
        "payload": {"status": "open"},
    }
