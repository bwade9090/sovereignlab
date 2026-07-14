"""Deterministically export public JSON Schema documents."""

import json
from pathlib import Path

from sovereignlab.schemas.benchmark import BenchmarkRecord
from sovereignlab.schemas.source import SourceManifest

SCHEMA_MODELS = {
    "benchmark-record-v1.schema.json": BenchmarkRecord,
    "source-manifest-v1.schema.json": SourceManifest,
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
