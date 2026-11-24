"""Shared checks for benchmark records, core and probes alike."""

from collections.abc import Callable, Iterable
from pathlib import Path

import pytest
from pydantic import TypeAdapter

from sovereignlab.execution import CallableToolRegistry, dispatch_tool_call
from sovereignlab.schemas import (
    BenchmarkBundle,
    BenchmarkRecord,
    SourceManifest,
    ToolCall,
    ToolOutcomeStatus,
)

ROOT = Path(__file__).resolve().parents[2]
_TOOL_CALL = TypeAdapter(ToolCall)


def _assert_reproduced(record: BenchmarkRecord, registry: CallableToolRegistry) -> None:
    """Run each tool expectation and check that the result carries every declared fact."""

    for index, expectation in enumerate(record.tool_expectations):
        call = _TOOL_CALL.validate_python(
            {
                "call_id": f"{record.record_id}-call-{index}",
                "tool_name": expectation.tool_name,
                "arguments": expectation.arguments,
            }
        )
        assert call.arguments.as_of == record.as_of, record.record_id

        result = dispatch_tool_call(call=call, registry=registry)

        assert result.status is ToolOutcomeStatus.SUCCESS, record.record_id
        observed = result.payload.model_dump(mode="json")
        observed.update(observed.pop("observation"))
        assert observed["source_id"] == expectation.source_id, record.record_id
        declared = dict(fact.split("=", maxsplit=1) for fact in expectation.expected_facts)
        assert {key: str(observed[key]) for key in declared} == declared, record.record_id
        if expectation.vintage is not None:
            assert observed["ledger_id"] == expectation.vintage.ledger_id
            assert observed["selected_edition"] == expectation.vintage.selected_edition


def _evidence_bundle(
    records: Iterable[BenchmarkRecord], registry: CallableToolRegistry
) -> BenchmarkBundle:
    """Validate records with the document manifests and everything one evidence version pins.

    The bundle validator rejects post-cutoff evidence, unresolvable vintages, broken rights
    links, and evidence shared across splits.
    """

    documents = tuple(
        SourceManifest.model_validate_json(path.read_bytes())
        for path in sorted((ROOT / "data" / "manifests").glob("bok-outlook-*.json"))
    )
    snapshots = tuple(
        artifact.manifest
        for entry in registry.snapshot_registry.entries
        for artifact in entry.artifacts
    )
    stes = registry.stes_registry
    archives = tuple(
        entry.data_artifact.manifest for entry in stes.entries if entry.data_artifact is not None
    )
    support = tuple(artifact.manifest for artifact in stes.support_artifacts)
    return BenchmarkBundle(
        sources=(*documents, *snapshots, *archives, *support),
        records=tuple(records),
        availability_ledgers=tuple(artifact.ledger for artifact in stes.ledger_artifacts),
        rights_catalogs=tuple(artifact.catalog for artifact in stes.catalog_artifacts),
    )


@pytest.fixture(scope="session")
def assert_reproduced() -> Callable[[BenchmarkRecord, CallableToolRegistry], None]:
    """Check that the offline tools reproduce a record's declared gold."""

    return _assert_reproduced


@pytest.fixture(scope="session")
def evidence_bundle() -> Callable[[Iterable[BenchmarkRecord], CallableToolRegistry], object]:
    """Build, and so validate, one bundle of records and their evidence."""

    return _evidence_bundle
