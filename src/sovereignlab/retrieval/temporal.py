"""Offline lexical retrieval that excludes post-cutoff documents before scoring."""

import math
import re
from collections import Counter
from datetime import date

from pydantic import Field, FiniteFloat, PositiveInt, model_validator

from sovereignlab.schemas.benchmark import EvidenceLocator, QuestionText
from sovereignlab.schemas.common import Identifier, NonEmptyText, Sha256, StrictModel
from sovereignlab.schemas.source import LanguageCode, SourceKind, SourceManifest

_TOKEN_PATTERN = re.compile(r"[0-9A-Za-z]+|[가-힣]+")
_BM25_K1 = 1.5
_BM25_B = 0.75
_SCORE_SIGNIFICANT_DIGITS = 12


class DocumentChunk(StrictModel):
    """One searchable passage bound to an immutable document manifest."""

    chunk_id: Identifier
    source_id: Identifier
    source_sha256: Sha256
    language: LanguageCode
    locator: EvidenceLocator
    text: NonEmptyText


class TemporalDocumentCorpus(StrictModel):
    """A validated set of document manifests and their searchable passages."""

    sources: tuple[SourceManifest, ...] = ()
    chunks: tuple[DocumentChunk, ...] = ()

    @model_validator(mode="after")
    def bind_chunks_to_document_sources(self) -> "TemporalDocumentCorpus":
        sources_by_id: dict[str, SourceManifest] = {}
        for source in self.sources:
            if source.source_id in sources_by_id:
                raise ValueError(f"duplicate document source_id: {source.source_id}")
            if source.source_kind is not SourceKind.DOCUMENT:
                raise ValueError(f"retrieval source must be a document: {source.source_id}")
            sources_by_id[source.source_id] = source

        chunk_ids: set[str] = set()
        for chunk in self.chunks:
            if chunk.chunk_id in chunk_ids:
                raise ValueError(f"duplicate document chunk_id: {chunk.chunk_id}")
            chunk_ids.add(chunk.chunk_id)

            source = sources_by_id.get(chunk.source_id)
            if source is None:
                raise ValueError(f"document chunk references unknown source: {chunk.source_id}")
            if chunk.language is not source.language:
                raise ValueError(f"document chunk language does not match source: {chunk.chunk_id}")
            if chunk.source_sha256 != source.content_sha256:
                raise ValueError(f"document chunk hash does not match source: {chunk.chunk_id}")
        return self


class TemporalDocumentQuery(StrictModel):
    """One language-specific document query at an inclusive publication-date cutoff."""

    question: QuestionText
    language: LanguageCode
    as_of: date
    top_k: PositiveInt = Field(default=5, le=20)

    @model_validator(mode="after")
    def require_supported_language(self) -> "TemporalDocumentQuery":
        if self.language is LanguageCode.UNDETERMINED:
            raise ValueError("document retrieval query language must be ko or en")
        return self


class RetrievedDocumentChunk(StrictModel):
    """A scored passage with enough provenance to construct documentary evidence."""

    chunk_id: Identifier
    source_id: Identifier
    source_sha256: Sha256
    language: LanguageCode
    published_on: date
    locator: EvidenceLocator
    text: NonEmptyText
    score: FiniteFloat = Field(gt=0)


class TemporalDocumentRetrievalResult(StrictModel):
    """The deterministic matches returned for one temporal document query."""

    query: TemporalDocumentQuery
    matches: tuple[RetrievedDocumentChunk, ...] = ()


def retrieve_temporal_documents(
    *,
    corpus: TemporalDocumentCorpus,
    query: TemporalDocumentQuery,
) -> TemporalDocumentRetrievalResult:
    """Retrieve passages after filtering manifests by language and publication date."""

    eligible_sources = {
        source.source_id: source
        for source in corpus.sources
        if source.language is query.language and source.published_on <= query.as_of
    }
    eligible_chunks = tuple(chunk for chunk in corpus.chunks if chunk.source_id in eligible_sources)
    query_features = frozenset(_lexical_features(query.question, query.language))
    if not eligible_chunks or not query_features:
        return TemporalDocumentRetrievalResult(query=query)

    document_features = tuple(
        Counter(_lexical_features(chunk.text, chunk.language)) for chunk in eligible_chunks
    )
    document_frequency = Counter(feature for features in document_features for feature in features)
    average_document_length = (
        sum(features.total() for features in document_features) / len(document_features)
    ) or 1.0

    matches: list[RetrievedDocumentChunk] = []
    for chunk, features in zip(eligible_chunks, document_features, strict=True):
        score = _canonical_score(
            _bm25_score(
                features=features,
                query_features=query_features,
                document_frequency=document_frequency,
                document_count=len(document_features),
                average_document_length=average_document_length,
            )
        )
        if score <= 0:
            continue
        source = eligible_sources[chunk.source_id]
        matches.append(
            RetrievedDocumentChunk(
                chunk_id=chunk.chunk_id,
                source_id=chunk.source_id,
                source_sha256=chunk.source_sha256,
                language=chunk.language,
                published_on=source.published_on,
                locator=chunk.locator,
                text=chunk.text,
                score=score,
            )
        )

    matches.sort(key=lambda match: (-match.score, match.source_id, match.chunk_id))
    return TemporalDocumentRetrievalResult(query=query, matches=tuple(matches[: query.top_k]))


def _lexical_features(text: str, language: LanguageCode) -> tuple[str, ...]:
    tokens = tuple(match.group(0).lower() for match in _TOKEN_PATTERN.finditer(text))
    if language is not LanguageCode.KOREAN:
        return tokens

    features = list(tokens)
    for token in tokens:
        if not token.isascii():
            features.extend(f"ko2:{token[index : index + 2]}" for index in range(len(token) - 1))
    return tuple(features)


def _bm25_score(
    *,
    features: Counter[str],
    query_features: frozenset[str],
    document_frequency: Counter[str],
    document_count: int,
    average_document_length: float,
) -> float:
    score = 0.0
    document_length = features.total()
    length_normalization = 1 - _BM25_B + _BM25_B * (document_length / average_document_length)
    for feature in sorted(query_features):
        frequency = features[feature]
        if frequency == 0:
            continue
        frequency_weight = (
            frequency * (_BM25_K1 + 1) / (frequency + _BM25_K1 * length_normalization)
        )
        frequency_across_documents = document_frequency[feature]
        inverse_document_frequency = math.log(
            1
            + (document_count - frequency_across_documents + 0.5)
            / (frequency_across_documents + 0.5)
        )
        score += inverse_document_frequency * frequency_weight
    return score


def _canonical_score(score: float) -> float:
    """Bound platform-level libm noise before ranking and trace serialization."""

    return float(f"{score:.{_SCORE_SIGNIFICANT_DIGITS}g}")
