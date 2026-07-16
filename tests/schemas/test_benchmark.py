"""Validation tests for individual gold benchmark records."""

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from sovereignlab.schemas import (
    AnnotationProvenance,
    AnnotationStatus,
    BenchmarkRecord,
    BenchmarkSplit,
    DocumentEvidence,
    EvidenceLocator,
    EvidenceRoute,
    LanguageCode,
    ToolExpectation,
)


@pytest.mark.parametrize(
    ("route", "use_documents", "use_tools", "reference_answer", "abstention_reason"),
    [
        (EvidenceRoute.DOCUMENTS, True, False, "Document answer.", None),
        (EvidenceRoute.DATA, False, True, "Data answer.", None),
        (EvidenceRoute.DOCUMENTS_AND_DATA, True, True, "Combined answer.", None),
        (EvidenceRoute.ABSTAIN, False, False, None, "Approved sources cannot answer."),
    ],
)
def test_each_route_has_one_valid_evidence_shape(
    annotation: AnnotationProvenance,
    document_evidence: DocumentEvidence,
    tool_expectation: ToolExpectation,
    route: EvidenceRoute,
    use_documents: bool,
    use_tools: bool,
    reference_answer: str | None,
    abstention_reason: str | None,
) -> None:
    record = _record(
        annotation=annotation,
        route=route,
        documents=(document_evidence,) if use_documents else (),
        tools=(tool_expectation,) if use_tools else (),
        reference_answer=reference_answer,
        abstention_reason=abstention_reason,
    )

    assert record.expected_route is route


def test_route_rejects_inconsistent_evidence(
    annotation: AnnotationProvenance,
    tool_expectation: ToolExpectation,
) -> None:
    with pytest.raises(ValidationError, match="inconsistent document/tool evidence"):
        _record(
            annotation=annotation,
            route=EvidenceRoute.DOCUMENTS,
            tools=(tool_expectation,),
            reference_answer="Invalid shape.",
        )


def test_vintage_evidence_requires_as_of(
    annotation: AnnotationProvenance,
    tool_expectation: ToolExpectation,
) -> None:
    expectation_payload = tool_expectation.model_dump(mode="python")
    expectation_payload["vintage"] = {
        "ledger_id": "example-availability-ledger-001",
        "selected_edition": "202405",
    }

    with pytest.raises(ValidationError, match="vintage evidence requires as_of"):
        _record(
            annotation=annotation,
            route=EvidenceRoute.DATA,
            tools=(ToolExpectation.model_validate(expectation_payload),),
            reference_answer="Unreachable without a cutoff.",
        )


def test_temporal_tag_requires_as_of(annotation: AnnotationProvenance) -> None:
    with pytest.raises(ValidationError, match="requires as_of"):
        _record(
            annotation=annotation,
            route=EvidenceRoute.ABSTAIN,
            reference_answer=None,
            abstention_reason="No temporal boundary was supplied.",
            tags=("temporal",),
        )


def test_tags_must_be_unique(annotation: AnnotationProvenance) -> None:
    with pytest.raises(ValidationError, match="tags must be unique"):
        _record(
            annotation=annotation,
            route=EvidenceRoute.ABSTAIN,
            reference_answer=None,
            abstention_reason="Unsupported.",
            tags=("unsupported", "unsupported"),
        )


def test_approved_annotation_requires_complete_review_metadata() -> None:
    with pytest.raises(ValidationError, match="requires reviewer"):
        AnnotationProvenance(
            status=AnnotationStatus.APPROVED,
            annotated_by="author",
            annotated_at=datetime(2026, 7, 14, 8, 0, tzinfo=UTC),
        )


def test_draft_annotation_rejects_review_metadata() -> None:
    with pytest.raises(ValidationError, match="draft annotation"):
        AnnotationProvenance(
            status=AnnotationStatus.DRAFT,
            annotated_by="author",
            annotated_at=datetime(2026, 7, 14, 8, 0, tzinfo=UTC),
            reviewed_by="reviewer",
            reviewed_at=datetime(2026, 7, 14, 9, 0, tzinfo=UTC),
        )


def test_draft_annotation_is_valid_without_review_metadata() -> None:
    annotation = AnnotationProvenance(
        status=AnnotationStatus.DRAFT,
        annotated_by="author",
        annotated_at=datetime(2026, 7, 14, 8, 0, tzinfo=UTC),
    )

    assert annotation.reviewed_by is None
    assert annotation.reviewed_at is None


def test_review_timestamp_cannot_precede_annotation() -> None:
    with pytest.raises(ValidationError, match="cannot precede"):
        AnnotationProvenance(
            status=AnnotationStatus.REVIEWED,
            annotated_by="author",
            annotated_at=datetime(2026, 7, 14, 9, 0, tzinfo=UTC),
            reviewed_by="reviewer",
            reviewed_at=datetime(2026, 7, 14, 8, 0, tzinfo=UTC),
        )


@pytest.mark.parametrize(
    ("route", "reference_answer", "abstention_reason", "message"),
    [
        (EvidenceRoute.ABSTAIN, None, None, "requires abstention_reason"),
        (EvidenceRoute.ABSTAIN, "Should not exist.", "Unsupported.", "cannot contain"),
        (EvidenceRoute.DOCUMENTS, None, None, "requires reference_answer"),
        (EvidenceRoute.DOCUMENTS, "Answer.", "Should not exist.", "cannot contain"),
    ],
)
def test_route_rejects_inconsistent_answer_fields(
    annotation: AnnotationProvenance,
    document_evidence: DocumentEvidence,
    route: EvidenceRoute,
    reference_answer: str | None,
    abstention_reason: str | None,
    message: str,
) -> None:
    with pytest.raises(ValidationError, match=message):
        _record(
            annotation=annotation,
            route=route,
            documents=(document_evidence,) if route is EvidenceRoute.DOCUMENTS else (),
            reference_answer=reference_answer,
            abstention_reason=abstention_reason,
        )


def test_evidence_locator_cannot_be_empty() -> None:
    with pytest.raises(ValidationError, match="at least one"):
        EvidenceLocator()


def _record(
    *,
    annotation: AnnotationProvenance,
    route: EvidenceRoute,
    documents: tuple[DocumentEvidence, ...] = (),
    tools: tuple[ToolExpectation, ...] = (),
    reference_answer: str | None,
    abstention_reason: str | None = None,
    tags: tuple[str, ...] = (),
) -> BenchmarkRecord:
    return BenchmarkRecord(
        record_id="route-shape-test-001",
        split=BenchmarkSplit.TEST,
        evidence_group_id="route-shape-group-001",
        language=LanguageCode.ENGLISH,
        question="Which evidence route should answer this synthetic question?",
        as_of=None,
        expected_route=route,
        document_evidence=documents,
        tool_expectations=tools,
        reference_answer=reference_answer,
        abstention_reason=abstention_reason,
        annotation=annotation,
        tags=tags,
    )
