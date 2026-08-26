"""Contract checks for the first approved bilingual documentary pair."""

from datetime import date
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
BATCH_PATH = CORE_DIRECTORY / "core-batch-002.jsonl"
SOURCE_IDS = ("bok-outlook-2026-05-ko", "bok-outlook-2026-05-en")


def _records(path: Path) -> tuple[BenchmarkRecord, ...]:
    return tuple(
        BenchmarkRecord.model_validate_json(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line
    )


def _manifests() -> tuple[SourceManifest, ...]:
    return tuple(
        SourceManifest.model_validate_json(
            (ROOT / "data" / "manifests" / f"{source_id}.json").read_text(encoding="utf-8")
        )
        for source_id in SOURCE_IDS
    )


def test_document_core_pair_matches_frozen_matrix_and_is_approved() -> None:
    matrix = CoreAuthoringMatrix.model_validate_json(MATRIX_PATH.read_text(encoding="utf-8"))
    pair = next(item for item in matrix.pairs if item.pair_id == "kv-core-doc-01")
    records = _records(BATCH_PATH)
    approved = tuple(
        record for path in sorted(CORE_DIRECTORY.glob("*.jsonl")) for record in _records(path)
    )

    assert {record.record_id for record in records} == {
        pair.ko_record_id,
        pair.en_record_id,
    }
    assert pair.document_unit_ids == ("bok-outlook-release-2026-05",)
    assert pair.data_unit_ids == ()
    assert all(record.split is pair.split is BenchmarkSplit.TRAIN for record in records)
    assert all(
        record.expected_route is pair.expected_route is EvidenceRoute.DOCUMENTS
        for record in records
    )
    assert all(record.evidence_group_id == pair.evidence_group_id for record in records)
    assert all(record.parallel_group_id == pair.pair_id for record in records)
    assert all(record.annotation.status is AnnotationStatus.APPROVED for record in records)
    assert all(record.annotation.reviewed_by == "Hyungbae Cho" for record in records)
    assert all(record.annotation.reviewed_at is not None for record in records)
    assert all("batch-002" in record.tags for record in records)
    assert all("draft-002" not in record.tags for record in records)

    assert len(approved) == 14
    assert all(record.annotation.status is AnnotationStatus.APPROVED for record in approved)


def test_document_core_pair_validates_at_language_specific_cutoffs() -> None:
    records = _records(BATCH_PATH)
    manifests = _manifests()

    BenchmarkBundle(sources=manifests, records=records)

    manifest_by_id = {manifest.source_id: manifest for manifest in manifests}
    assert {record.language.value for record in records} == {"ko", "en"}
    for record in records:
        assert len(record.document_evidence) == 1
        evidence = record.document_evidence[0]
        manifest = manifest_by_id[evidence.source_id]
        assert record.language is manifest.language
        assert record.as_of == manifest.published_on
        assert manifest.redistribution.status is RedistributionStatus.ALLOWED
        assert manifest.publisher == "Bank of Korea"


def test_english_translation_fails_closed_before_its_release_date() -> None:
    korean, english = _records(BATCH_PATH)
    manifests = _manifests()

    BenchmarkBundle(sources=manifests, records=(korean,))
    early_english = english.model_copy(update={"as_of": date(2026, 6, 29)})

    with pytest.raises(ValidationError, match="post-cutoff source bok-outlook-2026-05-en"):
        BenchmarkBundle(sources=manifests, records=(early_english,))


@pytest.mark.parametrize(
    ("new_evidence_group", "message"),
    [
        ("eg-doc-bok-outlook-2026-05", "evidence group"),
        ("eg-doc-bok-outlook-2026-05-en-only", "parallel group"),
    ],
)
def test_document_core_pair_rejects_cross_split_groups(
    new_evidence_group: str,
    message: str,
) -> None:
    korean, english = _records(BATCH_PATH)
    moved_english = english.model_copy(
        update={
            "split": BenchmarkSplit.DEVELOPMENT,
            "evidence_group_id": new_evidence_group,
        }
    )

    with pytest.raises(ValidationError, match=message):
        BenchmarkBundle(sources=_manifests(), records=(korean, moved_english))


def test_document_claims_have_stable_locators_and_transformation_disclosure() -> None:
    korean, english = _records(BATCH_PATH)

    assert korean.document_evidence[0].locator.page == 10
    assert english.document_evidence[0].locator.page == 9
    for record in (korean, english):
        evidence = record.document_evidence[0]
        assert evidence.locator.section is not None
        assert "+0.7" in evidence.supports_claim
        assert "+0.7" in record.reference_answer
        assert "Bank of Korea" in record.reference_answer or "한국은행" in record.reference_answer
    assert "요약·재표현" in korean.reference_answer
    assert "summarizes and paraphrases" in english.reference_answer
