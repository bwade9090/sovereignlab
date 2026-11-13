"""Typed tool adapter over the publication-date-safe document retriever."""

from enum import StrEnum

from sovereignlab.retrieval.registry import TemporalCorpusRegistry
from sovereignlab.retrieval.temporal import TemporalDocumentQuery, retrieve_temporal_documents
from sovereignlab.schemas import (
    DocumentMatchEvidence,
    DocumentRetrievalPayload,
    TemporalDocumentCall,
    TemporalDocumentResult,
    ToolAbstention,
    ToolName,
    ToolOutcomeStatus,
)


class TemporalDocumentAbstentionReason(StrEnum):
    """Documentary evidence conditions that return no matches."""

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
    """Retrieve passages from documents published by the cutoff."""

    arguments = call.arguments
    result = retrieve_temporal_documents(
        corpus=registry.corpus,
        query=TemporalDocumentQuery(
            question=arguments.question,
            language=arguments.language,
            as_of=arguments.as_of,
            top_k=arguments.top_k,
        ),
    )
    if not result.matches:
        reason = TemporalDocumentAbstentionReason.NO_TEMPORAL_DOCUMENT_MATCH
        return TemporalDocumentResult(
            call_id=call.call_id,
            tool_name=ToolName.RETRIEVE_TEMPORAL_DOCUMENTS,
            status=ToolOutcomeStatus.ABSTAINED,
            abstention=ToolAbstention(
                reason_code=reason.value,
                message=_ABSTENTION_MESSAGES[reason],
            ),
        )
    return TemporalDocumentResult(
        call_id=call.call_id,
        tool_name=ToolName.RETRIEVE_TEMPORAL_DOCUMENTS,
        status=ToolOutcomeStatus.SUCCESS,
        payload=DocumentRetrievalPayload(
            matches=tuple(
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
        ),
    )
