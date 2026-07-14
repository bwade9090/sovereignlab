"""Reusable, entirely synthetic schema fixtures."""

from datetime import UTC, date, datetime

import pytest

from sovereignlab.schemas import (
    AnnotationProvenance,
    AnnotationStatus,
    BenchmarkRecord,
    BenchmarkSplit,
    DocumentEvidence,
    EvidenceLocator,
    EvidenceRoute,
    LanguageCode,
    PublicationDateBasis,
    RedistributionPolicy,
    RedistributionStatus,
    SourceKind,
    SourceManifest,
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
