"""Digest-pinned registry of the committed synthetic retrieval corpus."""

import json
from dataclasses import dataclass, field
from pathlib import Path

from sovereignlab.artifacts import canonical_sha256, sha256_hex
from sovereignlab.retrieval.temporal import DocumentChunk, TemporalDocumentCorpus
from sovereignlab.schemas import SourceManifest

TEMPORAL_CORPUS_ID = "synthetic-temporal-retrieval-corpus-v1"
TEMPORAL_CORPUS_DESCRIPTOR_SHA256 = (
    "823117ee29a191bc306843e44ccd9d37e063db79cc87e15dcb7f2a11f5b5bf7e"
)
COMMITTED_SOURCE_MANIFEST_PATH = Path("data/fixtures/retrieval/source_manifests.jsonl")
COMMITTED_DOCUMENT_CHUNK_PATH = Path("data/fixtures/retrieval/document_chunks.jsonl")


@dataclass(frozen=True)
class TemporalCorpusRegistry:
    """A validated corpus and the exact JSONL bytes it was built from."""

    corpus_id: str
    corpus: TemporalDocumentCorpus
    source_manifest_bytes: bytes = field(repr=False, compare=False)
    document_chunk_bytes: bytes = field(repr=False, compare=False)

    @property
    def descriptor_sha256(self) -> str:
        """Hash the corpus inputs and inventory."""

        return canonical_sha256(
            {
                "corpus_id": self.corpus_id,
                "document_chunks": {
                    "byte_size": len(self.document_chunk_bytes),
                    "chunk_count": len(self.corpus.chunks),
                    "chunk_ids": sorted(chunk.chunk_id for chunk in self.corpus.chunks),
                    "sha256": sha256_hex(self.document_chunk_bytes),
                },
                "schema_version": "1.0.0",
                "source_manifests": {
                    "byte_size": len(self.source_manifest_bytes),
                    "sha256": sha256_hex(self.source_manifest_bytes),
                    "source_count": len(self.corpus.sources),
                    "source_ids": sorted(source.source_id for source in self.corpus.sources),
                },
            }
        )


def load_temporal_corpus_registry(
    repository_root: Path,
    *,
    corpus_id: str,
    source_manifest_path: Path,
    document_chunk_path: Path,
) -> TemporalCorpusRegistry:
    """Load one corpus from a source-manifest JSONL file and a chunk JSONL file."""

    source_manifest_bytes = (repository_root / source_manifest_path).read_bytes()
    document_chunk_bytes = (repository_root / document_chunk_path).read_bytes()
    corpus = TemporalDocumentCorpus(
        sources=tuple(
            SourceManifest.model_validate(row) for row in _jsonl_rows(source_manifest_bytes)
        ),
        chunks=tuple(
            DocumentChunk.model_validate(row) for row in _jsonl_rows(document_chunk_bytes)
        ),
    )
    return TemporalCorpusRegistry(
        corpus_id=corpus_id,
        corpus=corpus,
        source_manifest_bytes=source_manifest_bytes,
        document_chunk_bytes=document_chunk_bytes,
    )


def load_committed_temporal_corpus_registry(repository_root: Path) -> TemporalCorpusRegistry:
    """Load corpus v1: the committed synthetic bilingual fixture."""

    registry = load_temporal_corpus_registry(
        repository_root,
        corpus_id=TEMPORAL_CORPUS_ID,
        source_manifest_path=COMMITTED_SOURCE_MANIFEST_PATH,
        document_chunk_path=COMMITTED_DOCUMENT_CHUNK_PATH,
    )
    if registry.descriptor_sha256 != TEMPORAL_CORPUS_DESCRIPTOR_SHA256:
        raise ValueError(
            "committed temporal corpus changed; keep v1 as is and add a new corpus version"
        )
    return registry


def _jsonl_rows(payload: bytes) -> list[object]:
    return [json.loads(line) for line in payload.decode("utf-8").splitlines() if line.strip()]
