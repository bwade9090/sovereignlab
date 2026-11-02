"""Contract and evidence checks for the draft kv-core-both-02 pair."""

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
    SnapshotAsOfArguments,
    SnapshotAsOfCall,
    SourceManifest,
    ToolOutcomeStatus,
)
from sovereignlab.snapshots import (
    SnapshotAbstentionReason,
    load_committed_snapshot_registry,
    read_snapshot_as_of,
)

ROOT = Path(__file__).resolve().parents[2]
MATRIX_PATH = ROOT / "data" / "benchmark" / "core-authoring-matrix-v1.json"
CORE_DIRECTORY = ROOT / "data" / "benchmark" / "core"
DRAFT_PATH = ROOT / "data" / "benchmark" / "drafts" / "core-draft-012.jsonl"
DOC_SOURCE_IDS = ("bok-outlook-2025-11-ko", "bok-outlook-2025-11-en")
SNAPSHOT_SOURCE_ID = "ecos-200y108-10601-20260717t115242998550z"
RIGHTS_CATALOG_ID = "kor-rtd-rights-2026-07-17"
SOURCE_URL = (
    "https://ecos.bok.or.kr/api/StatisticSearch/%7Bapi-key%7D/json/kr/1/1000/200Y108/Q/1960Q1/"
    "2026Q3/10601"
)
AS_OF = date(2026, 7, 17)


def _records(path: Path) -> tuple[BenchmarkRecord, ...]:
    return tuple(
        BenchmarkRecord.model_validate_json(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line
    )


def _draft_records() -> tuple[BenchmarkRecord, ...]:
    return _records(DRAFT_PATH)


def _manifest(source_id: str) -> SourceManifest:
    path = ROOT / "data" / "manifests" / f"{source_id}.json"
    return SourceManifest.model_validate_json(path.read_text(encoding="utf-8"))


def _fact_map(record: BenchmarkRecord) -> dict[str, str]:
    expectation = record.tool_expectations[0]
    facts = dict(fact.split("=", maxsplit=1) for fact in expectation.expected_facts)
    assert len(facts) == len(expectation.expected_facts)
    return facts


def _call(record: BenchmarkRecord, *, as_of: date | None = None) -> SnapshotAsOfCall:
    arguments = dict(record.tool_expectations[0].arguments)
    if as_of is not None:
        arguments["as_of"] = as_of.isoformat()
    return SnapshotAsOfCall(
        call_id=f"{record.record_id}-snapshot",
        tool_name="read_snapshot_as_of",
        arguments=SnapshotAsOfArguments.model_validate(arguments),
    )


def test_draft_pair_matches_the_frozen_allocation_and_has_no_review_metadata() -> None:
    matrix = CoreAuthoringMatrix.model_validate_json(MATRIX_PATH.read_text(encoding="utf-8"))
    pair = next(item for item in matrix.pairs if item.pair_id == "kv-core-both-02")
    records = _draft_records()

    assert tuple(record.record_id for record in records) == (
        pair.ko_record_id,
        pair.en_record_id,
    )
    assert tuple(record.language.value for record in records) == ("ko", "en")
    assert pair.document_unit_ids == ("bok-outlook-release-2025-11",)
    assert pair.data_unit_ids == ("ecos-200y108-snapshot-20260717",)
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
        "documents",
        "vintage",
        "bok-outlook-ecos-gdp",
        "draft-012",
    )
    assert all(record.tags == expected_tags for record in records)


def test_approved_core_remains_twenty_four_and_drafts_are_separate() -> None:
    matrix = CoreAuthoringMatrix.model_validate_json(MATRIX_PATH.read_text(encoding="utf-8"))
    approved = tuple(
        record for path in sorted(CORE_DIRECTORY.glob("*.jsonl")) for record in _records(path)
    )
    drafts = _draft_records()

    assert len(approved) == 24
    assert all(record.annotation.status is AnnotationStatus.APPROVED for record in approved)
    assert len(drafts) == 2
    assert {record.record_id for record in approved}.isdisjoint(
        {record.record_id for record in drafts}
    )
    assert matrix.target_record_count - len(approved) - len(drafts) == 14


def test_draft_pair_forms_a_real_bundle_with_documents_snapshot_and_rights() -> None:
    catalog = RightsCatalog.model_validate_json(
        (ROOT / "data" / "rights" / f"{RIGHTS_CATALOG_ID}.json").read_text(encoding="utf-8")
    )
    BenchmarkBundle(
        sources=(
            _manifest(DOC_SOURCE_IDS[0]),
            _manifest(DOC_SOURCE_IDS[1]),
            _manifest(SNAPSHOT_SOURCE_ID),
        ),
        records=_draft_records(),
        rights_catalogs=(catalog,),
    )

    for source_id, page, section in zip(
        DOC_SOURCE_IDS,
        (7, 8),
        ("요약 3/7 — 경제전망", "Executive Summary iv — Economic Outlook"),
        strict=True,
    ):
        manifest = _manifest(source_id)
        assert manifest.redistribution.status is RedistributionStatus.ALLOWED
        assert manifest.publisher == "Bank of Korea"
        assert manifest.published_on <= AS_OF
        record = next(
            item for item in _draft_records() if item.document_evidence[0].source_id == source_id
        )
        assert record.document_evidence[0].locator.page == page
        assert record.document_evidence[0].locator.section == section


def test_real_snapshot_reader_reproduces_the_declared_gdp_gold() -> None:
    registry = load_committed_snapshot_registry(ROOT)
    payloads = []

    for record in _draft_records():
        expectation = record.tool_expectations[0]
        facts = _fact_map(record)
        result = read_snapshot_as_of(call=_call(record), registry=registry)

        assert expectation.tool_name == "read_snapshot_as_of"
        assert expectation.source_id == SNAPSHOT_SOURCE_ID
        assert expectation.vintage is None
        assert result.status is ToolOutcomeStatus.SUCCESS
        assert result.payload is not None
        payload = result.payload
        payloads.append(payload)
        assert payload.source_id == SNAPSHOT_SOURCE_ID
        assert payload.source_sha256 == facts["source_sha256"]
        assert payload.rights_catalog_id == facts["rights_catalog_id"]
        assert payload.rights_decision_id == facts["rights_decision_id"]
        assert payload.source_published_on.isoformat() == facts["source_published_on"]
        assert payload.vintage_semantics == facts["vintage_semantics"]
        assert payload.period == expectation.arguments["period"] == "2025Q4"
        assert payload.observation.raw_value == facts["raw_value"] == "585964"
        assert payload.observation.normalization_rule_id == facts["normalization_rule_id"]
        assert payload.observation.normalized_value == facts["normalized_value"]
        assert payload.observation.canonical_unit == facts["canonical_unit"]
        assert str(payload.observation.display_places) == facts["display_places"]
        assert payload.observation.display_value == facts["display_value"] == "585964.0"

    assert payloads[0] == payloads[1]


def test_bilingual_claims_combine_the_document_and_data_facts() -> None:
    korean, english = _draft_records()

    assert "2026년 7월 17일" in korean.question
    assert "「경제전망보고서(2025년 11월)」" in korean.question
    assert "2025년 4분기" in korean.question
    for term in ("1.0%", "0.9%", "585,964.0 십억원", "요약·재표현", "작성기관: 한국은행"):
        assert term in korean.reference_answer
    assert "1.0%" in korean.document_evidence[0].supports_claim
    assert "July 17, 2026" in english.question
    assert "November 2025 Korea Economic Outlook" in english.question
    assert "fourth quarter of 2025" in english.question
    for term in (
        "1.0%",
        "0.9%",
        "585,964.0 billion won",
        "summarizes and paraphrases",
        "original producer: Bank of Korea",
    ):
        assert term in english.reference_answer
    assert "1.0%" in english.document_evidence[0].supports_claim
    for record in (korean, english):
        assert SOURCE_URL in record.reference_answer
        assert _fact_map(record) == _fact_map(korean)


def test_day_before_capture_abstains_without_future_value_or_source() -> None:
    record = _draft_records()[0]
    result = read_snapshot_as_of(
        call=_call(record, as_of=AS_OF - timedelta(days=1)),
        registry=load_committed_snapshot_registry(ROOT),
    )

    assert result.status is ToolOutcomeStatus.ABSTAINED
    assert result.payload is None
    assert result.abstention is not None
    assert result.abstention.reason_code == (
        SnapshotAbstentionReason.NO_SNAPSHOT_AVAILABLE_BY_CUTOFF.value
    )
    serialized = result.model_dump_json()
    assert SNAPSHOT_SOURCE_ID not in serialized
    assert "585964" not in serialized
