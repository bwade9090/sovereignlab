"""Regression tests for publication-date-safe bilingual document retrieval."""

import json
from datetime import date
from pathlib import Path
from typing import Any

import pytest
from pydantic import ValidationError

from sovereignlab.retrieval import (
    DocumentChunk,
    TemporalDocumentCorpus,
    TemporalDocumentQuery,
    retrieve_temporal_documents,
)
from sovereignlab.schemas import LanguageCode, SourceKind, SourceManifest

FIXTURE_DIRECTORY = Path(__file__).parents[2] / "data" / "fixtures" / "retrieval"
CUTOFF = date(2024, 5, 31)


def _read_jsonl(path: Path) -> tuple[dict[str, Any], ...]:
    return tuple(json.loads(line) for line in path.read_text(encoding="utf-8").splitlines())


@pytest.fixture
def corpus() -> TemporalDocumentCorpus:
    sources = tuple(
        SourceManifest.model_validate(item)
        for item in _read_jsonl(FIXTURE_DIRECTORY / "source_manifests.jsonl")
    )
    chunks = tuple(
        DocumentChunk.model_validate(item)
        for item in _read_jsonl(FIXTURE_DIRECTORY / "document_chunks.jsonl")
    )
    return TemporalDocumentCorpus(sources=sources, chunks=chunks)


def _query(
    *,
    language: LanguageCode = LanguageCode.KOREAN,
    as_of: date = CUTOFF,
    top_k: int = 5,
) -> TemporalDocumentQuery:
    question = {
        LanguageCode.KOREAN: "GDP 성장 전망을 상향한 배경은 수출과 내수 중 무엇인가?",
        LanguageCode.ENGLISH: "Why was the growth outlook revised upward?",
    }[language]
    return TemporalDocumentQuery(
        question=question,
        language=language,
        as_of=as_of,
        top_k=top_k,
    )


def _replace_source(source: SourceManifest, **changes: Any) -> SourceManifest:
    data = source.model_dump(mode="python")
    data.update(changes)
    return SourceManifest.model_validate(data)


def _replace_chunk(chunk: DocumentChunk, **changes: Any) -> DocumentChunk:
    data = chunk.model_dump(mode="python")
    data.update(changes)
    return DocumentChunk.model_validate(data)


@pytest.mark.parametrize(
    ("language", "expected_source", "forbidden_source", "expected_phrase"),
    [
        (
            LanguageCode.KOREAN,
            "synthetic-outlook-2024-05-ko",
            "synthetic-outlook-2024-08-ko",
            "수출 증가와 내수 회복",
        ),
        (
            LanguageCode.ENGLISH,
            "synthetic-outlook-2024-05-en",
            "synthetic-outlook-2024-08-en",
            "Stronger exports",
        ),
    ],
)
def test_future_documents_are_filtered_before_bilingual_scoring(
    corpus: TemporalDocumentCorpus,
    language: LanguageCode,
    expected_source: str,
    forbidden_source: str,
    expected_phrase: str,
) -> None:
    query = _query(language=language)
    full_result = retrieve_temporal_documents(corpus=corpus, query=query)

    eligible_sources = tuple(source for source in corpus.sources if source.published_on <= CUTOFF)
    eligible_ids = {source.source_id for source in eligible_sources}
    past_only_corpus = TemporalDocumentCorpus(
        sources=eligible_sources,
        chunks=tuple(chunk for chunk in corpus.chunks if chunk.source_id in eligible_ids),
    )
    past_only_result = retrieve_temporal_documents(corpus=past_only_corpus, query=query)

    assert full_result == past_only_result
    assert full_result.matches[0].source_id == expected_source
    assert expected_phrase in full_result.matches[0].text
    assert all(match.language is language for match in full_result.matches)
    serialized = full_result.model_dump_json()
    assert forbidden_source not in serialized
    assert "가장 정확한 미래 답변" not in serialized
    assert "exact future answer" not in serialized


def test_cutoff_is_inclusive_and_top_k_limits_results(
    corpus: TemporalDocumentCorpus,
) -> None:
    query = _query(as_of=date(2024, 5, 23), top_k=1)

    result = retrieve_temporal_documents(corpus=corpus, query=query)

    assert len(result.matches) == 1
    assert result.matches[0].published_on == query.as_of


def test_query_before_all_publications_returns_no_matches(
    corpus: TemporalDocumentCorpus,
) -> None:
    result = retrieve_temporal_documents(
        corpus=corpus,
        query=_query(as_of=date(2024, 5, 22)),
    )

    assert result.matches == ()


def test_punctuation_only_and_no_overlap_queries_return_no_matches(
    corpus: TemporalDocumentCorpus,
) -> None:
    punctuation = TemporalDocumentQuery(
        question="?!?!?!",
        language=LanguageCode.ENGLISH,
        as_of=CUTOFF,
    )
    no_overlap = TemporalDocumentQuery(
        question="Quasar zephyr nebula",
        language=LanguageCode.ENGLISH,
        as_of=CUTOFF,
    )

    assert retrieve_temporal_documents(corpus=corpus, query=punctuation).matches == ()
    assert retrieve_temporal_documents(corpus=corpus, query=no_overlap).matches == ()


@pytest.mark.parametrize("top_k", [0, 21])
def test_query_rejects_out_of_range_top_k(top_k: int) -> None:
    with pytest.raises(ValidationError):
        _query(top_k=top_k)


def test_query_rejects_undetermined_language() -> None:
    with pytest.raises(ValidationError, match="must be ko or en"):
        TemporalDocumentQuery(
            question="A question with no determined language",
            language=LanguageCode.UNDETERMINED,
            as_of=CUTOFF,
        )


def test_corpus_rejects_duplicate_source_ids(corpus: TemporalDocumentCorpus) -> None:
    with pytest.raises(ValidationError, match="duplicate document source_id"):
        TemporalDocumentCorpus(sources=(*corpus.sources, corpus.sources[0]), chunks=corpus.chunks)


def test_corpus_rejects_non_document_sources(corpus: TemporalDocumentCorpus) -> None:
    non_document = _replace_source(corpus.sources[0], source_kind=SourceKind.API)

    with pytest.raises(ValidationError, match="retrieval source must be a document"):
        TemporalDocumentCorpus(sources=(non_document,), chunks=())


def test_corpus_rejects_duplicate_chunk_ids(corpus: TemporalDocumentCorpus) -> None:
    with pytest.raises(ValidationError, match="duplicate document chunk_id"):
        TemporalDocumentCorpus(
            sources=corpus.sources,
            chunks=(*corpus.chunks, corpus.chunks[0]),
        )


def test_corpus_rejects_unknown_chunk_source(corpus: TemporalDocumentCorpus) -> None:
    unknown = _replace_chunk(corpus.chunks[0], source_id="unknown-document")

    with pytest.raises(ValidationError, match="references unknown source"):
        TemporalDocumentCorpus(sources=corpus.sources, chunks=(unknown,))


def test_corpus_rejects_chunk_language_mismatch(corpus: TemporalDocumentCorpus) -> None:
    mismatch = _replace_chunk(corpus.chunks[0], language=LanguageCode.ENGLISH)

    with pytest.raises(ValidationError, match="language does not match"):
        TemporalDocumentCorpus(sources=corpus.sources, chunks=(mismatch,))


def test_corpus_rejects_chunk_hash_mismatch(corpus: TemporalDocumentCorpus) -> None:
    mismatch = _replace_chunk(corpus.chunks[0], source_sha256="f" * 64)

    with pytest.raises(ValidationError, match="hash does not match"):
        TemporalDocumentCorpus(sources=corpus.sources, chunks=(mismatch,))


def test_empty_validated_corpus_returns_no_matches() -> None:
    result = retrieve_temporal_documents(corpus=TemporalDocumentCorpus(), query=_query())

    assert result.matches == ()
