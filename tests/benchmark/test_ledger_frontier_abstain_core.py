"""Contract and evidence checks for the approved kv-core-abstain-05 pair."""

from datetime import date, timedelta
from pathlib import Path

from sovereignlab.schemas import (
    AnnotationStatus,
    BenchmarkBundle,
    BenchmarkRecord,
    BenchmarkSplit,
    CoreAuthoringMatrix,
    EditionAbstentionReason,
    EditionAvailabilityLedger,
    EvidenceRoute,
    RightsCatalog,
)

ROOT = Path(__file__).resolve().parents[2]
MATRIX_PATH = ROOT / "data" / "benchmark" / "core-authoring-matrix-v1.json"
CORE_DIRECTORY = ROOT / "data" / "benchmark" / "core"
BATCH_PATH = CORE_DIRECTORY / "core-batch-009.jsonl"
DRAFT_PATH = ROOT / "data" / "benchmark" / "drafts" / "core-draft-009.jsonl"
RIGHTS_CATALOG_ID = "kor-rtd-rights-2026-07-17"
CLI_SOURCE_ID = "oecd-stes-cli-kor-li-aa-20260717t115302688498z"
LEDGER_ID = "oecd-stes-ledger-20260717t115242998550z"
AS_OF = date(2026, 8, 15)


def _records(path: Path) -> tuple[BenchmarkRecord, ...]:
    return tuple(
        BenchmarkRecord.model_validate_json(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line
    )


def _core_records() -> tuple[BenchmarkRecord, ...]:
    return _records(BATCH_PATH)


def _catalog() -> RightsCatalog:
    return RightsCatalog.model_validate_json(
        (ROOT / "data" / "rights" / f"{RIGHTS_CATALOG_ID}.json").read_text(encoding="utf-8")
    )


def _ledger() -> EditionAvailabilityLedger:
    return EditionAvailabilityLedger.model_validate_json(
        (ROOT / "data" / "availability" / f"{LEDGER_ID}.json").read_text(encoding="utf-8")
    )


def test_approved_pair_matches_the_frozen_allocation_and_review_metadata() -> None:
    matrix = CoreAuthoringMatrix.model_validate_json(MATRIX_PATH.read_text(encoding="utf-8"))
    pair = next(item for item in matrix.pairs if item.pair_id == "kv-core-abstain-05")
    records = _core_records()

    assert not DRAFT_PATH.exists()
    assert tuple(record.record_id for record in records) == (
        pair.ko_record_id,
        pair.en_record_id,
    )
    assert tuple(record.language.value for record in records) == ("ko", "en")
    assert pair.data_unit_ids == ()
    assert pair.document_unit_ids == ()
    assert all(record.split is pair.split is BenchmarkSplit.TEST for record in records)
    assert all(
        record.expected_route is pair.expected_route is EvidenceRoute.ABSTAIN for record in records
    )
    assert all(record.evidence_group_id == pair.evidence_group_id for record in records)
    assert all(record.parallel_group_id == pair.pair_id for record in records)
    assert all(record.document_evidence == () for record in records)
    assert all(record.tool_expectations == () for record in records)
    assert all(record.reference_answer is None for record in records)
    assert all(record.abstention_reason for record in records)
    assert all(record.as_of == AS_OF for record in records)
    assert all(record.annotation.status is AnnotationStatus.APPROVED for record in records)
    assert all(record.annotation.annotated_by == "Claude AI draft" for record in records)
    assert all(record.annotation.reviewed_by == "Hyungbae Cho" for record in records)
    review_times = {record.annotation.reviewed_at for record in records}
    assert None not in review_times
    assert len(review_times) == 1
    reviewed_at = next(iter(review_times))
    assert reviewed_at is not None
    assert reviewed_at.utcoffset() == timedelta(0)
    assert all(record.annotation.annotated_at <= reviewed_at for record in records)
    expected_tags = (
        "core",
        "temporal",
        "vintage",
        "abstention",
        "completeness-frontier",
        "batch-009",
    )
    assert all(record.tags == expected_tags for record in records)


def test_approved_core_contains_twenty_records_and_the_new_pair() -> None:
    approved = tuple(
        record for path in sorted(CORE_DIRECTORY.glob("*.jsonl")) for record in _records(path)
    )
    records = _core_records()

    assert len(approved) == 20
    assert all(record.annotation.status is AnnotationStatus.APPROVED for record in approved)
    assert {record.record_id for record in records} <= {record.record_id for record in approved}
    assert len(records) == 2
    assert all(record.annotation.status is AnnotationStatus.APPROVED for record in records)


def test_ledger_abstains_beyond_its_completeness_frontier() -> None:
    ledger = _ledger()
    record = _core_records()[0]
    cutoff = ledger.cutoff_exclusive(record.as_of)

    assert cutoff > ledger.complete_through
    selection = ledger.select_edition(cutoff)
    assert selection.selected_edition is None
    assert selection.abstention is EditionAbstentionReason.CUTOFF_BEYOND_COMPLETE_THROUGH


def test_approved_pair_forms_a_bundle_without_evidence_sources() -> None:
    BenchmarkBundle(
        sources=(),
        records=_core_records(),
        rights_catalogs=(_catalog(),),
    )


def test_bilingual_claims_are_parallel_and_leak_no_observation_value() -> None:
    korean, english = _core_records()

    assert "진폭조정" in korean.question
    assert "2026년 5월" in korean.question
    assert "2026년 8월 15일" in korean.question
    assert "complete_through" in korean.abstention_reason
    assert "cutoff_beyond_complete_through" in korean.abstention_reason
    assert "기권" in korean.abstention_reason
    assert "amplitude-adjusted" in english.question
    assert "May 2026" in english.question
    assert "August 15, 2026" in english.question
    assert "complete_through" in english.abstention_reason
    assert "cutoff_beyond_complete_through" in english.abstention_reason
    assert "abstain" in english.abstention_reason
    for record in (korean, english):
        serialized = record.model_dump_json()
        assert "102.66" not in serialized
        assert "202607" not in serialized
        assert CLI_SOURCE_ID not in serialized
        assert LEDGER_ID not in serialized


def test_pre_frontier_cutoff_still_selects_an_edition() -> None:
    ledger = _ledger()
    cutoff = ledger.cutoff_exclusive(date(2026, 7, 9))

    assert cutoff <= ledger.complete_through
    selection = ledger.select_edition(cutoff)
    assert selection.abstention is None
    assert selection.selected_edition == "202607"
