"""Contract and evidence checks for the approved kv-core-abstain-03 pair."""

from datetime import date, timedelta
from pathlib import Path

from sovereignlab.schemas import (
    AnnotationStatus,
    BenchmarkBundle,
    BenchmarkRecord,
    BenchmarkSplit,
    CoreAuthoringMatrix,
    EvidenceRoute,
    RedistributionStatus,
    RightsCatalog,
    SourceManifest,
    VintageSemantics,
)

ROOT = Path(__file__).resolve().parents[2]
MATRIX_PATH = ROOT / "data" / "benchmark" / "core-authoring-matrix-v1.json"
CORE_DIRECTORY = ROOT / "data" / "benchmark" / "core"
BATCH_PATH = CORE_DIRECTORY / "core-batch-007.jsonl"
DRAFT_PATH = ROOT / "data" / "benchmark" / "drafts" / "core-draft-007.jsonl"
RIGHTS_CATALOG_ID = "kor-rtd-rights-2026-07-17"
APPROVED_OECD_ITEM_ID = "KOR.M.LI_AA.IX._T"
KOSIS_CPI_SOURCE_ID = "kosis-101-dt-1j22003-t-t10-20260717t115242998550z"
AS_OF = date(2026, 7, 17)


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


def test_approved_pair_matches_the_frozen_allocation_and_review_metadata() -> None:
    matrix = CoreAuthoringMatrix.model_validate_json(MATRIX_PATH.read_text(encoding="utf-8"))
    pair = next(item for item in matrix.pairs if item.pair_id == "kv-core-abstain-03")
    records = _core_records()

    assert not DRAFT_PATH.exists()
    assert tuple(record.record_id for record in records) == (
        pair.ko_record_id,
        pair.en_record_id,
    )
    assert tuple(record.language.value for record in records) == ("ko", "en")
    assert pair.data_unit_ids == ()
    assert pair.document_unit_ids == ()
    assert all(record.split is pair.split is BenchmarkSplit.TRAIN for record in records)
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
        "false-premise",
        "batch-007",
    )
    assert all(record.tags == expected_tags for record in records)


def test_approved_core_contains_eighteen_records_and_the_new_pair() -> None:
    approved = tuple(
        record for path in sorted(CORE_DIRECTORY.glob("*.jsonl")) for record in _records(path)
    )
    records = _core_records()

    assert len(approved) == 18
    assert all(record.annotation.status is AnnotationStatus.APPROVED for record in approved)
    assert {record.record_id for record in records} <= {record.record_id for record in approved}
    assert len(records) == 2
    assert all(record.annotation.status is AnnotationStatus.APPROVED for record in records)


def test_rights_catalog_approves_no_oecd_cpi_revision_scope() -> None:
    catalog = _catalog()
    oecd_items = {
        decision.item_id for decision in catalog.decisions if decision.source_system.value == "oecd"
    }

    assert oecd_items == {APPROVED_OECD_ITEM_ID}
    for record in _core_records():
        assert APPROVED_OECD_ITEM_ID in record.abstention_reason


def test_approved_pair_forms_a_bundle_without_evidence_sources() -> None:
    BenchmarkBundle(
        sources=(),
        records=_core_records(),
        rights_catalogs=(_catalog(),),
    )


def test_bilingual_claims_are_parallel_and_leak_no_observation_value() -> None:
    korean, english = _core_records()

    assert "에디션" in korean.question
    assert "2019년 11월" in korean.question
    assert "2026년 7월 17일" in korean.question
    assert "커버리지" in korean.abstention_reason
    assert "허위 전제" in korean.abstention_reason
    assert "메타데이터 전용" in korean.abstention_reason
    assert "기권" in korean.abstention_reason
    assert "editions" in english.question
    assert "November 2019" in english.question
    assert "July 17, 2026" in english.question
    assert "archive coverage" in english.abstention_reason
    assert "false premise" in english.abstention_reason
    assert "metadata-only" in english.abstention_reason
    assert "abstain" in english.abstention_reason
    for record in (korean, english):
        serialized = record.model_dump_json()
        assert "104.87" not in serialized
        assert "119.99" not in serialized
        assert "102.66" not in serialized
        assert KOSIS_CPI_SOURCE_ID not in serialized


def test_only_approved_cpi_evidence_is_latest_only() -> None:
    manifest = SourceManifest.model_validate_json(
        (ROOT / "data" / "manifests" / f"{KOSIS_CPI_SOURCE_ID}.json").read_text(encoding="utf-8")
    )

    assert manifest.vintage_semantics is VintageSemantics.LATEST_ONLY
    assert manifest.redistribution.status is RedistributionStatus.ALLOWED
    assert manifest.rights_decision is not None
    assert manifest.rights_decision.catalog_id == RIGHTS_CATALOG_ID
