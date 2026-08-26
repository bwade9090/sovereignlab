"""Contract and evidence checks for the approved kv-core-data-02 pair."""

from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path

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
    EvidenceRoute,
    RedistributionStatus,
    RightsCatalog,
    SnapshotAsOfArguments,
    SnapshotAsOfCall,
    SourceManifest,
    SourceSystem,
    ToolOutcomeStatus,
    VintageSemantics,
)
from sovereignlab.snapshots import (
    SnapshotAbstentionReason,
    load_committed_snapshot_registry,
    read_snapshot_as_of,
)

ROOT = Path(__file__).resolve().parents[2]
MATRIX_PATH = ROOT / "data" / "benchmark" / "core-authoring-matrix-v1.json"
CORE_DIRECTORY = ROOT / "data" / "benchmark" / "core"
BATCH_PATH = CORE_DIRECTORY / "core-batch-003.jsonl"
DRAFT_PATH = ROOT / "data" / "benchmark" / "drafts" / "core-draft-003.jsonl"
SOURCE_ID = "ecos-200y108-10601-20260717t115242998550z"
SOURCE_SHA256 = "75c96ce62270a8a6c2a3c6bebaef981945b41f37f62cab6911698ce64d8dd9ea"
SOURCE_URL = (
    "https://ecos.bok.or.kr/api/StatisticSearch/%7Bapi-key%7D/json/kr/1/1000/"
    "200Y108/Q/1960Q1/2026Q3/10601"
)
RIGHTS_CATALOG_ID = "kor-rtd-rights-2026-07-17"
RIGHTS_DECISION_ID = "ecos-200y108-10601-rights-v1"
NORMALIZATION_RULE_ID = "ecos-200y108-10601-billion-krw-v1"
AS_OF = date(2026, 7, 17)
EXPECTED_FACT_KEYS = {
    "source_sha256",
    "rights_catalog_id",
    "rights_decision_id",
    "source_published_on",
    "vintage_semantics",
    "raw_value",
    "normalization_rule_id",
    "normalized_value",
    "canonical_unit",
    "display_places",
    "display_value",
}


def _records(path: Path) -> tuple[BenchmarkRecord, ...]:
    return tuple(
        BenchmarkRecord.model_validate_json(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line
    )


def _core_records() -> tuple[BenchmarkRecord, ...]:
    return _records(BATCH_PATH)


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


def test_approved_pair_matches_the_frozen_allocation_and_review_metadata() -> None:
    matrix = CoreAuthoringMatrix.model_validate_json(MATRIX_PATH.read_text(encoding="utf-8"))
    pair = next(item for item in matrix.pairs if item.pair_id == "kv-core-data-02")
    records = _core_records()

    assert not DRAFT_PATH.exists()
    assert tuple(record.record_id for record in records) == (
        pair.ko_record_id,
        pair.en_record_id,
    )
    assert tuple(record.language.value for record in records) == ("ko", "en")
    assert pair.data_unit_ids == ("ecos-200y108-snapshot-20260717",)
    assert pair.document_unit_ids == ()
    assert all(record.split is pair.split is BenchmarkSplit.TRAIN for record in records)
    assert all(
        record.expected_route is pair.expected_route is EvidenceRoute.DATA for record in records
    )
    assert all(record.evidence_group_id == pair.evidence_group_id for record in records)
    assert all(record.parallel_group_id == pair.pair_id for record in records)
    assert all(record.document_evidence == () for record in records)
    assert all(record.annotation.status is AnnotationStatus.APPROVED for record in records)
    assert all(record.annotation.annotated_by == "Codex AI draft" for record in records)
    assert all(record.annotation.reviewed_by == "Hyungbae Cho" for record in records)
    review_times = {record.annotation.reviewed_at for record in records}
    assert None not in review_times
    assert len(review_times) == 1
    reviewed_at = next(iter(review_times))
    assert reviewed_at is not None
    assert reviewed_at.utcoffset() == timedelta(0)
    assert all(record.annotation.annotated_at <= reviewed_at for record in records)
    assert all("batch-003" in record.tags for record in records)
    assert all("draft-003" not in record.tags for record in records)


def test_approved_core_contains_fourteen_records_and_the_pair() -> None:
    approved = tuple(
        record for path in sorted(CORE_DIRECTORY.glob("*.jsonl")) for record in _records(path)
    )
    records = _core_records()

    assert len(approved) == 14
    assert all(record.annotation.status is AnnotationStatus.APPROVED for record in approved)
    assert {record.record_id for record in records} <= {record.record_id for record in approved}
    assert len(records) == 2
    assert all(record.annotation.status is AnnotationStatus.APPROVED for record in records)


def test_approved_pair_forms_a_real_bundle_with_the_approved_snapshot_rights() -> None:
    manifest = SourceManifest.model_validate_json(
        (ROOT / "data" / "manifests" / f"{SOURCE_ID}.json").read_text(encoding="utf-8")
    )
    catalog = RightsCatalog.model_validate_json(
        (ROOT / "data" / "rights" / f"{RIGHTS_CATALOG_ID}.json").read_text(encoding="utf-8")
    )

    BenchmarkBundle(
        sources=(manifest,),
        records=_core_records(),
        rights_catalogs=(catalog,),
    )

    assert manifest.source_id == SOURCE_ID
    assert manifest.content_sha256 == SOURCE_SHA256
    assert str(manifest.canonical_url) == SOURCE_URL
    assert manifest.published_on == AS_OF
    assert manifest.vintage_semantics is VintageSemantics.LATEST_ONLY
    assert manifest.redistribution.status is RedistributionStatus.ALLOWED
    assert manifest.rights_decision is not None
    assert manifest.rights_decision.catalog_id == RIGHTS_CATALOG_ID
    assert manifest.rights_decision.decision_id == RIGHTS_DECISION_ID


def test_real_snapshot_reader_reproduces_every_declared_gold_fact() -> None:
    registry = load_committed_snapshot_registry(ROOT)
    payloads = []

    for record in _core_records():
        expectation = record.tool_expectations[0]
        facts = _fact_map(record)
        result = read_snapshot_as_of(call=_call(record), registry=registry)

        assert set(facts) == EXPECTED_FACT_KEYS
        assert expectation.source_id == SOURCE_ID
        assert expectation.tool_name == "read_snapshot_as_of"
        assert expectation.vintage is None
        assert set(expectation.arguments) == {
            "source_system",
            "table_id",
            "item_id",
            "period",
            "as_of",
            "normalization_rule_id",
        }
        assert result.status is ToolOutcomeStatus.SUCCESS
        assert result.payload is not None
        assert result.abstention is None
        assert result.error is None
        payload = result.payload
        payloads.append(payload)
        assert payload.source_id == SOURCE_ID
        assert payload.source_sha256 == facts["source_sha256"]
        assert payload.rights_catalog_id == facts["rights_catalog_id"]
        assert payload.rights_decision_id == facts["rights_decision_id"]
        assert payload.source_published_on.isoformat() == facts["source_published_on"]
        assert payload.vintage_semantics == facts["vintage_semantics"]
        assert payload.as_of == record.as_of == AS_OF
        assert payload.period == expectation.arguments["period"] == "2026Q1"
        assert payload.observation.raw_value == facts["raw_value"]
        assert payload.observation.normalization_rule_id == facts["normalization_rule_id"]
        assert payload.observation.normalized_value == facts["normalized_value"]
        assert payload.observation.canonical_unit == facts["canonical_unit"]
        assert str(payload.observation.display_places) == facts["display_places"]
        assert payload.observation.display_value == facts["display_value"]

    assert payloads[0] == payloads[1]


def test_normalization_precision_and_bilingual_claims_are_exact() -> None:
    korean, english = _core_records()
    facts = _fact_map(korean)
    rule = normalization_rule(SourceSystem.ECOS, "200Y108", "10601")
    normalized = normalize_source_value(rule, facts["raw_value"])

    assert rule.rule_id == NORMALIZATION_RULE_ID
    assert normalized.exact_value == Decimal("596692.8")
    assert normalized.unit is NormalizedUnit.BILLION_KRW
    assert (
        format_display(normalized.exact_value, places=rule.recommended_display_places)
        == (facts["display_value"])
    )
    assert "계절조정" in korean.question
    assert "실질" in korean.question
    assert "십억원" in korean.question
    assert "596,692.8 십억원" in korean.reference_answer
    assert "작성기관: 한국은행" in korean.reference_answer
    assert "국내총생산에 대한 지출" in korean.reference_answer
    assert "조회일 2026-07-17" in korean.reference_answer
    assert "빈티지 구조로 가공" in korean.reference_answer
    assert "seasonally adjusted real" in english.question
    assert "in billion won" in english.question
    assert "596,692.8 billion won" in english.reference_answer
    assert "original producer: Bank of Korea" in english.reference_answer
    assert "Expenditure on GDP" in english.reference_answer
    assert "retrieved July 17, 2026" in english.reference_answer
    assert "structures the capture as vintage data" in english.reference_answer
    for record in (korean, english):
        assert "Bank of Korea" in record.reference_answer or "한국은행" in record.reference_answer
        assert SOURCE_URL in record.reference_answer
        assert record.as_of == AS_OF
        assert _fact_map(record) == facts


def test_day_before_capture_abstains_without_future_value_or_source() -> None:
    record = _core_records()[0]
    result = read_snapshot_as_of(
        call=_call(record, as_of=date(2026, 7, 16)),
        registry=load_committed_snapshot_registry(ROOT),
    )

    assert result.status is ToolOutcomeStatus.ABSTAINED
    assert result.payload is None
    assert result.error is None
    assert result.abstention is not None
    assert result.abstention.reason_code == (
        SnapshotAbstentionReason.NO_SNAPSHOT_AVAILABLE_BY_CUTOFF.value
    )
    serialized = result.model_dump_json()
    assert SOURCE_ID not in serialized
    assert "596692.8" not in serialized
