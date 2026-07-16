"""Validation tests for source provenance snapshots."""

from datetime import date

import pytest
from pydantic import ValidationError

from sovereignlab.schemas import (
    PublicationDateBasis,
    RedistributionPolicy,
    RedistributionStatus,
    SourceManifest,
    VintageSemantics,
)


def test_source_manifest_accepts_a_complete_snapshot(document_source: SourceManifest) -> None:
    assert document_source.schema_version == "2.0.0"
    assert document_source.content_sha256 == "a" * 64
    assert document_source.canonical_url.scheme == "https"
    assert document_source.vintage_semantics is VintageSemantics.LATEST_ONLY
    assert document_source.rights_decision is None


@pytest.mark.parametrize("checksum", ["A" * 64, "a" * 63, "not-a-hash"])
def test_source_manifest_rejects_noncanonical_sha256(
    document_source: SourceManifest,
    checksum: str,
) -> None:
    payload = document_source.model_dump(mode="python")
    payload["content_sha256"] = checksum

    with pytest.raises(ValidationError, match="content_sha256"):
        SourceManifest.model_validate(payload)


def test_source_manifest_requires_timezone_aware_retrieval(
    document_source: SourceManifest,
) -> None:
    payload = document_source.model_dump(mode="python")
    payload["retrieved_at"] = "2026-07-14T08:00:00"

    with pytest.raises(ValidationError, match="timezone"):
        SourceManifest.model_validate(payload)


def test_source_manifest_rejects_retrieval_before_publication(
    document_source: SourceManifest,
) -> None:
    payload = document_source.model_dump(mode="python")
    payload["published_on"] = date(2027, 1, 1)

    with pytest.raises(ValidationError, match="cannot precede"):
        SourceManifest.model_validate(payload)


def test_retrieval_date_fallback_requires_notes(document_source: SourceManifest) -> None:
    payload = document_source.model_dump(mode="python")
    payload["publication_date_basis"] = PublicationDateBasis.RETRIEVAL_DATE_FALLBACK
    payload["publication_date_notes"] = None

    with pytest.raises(ValidationError, match="fallback requires"):
        SourceManifest.model_validate(payload)


def test_allowed_redistribution_requires_license_name() -> None:
    with pytest.raises(ValidationError, match="license_name"):
        RedistributionPolicy(status=RedistributionStatus.ALLOWED)


def test_unknown_redistribution_requires_notes() -> None:
    with pytest.raises(ValidationError, match="requires notes"):
        RedistributionPolicy(status=RedistributionStatus.UNKNOWN)


def test_source_manifest_rejects_undeclared_fields(document_source: SourceManifest) -> None:
    payload = document_source.model_dump(mode="python")
    payload["local_path"] = "private/source.pdf"

    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        SourceManifest.model_validate(payload)


def test_historical_archive_semantics_require_a_data_source(
    document_source: SourceManifest,
) -> None:
    payload = document_source.model_dump(mode="python")
    payload["vintage_semantics"] = VintageSemantics.HISTORICAL_ARCHIVE

    with pytest.raises(ValidationError, match="historical-archive vintage semantics require"):
        SourceManifest.model_validate(payload)


def test_rights_decisions_apply_only_to_data_sources(
    document_source: SourceManifest,
    allowed_api_source: SourceManifest,
) -> None:
    payload = document_source.model_dump(mode="python")
    payload["rights_decision"] = allowed_api_source.rights_decision.model_dump(mode="python")

    with pytest.raises(ValidationError, match="apply only to data sources"):
        SourceManifest.model_validate(payload)


def test_allowed_data_redistribution_requires_a_rights_link(
    allowed_api_source: SourceManifest,
) -> None:
    payload = allowed_api_source.model_dump(mode="python")
    payload["rights_decision"] = None

    with pytest.raises(ValidationError, match="requires a typed rights decision link"):
        SourceManifest.model_validate(payload)


def test_allowed_document_does_not_require_a_rights_link(
    document_source: SourceManifest,
) -> None:
    payload = document_source.model_dump(mode="python")
    payload["redistribution"] = {
        "status": RedistributionStatus.ALLOWED,
        "license_name": "Example Open License",
    }

    manifest = SourceManifest.model_validate(payload)

    assert manifest.redistribution.status is RedistributionStatus.ALLOWED


def test_archive_data_source_with_rights_link_is_valid(
    allowed_api_source: SourceManifest,
) -> None:
    payload = allowed_api_source.model_dump(mode="python")
    payload["vintage_semantics"] = VintageSemantics.HISTORICAL_ARCHIVE

    manifest = SourceManifest.model_validate(payload)

    assert manifest.vintage_semantics is VintageSemantics.HISTORICAL_ARCHIVE
    assert manifest.rights_decision is not None
