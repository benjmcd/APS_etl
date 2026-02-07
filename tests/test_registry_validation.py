import textwrap
from pathlib import Path

import jsonschema
import pytest

from aps_etl.registry import load_registry_payload


def test_registry_schema_accepts_valid_payload(tmp_path: Path) -> None:
    schema_path = tmp_path / "schema.json"
    registry_path = tmp_path / "queries.yaml"
    schema_contents = Path("registry_schema.json").read_text(encoding="utf-8")
    schema_path.write_text(schema_contents, encoding="utf-8")
    registry_path.write_text(
        """
version: 1
queries:
  - name: "sample"
    q: "NuScale"
""",
        encoding="utf-8",
    )

    payload = load_registry_payload(registry_path, schema_path)

    assert payload["version"] == 1


def test_registry_schema_rejects_invalid_payload(tmp_path: Path) -> None:
    schema_path = tmp_path / "schema.json"
    registry_path = tmp_path / "queries.yaml"
    schema_contents = Path("registry_schema.json").read_text(encoding="utf-8")
    schema_path.write_text(schema_contents, encoding="utf-8")
    registry_path.write_text(
        """
version: 2
queries: []
""",
        encoding="utf-8",
    )

    with pytest.raises(jsonschema.ValidationError):
        load_registry_payload(registry_path, schema_path)


@pytest.mark.parametrize(
    "filters_yaml",
    [
        """
filters_and:
  - field: DocumentType
    value: "Inspection Report"
""",
        """
filters_and:
  - type: text
    field: DocumentType
    operator: bogus
    value: "Inspection Report"
""",
        """
filters_and:
  - type: date_range
    field: DateAddedTimestamp
    le: "2024-01-31"
""",
    ],
)
def test_registry_schema_rejects_invalid_filters(tmp_path: Path, filters_yaml: str) -> None:
    schema_path = tmp_path / "schema.json"
    registry_path = tmp_path / "queries.yaml"
    schema_contents = Path("registry_schema.json").read_text(encoding="utf-8")
    schema_path.write_text(schema_contents, encoding="utf-8")
    registry_path.write_text(
        f"""
version: 1
queries:
  - name: "sample"
    q: "NuScale"
{textwrap.indent(filters_yaml, "    ")}
""",
        encoding="utf-8",
    )

    with pytest.raises(jsonschema.ValidationError):
        load_registry_payload(registry_path, schema_path)
