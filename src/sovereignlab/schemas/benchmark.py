"""Gold benchmark record contract for routing and evidence evaluation."""

from datetime import date
from enum import StrEnum
from typing import Annotated, Literal

from pydantic import (
    AwareDatetime,
    Field,
    JsonValue,
    PositiveInt,
    StringConstraints,
    model_validator,
)

from sovereignlab.schemas.availability import EditionCode
from sovereignlab.schemas.common import (
    EVIDENCE_SCHEMA_VERSION,
    Identifier,
    NonEmptyText,
    StrictModel,
)
from sovereignlab.schemas.source import LanguageCode

QuestionText = Annotated[str, StringConstraints(min_length=5, max_length=2_000)]


class EvidenceRoute(StrEnum):
    """The mutually exclusive evidence plans evaluated by the router."""

    DOCUMENTS = "documents"
    DATA = "data"
    DOCUMENTS_AND_DATA = "documents_and_data"
    ABSTAIN = "abstain"


class BenchmarkSplit(StrEnum):
    """Evidence-disjoint dataset partitions."""

    TRAIN = "train"
    DEVELOPMENT = "dev"
    TEST = "test"


class AnnotationStatus(StrEnum):
    """Human-review maturity of a benchmark item."""

    DRAFT = "draft"
    REVIEWED = "reviewed"
    APPROVED = "approved"


class AnnotationProvenance(StrictModel):
    """Who created and reviewed a benchmark item, and when."""

    status: AnnotationStatus
    annotated_by: NonEmptyText
    annotated_at: AwareDatetime
    reviewed_by: NonEmptyText | None = None
    reviewed_at: AwareDatetime | None = None

    @model_validator(mode="after")
    def enforce_review_state(self) -> "AnnotationProvenance":
        has_review = self.reviewed_by is not None or self.reviewed_at is not None
        if self.status is AnnotationStatus.DRAFT and has_review:
            raise ValueError("draft annotation cannot contain review metadata")
        if self.status is not AnnotationStatus.DRAFT:
            if self.reviewed_by is None or self.reviewed_at is None:
                raise ValueError("reviewed or approved annotation requires reviewer and timestamp")
            if self.reviewed_at < self.annotated_at:
                raise ValueError("reviewed_at cannot precede annotated_at")
        return self


class EvidenceLocator(StrictModel):
    """A stable locator within a documentary source."""

    page: PositiveInt | None = None
    section: NonEmptyText | None = Field(default=None, max_length=500)
    fragment_id: Identifier | None = None

    @model_validator(mode="after")
    def require_one_locator(self) -> "EvidenceLocator":
        if self.page is None and self.section is None and self.fragment_id is None:
            raise ValueError("at least one evidence locator is required")
        return self


class DocumentEvidence(StrictModel):
    """Expected documentary support for one reference claim."""

    source_id: Identifier
    locator: EvidenceLocator
    supports_claim: NonEmptyText


class VintageEvidence(StrictModel):
    """The ledger-resolved data vintage one temporal tool expectation must use."""

    ledger_id: Identifier
    selected_edition: EditionCode


class ToolExpectation(StrictModel):
    """Expected deterministic tool call and facts derived from its response."""

    source_id: Identifier
    tool_name: Identifier
    arguments: dict[str, JsonValue]
    expected_facts: tuple[NonEmptyText, ...] = Field(min_length=1)
    vintage: VintageEvidence | None = None


class BenchmarkRecord(StrictModel):
    """One auditable routing/evidence task in the bilingual gold benchmark."""

    schema_version: Literal["2.0.0"] = EVIDENCE_SCHEMA_VERSION
    record_id: Identifier
    split: BenchmarkSplit
    evidence_group_id: Identifier
    parallel_group_id: Identifier | None = None
    language: LanguageCode
    question: QuestionText
    as_of: date | None = None
    expected_route: EvidenceRoute
    document_evidence: tuple[DocumentEvidence, ...] = ()
    tool_expectations: tuple[ToolExpectation, ...] = ()
    reference_answer: NonEmptyText | None = None
    abstention_reason: NonEmptyText | None = None
    annotation: AnnotationProvenance
    tags: tuple[Identifier, ...] = ()

    @model_validator(mode="after")
    def enforce_route_contract(self) -> "BenchmarkRecord":
        has_documents = bool(self.document_evidence)
        has_tools = bool(self.tool_expectations)

        expected_inputs = {
            EvidenceRoute.DOCUMENTS: (True, False),
            EvidenceRoute.DATA: (False, True),
            EvidenceRoute.DOCUMENTS_AND_DATA: (True, True),
            EvidenceRoute.ABSTAIN: (False, False),
        }
        if (has_documents, has_tools) != expected_inputs[self.expected_route]:
            raise ValueError(
                f"{self.expected_route.value} route has inconsistent document/tool evidence"
            )

        if self.expected_route is EvidenceRoute.ABSTAIN:
            if self.abstention_reason is None:
                raise ValueError("abstain route requires abstention_reason")
            if self.reference_answer is not None:
                raise ValueError("abstain route cannot contain reference_answer")
        else:
            if self.reference_answer is None:
                raise ValueError("non-abstain route requires reference_answer")
            if self.abstention_reason is not None:
                raise ValueError("non-abstain route cannot contain abstention_reason")

        if "temporal" in self.tags and self.as_of is None:
            raise ValueError("temporal benchmark item requires as_of")
        if self.as_of is None and any(
            expectation.vintage is not None for expectation in self.tool_expectations
        ):
            raise ValueError("vintage evidence requires as_of")
        if len(set(self.tags)) != len(self.tags):
            raise ValueError("benchmark tags must be unique")
        return self
