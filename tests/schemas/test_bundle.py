"""Cross-record leakage and reference-integrity tests."""

from datetime import date

import pytest
from pydantic import ValidationError

from sovereignlab.schemas import (
    AnnotationProvenance,
    BenchmarkBundle,
    BenchmarkRecord,
    BenchmarkSplit,
    DocumentEvidence,
    EvidenceRoute,
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
