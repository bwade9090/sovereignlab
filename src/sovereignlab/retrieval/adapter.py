"""Typed execution adapter over the publication-date-safe document retriever."""

from enum import StrEnum

from pydantic import ValidationError

from sovereignlab.retrieval.registry import TemporalCorpusRegistry
from sovereignlab.retrieval.temporal import (
    TemporalDocumentCorpus,
    TemporalDocumentQuery,
    TemporalDocumentRetrievalResult,
)
from sovereignlab.retrieval.temporal import (
    retrieve_temporal_documents as _reference_retrieve_temporal_documents,
)
from sovereignlab.schemas import (
    DocumentMatchEvidence,
    DocumentRetrievalPayload,
    ExecutionFailure,
    FailurePhase,
    TemporalDocumentCall,
    TemporalDocumentResult,
    ToolAbstention,
    ToolName,
    ToolOutcomeStatus,
)

_retrieve_temporal_documents = _reference_retrieve_temporal_documents


class TemporalDocumentAbstentionReason(StrEnum):
    """Known documentary evidence conditions that safely return no matches."""

    NO_TEMPORAL_DOCUMENT_MATCH = "no_temporal_document_match"


_ABSTENTION_MESSAGES = {
    TemporalDocumentAbstentionReason.NO_TEMPORAL_DOCUMENT_MATCH: (
        "No eligible document passage matched the validated query."
    ),
}


def execute_temporal_document_call(
    *,
    call: TemporalDocumentCall,
    registry: TemporalCorpusRegistry,
) -> TemporalDocumentResult:
    """Execute one typed call without accepting model-selected corpus inputs."""

    if not isinstance(registry, TemporalCorpusRegistry):
        return _error(
            call,
            code="temporal_corpus_misconfigured",
            message="The trusted temporal retrieval corpus is misconfigured.",
        )
    try:
        corpus = TemporalCorpusRegistry.validated_corpus(registry)
    except Exception:
        return _error(
            call,
            code="temporal_corpus_misconfigured",
            message="The trusted temporal retrieval corpus is misconfigured.",
        )

    arguments = call.arguments
    try:
        query = TemporalDocumentQuery(
            question=arguments.question,
            language=arguments.language,
            as_of=arguments.as_of,
            top_k=arguments.top_k,
        )
        result = _retrieve_temporal_documents(
            corpus=corpus,
            query=query,
        )
    except Exception:
        return _error(
            call,
            code="temporal_retrieval_failed",
            message="The deterministic temporal document retriever failed unexpectedly.",
        )

    try:
        _validate_result(result, query, corpus)
        if not result.matches:
            return _abstain(
                call,
                TemporalDocumentAbstentionReason.NO_TEMPORAL_DOCUMENT_MATCH,
            )
        evidence = tuple(
            DocumentMatchEvidence(
                chunk_id=match.chunk_id,
                source_id=match.source_id,
                source_sha256=match.source_sha256,
                language=match.language,
                published_on=match.published_on,
                locator=match.locator,
                text=match.text,
                score=match.score,
            )
            for match in result.matches
        )
        return TemporalDocumentResult(
            call_id=call.call_id,
            tool_name=ToolName.RETRIEVE_TEMPORAL_DOCUMENTS,
            status=ToolOutcomeStatus.SUCCESS,
            payload=DocumentRetrievalPayload(matches=evidence),
        )
    except (TypeError, ValidationError, ValueError):
        return _error(
            call,
            code="temporal_retrieval_failed",
            message="The deterministic temporal document result was invalid.",
        )
    except Exception:
        return _error(
            call,
            code="temporal_retrieval_failed",
            message="The deterministic temporal document adapter failed unexpectedly.",
        )


def _validate_result(
    result: TemporalDocumentRetrievalResult,
    query: TemporalDocumentQuery,
    corpus: TemporalDocumentCorpus,
) -> None:
    if not isinstance(result, TemporalDocumentRetrievalResult) or result.query != query:
        raise ValueError("temporal retrieval result differs from its validated query")
    matches = result.matches
    if len(matches) > query.top_k:
        raise ValueError("temporal retrieval result exceeds top_k")
    chunk_ids = tuple(match.chunk_id for match in matches)
    if len(chunk_ids) != len(set(chunk_ids)):
        raise ValueError("temporal retrieval result repeats a chunk")
    expected_order = tuple(
        sorted(matches, key=lambda match: (-match.score, match.source_id, match.chunk_id))
    )
    if matches != expected_order:
        raise ValueError("temporal retrieval result order is not deterministic")
    if any(match.language is not query.language for match in matches):
        raise ValueError("temporal retrieval result language differs from its query")
    if any(match.published_on > query.as_of for match in matches):
        raise ValueError("temporal retrieval result contains post-cutoff evidence")

    chunks_by_id = {chunk.chunk_id: chunk for chunk in corpus.chunks}
    sources_by_id = {source.source_id: source for source in corpus.sources}
    for match in matches:
        chunk = chunks_by_id.get(match.chunk_id)
        if chunk is None:
            raise ValueError("temporal retrieval result contains an unregistered chunk")
        source = sources_by_id[chunk.source_id]
        registered_fields = (
            chunk.source_id,
            chunk.source_sha256,
            chunk.language,
            source.published_on,
            chunk.locator,
            chunk.text,
        )
        returned_fields = (
            match.source_id,
            match.source_sha256,
            match.language,
            match.published_on,
            match.locator,
            match.text,
        )
        if returned_fields != registered_fields:
            raise ValueError("temporal retrieval result differs from its registered chunk")

    expected = _reference_retrieve_temporal_documents(
        corpus=corpus,
        query=query,
    )
    if result != expected:
        raise ValueError("temporal retrieval result is not exactly reproducible")


def _abstain(
    call: TemporalDocumentCall,
    reason: TemporalDocumentAbstentionReason,
) -> TemporalDocumentResult:
    return TemporalDocumentResult(
        call_id=call.call_id,
        tool_name=ToolName.RETRIEVE_TEMPORAL_DOCUMENTS,
        status=ToolOutcomeStatus.ABSTAINED,
        abstention=ToolAbstention(
            reason_code=reason.value,
            message=_ABSTENTION_MESSAGES[reason],
        ),
    )


def _error(
    call: TemporalDocumentCall,
    *,
    code: str,
    message: str,
) -> TemporalDocumentResult:
    return TemporalDocumentResult(
        call_id=call.call_id,
        tool_name=ToolName.RETRIEVE_TEMPORAL_DOCUMENTS,
        status=ToolOutcomeStatus.ERROR,
        error=ExecutionFailure(
            phase=FailurePhase.TOOL_EXECUTION,
            code=code,
            message=message,
            call_id=call.call_id,
        ),
    )
