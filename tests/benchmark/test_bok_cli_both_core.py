"""Contract and evidence checks for the approved kv-core-both-01 pair."""

from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path

import pytest
from pydantic import ValidationError

from sovereignlab.normalization import (
    NormalizedUnit,
    format_display,
    normalization_rule,
    normalize_source_value,
)
from sovereignlab.schemas import (
    AnnotationStatus,
    BenchmarkBundle,
    BenchmarkRecord,
    BenchmarkSplit,
    CoreAuthoringMatrix,
    EditionAvailabilityLedger,
    EvidenceRoute,
    RedistributionStatus,
    RightsCatalog,
    SourceManifest,
    SourceSystem,
)
from sovereignlab.vintage import AsOfQuery, StesSeriesKey, resolve_stes_as_of

ROOT = Path(__file__).resolve().parents[2]
MATRIX_PATH = ROOT / "data" / "benchmark" / "core-authoring-matrix-v1.json"
CORE_DIRECTORY = ROOT / "data" / "benchmark" / "core"
BATCH_PATH = CORE_DIRECTORY / "core-batch-010.jsonl"
DRAFT_PATH = ROOT / "data" / "benchmark" / "drafts" / "core-draft-010.jsonl"
DOC_SOURCE_IDS = ("bok-outlook-2026-05-ko", "bok-outlook-2026-05-en")
CLI_SOURCE_ID = "oecd-stes-cli-kor-li-aa-20260717t115302688498z"
LEDGER_ID = "oecd-stes-ledger-20260717t115242998550z"
AVAILABILITY_SOURCE_ID = "oecd-stes-availableconstraint-20260717t101906273935z"
CONTENT_SOURCE_ID = "oecd-stes-contentconstraint-20260717t101906273935z"
RIGHTS_CATALOG_ID = "kor-rtd-rights-2026-07-17"
NORMALIZATION_RULE_ID = "oecd-stes-kor-li-aa-index-v1"
AS_OF = date(2026, 7, 9)


def _records(path: Path) -> tuple[BenchmarkRecord, ...]:
    return tuple(
        BenchmarkRecord.model_validate_json(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line
    )


def _core_records() -> tuple[BenchmarkRecord, ...]:
    return _records(BATCH_PATH)


def _manifest(source_id: str) -> SourceManifest:
    path = ROOT / "data" / "manifests" / f"{source_id}.json"
    return SourceManifest.model_validate_json(path.read_text(encoding="utf-8"))


def _ledger() -> EditionAvailabilityLedger:
    return EditionAvailabilityLedger.model_validate_json(
        (ROOT / "data" / "availability" / f"{LEDGER_ID}.json").read_text(encoding="utf-8")
    )


def _catalog() -> RightsCatalog:
    return RightsCatalog.model_validate_json(
        (ROOT / "data" / "rights" / f"{RIGHTS_CATALOG_ID}.json").read_text(encoding="utf-8")
    )


def _fact_map(record: BenchmarkRecord) -> dict[str, str]:
    expectation = record.tool_expectations[0]
    facts = dict(fact.split("=", maxsplit=1) for fact in expectation.expected_facts)
    assert len(facts) == len(expectation.expected_facts)
    return facts


def _bundle_sources() -> tuple[SourceManifest, ...]:
    return (
        _manifest(DOC_SOURCE_IDS[0]),
        _manifest(DOC_SOURCE_IDS[1]),
        _manifest(CLI_SOURCE_ID),
        _manifest(AVAILABILITY_SOURCE_ID),
        _manifest(CONTENT_SOURCE_ID),
    )


def test_approved_pair_matches_the_frozen_allocation_and_review_metadata() -> None:
    matrix = CoreAuthoringMatrix.model_validate_json(MATRIX_PATH.read_text(encoding="utf-8"))
    pair = next(item for item in matrix.pairs if item.pair_id == "kv-core-both-01")
    records = _core_records()

    assert not DRAFT_PATH.exists()
    assert tuple(record.record_id for record in records) == (
        pair.ko_record_id,
        pair.en_record_id,
    )
    assert tuple(record.language.value for record in records) == ("ko", "en")
    assert pair.document_unit_ids == ("bok-outlook-release-2026-05",)
    assert pair.data_unit_ids == ("oecd-stes-edition-202607",)
    assert all(record.split is pair.split is BenchmarkSplit.TRAIN for record in records)
    assert all(
        record.expected_route is pair.expected_route is EvidenceRoute.DOCUMENTS_AND_DATA
        for record in records
    )
    assert all(record.evidence_group_id == pair.evidence_group_id for record in records)
    assert all(record.parallel_group_id == pair.pair_id for record in records)
    assert all(len(record.document_evidence) == 1 for record in records)
    assert all(len(record.tool_expectations) == 1 for record in records)
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
        "documents",
        "vintage",
        "bok-outlook-cli",
        "batch-010",
    )
    assert all(record.tags == expected_tags for record in records)


def test_approved_core_contains_twenty_two_records_and_the_new_pair() -> None:
    approved = tuple(
        record for path in sorted(CORE_DIRECTORY.glob("*.jsonl")) for record in _records(path)
    )
    records = _core_records()

    assert len(approved) == 22
    assert all(record.annotation.status is AnnotationStatus.APPROVED for record in approved)
    assert {record.record_id for record in records} <= {record.record_id for record in approved}
    assert len(records) == 2
    assert all(record.annotation.status is AnnotationStatus.APPROVED for record in records)


def test_approved_pair_forms_a_real_bundle_with_documents_ledger_and_rights() -> None:
    BenchmarkBundle(
        sources=_bundle_sources(),
        records=_core_records(),
        availability_ledgers=(_ledger(),),
        rights_catalogs=(_catalog(),),
    )

    for source_id, page, section in zip(
        DOC_SOURCE_IDS,
        (8, 6),
        ("요약 2/10 — 경제전망 요약", "Executive Summary ii"),
        strict=True,
    ):
        manifest = _manifest(source_id)
        assert manifest.redistribution.status is RedistributionStatus.ALLOWED
        assert manifest.publisher == "Bank of Korea"
        assert manifest.published_on <= AS_OF
        record = next(
            item for item in _core_records() if item.document_evidence[0].source_id == source_id
        )
        assert record.document_evidence[0].locator.page == page
        assert record.document_evidence[0].locator.section == section


def test_real_resolver_reproduces_the_declared_cli_gold() -> None:
    records = _core_records()
    ledger = _ledger()
    cli_manifest = _manifest(CLI_SOURCE_ID)
    archive = (ROOT / "data" / "archive" / "oecd-stes" / f"{CLI_SOURCE_ID}.csv").read_bytes()

    for record in records:
        expectation = record.tool_expectations[0]
        arguments = expectation.arguments
        facts = _fact_map(record)
        assert expectation.tool_name == "resolve_stes_as_of"
        assert expectation.source_id == CLI_SOURCE_ID
        assert expectation.vintage is not None
        assert expectation.vintage.ledger_id == LEDGER_ID
        assert expectation.vintage.selected_edition == facts["selected_edition"] == "202607"

        resolution = resolve_stes_as_of(
            archive_bytes=archive,
            manifest=cli_manifest,
            ledger=ledger,
            query=AsOfQuery(
                as_of=record.as_of,
                series=StesSeriesKey(
                    ref_area=arguments["ref_area"],
                    freq=arguments["freq"],
                    measure=arguments["measure"],
                    unit_measure=arguments["unit_measure"],
                    activity=arguments["activity"],
                ),
                period=arguments["period"],
            ),
        )
        assert resolution.abstention is None
        assert resolution.evidence is not None
        assert resolution.evidence.observation.edition == facts["selected_edition"]
        assert resolution.evidence.observation.observation_value == facts["raw_value"]

        rule = normalization_rule(
            SourceSystem.OECD,
            "DSD_STES_REVISIONS@DF_STES_REVISIONS",
            "KOR.M.LI_AA.IX._T",
        )
        assert rule.rule_id == NORMALIZATION_RULE_ID
        normalized = normalize_source_value(rule, resolution.evidence.observation.observation_value)
        assert normalized.exact_value == Decimal(facts["normalized_value"])
        assert normalized.unit is NormalizedUnit.OECD_AMPLITUDE_ADJUSTED_INDEX
        assert normalized.unit.value == facts["canonical_unit"]
        assert format_display(normalized.exact_value, places=2) == facts["normalized_value"]


def test_bilingual_claims_combine_the_document_and_data_facts() -> None:
    korean, english = _core_records()
    facts = _fact_map(korean)

    assert "2026년 7월 9일" in korean.question
    assert "GDP 성장률" in korean.question
    assert "진폭조정" in korean.question
    assert "2.6%" in korean.reference_answer
    assert "2.0%" in korean.reference_answer
    assert "202607 edition" in korean.reference_answer
    assert "102.66" in korean.reference_answer
    assert "요약·재표현" in korean.reference_answer
    assert "2.6%" in korean.document_evidence[0].supports_claim
    assert "July 9, 2026" in english.question
    assert "GDP growth" in english.question
    assert "amplitude-adjusted" in english.question
    assert "2.6%" in english.reference_answer
    assert "2.0%" in english.reference_answer
    assert "edition 202607" in english.reference_answer
    assert "102.66" in english.reference_answer
    assert "summarizes and paraphrases" in english.reference_answer
    assert "2.6%" in english.document_evidence[0].supports_claim
    for record in (korean, english):
        assert "Bank of Korea" in record.reference_answer or "한국은행" in record.reference_answer
        assert record.as_of == AS_OF
        assert _fact_map(record) == facts


def test_english_document_fails_closed_before_its_release_date() -> None:
    korean, english = _core_records()
    early_english = english.model_copy(update={"as_of": date(2026, 7, 5)})

    with pytest.raises(ValidationError, match="post-cutoff source bok-outlook-2026-05-en"):
        BenchmarkBundle(
            sources=_bundle_sources(),
            records=(korean, early_english),
            availability_ledgers=(_ledger(),),
            rights_catalogs=(_catalog(),),
        )


def test_pre_availability_cutoff_still_abstains_on_the_ledger() -> None:
    ledger = _ledger()
    cutoff = ledger.cutoff_exclusive(date(2026, 6, 30))

    selection = ledger.select_edition(cutoff)
    assert selection.selected_edition is None
    assert selection.abstention is not None
