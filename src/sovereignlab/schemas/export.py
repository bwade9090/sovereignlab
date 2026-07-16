"""Deterministically export public JSON Schema documents."""

import json
from pathlib import Path

from sovereignlab.schemas.availability import EditionAvailabilityLedger
from sovereignlab.schemas.benchmark import BenchmarkRecord
from sovereignlab.schemas.rights import RightsCatalog, RightsInstrument, SeriesRightsDecision
from sovereignlab.schemas.source import SourceManifest

SCHEMA_MODELS = {
    "benchmark-record-v2.schema.json": BenchmarkRecord,
    "edition-availability-ledger-v1.schema.json": EditionAvailabilityLedger,
    "rights-catalog-v1.schema.json": RightsCatalog,
    "rights-instrument-v1.schema.json": RightsInstrument,
    "series-rights-decision-v1.schema.json": SeriesRightsDecision,
    "source-manifest-v2.schema.json": SourceManifest,
}


def write_json_schemas(output_directory: Path) -> tuple[Path, ...]:
    """Write stable, sorted JSON Schema files and return their paths."""

    output_directory.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for filename, model in SCHEMA_MODELS.items():
        output_path = output_directory / filename
        serialized = json.dumps(model.model_json_schema(), indent=2, sort_keys=True)
        output_path.write_text(f"{serialized}\n", encoding="utf-8", newline="\n")
        written.append(output_path)
    return tuple(written)
