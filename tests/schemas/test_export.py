"""Keep public schemas and synthetic JSON examples synchronized with code."""

import json
from pathlib import Path

import pytest

from sovereignlab.schemas import BenchmarkBundle, BenchmarkRecord, SourceManifest
from sovereignlab.schemas.export import SCHEMA_MODELS, write_json_schemas

ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.parametrize(("filename", "model"), SCHEMA_MODELS.items())
def test_committed_json_schema_matches_model(filename: str, model: type) -> None:
    committed = json.loads((ROOT / "data" / "schemas" / filename).read_text(encoding="utf-8"))

    assert committed == model.model_json_schema()


def test_synthetic_json_examples_form_a_valid_bundle() -> None:
    source = SourceManifest.model_validate_json(
        (ROOT / "data" / "fixtures" / "source_manifest.example.json").read_text(encoding="utf-8")
    )
    record = BenchmarkRecord.model_validate_json(
        (ROOT / "data" / "fixtures" / "benchmark_record.example.json").read_text(encoding="utf-8")
    )

    bundle = BenchmarkBundle(sources=(source,), records=(record,))

    assert bundle.records[0].record_id == "example-doc-en-001"


def test_schema_export_is_deterministic(tmp_path: Path) -> None:
    first_paths = write_json_schemas(tmp_path)
    first_contents = {path.name: path.read_bytes() for path in first_paths}

    second_paths = write_json_schemas(tmp_path)
    second_contents = {path.name: path.read_bytes() for path in second_paths}

    assert first_paths == second_paths
    assert first_contents == second_contents
    assert all(content.endswith(b"\n") for content in second_contents.values())
