"""Keep public schemas and synthetic JSON examples synchronized with code."""

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest

from sovereignlab.schemas import (
    BenchmarkBundle,
    BenchmarkRecord,
    RightsCatalog,
    RightsInstrument,
    SeriesRightsDecision,
    SourceManifest,
)
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


def test_synthetic_rights_examples_form_a_valid_catalog() -> None:
    instrument = RightsInstrument.model_validate_json(
        (ROOT / "data" / "fixtures" / "rights_instrument.example.json").read_text(encoding="utf-8")
    )
    decision = SeriesRightsDecision.model_validate_json(
        (ROOT / "data" / "fixtures" / "series_rights_decision.example.json").read_text(
            encoding="utf-8"
        )
    )
    catalog = RightsCatalog(
        catalog_id="example-rights-catalog-001",
        recorded_at=datetime(2026, 7, 16, 9, 0, tzinfo=UTC),
        project_use_profile="noncommercial_public_research",
        instruments=(instrument,),
        decisions=(decision,),
    )

    assert catalog.instruments == (instrument,)
    assert catalog.decisions == (decision,)


def test_committed_ecos_rights_catalog_validates() -> None:
    catalog = RightsCatalog.model_validate_json(
        (ROOT / "data" / "rights" / "kor-rtd-rights-2026-07-16.json").read_text(encoding="utf-8")
    )

    assert catalog.catalog_id == "kor-rtd-rights-2026-07-16"
    assert {decision.decision_id for decision in catalog.decisions} == {
        "ecos-200y108-10601-rights-v1",
        "ecos-301y017-sa000-rights-v1",
    }
    assert all(decision.decision_state.value == "allowed" for decision in catalog.decisions)


def test_schema_export_is_deterministic(tmp_path: Path) -> None:
    first_paths = write_json_schemas(tmp_path)
    first_contents = {path.name: path.read_bytes() for path in first_paths}

    second_paths = write_json_schemas(tmp_path)
    second_contents = {path.name: path.read_bytes() for path in second_paths}

    assert first_paths == second_paths
    assert first_contents == second_contents
    assert all(content.endswith(b"\n") for content in second_contents.values())
