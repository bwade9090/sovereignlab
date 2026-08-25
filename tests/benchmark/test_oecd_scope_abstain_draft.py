"""Contract and evidence checks for the draft kv-core-abstain-02 pair."""

from datetime import date, timedelta
from pathlib import Path

from sovereignlab.schemas import (
    AnnotationStatus,
    BenchmarkBundle,
    BenchmarkRecord,
    BenchmarkSplit,
    CoreAuthoringMatrix,
    EditionAvailabilityLedger,
    EvidenceRoute,
    RightsCatalog,
    SourceManifest,
)
from sovereignlab.vintage import AsOfQuery, StesSeriesKey, resolve_stes_as_of

ROOT = Path(__file__).resolve().parents[2]
MATRIX_PATH = ROOT / "data" / "benchmark" / "core-authoring-matrix-v1.json"
CORE_DIRECTORY = ROOT / "data" / "benchmark" / "core"
DRAFT_PATH = ROOT / "data" / "benchmark" / "drafts" / "core-draft-006.jsonl"
RIGHTS_CATALOG_ID = "kor-rtd-rights-2026-07-17"
APPROVED_OECD_ITEM_ID = "KOR.M.LI_AA.IX._T"
CLI_SOURCE_ID = "oecd-stes-cli-kor-li-aa-20260717t115302688498z"
LEDGER_ID = "oecd-stes-ledger-20260717t115242998550z"
AS_OF = date(2026, 7, 9)


def _records(path: Path) -> tuple[BenchmarkRecord, ...]:
    return tuple(
        BenchmarkRecord.model_validate_json(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line
    )


def _draft_records() -> tuple[BenchmarkRecord, ...]:
    return _records(DRAFT_PATH)


def _catalog() -> RightsCatalog:
    return RightsCatalog.model_validate_json(
        (ROOT / "data" / "rights" / f"{RIGHTS_CATALOG_ID}.json").read_text(encoding="utf-8")
    )


def test_draft_pair_matches_the_frozen_allocation_and_has_no_review_metadata() -> None:
    matrix = CoreAuthoringMatrix.model_validate_json(MATRIX_PATH.read_text(encoding="utf-8"))
    pair = next(item for item in matrix.pairs if item.pair_id == "kv-core-abstain-02")
    records = _draft_records()

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
    assert all(record.annotation.status is AnnotationStatus.DRAFT for record in records)
    assert all(record.annotation.annotated_by == "Claude AI draft" for record in records)
    assert all(record.annotation.reviewed_by is None for record in records)
    assert all(record.annotation.reviewed_at is None for record in records)
    annotation_times = {record.annotation.annotated_at for record in records}
    assert len(annotation_times) == 1
    assert next(iter(annotation_times)).utcoffset() == timedelta(0)
    expected_tags = (
        "core",
        "temporal",
        "vintage",
        "abstention",
        "unapproved-scope",
        "draft-006",
    )
    assert all(record.tags == expected_tags for record in records)


def test_approved_core_remains_twelve_and_drafts_are_separate() -> None:
    matrix = CoreAuthoringMatrix.model_validate_json(MATRIX_PATH.read_text(encoding="utf-8"))
    approved = tuple(
        record for path in sorted(CORE_DIRECTORY.glob("*.jsonl")) for record in _records(path)
    )
    drafts = _draft_records()
    approved_ids = {record.record_id for record in approved}
    draft_ids = {record.record_id for record in drafts}

    assert len(approved) == 12
    assert all(record.annotation.status is AnnotationStatus.APPROVED for record in approved)
    assert len(drafts) == 2
    assert all(record.annotation.status is AnnotationStatus.DRAFT for record in drafts)
    assert approved_ids.isdisjoint(draft_ids)
    assert matrix.target_record_count - len(approved) - len(drafts) == 26


def test_rights_catalog_approves_no_neighboring_oecd_scope() -> None:
    catalog = _catalog()
    oecd_items = {
        decision.item_id for decision in catalog.decisions if decision.source_system.value == "oecd"
    }

    assert oecd_items == {APPROVED_OECD_ITEM_ID}
    for record in _draft_records():
        assert APPROVED_OECD_ITEM_ID in record.abstention_reason


def test_draft_pair_forms_a_bundle_without_evidence_sources() -> None:
    BenchmarkBundle(
        sources=(),
        records=_draft_records(),
        rights_catalogs=(_catalog(),),
    )


def test_bilingual_claims_are_parallel_and_leak_no_observation_value() -> None:
    korean, english = _draft_records()

    assert "정규화(normalised) CLI" in korean.question
    assert "2026년 5월" in korean.question
    assert "2026년 7월 9일" in korean.question
    assert "진폭조정" in korean.abstention_reason
    assert "기권" in korean.abstention_reason
    assert "normalised CLI" in english.question
    assert "May 2026" in english.question
    assert "July 9, 2026" in english.question
    assert "amplitude-adjusted" in english.abstention_reason
    assert "abstain" in english.abstention_reason
    for record in (korean, english):
        serialized = record.model_dump_json()
        assert "102.66" not in serialized
        assert CLI_SOURCE_ID not in serialized
        assert LEDGER_ID not in serialized


def test_approved_scope_still_resolves_at_the_same_cutoff() -> None:
    manifest = SourceManifest.model_validate_json(
        (ROOT / "data" / "manifests" / f"{CLI_SOURCE_ID}.json").read_text(encoding="utf-8")
    )
    ledger_path = ROOT / "data" / "availability" / f"{LEDGER_ID}.json"
    ledger = EditionAvailabilityLedger.model_validate_json(ledger_path.read_text(encoding="utf-8"))
    archive = (ROOT / "data" / "archive" / "oecd-stes" / f"{CLI_SOURCE_ID}.csv").read_bytes()

    resolution = resolve_stes_as_of(
        archive_bytes=archive,
        manifest=manifest,
        ledger=ledger,
        query=AsOfQuery(
            as_of=AS_OF,
            series=StesSeriesKey(
                ref_area="KOR",
                freq="M",
                measure="LI_AA",
                unit_measure="IX",
                activity="_T",
            ),
            period="2026-05",
        ),
    )

    assert resolution.abstention is None
    assert resolution.evidence is not None
    assert resolution.evidence.observation.edition == "202607"
    assert resolution.evidence.observation.observation_value == "102.66"
