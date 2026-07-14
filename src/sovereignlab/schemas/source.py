"""Versioned provenance contract for every evidence snapshot."""

from datetime import date
from enum import StrEnum
from typing import Literal

from pydantic import AnyHttpUrl, AwareDatetime, Field, PositiveInt, model_validator

from sovereignlab.schemas.common import (
    SCHEMA_VERSION,
    Identifier,
    MediaType,
    NonEmptyText,
    Sha256,
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


class SourceManifest(StrictModel):
    """One immutable, release-specific snapshot of an official source."""

    schema_version: Literal["1.0.0"] = SCHEMA_VERSION
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
