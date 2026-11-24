"""The approved K-VINTAGE core: allocation, review state, evidence, and gold reproduction.

Every check is driven by the committed records, so a newly approved pair is covered as soon
as its batch file lands in ``data/benchmark/core/``.
"""

from pathlib import Path

import pytest
from pydantic import TypeAdapter

from sovereignlab.execution import CallableToolRegistry, dispatch_tool_call
from sovereignlab.schemas import (
    AnnotationStatus,
    BenchmarkBundle,
    BenchmarkRecord,
    CoreAuthoringMatrix,
    LanguageCode,
    SourceManifest,
    ToolCall,
    ToolOutcomeStatus,
)

ROOT = Path(__file__).resolve().parents[2]
MATRIX = CoreAuthoringMatrix.model_validate_json(
    (ROOT / "data" / "benchmark" / "core-authoring-matrix-v1.json").read_bytes()
)
RECORDS = tuple(
    BenchmarkRecord.model_validate_json(line)
    for path in sorted((ROOT / "data" / "benchmark" / "core").glob("*.jsonl"))
    for line in path.read_text(encoding="utf-8").splitlines()
    if line
)
RECORDS_WITH_TOOLS = tuple(record for record in RECORDS if record.tool_expectations)
_TOOL_CALL = TypeAdapter(ToolCall)


def _evidence_version(record: BenchmarkRecord, registries: dict[int, CallableToolRegistry]) -> int:
    """Return the evidence version a record is checked against.

    A vintage gold was computed against one availability ledger, so the record belongs to the
    version whose active ledger it names. Every other record is checked against the latest
    version, which must still reproduce it.
    """

    ledgers = {
        expectation.vintage.ledger_id
        for expectation in record.tool_expectations
        if expectation.vintage is not None
    }
    if not ledgers:
        return max(registries)
    (ledger_id,) = ledgers
    (version,) = (
        version
        for version, registry in registries.items()
        if registry.stes_registry.active_ledger_id == ledger_id
    )
    return version


def test_every_core_record_fills_its_slot_in_the_frozen_matrix() -> None:
    pairs = {pair.pair_id: pair for pair in MATRIX.pairs}
    record_ids = [record.record_id for record in RECORDS]
    assert len(record_ids) == len(set(record_ids))

    for record in RECORDS:
        pair = pairs[record.parallel_group_id]
        expected_id = (
            pair.ko_record_id if record.language is LanguageCode.KOREAN else (pair.en_record_id)
        )
        assert record.record_id == expected_id
        assert record.split is pair.split, record.record_id
        assert record.expected_route is pair.expected_route, record.record_id
        assert record.evidence_group_id == pair.evidence_group_id, record.record_id

    # Pairs are approved whole: Korean and English together.
    authored = {record.parallel_group_id for record in RECORDS}
    for pair_id in authored:
        assert {pairs[pair_id].ko_record_id, pairs[pair_id].en_record_id} <= set(record_ids)


def test_every_core_record_carries_the_owner_review() -> None:
    for record in RECORDS:
        assert record.annotation.status is AnnotationStatus.APPROVED, record.record_id
        assert record.annotation.reviewed_by == "Hyungbae Cho", record.record_id
        assert "core" in record.tags, record.record_id


def test_core_and_its_evidence_form_one_valid_bundle_per_evidence_version(
    tool_registries: dict[int, CallableToolRegistry],
) -> None:
    # The bundle validator rejects post-cutoff evidence, unresolvable vintages, broken rights
    # links, and evidence shared across splits. A vintage must cite its version's active ledger,
    # so records are grouped by the evidence version they are checked against.
    documents = tuple(
        SourceManifest.model_validate_json(path.read_bytes())
        for path in sorted((ROOT / "data" / "manifests").glob("bok-outlook-*.json"))
    )
    grouped = {version: [] for version in tool_registries}
    for record in RECORDS:
        grouped[_evidence_version(record, tool_registries)].append(record)

    for version, registry in tool_registries.items():
        snapshots = tuple(
            artifact.manifest
            for entry in registry.snapshot_registry.entries
            for artifact in entry.artifacts
        )
        stes = registry.stes_registry
        archives = tuple(
            entry.data_artifact.manifest
            for entry in stes.entries
            if entry.data_artifact is not None
        )
        support = tuple(artifact.manifest for artifact in stes.support_artifacts)
        BenchmarkBundle(
            sources=(*documents, *snapshots, *archives, *support),
            records=tuple(grouped[version]),
            availability_ledgers=tuple(artifact.ledger for artifact in stes.ledger_artifacts),
            rights_catalogs=tuple(artifact.catalog for artifact in stes.catalog_artifacts),
        )


@pytest.mark.parametrize(
    "record",
    RECORDS_WITH_TOOLS,
    ids=[record.record_id for record in RECORDS_WITH_TOOLS],
)
def test_the_offline_tools_reproduce_each_declared_gold(
    record: BenchmarkRecord,
    tool_registries: dict[int, CallableToolRegistry],
) -> None:
    registry = tool_registries[_evidence_version(record, tool_registries)]
    for index, expectation in enumerate(record.tool_expectations):
        call = _TOOL_CALL.validate_python(
            {
                "call_id": f"{record.record_id}-call-{index}",
                "tool_name": expectation.tool_name,
                "arguments": expectation.arguments,
            }
        )
        assert call.arguments.as_of == record.as_of

        result = dispatch_tool_call(call=call, registry=registry)

        assert result.status is ToolOutcomeStatus.SUCCESS
        observed = result.payload.model_dump(mode="json")
        observed.update(observed.pop("observation"))
        assert observed["source_id"] == expectation.source_id
        declared = dict(fact.split("=", maxsplit=1) for fact in expectation.expected_facts)
        assert {key: str(observed[key]) for key in declared} == declared
        if expectation.vintage is not None:
            assert observed["ledger_id"] == expectation.vintage.ledger_id
            assert observed["selected_edition"] == expectation.vintage.selected_edition
