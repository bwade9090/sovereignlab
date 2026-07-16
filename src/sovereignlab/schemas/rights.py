"""Strict, versioned contracts for source-specific series rights decisions."""

import re
import unicodedata
from datetime import date
from enum import StrEnum
from string import Formatter
from typing import Annotated, Literal

from pydantic import (
    AnyHttpUrl,
    AwareDatetime,
    Field,
    PositiveInt,
    StringConstraints,
    model_validator,
)

from sovereignlab.schemas.common import (
    SCHEMA_VERSION,
    Identifier,
    NonEmptyText,
    Sha256,
    StrictModel,
)
from sovereignlab.schemas.source import RedistributionStatus

ExternalIdentifier = Annotated[
    str,
    StringConstraints(
        min_length=1,
        max_length=256,
        pattern=r"^[A-Za-z0-9][A-Za-z0-9._:/-]*$",
    ),
]
ApprovalRecordReference = Annotated[
    str,
    StringConstraints(
        pattern=r"^docs/decisions/[0-9]{4}-[a-z0-9-]+\.md#approval-record$",
    ),
]


class SourceSystem(StrEnum):
    """Official systems for which the rights contract has an explicit policy branch."""

    ECOS = "ecos"
    KOSIS = "kosis"
    OECD = "oecd"
    OTHER_OFFICIAL = "other_official"


class KosisContentCategory(StrEnum):
    """KOSIS use-guide categories with materially different redistribution terms."""

    DOMESTIC_STATISTICS = "domestic_statistics"
    EASY_VIEW_STATISTICS = "easy_view_statistics"
    INTERNATIONAL_STATISTICS = "international_statistics"
    NORTH_KOREA_STATISTICS = "north_korea_statistics"
    PUBLICATION = "publication"


class RightsOperation(StrEnum):
    """Operations that an official rights instrument may permit or prohibit."""

    USE = "use"
    PROCESS = "process"
    REDISTRIBUTE = "redistribute"
    COMMERCIAL_USE = "commercial_use"
    NONCOMMERCIAL_USE = "noncommercial_use"
    SELL_UNCHANGED = "sell_unchanged"
    DISTORT = "distort"
    REIDENTIFY = "reidentify"


class OperationStatus(StrEnum):
    """The exact legal status assigned to one operation by the instrument."""

    PERMITTED = "permitted"
    PROHIBITED = "prohibited"
    REQUIRES_ADDITIONAL_APPROVAL = "requires_additional_approval"
    NOT_EXPRESSLY_GRANTED = "not_expressly_granted"


class ProjectUseProfile(StrEnum):
    """Approved use profile against which every catalog decision is evaluated."""

    NONCOMMERCIAL_PUBLIC_RESEARCH = "noncommercial_public_research"


class ContentClass(StrEnum):
    """Publisher category that selects the applicable branch of a use guide."""

    ECOS_BOK_AUTHORED = "ecos_bok_authored"
    ECOS_OTHER_AUTHORED = "ecos_other_authored"
    KOSIS_DOMESTIC_STATISTICS = "kosis_domestic_statistics"
    KOSIS_EASY_VIEW_STATISTICS = "kosis_easy_view_statistics"
    KOSIS_INTERNATIONAL_STATISTICS = "kosis_international_statistics"
    KOSIS_NORTH_KOREA_STATISTICS = "kosis_north_korea_statistics"
    KOSIS_PUBLICATION = "kosis_publication"
    OECD_DATA = "oecd_data"
    OTHER_OFFICIAL_DATA = "other_official_data"


class ProducerMappingBasis(StrEnum):
    """How an exact series was mapped to its producer or content category."""

    DIRECT_SOURCE_METADATA = "direct_source_metadata"
    OWNER_APPROVED_OFFICIAL_CROSS_SOURCE_TITLE_FREQUENCY_MAPPING = (
        "owner_approved_official_cross_source_title_frequency_mapping"
    )
    OFFICIAL_PUBLISHER_DOCUMENTATION = "official_publisher_documentation"
    OFFICIAL_CONTENT_CATEGORY = "official_content_category"
    UNRESOLVED = "unresolved"


class RightsEvidenceKind(StrEnum):
    """Official evidence types supporting producer/category and rights mappings."""

    SOURCE_METADATA = "source_metadata"
    PUBLISHER_USE_GUIDE = "publisher_use_guide"
    OFFICIAL_CROSS_SOURCE_CATALOG = "official_cross_source_catalog"
    OFFICIAL_PUBLISHER_RELEASE = "official_publisher_release"
    DATASET_TERMS = "dataset_terms"
    PRODUCER_SPECIFIC_TERMS = "producer_specific_terms"


class EvidenceClaim(StrEnum):
    """Facts an evidence record explicitly asserts."""

    RIGHTS_TERMS = "rights_terms"
    SERIES_SCOPE = "series_scope"
    ORIGINAL_PRODUCER = "original_producer"
    TITLE_FREQUENCY = "title_frequency"
    CONTENT_CATEGORY = "content_category"


class AttributionField(StrEnum):
    """Structured source details that must accompany redistributed statistics."""

    PUBLISHER = "publisher"
    ORIGINAL_PRODUCER = "original_producer"
    STATISTIC_NAME = "statistic_name"
    SURVEY_NAME = "survey_name"
    TABLE_NAME = "table_name"
    AUTHORING_DATE = "authoring_date"
    REFERENCE_DATE = "reference_date"
    RETRIEVAL_DATE = "retrieval_date"
    SOURCE_URL = "source_url"


class ThirdPartyStatus(StrEnum):
    """Whether the portal publisher is also the original statistical producer."""

    FIRST_PARTY = "first_party"
    THIRD_PARTY = "third_party"
    UNKNOWN = "unknown"


class OperationRule(StrictModel):
    """One operation and its exact status under the cited rights instrument."""

    operation: RightsOperation
    status: OperationStatus
    notes: NonEmptyText | None = None

    @model_validator(mode="after")
    def explain_nonpermitted_status(self) -> "OperationRule":
        if self.status is not OperationStatus.PERMITTED and self.notes is None:
            raise ValueError("non-permitted operation status requires notes")
        return self


class EvidenceObservation(StrictModel):
    """Structured facts observed at one official evidence URL."""

    source_system: SourceSystem | None = None
    table_id: ExternalIdentifier | None = None
    item_id: ExternalIdentifier | None = None
    table_title: NonEmptyText | None = None
    item_title: NonEmptyText | None = None
    mapping_title: NonEmptyText | None = None
    frequency: NonEmptyText | None = None
    original_producer: NonEmptyText | None = None
    kosis_content_category: KosisContentCategory | None = None


class RightsEvidence(StrictModel):
    """One official URL and the structured claims observed there."""

    kind: RightsEvidenceKind
    official_url: AnyHttpUrl
    accessed_on: date
    claims: tuple[EvidenceClaim, ...] = Field(min_length=1)
    assertion: NonEmptyText
    observed: EvidenceObservation | None = None

    @model_validator(mode="after")
    def require_claim_observations(self) -> "RightsEvidence":
        _require_unique(self.claims, "evidence claims")
        observed = self.observed
        non_terms_claims = set(self.claims) - {EvidenceClaim.RIGHTS_TERMS}
        if non_terms_claims and observed is None:
            raise ValueError("non-terms evidence claims require structured observations")
        if observed is None:
            return self
        if EvidenceClaim.SERIES_SCOPE in self.claims and (
            observed.source_system is None or observed.table_id is None or observed.item_id is None
        ):
            raise ValueError("series-scope claim requires source system, table ID, and item ID")
        if EvidenceClaim.ORIGINAL_PRODUCER in self.claims and observed.original_producer is None:
            raise ValueError("producer claim requires observed original_producer")
        if EvidenceClaim.TITLE_FREQUENCY in self.claims and (
            observed.frequency is None
            or (observed.table_title is None and observed.mapping_title is None)
        ):
            raise ValueError("title/frequency claim requires an observed title and frequency")
        if (
            EvidenceClaim.CONTENT_CATEGORY in self.claims
            and observed.kosis_content_category is None
        ):
            raise ValueError("content-category claim requires observed KOSIS category")
        return self


class AttributionRequirement(StrictModel):
    """Structured attribution fields plus a mechanically checkable template."""

    fields: tuple[AttributionField, ...] = Field(min_length=1)
    template: NonEmptyText

    @model_validator(mode="after")
    def match_template_to_fields(self) -> "AttributionRequirement":
        _require_unique(self.fields, "attribution fields")
        try:
            parsed = tuple(Formatter().parse(self.template))
        except ValueError as error:
            raise ValueError("attribution template is not valid format syntax") from error

        placeholders: list[str] = []
        for _, field_name, format_spec, conversion in parsed:
            if field_name is None:
                continue
            if format_spec or conversion or "." in field_name or "[" in field_name:
                raise ValueError("attribution placeholders must be plain field names")
            placeholders.append(field_name)
        _require_unique(tuple(placeholders), "attribution placeholders")
        declared = {field.value for field in self.fields}
        if set(placeholders) != declared:
            raise ValueError("attribution placeholders must exactly match declared fields")
        return self


class InstrumentVerificationCapture(StrictModel):
    """Optional immutable capture proof for a dynamic official use-guide page."""

    capture_url: AnyHttpUrl
    captured_at: AwareDatetime
    content_sha256: Sha256
    byte_size: PositiveInt


class RightsInstrument(StrictModel):
    """One immutable capture of an official licence or publisher use guide."""

    schema_version: Literal["1.0.0"] = SCHEMA_VERSION
    instrument_id: Identifier
    issuer: NonEmptyText
    title: NonEmptyText
    official_url: AnyHttpUrl
    accessed_on: date
    applicable_source_systems: tuple[SourceSystem, ...] = Field(min_length=1)
    applicable_content_classes: tuple[ContentClass, ...] = Field(min_length=1)
    license_identifier: NonEmptyText | None = None
    terms_summary: NonEmptyText
    terms_evidence: RightsEvidence
    verification_capture: InstrumentVerificationCapture | None = None

    @model_validator(mode="after")
    def enforce_instrument_scope_and_evidence(self) -> "RightsInstrument":
        _require_unique(self.applicable_source_systems, "applicable_source_systems")
        _require_unique(self.applicable_content_classes, "applicable_content_classes")
        for content_class in self.applicable_content_classes:
            expected_system, _ = _content_class_scope(content_class)
            if expected_system not in self.applicable_source_systems:
                raise ValueError("instrument content class is outside its source-system scope")

        evidence = self.terms_evidence
        if EvidenceClaim.RIGHTS_TERMS not in evidence.claims:
            raise ValueError("instrument terms evidence must claim rights terms")
        if evidence.kind not in {
            RightsEvidenceKind.PUBLISHER_USE_GUIDE,
            RightsEvidenceKind.DATASET_TERMS,
            RightsEvidenceKind.PRODUCER_SPECIFIC_TERMS,
        }:
            raise ValueError("instrument terms evidence has an invalid evidence kind")
        if evidence.official_url != self.official_url:
            raise ValueError("instrument terms-evidence URL must match official_url")
        if evidence.accessed_on != self.accessed_on:
            raise ValueError("instrument terms-evidence access date must match accessed_on")
        if evidence.assertion != self.terms_summary:
            raise ValueError("instrument terms-evidence assertion must match terms_summary")
        return self


class SeriesRightsDecision(StrictModel):
    """An auditable ruling for one exact publisher table/item scope."""

    schema_version: Literal["1.0.0"] = SCHEMA_VERSION
    decision_id: Identifier
    publisher: NonEmptyText
    original_producer: NonEmptyText | None = None
    kosis_content_category: KosisContentCategory | None = None
    source_system: SourceSystem
    table_id: ExternalIdentifier
    item_id: ExternalIdentifier
    table_title: NonEmptyText
    item_title: NonEmptyText
    producer_mapping_title: NonEmptyText
    frequency: NonEmptyText
    unit: NonEmptyText
    content_class: ContentClass
    producer_mapping_basis: ProducerMappingBasis
    evidence: tuple[RightsEvidence, ...] = Field(min_length=1)
    rights_instrument_id: Identifier
    rights_instrument_url: AnyHttpUrl
    rights_instrument_accessed_on: date
    third_party_status: ThirdPartyStatus
    operation_rules: tuple[OperationRule, ...] = Field(min_length=1)
    intended_operations: tuple[RightsOperation, ...] = Field(min_length=1)
    attribution: AttributionRequirement | None = None
    decision_state: RedistributionStatus
    decision_basis: NonEmptyText
    approved_by: NonEmptyText | None = None
    approval_recorded_at: AwareDatetime | None = None
    approval_record_reference: ApprovalRecordReference | None = None
    valid_until: date | None = None

    @model_validator(mode="after")
    def enforce_decision_integrity(self) -> "SeriesRightsDecision":
        self._validate_classification()
        self._validate_evidence()
        self._validate_approval()
        self._validate_allowed_decision()
        if (
            self.valid_until is not None
            and self.approval_recorded_at is not None
            and self.valid_until < self.approval_recorded_at.date()
        ):
            raise ValueError("valid_until cannot precede approval_recorded_at")
        return self

    def _validate_classification(self) -> None:
        expected_system, expected_category = _content_class_scope(self.content_class)
        if self.source_system is not expected_system:
            raise ValueError("content class does not match source system")
        if self.kosis_content_category is not expected_category:
            raise ValueError("content class does not match exact KOSIS content category")
        if self.content_class is ContentClass.ECOS_BOK_AUTHORED and (
            self.original_producer != "한국은행"
            or self.third_party_status is not ThirdPartyStatus.FIRST_PARTY
        ):
            raise ValueError(
                "ECOS Bank of Korea classification requires 한국은행 as first-party producer"
            )
        if self.content_class is ContentClass.ECOS_OTHER_AUTHORED and (
            self.original_producer is None
            or self.third_party_status is not ThirdPartyStatus.THIRD_PARTY
        ):
            raise ValueError(
                "ECOS other-authored classification requires a named third-party producer"
            )
        if self.original_producer is None and self.kosis_content_category is None:
            raise ValueError("series rights decision requires a producer or KOSIS content category")
        if (
            self.third_party_status is ThirdPartyStatus.FIRST_PARTY
            and self.publisher != self.original_producer
        ):
            raise ValueError("first-party classification requires publisher to equal producer")
        if (
            self.third_party_status is ThirdPartyStatus.THIRD_PARTY
            and self.publisher == self.original_producer
        ):
            raise ValueError("third-party classification requires publisher and producer to differ")

    def _validate_evidence(self) -> None:
        _require_unique(
            tuple(rule.operation for rule in self.operation_rules),
            "operation_rules operations",
        )
        _require_unique(self.intended_operations, "intended_operations")
        evidence_keys = tuple((item.kind, str(item.official_url)) for item in self.evidence)
        _require_unique(evidence_keys, "evidence kind/URL pairs")

        if self.source_system is SourceSystem.KOSIS and not any(
            item.kind is RightsEvidenceKind.SOURCE_METADATA
            and item.observed is not None
            and item.observed.source_system is SourceSystem.KOSIS
            and item.observed.kosis_content_category is self.kosis_content_category
            and EvidenceClaim.CONTENT_CATEGORY in item.claims
            for item in self.evidence
        ):
            raise ValueError("KOSIS decision requires exact content-category evidence")

        if self.producer_mapping_basis is ProducerMappingBasis.DIRECT_SOURCE_METADATA:
            if not self._has_exact_source_scope_evidence():
                raise ValueError("direct mapping requires exact source-scope metadata evidence")
            if not self._has_exact_producer_evidence(RightsEvidenceKind.SOURCE_METADATA):
                raise ValueError("direct mapping requires exact producer metadata evidence")
        elif (
            self.producer_mapping_basis
            is ProducerMappingBasis.OWNER_APPROVED_OFFICIAL_CROSS_SOURCE_TITLE_FREQUENCY_MAPPING
        ):
            if _normalize_mapping_title(self.table_title) != _normalize_mapping_title(
                self.producer_mapping_title
            ):
                raise ValueError(
                    "cross-source mapping requires equivalent normalized source and mapping titles"
                )
            if not self._has_exact_source_scope_evidence():
                raise ValueError(
                    "cross-source mapping requires exact source-scope metadata evidence"
                )
            if not self._has_exact_producer_evidence(
                RightsEvidenceKind.OFFICIAL_CROSS_SOURCE_CATALOG
            ):
                raise ValueError(
                    "cross-source mapping requires exact official producer/title/frequency evidence"
                )
        elif self.producer_mapping_basis is ProducerMappingBasis.OFFICIAL_PUBLISHER_DOCUMENTATION:
            if not self._has_exact_source_scope_evidence() or not self._has_exact_producer_evidence(
                RightsEvidenceKind.OFFICIAL_PUBLISHER_RELEASE
            ):
                raise ValueError(
                    "publisher-documentation mapping requires exact scope and producer evidence"
                )

    def _validate_approval(self) -> None:
        approval_parts = (
            self.approved_by,
            self.approval_recorded_at,
            self.approval_record_reference,
        )
        if any(part is not None for part in approval_parts) and not all(
            part is not None for part in approval_parts
        ):
            raise ValueError("approval fields must be provided as a complete trio")

    def _validate_allowed_decision(self) -> None:
        if self.decision_state is not RedistributionStatus.ALLOWED:
            return
        if (
            self.approved_by is None
            or self.approval_recorded_at is None
            or self.approval_record_reference is None
        ):
            raise ValueError("allowed decision requires a complete approval record")
        if self.original_producer is None:
            raise ValueError("allowed decision requires an original producer")
        if self.producer_mapping_basis in {
            ProducerMappingBasis.OFFICIAL_CONTENT_CATEGORY,
            ProducerMappingBasis.UNRESOLVED,
        }:
            raise ValueError("allowed decision requires a resolved producer mapping")

        required_intended = {
            RightsOperation.USE,
            RightsOperation.PROCESS,
            RightsOperation.REDISTRIBUTE,
            RightsOperation.NONCOMMERCIAL_USE,
        }
        if not required_intended.issubset(self.intended_operations):
            raise ValueError("allowed decision is missing required intended operations")

        if self.content_class is ContentClass.OECD_DATA:
            raise ValueError("OECD data cannot be raw allowed under the current policy")
        if self.content_class in {
            ContentClass.KOSIS_INTERNATIONAL_STATISTICS,
            ContentClass.KOSIS_NORTH_KOREA_STATISTICS,
        }:
            raise ValueError("KOSIS international/North Korea data cannot be redistributed")

        evidence_kinds = {item.kind for item in self.evidence}
        if self.content_class is ContentClass.ECOS_OTHER_AUTHORED and (
            RightsEvidenceKind.PRODUCER_SPECIFIC_TERMS not in evidence_kinds
        ):
            raise ValueError("ECOS third-party raw redistribution requires producer-specific terms")
        if self.content_class is ContentClass.KOSIS_PUBLICATION and (
            RightsEvidenceKind.DATASET_TERMS not in evidence_kinds
        ):
            raise ValueError("KOSIS publication raw redistribution requires dataset terms")

        rule_by_operation = {rule.operation: rule for rule in self.operation_rules}
        if any(
            rule_by_operation.get(operation) is None
            or rule_by_operation[operation].status is not OperationStatus.PERMITTED
            for operation in self.intended_operations
        ):
            raise ValueError("allowed decision requires every intended operation to be permitted")
        distort_rule = rule_by_operation.get(RightsOperation.DISTORT)
        if distort_rule is None or distort_rule.status is not OperationStatus.PROHIBITED:
            raise ValueError("allowed decision requires distortion to be prohibited")

        if self.attribution is None:
            raise ValueError("allowed decision requires structured attribution")
        common_attribution = {
            AttributionField.PUBLISHER,
            AttributionField.ORIGINAL_PRODUCER,
            AttributionField.STATISTIC_NAME,
            AttributionField.RETRIEVAL_DATE,
            AttributionField.SOURCE_URL,
        }
        if not common_attribution.issubset(self.attribution.fields):
            raise ValueError("allowed decision is missing common attribution fields")

        if self.content_class in {
            ContentClass.KOSIS_DOMESTIC_STATISTICS,
            ContentClass.KOSIS_EASY_VIEW_STATISTICS,
        }:
            for operation in (RightsOperation.SELL_UNCHANGED, RightsOperation.REIDENTIFY):
                rule = rule_by_operation.get(operation)
                if rule is None or rule.status is not OperationStatus.PROHIBITED:
                    raise ValueError(
                        "KOSIS domestic/easy-view allowed decision is missing prohibited operations"
                    )
            detailed_attribution = {
                AttributionField.SURVEY_NAME,
                AttributionField.TABLE_NAME,
                AttributionField.AUTHORING_DATE,
                AttributionField.REFERENCE_DATE,
            }
            if not detailed_attribution.issubset(self.attribution.fields):
                raise ValueError(
                    "KOSIS domestic/easy-view decision is missing detailed attribution fields"
                )

    def _has_exact_source_scope_evidence(self) -> bool:
        for item in self.evidence:
            observed = item.observed
            if (
                item.kind is RightsEvidenceKind.SOURCE_METADATA
                and observed is not None
                and {EvidenceClaim.SERIES_SCOPE, EvidenceClaim.TITLE_FREQUENCY}.issubset(
                    item.claims
                )
                and observed.source_system is self.source_system
                and observed.table_id == self.table_id
                and observed.item_id == self.item_id
                and observed.table_title == self.table_title
                and observed.item_title == self.item_title
                and observed.frequency == self.frequency
            ):
                return True
        return False

    def _has_exact_producer_evidence(self, evidence_kind: RightsEvidenceKind) -> bool:
        for item in self.evidence:
            observed = item.observed
            if (
                item.kind is evidence_kind
                and observed is not None
                and {EvidenceClaim.ORIGINAL_PRODUCER, EvidenceClaim.TITLE_FREQUENCY}.issubset(
                    item.claims
                )
                and observed.original_producer == self.original_producer
                and observed.mapping_title == self.producer_mapping_title
                and observed.frequency == self.frequency
                and (
                    evidence_kind is not RightsEvidenceKind.OFFICIAL_CROSS_SOURCE_CATALOG
                    or (
                        observed.source_system is not None
                        and observed.source_system is not self.source_system
                    )
                )
                and (
                    evidence_kind is not RightsEvidenceKind.SOURCE_METADATA
                    or (
                        observed.source_system is self.source_system
                        and observed.table_id == self.table_id
                    )
                )
            ):
                return True
        return False

    @property
    def scope(self) -> tuple[str, str, str, str]:
        """Return the exact scope key used by the catalog cross-record validator."""

        return (self.publisher, self.source_system.value, self.table_id, self.item_id)


class RightsCatalog(StrictModel):
    """Resolve instrument references and reject ambiguous per-series rulings."""

    schema_version: Literal["1.0.0"] = SCHEMA_VERSION
    catalog_id: Identifier
    recorded_at: AwareDatetime
    project_use_profile: ProjectUseProfile
    supersedes_catalog_id: Identifier | None = None
    instruments: tuple[RightsInstrument, ...] = Field(min_length=1)
    decisions: tuple[SeriesRightsDecision, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def enforce_catalog_integrity(self) -> "RightsCatalog":
        if self.supersedes_catalog_id == self.catalog_id:
            raise ValueError("catalog cannot supersede itself")

        instrument_by_id = _unique_by_attribute(self.instruments, "instrument_id")
        _unique_by_attribute(self.decisions, "decision_id")

        scope_by_decision: dict[tuple[str, str, str, str], str] = {}
        for instrument in self.instruments:
            if instrument.accessed_on > self.recorded_at.date():
                raise ValueError(
                    f"instrument {instrument.instrument_id} access cannot follow catalog recording"
                )
            capture = instrument.verification_capture
            if capture is not None and capture.captured_at > self.recorded_at:
                raise ValueError(
                    f"instrument {instrument.instrument_id} capture cannot follow catalog recording"
                )

        for decision in self.decisions:
            existing = scope_by_decision.setdefault(decision.scope, decision.decision_id)
            if existing != decision.decision_id:
                raise ValueError(
                    f"series scope {decision.scope!r} has multiple decisions: "
                    f"{existing}, {decision.decision_id}"
                )

            instrument = instrument_by_id.get(decision.rights_instrument_id)
            if instrument is None:
                raise ValueError(
                    f"decision {decision.decision_id} references unknown rights instrument "
                    f"{decision.rights_instrument_id}"
                )
            if decision.source_system not in instrument.applicable_source_systems:
                raise ValueError("decision source system is outside rights-instrument scope")
            if decision.content_class not in instrument.applicable_content_classes:
                raise ValueError("decision content class is outside rights-instrument scope")
            if decision.rights_instrument_url != instrument.official_url:
                raise ValueError(
                    f"decision {decision.decision_id} rights-instrument URL does not match catalog"
                )
            if decision.rights_instrument_accessed_on != instrument.accessed_on:
                raise ValueError(
                    f"decision {decision.decision_id} rights-instrument access date does not "
                    "match catalog"
                )
            if (
                decision.approval_recorded_at is not None
                and decision.approval_recorded_at.date() < instrument.accessed_on
            ):
                raise ValueError(
                    f"decision {decision.decision_id} approval cannot precede instrument access"
                )
            if (
                decision.approval_recorded_at is not None
                and decision.approval_recorded_at > self.recorded_at
            ):
                raise ValueError(
                    f"decision {decision.decision_id} approval cannot follow catalog recording"
                )
            if any(item.accessed_on > self.recorded_at.date() for item in decision.evidence):
                raise ValueError(
                    f"decision {decision.decision_id} evidence access cannot follow "
                    "catalog recording"
                )
            if (
                decision.decision_state is RedistributionStatus.ALLOWED
                and decision.valid_until is not None
                and decision.valid_until < self.recorded_at.date()
            ):
                raise ValueError(f"decision {decision.decision_id} is expired at catalog recording")
            if (
                self.project_use_profile is ProjectUseProfile.NONCOMMERCIAL_PUBLIC_RESEARCH
                and RightsOperation.COMMERCIAL_USE in decision.intended_operations
            ):
                raise ValueError("noncommercial catalog cannot intend commercial use")
            if (
                decision.decision_state is RedistributionStatus.ALLOWED
                and decision.content_class is ContentClass.ECOS_OTHER_AUTHORED
                and instrument.terms_evidence.kind is not RightsEvidenceKind.PRODUCER_SPECIFIC_TERMS
            ):
                raise ValueError(
                    "ECOS third-party allowed decision requires a producer-specific instrument"
                )
            if (
                decision.decision_state is RedistributionStatus.ALLOWED
                and decision.content_class is ContentClass.KOSIS_PUBLICATION
                and (
                    instrument.license_identifier is None
                    or instrument.terms_evidence.kind is not RightsEvidenceKind.DATASET_TERMS
                )
            ):
                raise ValueError(
                    "KOSIS publication allowed decision requires licensed dataset-terms instrument"
                )
        return self


def _content_class_scope(
    content_class: ContentClass,
) -> tuple[SourceSystem, KosisContentCategory | None]:
    mapping = {
        ContentClass.ECOS_BOK_AUTHORED: (SourceSystem.ECOS, None),
        ContentClass.ECOS_OTHER_AUTHORED: (SourceSystem.ECOS, None),
        ContentClass.KOSIS_DOMESTIC_STATISTICS: (
            SourceSystem.KOSIS,
            KosisContentCategory.DOMESTIC_STATISTICS,
        ),
        ContentClass.KOSIS_EASY_VIEW_STATISTICS: (
            SourceSystem.KOSIS,
            KosisContentCategory.EASY_VIEW_STATISTICS,
        ),
        ContentClass.KOSIS_INTERNATIONAL_STATISTICS: (
            SourceSystem.KOSIS,
            KosisContentCategory.INTERNATIONAL_STATISTICS,
        ),
        ContentClass.KOSIS_NORTH_KOREA_STATISTICS: (
            SourceSystem.KOSIS,
            KosisContentCategory.NORTH_KOREA_STATISTICS,
        ),
        ContentClass.KOSIS_PUBLICATION: (
            SourceSystem.KOSIS,
            KosisContentCategory.PUBLICATION,
        ),
        ContentClass.OECD_DATA: (SourceSystem.OECD, None),
        ContentClass.OTHER_OFFICIAL_DATA: (SourceSystem.OTHER_OFFICIAL, None),
    }
    return mapping[content_class]


def _normalize_mapping_title(value: str) -> str:
    normalized = unicodedata.normalize("NFKC", value).strip()
    without_outline_prefix = re.sub(r"^\d+(?:\.\d+)*\.\s*", "", normalized)
    return " ".join(without_outline_prefix.split())


def _require_unique(items: tuple[object, ...], field_name: str) -> None:
    if len(set(items)) != len(items):
        raise ValueError(f"{field_name} must contain unique values")


def _unique_by_attribute[IndexedModel](
    items: tuple[IndexedModel, ...], attribute: str
) -> dict[str, IndexedModel]:
    indexed: dict[str, IndexedModel] = {}
    for item in items:
        item_id = getattr(item, attribute)
        if item_id in indexed:
            raise ValueError(f"duplicate {attribute}: {item_id}")
        indexed[item_id] = item
    return indexed
