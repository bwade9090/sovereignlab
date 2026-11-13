"""Behaviour of the synthetic corpus registry and the typed retrieval adapter."""

from datetime import date
from pathlib import Path

import pytest

from sovereignlab.retrieval import (
    TEMPORAL_CORPUS_DESCRIPTOR_SHA256,
    TemporalCorpusRegistry,
    execute_temporal_document_call,
    load_committed_temporal_corpus_registry,
)
from sovereignlab.schemas import (
    LanguageCode,
    TemporalDocumentArguments,
    TemporalDocumentCall,
    TemporalDocumentResult,
    ToolOutcomeStatus,
)

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
_QUESTIONS = {
    LanguageCode.KOREAN: "성장 전망 상향 배경은 수출 증가와 내수 회복 중 무엇인가요?",
    LanguageCode.ENGLISH: "Why was the growth outlook revised upward?",
}


@pytest.fixture(scope="module")
def registry() -> TemporalCorpusRegistry:
    return load_committed_temporal_corpus_registry(REPOSITORY_ROOT)


def _retrieve(
    registry: TemporalCorpusRegistry,
    language: LanguageCode,
    as_of: date,
    top_k: int = 5,
) -> TemporalDocumentResult:
    return execute_temporal_document_call(
        call=TemporalDocumentCall(
            call_id="document-call-01",
            tool_name="retrieve_temporal_documents",
            arguments=TemporalDocumentArguments(
                question=_QUESTIONS[language],
                language=language,
                as_of=as_of,
                top_k=top_k,
            ),
        ),
        registry=registry,
    )


def test_committed_corpus_digest_is_pinned(registry: TemporalCorpusRegistry) -> None:
    assert registry.descriptor_sha256 == TEMPORAL_CORPUS_DESCRIPTOR_SHA256
    assert len(registry.corpus.sources) == 4
    assert len(registry.corpus.chunks) == 6


@pytest.mark.parametrize("language", [LanguageCode.KOREAN, LanguageCode.ENGLISH])
def test_documents_published_after_the_cutoff_are_never_returned(
    registry: TemporalCorpusRegistry,
    language: LanguageCode,
) -> None:
    # The August 2024 fixture document contains the best-matching "future" passage.
    before = _retrieve(registry, language, date(2024, 8, 21))
    after = _retrieve(registry, language, date(2024, 8, 22))

    assert before.status is after.status is ToolOutcomeStatus.SUCCESS
    assert before.payload is not None and after.payload is not None
    assert all(match.published_on == date(2024, 5, 23) for match in before.payload.matches)
    assert all(match.language is language for match in before.payload.matches)
    assert before.payload.matches[0].chunk_id == f"synthetic-2024-05-{language.value}-growth"
    assert any(match.published_on == date(2024, 8, 22) for match in after.payload.matches)


def test_matches_are_ranked_and_limited_to_top_k(registry: TemporalCorpusRegistry) -> None:
    result = _retrieve(registry, LanguageCode.ENGLISH, date(2024, 8, 22), top_k=1)

    assert result.payload is not None
    assert len(result.payload.matches) == 1
    everything = _retrieve(registry, LanguageCode.ENGLISH, date(2024, 8, 22)).payload
    assert everything is not None
    scores = [match.score for match in everything.matches]
    assert scores == sorted(scores, reverse=True)
    assert result.payload.matches[0] == everything.matches[0]


def test_no_eligible_passage_abstains(registry: TemporalCorpusRegistry) -> None:
    result = _retrieve(registry, LanguageCode.KOREAN, date(2024, 5, 22))

    assert result.status is ToolOutcomeStatus.ABSTAINED
    assert result.payload is None
    assert result.abstention is not None
    assert result.abstention.reason_code == "no_temporal_document_match"
