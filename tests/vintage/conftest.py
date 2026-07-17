"""Synthetic provenance fixtures for vintage resolver tests."""

from datetime import UTC, date, datetime

import pytest

from sovereignlab.schemas import (
    AvailabilityAssertion,
    AvailabilityEvidence,
    AvailabilityEvidenceBasis,
    EditionAvailabilityLedger,
    EditionAvailabilityRecord,
    EditionResolutionStatus,
    LanguageCode,
    PublicationDateBasis,
    RedistributionPolicy,
    RedistributionStatus,
    SourceKind,
    SourceManifest,
    VintageSemantics,
)


@pytest.fixture
def archive_source() -> SourceManifest:
    return SourceManifest(
        source_id="example-archive-flow",
        source_kind=SourceKind.DATASET,
        publisher="Example Public Institution",
        title="Example consolidated edition archive",
        document_family="sdmx-archive",
        language=LanguageCode.UNDETERMINED,
        published_on=date(2026, 7, 14),
        publication_date_basis=PublicationDateBasis.PUBLISHER_METADATA,
        retrieved_at=datetime(2026, 7, 14, 8, 0, tzinfo=UTC),
        canonical_url="https://example.org/api/sdmx/archive",
        media_type="text/csv",
        content_sha256="d" * 64,
        byte_size=8_192,
        redistribution=RedistributionPolicy(
            status=RedistributionStatus.METADATA_ONLY,
            notes="Synthetic fixture.",
        ),
        vintage_semantics=VintageSemantics.HISTORICAL_ARCHIVE,
    )


def _evidence(
    *,
    supports: AvailabilityAssertion,
    asserted_instant: datetime,
) -> AvailabilityEvidence:
    return AvailabilityEvidence(
        basis=AvailabilityEvidenceBasis.FIRST_OBSERVED_AT,
        supports=supports,
        asserted_instant=asserted_instant,
        source_manifest_ids=("example-capture-manifest",),
    )


@pytest.fixture
def availability_ledger() -> EditionAvailabilityLedger:
    may_available = datetime(2024, 5, 10, 9, 0, tzinfo=UTC)
    june_available = datetime(2024, 6, 12, 9, 0, tzinfo=UTC)
    june_absent = datetime(2024, 6, 11, 9, 0, tzinfo=UTC)
    return EditionAvailabilityLedger(
        ledger_id="example-availability-ledger-001",
        dataflow_id="EXAMPLE:DSD_EXAMPLE@DF_EXAMPLE",
        dataflow_version="1.0",
        generated_at=datetime(2026, 7, 14, 9, 0, tzinfo=UTC),
        captured_at=datetime(2026, 7, 14, 8, 0, tzinfo=UTC),
        complete_through=datetime(2026, 7, 14, 8, 0, tzinfo=UTC),
        cutoff_timezone="Asia/Seoul",
        editions=(
            EditionAvailabilityRecord(
                edition="202405",
                status=EditionResolutionStatus.RESOLVED,
                available_by=may_available,
                evidence=(
                    _evidence(
                        supports=AvailabilityAssertion.AVAILABLE_BY,
                        asserted_instant=may_available,
                    ),
                ),
            ),
            EditionAvailabilityRecord(
                edition="202406",
                status=EditionResolutionStatus.RESOLVED,
                available_by=june_available,
                last_absent_at=june_absent,
                evidence=(
                    _evidence(
                        supports=AvailabilityAssertion.AVAILABLE_BY,
                        asserted_instant=june_available,
                    ),
                    _evidence(
                        supports=AvailabilityAssertion.LAST_ABSENT_AT,
                        asserted_instant=june_absent,
                    ),
                ),
            ),
        ),
    )
