"""Reusable, entirely synthetic schema fixtures."""

from datetime import UTC, date, datetime

import pytest

from sovereignlab.schemas import (
    AnnotationProvenance,
    AnnotationStatus,
    AttributionField,
    AttributionRequirement,
    BenchmarkRecord,
    BenchmarkSplit,
    ContentClass,
    DocumentEvidence,
    EvidenceClaim,
    EvidenceLocator,
    EvidenceObservation,
    EvidenceRoute,
    InstrumentVerificationCapture,
    LanguageCode,
    OperationRule,
    OperationStatus,
    ProducerMappingBasis,
    ProjectUseProfile,
    PublicationDateBasis,
    RedistributionPolicy,
    RedistributionStatus,
    RightsCatalog,
    RightsEvidence,
    RightsEvidenceKind,
    RightsInstrument,
    RightsOperation,
    SeriesRightsDecision,
    SourceKind,
    SourceManifest,
    SourceSystem,
    ThirdPartyStatus,
    ToolExpectation,
)


@pytest.fixture
def annotation() -> AnnotationProvenance:
    return AnnotationProvenance(
        status=AnnotationStatus.APPROVED,
        annotated_by="fixture-author",
        annotated_at=datetime(2026, 7, 14, 8, 0, tzinfo=UTC),
        reviewed_by="fixture-reviewer",
        reviewed_at=datetime(2026, 7, 14, 9, 0, tzinfo=UTC),
    )


@pytest.fixture
def rights_instrument() -> RightsInstrument:
    terms_summary = "Synthetic terms permit attributed non-commercial redistribution."
    return RightsInstrument(
        instrument_id="example-statistics-use-guide",
        issuer="Example Public Institution",
        title="Example Statistics Information Use Guide",
        official_url="https://example.org/rights/statistics",
        accessed_on=date(2026, 7, 16),
        applicable_source_systems=(SourceSystem.OTHER_OFFICIAL,),
        applicable_content_classes=(ContentClass.OTHER_OFFICIAL_DATA,),
        terms_summary=terms_summary,
        terms_evidence=RightsEvidence(
            kind=RightsEvidenceKind.PUBLISHER_USE_GUIDE,
            official_url="https://example.org/rights/statistics",
            accessed_on=date(2026, 7, 16),
            claims=(EvidenceClaim.RIGHTS_TERMS,),
            assertion=terms_summary,
        ),
        verification_capture=InstrumentVerificationCapture(
            capture_url="https://example.org/rights/statistics.js",
            captured_at=datetime(2026, 7, 16, 7, 0, tzinfo=UTC),
            content_sha256="c" * 64,
            byte_size=4_096,
        ),
    )


@pytest.fixture
def series_rights_decision(rights_instrument: RightsInstrument) -> SeriesRightsDecision:
    return SeriesRightsDecision(
        decision_id="example-series-rights-001",
        publisher="Example Public Institution",
        original_producer="Example Public Institution",
        source_system=SourceSystem.OTHER_OFFICIAL,
        table_id="TABLE_001",
        item_id="ITEM_001",
        table_title="Synthetic Statistics Table",
        item_title="Synthetic Index",
        producer_mapping_title="Synthetic Statistics Table",
        frequency="monthly",
        unit="index",
        content_class=ContentClass.OTHER_OFFICIAL_DATA,
        producer_mapping_basis=ProducerMappingBasis.DIRECT_SOURCE_METADATA,
        evidence=(
            RightsEvidence(
                kind=RightsEvidenceKind.SOURCE_METADATA,
                official_url="https://example.org/api/tables/TABLE_001",
                accessed_on=date(2026, 7, 16),
                claims=(
                    EvidenceClaim.SERIES_SCOPE,
                    EvidenceClaim.ORIGINAL_PRODUCER,
                    EvidenceClaim.TITLE_FREQUENCY,
                ),
                assertion="The exact synthetic scope is produced by the example institution.",
                observed=EvidenceObservation(
                    source_system=SourceSystem.OTHER_OFFICIAL,
                    table_id="TABLE_001",
                    item_id="ITEM_001",
                    table_title="Synthetic Statistics Table",
                    item_title="Synthetic Index",
                    mapping_title="Synthetic Statistics Table",
                    frequency="monthly",
                    original_producer="Example Public Institution",
                ),
            ),
            RightsEvidence(
                kind=RightsEvidenceKind.PUBLISHER_USE_GUIDE,
                official_url=rights_instrument.official_url,
                accessed_on=rights_instrument.accessed_on,
                claims=(EvidenceClaim.RIGHTS_TERMS,),
                assertion=rights_instrument.terms_summary,
            ),
        ),
        rights_instrument_id=rights_instrument.instrument_id,
        rights_instrument_url=rights_instrument.official_url,
        rights_instrument_accessed_on=rights_instrument.accessed_on,
        third_party_status=ThirdPartyStatus.FIRST_PARTY,
        operation_rules=(
            OperationRule(operation=RightsOperation.USE, status=OperationStatus.PERMITTED),
            OperationRule(operation=RightsOperation.PROCESS, status=OperationStatus.PERMITTED),
            OperationRule(
                operation=RightsOperation.REDISTRIBUTE,
                status=OperationStatus.PERMITTED,
            ),
            OperationRule(
                operation=RightsOperation.NONCOMMERCIAL_USE,
                status=OperationStatus.PERMITTED,
            ),
            OperationRule(
                operation=RightsOperation.DISTORT,
                status=OperationStatus.PROHIBITED,
                notes="Synthetic terms prohibit distortion.",
            ),
            OperationRule(
                operation=RightsOperation.REIDENTIFY,
                status=OperationStatus.PROHIBITED,
                notes="Synthetic terms prohibit re-identification.",
            ),
        ),
        intended_operations=(
            RightsOperation.USE,
            RightsOperation.PROCESS,
            RightsOperation.REDISTRIBUTE,
            RightsOperation.NONCOMMERCIAL_USE,
        ),
        attribution=AttributionRequirement(
            fields=(
                AttributionField.PUBLISHER,
                AttributionField.ORIGINAL_PRODUCER,
                AttributionField.STATISTIC_NAME,
                AttributionField.RETRIEVAL_DATE,
                AttributionField.SOURCE_URL,
            ),
            template=(
                "Source: {publisher} ({original_producer}), {statistic_name}, "
                "retrieved {retrieval_date}. {source_url}"
            ),
        ),
        decision_state=RedistributionStatus.ALLOWED,
        decision_basis="Synthetic owner-approved ruling for contract tests.",
        approved_by="fixture-owner",
        approval_recorded_at=datetime(2026, 7, 16, 8, 0, tzinfo=UTC),
        approval_record_reference="docs/decisions/9999-example.md#approval-record",
    )


@pytest.fixture
def rights_catalog(
    rights_instrument: RightsInstrument,
    series_rights_decision: SeriesRightsDecision,
) -> RightsCatalog:
    return RightsCatalog(
        catalog_id="example-rights-catalog-001",
        recorded_at=datetime(2026, 7, 16, 9, 0, tzinfo=UTC),
        project_use_profile=ProjectUseProfile.NONCOMMERCIAL_PUBLIC_RESEARCH,
        instruments=(rights_instrument,),
        decisions=(series_rights_decision,),
    )


@pytest.fixture
def document_source() -> SourceManifest:
    return SourceManifest(
        source_id="example-outlook-2024-05-en",
        source_kind=SourceKind.DOCUMENT,
        publisher="Example Public Institution",
        title="Example Economic Outlook",
        document_family="economic-outlook",
        language=LanguageCode.ENGLISH,
        published_on=date(2024, 5, 23),
        publication_date_basis=PublicationDateBasis.PUBLISHER_METADATA,
        retrieved_at=datetime(2026, 7, 14, 8, 0, tzinfo=UTC),
        canonical_url="https://example.org/outlook/2024-05.pdf",
        media_type="application/pdf",
        content_sha256="a" * 64,
        byte_size=12_345,
        redistribution=RedistributionPolicy(
            status=RedistributionStatus.METADATA_ONLY,
            notes="Synthetic fixture; no source content is redistributed.",
        ),
        release_label="May 2024",
    )


@pytest.fixture
def api_source() -> SourceManifest:
    return SourceManifest(
        source_id="example-oecd-sdmx-api",
        source_kind=SourceKind.API,
        publisher="Example Public Institution",
        title="Example SDMX API snapshot",
        document_family="sdmx-api",
        language=LanguageCode.UNDETERMINED,
        published_on=date(2024, 1, 1),
        publication_date_basis=PublicationDateBasis.PUBLISHER_METADATA,
        retrieved_at=datetime(2026, 7, 14, 8, 0, tzinfo=UTC),
        canonical_url="https://example.org/api/sdmx/data",
        media_type="application/json",
        content_sha256="b" * 64,
        byte_size=2_048,
        redistribution=RedistributionPolicy(
            status=RedistributionStatus.METADATA_ONLY,
            notes="Synthetic fixture.",
        ),
    )


@pytest.fixture
def document_evidence(document_source: SourceManifest) -> DocumentEvidence:
    return DocumentEvidence(
        source_id=document_source.source_id,
        locator=EvidenceLocator(page=3, section="Growth outlook"),
        supports_claim="The example forecast was revised upward.",
    )


@pytest.fixture
def tool_expectation(api_source: SourceManifest) -> ToolExpectation:
    return ToolExpectation(
        source_id=api_source.source_id,
        tool_name="oecd_sdmx",
        arguments={"country": "KOR", "indicator": "REAL_GDP"},
        expected_facts=("The returned observation has an explicit time period.",),
    )


@pytest.fixture
def document_record(
    annotation: AnnotationProvenance,
    document_evidence: DocumentEvidence,
) -> BenchmarkRecord:
    return BenchmarkRecord(
        record_id="example-doc-en-001",
        split=BenchmarkSplit.TEST,
        evidence_group_id="example-release-2024-05",
        parallel_group_id="example-parallel-001",
        language=LanguageCode.ENGLISH,
        question="As of May 2024, why was the example growth forecast revised?",
        as_of=date(2024, 5, 31),
        expected_route=EvidenceRoute.DOCUMENTS,
        document_evidence=(document_evidence,),
        reference_answer="The example report attributes the revision to stronger exports.",
        annotation=annotation,
        tags=("temporal",),
    )
