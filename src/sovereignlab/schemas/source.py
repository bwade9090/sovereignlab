"""Versioned provenance contract for every evidence snapshot."""

from datetime import date
from enum import StrEnum
from typing import Literal

from pydantic import AnyHttpUrl, AwareDatetime, Field, PositiveInt, model_validator

from sovereignlab.schemas.common import (
    EVIDENCE_SCHEMA_VERSION,
    ExternalIdentifier,
    Identifier,
    MediaType,
    NonEmptyText,
    Sha256,
    SourceSystem,
    StrictModel,
)


class LanguageCode(StrEnum):
    """Languages supported by the MVP plus undetermined/non-linguistic sources."""

    KOREAN = "ko"
    ENGLISH = "en"
    UNDETERMINED = "und"


class SourceKind(StrEnum):
    """Evidence source categories with distinct downstream handling."""

    DOCUMENT = "document"
    DATASET = "dataset"
    API = "api"


class RedistributionStatus(StrEnum):
    """What may be published from a retrieved source snapshot."""

    ALLOWED = "allowed"
    METADATA_ONLY = "metadata_only"
    RESTRICTED = "restricted"
    UNKNOWN = "unknown"


class PublicationDateBasis(StrEnum):
    """How the source availability date was established."""

    PUBLISHER_METADATA = "publisher_metadata"
    CONTENT_DATE = "content_date"
    HTTP_HEADER = "http_header"
    RETRIEVAL_DATE_FALLBACK = "retrieval_date_fallback"


class VintageSemantics(StrEnum):
    """Whether a snapshot is a latest-only response or a consolidated edition archive."""

    LATEST_ONLY = "latest_only"
    HISTORICAL_ARCHIVE = "historical_archive"


class RedistributionPolicy(StrictModel):
    """Source-specific redistribution decision and its evidence."""

    status: RedistributionStatus
    license_name: NonEmptyText | None = None
    license_url: AnyHttpUrl | None = None
    notes: NonEmptyText | None = None

    @model_validator(mode="after")
    def require_auditable_policy(self) -> "RedistributionPolicy":
        if self.status is RedistributionStatus.ALLOWED and self.license_name is None:
            raise ValueError("allowed redistribution requires license_name")
        if (
            self.status in {RedistributionStatus.RESTRICTED, RedistributionStatus.UNKNOWN}
            and self.notes is None
        ):
            raise ValueError(f"{self.status.value} redistribution requires notes")
        return self


class SourceRightsReference(StrictModel):
    """Typed link from one data snapshot to its owner-approved series rights decision."""

    catalog_id: Identifier
    decision_id: Identifier
    source_system: SourceSystem
    table_id: ExternalIdentifier
    item_id: ExternalIdentifier


class SourceManifest(StrictModel):
    """One immutable, release-specific snapshot of an official source."""

    schema_version: Literal["2.0.0"] = EVIDENCE_SCHEMA_VERSION
    source_id: Identifier
    source_kind: SourceKind
    publisher: NonEmptyText
    title: NonEmptyText
    document_family: Identifier
    language: LanguageCode
    published_on: date
    publication_date_basis: PublicationDateBasis
    publication_date_notes: NonEmptyText | None = None
    retrieved_at: AwareDatetime
    canonical_url: AnyHttpUrl
    media_type: MediaType
    content_sha256: Sha256
    byte_size: PositiveInt
    redistribution: RedistributionPolicy
    vintage_semantics: VintageSemantics = VintageSemantics.LATEST_ONLY
    rights_decision: SourceRightsReference | None = None
    release_label: NonEmptyText | None = Field(default=None, max_length=256)

    @model_validator(mode="after")
    def retrieval_cannot_precede_publication(self) -> "SourceManifest":
        if self.retrieved_at.date() < self.published_on:
            raise ValueError("retrieved_at cannot precede published_on")
        if (
            self.publication_date_basis is PublicationDateBasis.RETRIEVAL_DATE_FALLBACK
            and self.publication_date_notes is None
        ):
            raise ValueError("retrieval-date fallback requires publication_date_notes")
        return self

    @model_validator(mode="after")
    def enforce_vintage_and_rights_linkage(self) -> "SourceManifest":
        is_data_source = self.source_kind in {SourceKind.DATASET, SourceKind.API}
        if self.vintage_semantics is VintageSemantics.HISTORICAL_ARCHIVE and not is_data_source:
            raise ValueError("historical-archive vintage semantics require a data source")
        if self.rights_decision is not None and not is_data_source:
            raise ValueError("series rights decisions apply only to data sources")
        if (
            self.redistribution.status is RedistributionStatus.ALLOWED
            and is_data_source
            and self.rights_decision is None
        ):
            raise ValueError("allowed data redistribution requires a typed rights decision link")
        return self
