"""The approved K-VINTAGE core: allocation, review state, evidence, and gold reproduction.

Every check is driven by the committed records, so a newly approved pair is covered as soon
as its batch file lands in ``data/benchmark/core/``.
"""

from collections.abc import Callable
from pathlib import Path

import pytest

from sovereignlab.execution import CallableToolRegistry
from sovereignlab.probes import EDITION_SPLITS
from sovereignlab.schemas import (
    AnnotationStatus,
    BenchmarkRecord,
    CoreAuthoringMatrix,
    LanguageCode,
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
    evidence_bundle: Callable[[list[BenchmarkRecord], CallableToolRegistry], object],
) -> None:
    # A vintage must cite its version's active ledger, so records are grouped by the evidence
    # version they are checked against.
    grouped = {version: [] for version in tool_registries}
    for record in RECORDS:
        grouped[_evidence_version(record, tool_registries)].append(record)

    for version, registry in tool_registries.items():
        evidence_bundle(grouped[version], registry)


def test_core_vintages_keep_each_oecd_edition_in_its_probe_split() -> None:
    # The core and the tier-2 probes share OECD editions, so an edition belongs to one split in
    # both tiers; otherwise training on probes would leak a core evaluation edition (ADR 0014).
    for record in RECORDS_WITH_TOOLS:
        for expectation in record.tool_expectations:
            if expectation.vintage is not None:
                edition = expectation.vintage.selected_edition
                assert record.split is EDITION_SPLITS[edition], record.record_id


@pytest.mark.parametrize(
    "record",
    RECORDS_WITH_TOOLS,
    ids=[record.record_id for record in RECORDS_WITH_TOOLS],
)
def test_the_offline_tools_reproduce_each_declared_gold(
    record: BenchmarkRecord,
    tool_registries: dict[int, CallableToolRegistry],
    assert_reproduced: Callable[[BenchmarkRecord, CallableToolRegistry], None],
) -> None:
    assert_reproduced(record, tool_registries[_evidence_version(record, tool_registries)])
