"""Cross-record leakage, vintage, rights-link, and reference-integrity tests."""

from datetime import date, datetime

import pytest
from pydantic import ValidationError

from sovereignlab.schemas import (
    AnnotationProvenance,
    BenchmarkBundle,
    BenchmarkRecord,
    BenchmarkSplit,
    DocumentEvidence,
    EditionAvailabilityLedger,
    EvidenceRoute,
    RedistributionStatus,
    RightsCatalog,
    SeriesRightsDecision,
    SourceManifest,
    ToolExpectation,
)


def test_bundle_accepts_valid_references(
    document_source: SourceManifest,
    api_source: SourceManifest,
    document_record: BenchmarkRecord,
) -> None:
    bundle = BenchmarkBundle(
        sources=(document_source, api_source),
        records=(document_record,),
    )

    assert len(bundle.sources) == 2
    assert len(bundle.records) == 1


def test_bundle_accepts_valid_data_tool_reference(
    api_source: SourceManifest,
    annotation: AnnotationProvenance,
    tool_expectation: ToolExpectation,
) -> None:
    record = BenchmarkRecord(
        record_id="example-data-en-001",
        split=BenchmarkSplit.TEST,
        evidence_group_id="example-data-group-001",
        language="en",
        question="What value does the synthetic official-data tool return?",
        expected_route=EvidenceRoute.DATA,
        tool_expectations=(tool_expectation,),
        reference_answer="A synthetic observation with a time period.",
        annotation=annotation,
    )

    bundle = BenchmarkBundle(sources=(api_source,), records=(record,))

    assert bundle.records[0].tool_expectations[0].tool_name == "oecd_sdmx"


def test_bundle_rejects_unknown_source_reference(
    api_source: SourceManifest,
    document_record: BenchmarkRecord,
) -> None:
    with pytest.raises(ValidationError, match="unknown source"):
        BenchmarkBundle(sources=(api_source,), records=(document_record,))


def test_bundle_rejects_post_cutoff_document(
    document_source: SourceManifest,
    document_record: BenchmarkRecord,
) -> None:
    record_payload = document_record.model_dump(mode="python")
    record_payload["as_of"] = date(2024, 5, 1)
    earlier_record = BenchmarkRecord.model_validate(record_payload)

    with pytest.raises(ValidationError, match="post-cutoff"):
        BenchmarkBundle(sources=(document_source,), records=(earlier_record,))


def test_bundle_rejects_duplicate_source_ids(
    document_source: SourceManifest,
    document_record: BenchmarkRecord,
) -> None:
    with pytest.raises(ValidationError, match="duplicate source_id"):
        BenchmarkBundle(
            sources=(document_source, document_source),
            records=(document_record,),
        )


def test_bundle_rejects_duplicate_record_ids(
    document_source: SourceManifest,
    document_record: BenchmarkRecord,
) -> None:
    with pytest.raises(ValidationError, match="duplicate record_id"):
        BenchmarkBundle(
            sources=(document_source,),
            records=(document_record, document_record),
        )


def test_document_evidence_must_reference_document_source(
    api_source: SourceManifest,
    document_record: BenchmarkRecord,
) -> None:
    evidence_payload = document_record.document_evidence[0].model_dump(mode="python")
    evidence_payload["source_id"] = api_source.source_id
    record_payload = document_record.model_dump(mode="python")
    record_payload["document_evidence"] = (DocumentEvidence.model_validate(evidence_payload),)
    record = BenchmarkRecord.model_validate(record_payload)

    with pytest.raises(ValidationError, match="non-document source"):
        BenchmarkBundle(sources=(api_source,), records=(record,))


def test_tool_expectation_must_reference_data_source(
    document_source: SourceManifest,
    annotation: AnnotationProvenance,
    tool_expectation: ToolExpectation,
) -> None:
    tool_payload = tool_expectation.model_dump(mode="python")
    tool_payload["source_id"] = document_source.source_id
    record = BenchmarkRecord(
        record_id="wrong-tool-source-001",
        split=BenchmarkSplit.TEST,
        evidence_group_id="wrong-tool-group-001",
        language="en",
        question="What value does the synthetic data tool return?",
        expected_route=EvidenceRoute.DATA,
        tool_expectations=(ToolExpectation.model_validate(tool_payload),),
        reference_answer="A synthetic value.",
        annotation=annotation,
    )

    with pytest.raises(ValidationError, match="non-data source"):
        BenchmarkBundle(sources=(document_source,), records=(record,))


def test_bundle_rejects_post_cutoff_tool_snapshot(
    api_source: SourceManifest,
    annotation: AnnotationProvenance,
    tool_expectation: ToolExpectation,
) -> None:
    record = BenchmarkRecord(
        record_id="future-tool-source-001",
        split=BenchmarkSplit.TEST,
        evidence_group_id="future-tool-group-001",
        language="en",
        question="As of 2023, what did the synthetic data snapshot show?",
        as_of=date(2023, 12, 31),
        expected_route=EvidenceRoute.DATA,
        tool_expectations=(tool_expectation,),
        reference_answer="This answer must not be reachable from a later snapshot.",
        annotation=annotation,
        tags=("temporal",),
    )

    with pytest.raises(ValidationError, match="post-cutoff"):
        BenchmarkBundle(sources=(api_source,), records=(record,))


def test_evidence_group_cannot_cross_splits(
    document_source: SourceManifest,
    document_record: BenchmarkRecord,
) -> None:
    second_payload = document_record.model_dump(mode="python")
    second_payload.update(record_id="example-doc-en-002", split=BenchmarkSplit.DEVELOPMENT)
    second_record = BenchmarkRecord.model_validate(second_payload)

    with pytest.raises(ValidationError, match=r"evidence group .* crosses dataset splits"):
        BenchmarkBundle(
            sources=(document_source,),
            records=(document_record, second_record),
        )


def test_parallel_group_cannot_cross_splits(
    document_source: SourceManifest,
    document_record: BenchmarkRecord,
) -> None:
    second_payload = document_record.model_dump(mode="python")
    second_payload.update(
        record_id="example-doc-ko-001",
        split=BenchmarkSplit.TRAIN,
        evidence_group_id="different-evidence-group",
    )
    second_record = BenchmarkRecord.model_validate(second_payload)

    with pytest.raises(ValidationError, match=r"parallel group .* crosses dataset splits"):
        BenchmarkBundle(
            sources=(document_source,),
            records=(document_record, second_record),
        )


def test_same_evidence_group_may_share_one_split(
    document_source: SourceManifest,
    document_record: BenchmarkRecord,
) -> None:
    second_payload = document_record.model_dump(mode="python")
    second_payload.update(
        record_id="example-doc-en-002",
        parallel_group_id=None,
    )
    second_record = BenchmarkRecord.model_validate(second_payload)

    bundle = BenchmarkBundle(
        sources=(document_source,),
        records=(document_record, second_record),
    )

    assert len(bundle.records) == 2


def test_bundle_accepts_a_ledger_resolved_archive_record(
    archive_source: SourceManifest,
    api_source: SourceManifest,
    archive_record: BenchmarkRecord,
    availability_ledger: EditionAvailabilityLedger,
) -> None:
    bundle = BenchmarkBundle(
        sources=(archive_source, api_source),
        records=(archive_record,),
        availability_ledgers=(availability_ledger,),
    )

    assert bundle.records[0].tool_expectations[0].vintage.selected_edition == "202405"


def test_bundle_rejects_duplicate_ledger_ids(
    archive_source: SourceManifest,
    api_source: SourceManifest,
    archive_record: BenchmarkRecord,
    availability_ledger: EditionAvailabilityLedger,
) -> None:
    with pytest.raises(ValidationError, match="duplicate ledger_id"):
        BenchmarkBundle(
            sources=(archive_source, api_source),
            records=(archive_record,),
            availability_ledgers=(availability_ledger, availability_ledger),
        )


def test_bundle_rejects_duplicate_catalog_ids(
    document_source: SourceManifest,
    document_record: BenchmarkRecord,
    rights_catalog: RightsCatalog,
) -> None:
    with pytest.raises(ValidationError, match="duplicate catalog_id"):
        BenchmarkBundle(
            sources=(document_source,),
            records=(document_record,),
            rights_catalogs=(rights_catalog, rights_catalog),
        )


def test_ledger_evidence_must_reference_known_sources(
    archive_source: SourceManifest,
    archive_record: BenchmarkRecord,
    availability_ledger: EditionAvailabilityLedger,
) -> None:
    with pytest.raises(ValidationError, match="availability evidence references unknown source"):
        BenchmarkBundle(
            sources=(archive_source,),
            records=(archive_record,),
            availability_ledgers=(availability_ledger,),
        )


def test_rights_link_requires_a_known_catalog(allowed_api_source: SourceManifest) -> None:
    with pytest.raises(ValidationError, match="unknown rights catalog"):
        BenchmarkBundle(sources=(allowed_api_source,), records=())


def test_rights_link_requires_a_known_decision(
    allowed_api_source: SourceManifest,
    rights_catalog: RightsCatalog,
) -> None:
    payload = allowed_api_source.model_dump(mode="python")
    payload["rights_decision"]["decision_id"] = "missing-decision-001"
    source = SourceManifest.model_validate(payload)

    with pytest.raises(ValidationError, match="unknown rights decision"):
        BenchmarkBundle(sources=(source,), records=(), rights_catalogs=(rights_catalog,))


def test_rights_link_scope_must_match_the_decision(
    allowed_api_source: SourceManifest,
    rights_catalog: RightsCatalog,
) -> None:
    payload = allowed_api_source.model_dump(mode="python")
    payload["rights_decision"]["table_id"] = "TABLE_999"
    source = SourceManifest.model_validate(payload)

    with pytest.raises(ValidationError, match="scope does not match"):
        BenchmarkBundle(sources=(source,), records=(), rights_catalogs=(rights_catalog,))


def test_allowed_source_requires_an_allowed_decision(
    allowed_api_source: SourceManifest,
    rights_catalog: RightsCatalog,
    series_rights_decision: SeriesRightsDecision,
) -> None:
    decision_payload = series_rights_decision.model_dump(mode="python")
    decision_payload["decision_state"] = RedistributionStatus.METADATA_ONLY
    catalog_payload = rights_catalog.model_dump(mode="python")
    catalog_payload["decisions"] = (SeriesRightsDecision.model_validate(decision_payload),)
    catalog = RightsCatalog.model_validate(catalog_payload)

    with pytest.raises(ValidationError, match="requires an allowed"):
        BenchmarkBundle(sources=(allowed_api_source,), records=(), rights_catalogs=(catalog,))


def test_expired_rights_decision_is_rejected(
    allowed_api_source: SourceManifest,
    rights_catalog: RightsCatalog,
    series_rights_decision: SeriesRightsDecision,
) -> None:
    decision_payload = series_rights_decision.model_dump(mode="python")
    decision_payload["valid_until"] = date(2026, 7, 17)
    catalog_payload = rights_catalog.model_dump(mode="python")
    catalog_payload["decisions"] = (SeriesRightsDecision.model_validate(decision_payload),)
    catalog = RightsCatalog.model_validate(catalog_payload)
    source_payload = allowed_api_source.model_dump(mode="python")
    source_payload["retrieved_at"] = datetime.fromisoformat("2026-07-18T10:00:00+00:00")
    source = SourceManifest.model_validate(source_payload)

    with pytest.raises(ValidationError, match="expired before retrieval"):
        BenchmarkBundle(sources=(source,), records=(), rights_catalogs=(catalog,))


def test_valid_rights_link_is_accepted(
    allowed_api_source: SourceManifest,
    rights_catalog: RightsCatalog,
) -> None:
    bundle = BenchmarkBundle(
        sources=(allowed_api_source,),
        records=(),
        rights_catalogs=(rights_catalog,),
    )

    assert bundle.sources[0].rights_decision is not None


def test_metadata_only_source_may_carry_a_rights_link(
    allowed_api_source: SourceManifest,
    rights_catalog: RightsCatalog,
) -> None:
    payload = allowed_api_source.model_dump(mode="python")
    payload["redistribution"] = {
        "status": RedistributionStatus.METADATA_ONLY,
        "notes": "Synthetic fixture; observation withheld.",
    }
    source = SourceManifest.model_validate(payload)

    bundle = BenchmarkBundle(sources=(source,), records=(), rights_catalogs=(rights_catalog,))

    assert bundle.sources[0].redistribution.status is RedistributionStatus.METADATA_ONLY


def test_archive_source_requires_as_of(
    archive_source: SourceManifest,
    api_source: SourceManifest,
    archive_record: BenchmarkRecord,
    availability_ledger: EditionAvailabilityLedger,
) -> None:
    record_payload = archive_record.model_dump(mode="python")
    record_payload["as_of"] = None
    record_payload["tags"] = ()
    record_payload["tool_expectations"][0]["vintage"] = None
    record = BenchmarkRecord.model_validate(record_payload)

    with pytest.raises(ValidationError, match="without as_of"):
        BenchmarkBundle(
            sources=(archive_source, api_source),
            records=(record,),
            availability_ledgers=(availability_ledger,),
        )


def test_archive_source_requires_vintage_evidence(
    archive_source: SourceManifest,
    api_source: SourceManifest,
    archive_record: BenchmarkRecord,
    availability_ledger: EditionAvailabilityLedger,
) -> None:
    record_payload = archive_record.model_dump(mode="python")
    record_payload["tool_expectations"][0]["vintage"] = None
    record = BenchmarkRecord.model_validate(record_payload)

    with pytest.raises(ValidationError, match="without vintage evidence"):
        BenchmarkBundle(
            sources=(archive_source, api_source),
            records=(record,),
            availability_ledgers=(availability_ledger,),
        )


def test_vintage_must_reference_a_known_ledger(
    archive_source: SourceManifest,
    api_source: SourceManifest,
    archive_record: BenchmarkRecord,
) -> None:
    with pytest.raises(ValidationError, match="unknown availability ledger"):
        BenchmarkBundle(
            sources=(archive_source, api_source),
            records=(archive_record,),
        )


def test_vintage_resolution_requires_a_seoul_ledger(
    archive_source: SourceManifest,
    api_source: SourceManifest,
    archive_record: BenchmarkRecord,
    availability_ledger: EditionAvailabilityLedger,
) -> None:
    ledger_payload = availability_ledger.model_dump(mode="python")
    ledger_payload["cutoff_timezone"] = "UTC"
    ledger = EditionAvailabilityLedger.model_validate(ledger_payload)

    with pytest.raises(ValidationError, match="Asia/Seoul end-of-day ledger"):
        BenchmarkBundle(
            sources=(archive_source, api_source),
            records=(archive_record,),
            availability_ledgers=(ledger,),
        )


def test_gold_vintage_must_be_ledger_resolvable(
    archive_source: SourceManifest,
    api_source: SourceManifest,
    archive_record: BenchmarkRecord,
    availability_ledger: EditionAvailabilityLedger,
) -> None:
    record_payload = archive_record.model_dump(mode="python")
    record_payload["as_of"] = date(2024, 4, 30)
    record = BenchmarkRecord.model_validate(record_payload)

    with pytest.raises(ValidationError, match="cannot resolve"):
        BenchmarkBundle(
            sources=(archive_source, api_source),
            records=(record,),
            availability_ledgers=(availability_ledger,),
        )


def test_gold_vintage_must_match_the_ledger_resolved_edition(
    archive_source: SourceManifest,
    api_source: SourceManifest,
    archive_record: BenchmarkRecord,
    availability_ledger: EditionAvailabilityLedger,
) -> None:
    record_payload = archive_record.model_dump(mode="python")
    record_payload["as_of"] = date(2024, 6, 30)
    record = BenchmarkRecord.model_validate(record_payload)

    with pytest.raises(ValidationError, match="does not match the ledger-resolved edition"):
        BenchmarkBundle(
            sources=(archive_source, api_source),
            records=(record,),
            availability_ledgers=(availability_ledger,),
        )


def test_vintage_evidence_requires_an_archive_source(
    api_source: SourceManifest,
    archive_record: BenchmarkRecord,
    availability_ledger: EditionAvailabilityLedger,
) -> None:
    record_payload = archive_record.model_dump(mode="python")
    record_payload["tool_expectations"][0]["source_id"] = api_source.source_id
    record = BenchmarkRecord.model_validate(record_payload)

    with pytest.raises(ValidationError, match="requires a historical-archive source"):
        BenchmarkBundle(
            sources=(api_source,),
            records=(record,),
            availability_ledgers=(availability_ledger,),
        )


def test_superseded_catalog_cannot_authorize_redistribution(
    allowed_api_source: SourceManifest,
    rights_catalog: RightsCatalog,
) -> None:
    successor_payload = rights_catalog.model_dump(mode="python")
    successor_payload.update(
        catalog_id="example-rights-catalog-002",
        supersedes_catalog_id=rights_catalog.catalog_id,
    )
    successor = RightsCatalog.model_validate(successor_payload)

    with pytest.raises(ValidationError, match="superseded rights catalog"):
        BenchmarkBundle(
            sources=(allowed_api_source,),
            records=(),
            rights_catalogs=(rights_catalog, successor),
        )


def test_one_scope_cannot_span_multiple_active_catalogs(
    document_source: SourceManifest,
    document_record: BenchmarkRecord,
    rights_catalog: RightsCatalog,
) -> None:
    sibling_payload = rights_catalog.model_dump(mode="python")
    sibling_payload.update(catalog_id="example-rights-catalog-002")
    sibling = RightsCatalog.model_validate(sibling_payload)

    with pytest.raises(ValidationError, match="multiple active catalogs"):
        BenchmarkBundle(
            sources=(document_source,),
            records=(document_record,),
            rights_catalogs=(rights_catalog, sibling),
        )


def test_superseded_ledger_cannot_resolve_a_vintage(
    archive_source: SourceManifest,
    api_source: SourceManifest,
    archive_record: BenchmarkRecord,
    availability_ledger: EditionAvailabilityLedger,
) -> None:
    successor_payload = availability_ledger.model_dump(mode="python")
    successor_payload.update(
        ledger_id="example-availability-ledger-002",
        supersedes_ledger_id=availability_ledger.ledger_id,
    )
    successor = EditionAvailabilityLedger.model_validate(successor_payload)

    with pytest.raises(ValidationError, match="superseded availability ledger"):
        BenchmarkBundle(
            sources=(archive_source, api_source),
            records=(archive_record,),
            availability_ledgers=(availability_ledger, successor),
        )


def test_rights_expiry_compares_instants_not_offsets(
    allowed_api_source: SourceManifest,
    rights_catalog: RightsCatalog,
    series_rights_decision: SeriesRightsDecision,
) -> None:
    decision_payload = series_rights_decision.model_dump(mode="python")
    decision_payload["valid_until"] = date(2026, 7, 16)
    catalog_payload = rights_catalog.model_dump(mode="python")
    catalog_payload["decisions"] = (SeriesRightsDecision.model_validate(decision_payload),)
    catalog = RightsCatalog.model_validate(catalog_payload)

    for retrieved_at in ("2026-07-16T23:30:00+00:00", "2026-07-17T08:30:00+09:00"):
        source_payload = allowed_api_source.model_dump(mode="python")
        source_payload["retrieved_at"] = retrieved_at
        source = SourceManifest.model_validate(source_payload)

        with pytest.raises(ValidationError, match="expired before retrieval"):
            BenchmarkBundle(sources=(source,), records=(), rights_catalogs=(catalog,))

    source_payload = allowed_api_source.model_dump(mode="python")
    source_payload["retrieved_at"] = "2026-07-16T10:00:00+00:00"
    valid_source = SourceManifest.model_validate(source_payload)

    bundle = BenchmarkBundle(sources=(valid_source,), records=(), rights_catalogs=(catalog,))

    assert bundle.sources[0].rights_decision is not None


def test_rights_expiry_rejects_out_of_range_valid_until(
    allowed_api_source: SourceManifest,
    rights_catalog: RightsCatalog,
    series_rights_decision: SeriesRightsDecision,
) -> None:
    decision_payload = series_rights_decision.model_dump(mode="python")
    decision_payload["valid_until"] = date(9999, 12, 31)
    catalog_payload = rights_catalog.model_dump(mode="python")
    catalog_payload["decisions"] = (SeriesRightsDecision.model_validate(decision_payload),)
    catalog = RightsCatalog.model_validate(catalog_payload)

    with pytest.raises(ValidationError, match="out of the supported range"):
        BenchmarkBundle(
            sources=(allowed_api_source,),
            records=(),
            rights_catalogs=(catalog,),
        )
