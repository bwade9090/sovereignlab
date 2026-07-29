"""Publication-date-safe bilingual document retrieval."""

from sovereignlab.retrieval.adapter import (
    TemporalDocumentAbstentionReason,
    execute_temporal_document_call,
)
from sovereignlab.retrieval.registry import (
    COMMITTED_DOCUMENT_CHUNK_PATH,
    COMMITTED_SOURCE_MANIFEST_PATH,
    MAX_TEMPORAL_CORPUS_CHUNKS,
    MAX_TEMPORAL_CORPUS_FILE_BYTES,
    MAX_TEMPORAL_CORPUS_SOURCES,
    TEMPORAL_CORPUS_DESCRIPTOR_SHA256,
    TEMPORAL_CORPUS_ID,
    TemporalCorpusRegistry,
    TemporalCorpusRegistryLoadError,
    load_committed_temporal_corpus_registry,
    load_temporal_corpus_registry,
)
from sovereignlab.retrieval.temporal import (
    DocumentChunk,
    RetrievedDocumentChunk,
    TemporalDocumentCorpus,
    TemporalDocumentQuery,
    TemporalDocumentRetrievalResult,
    retrieve_temporal_documents,
)

__all__ = [
    "COMMITTED_DOCUMENT_CHUNK_PATH",
    "COMMITTED_SOURCE_MANIFEST_PATH",
    "MAX_TEMPORAL_CORPUS_CHUNKS",
    "MAX_TEMPORAL_CORPUS_FILE_BYTES",
    "MAX_TEMPORAL_CORPUS_SOURCES",
    "TEMPORAL_CORPUS_DESCRIPTOR_SHA256",
    "TEMPORAL_CORPUS_ID",
    "DocumentChunk",
    "RetrievedDocumentChunk",
    "TemporalCorpusRegistry",
    "TemporalCorpusRegistryLoadError",
    "TemporalDocumentAbstentionReason",
    "TemporalDocumentCorpus",
    "TemporalDocumentQuery",
    "TemporalDocumentRetrievalResult",
    "execute_temporal_document_call",
    "load_committed_temporal_corpus_registry",
    "load_temporal_corpus_registry",
    "retrieve_temporal_documents",
]
