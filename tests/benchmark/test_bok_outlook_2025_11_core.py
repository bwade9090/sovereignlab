"""Contract and evidence checks for the approved kv-core-doc-02 pair."""

from datetime import date, timedelta
from pathlib import Path

import pytest
from pydantic import ValidationError

from sovereignlab.schemas import (
    AnnotationStatus,
    BenchmarkBundle,
    BenchmarkRecord,
    BenchmarkSplit,
    CoreAuthoringMatrix,
    EvidenceRoute,
    RedistributionStatus,
    SourceManifest,
)

ROOT = Path(__file__).resolve().parents[2]
MATRIX_PATH = ROOT / "data" / "benchmark" / "core-authoring-matrix-v1.json"
CORE_DIRECTORY = ROOT / "data" / "benchmark" / "core"
BATCH_PATH = CORE_DIRECTORY / "core-batch-011.jsonl"
DRAFT_PATH = ROOT / "data" / "benchmark" / "drafts" / "core-draft-011.jsonl"
SOURCE_IDS = ("bok-outlook-2025-11-ko", "bok-outlook-2025-11-en")


def _records(path: Path) -> tuple[BenchmarkRecord, ...]:
    return tuple(
        BenchmarkRecord.model_validate_json(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line
    )


def _core_records() -> tuple[BenchmarkRecord, ...]:
    return _records(BATCH_PATH)


def _manifests() -> tuple[SourceManifest, ...]:
    return tuple(
        SourceManifest.model_validate_json(
            (ROOT / "data" / "manifests" / f"{source_id}.json").read_text(encoding="utf-8")
        )
        for source_id in SOURCE_IDS
    )


def test_approved_pair_matches_the_frozen_allocation_and_review_metadata() -> None:
    matrix = CoreAuthoringMatrix.model_validate_json(MATRIX_PATH.read_text(encoding="utf-8"))
    pair = next(item for item in matrix.pairs if item.pair_id == "kv-core-doc-02")
    records = _core_records()

    assert not DRAFT_PATH.exists()
    assert tuple(record.record_id for record in records) == (
        pair.ko_record_id,
        pair.en_record_id,
    )
    assert tuple(record.language.value for record in records) == ("ko", "en")
    assert pair.document_unit_ids == ("bok-outlook-release-2025-11",)
    assert pair.data_unit_ids == ()
    assert all(record.split is pair.split is BenchmarkSplit.TRAIN for record in records)
    assert all(
        record.expected_route is pair.expected_route is EvidenceRoute.DOCUMENTS
        for record in records
    )
    assert all(record.evidence_group_id == pair.evidence_group_id for record in records)
    assert all(record.parallel_group_id == pair.pair_id for record in records)
    assert all(record.tool_expectations == () for record in records)
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
    expected_tags = ("core", "temporal", "documents", "bok-outlook", "batch-011")
    assert all(record.tags == expected_tags for record in records)


def test_approved_core_contains_twenty_six_records_and_the_new_pair() -> None:
    approved = tuple(
        record for path in sorted(CORE_DIRECTORY.glob("*.jsonl")) for record in _records(path)
    )
    records = _core_records()

    assert len(approved) == 26
    assert all(record.annotation.status is AnnotationStatus.APPROVED for record in approved)
    assert {record.record_id for record in records} <= {record.record_id for record in approved}
    assert len(records) == 2
    assert all(record.annotation.status is AnnotationStatus.APPROVED for record in records)


def test_approved_pair_validates_at_each_editions_own_cutoff() -> None:
    records = _core_records()
    manifests = _manifests()

    BenchmarkBundle(sources=manifests, records=records)

    manifest_by_id = {manifest.source_id: manifest for manifest in manifests}
    assert [record.as_of for record in records] == [date(2026, 3, 31), date(2026, 1, 22)]
    for record in records:
        evidence = record.document_evidence[0]
        manifest = manifest_by_id[evidence.source_id]
        assert len(record.document_evidence) == 1
        assert record.language is manifest.language
        assert record.as_of == manifest.published_on
        assert manifest.redistribution.status is RedistributionStatus.ALLOWED
        assert manifest.publisher == "Bank of Korea"


@pytest.mark.parametrize(
    ("index", "source_id"),
    [(0, "bok-outlook-2025-11-ko"), (1, "bok-outlook-2025-11-en")],
    ids=["korean", "english"],
)
def test_each_record_fails_closed_the_day_before_its_edition(index: int, source_id: str) -> None:
    record = _core_records()[index]
    early = record.model_copy(update={"as_of": record.as_of - timedelta(days=1)})

    with pytest.raises(ValidationError, match=f"post-cutoff source {source_id}"):
        BenchmarkBundle(sources=_manifests(), records=(early,))


def test_inflation_rationale_uses_literal_locators_and_disclosure() -> None:
    korean, english = _core_records()

    assert korean.document_evidence[0].locator.page == 5
    assert korean.document_evidence[0].locator.section == "요약 1/7"
    assert english.document_evidence[0].locator.page == 5
    assert english.document_evidence[0].locator.section == "Executive Summary i"
    for record in (korean, english):
        assert "2.1%" in record.document_evidence[0].supports_claim
        assert "2.1%" in record.reference_answer
        assert "Bank of Korea" in record.reference_answer or "한국은행" in record.reference_answer
    assert "「경제전망보고서(2025년 11월)」" in korean.question
    for term in ("높아진 환율", "내수부진 완화", "국제유가 하락"):
        assert term in korean.reference_answer
    assert "요약·재표현" in korean.reference_answer
    assert "November 2025 Korea Economic Outlook" in english.question
    for term in ("weaker Korean won", "domestic demand", "lower global oil prices"):
        assert term in english.reference_answer
    assert "summarizes and paraphrases" in english.reference_answer
