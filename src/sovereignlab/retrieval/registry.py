"""Trusted, digest-linked registry for the committed synthetic retrieval corpus."""

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path

from pydantic import ValidationError

from sovereignlab.retrieval.temporal import DocumentChunk, TemporalDocumentCorpus
from sovereignlab.schemas import SourceManifest

TEMPORAL_CORPUS_ID = "synthetic-temporal-retrieval-corpus-v1"
TEMPORAL_CORPUS_DESCRIPTOR_SHA256 = (
    "823117ee29a191bc306843e44ccd9d37e063db79cc87e15dcb7f2a11f5b5bf7e"
)
COMMITTED_SOURCE_MANIFEST_PATH = Path("data/fixtures/retrieval/source_manifests.jsonl")
COMMITTED_DOCUMENT_CHUNK_PATH = Path("data/fixtures/retrieval/document_chunks.jsonl")
MAX_TEMPORAL_CORPUS_FILE_BYTES = 1_000_000
MAX_TEMPORAL_CORPUS_SOURCES = 100
MAX_TEMPORAL_CORPUS_CHUNKS = 1_000


class TemporalCorpusRegistryLoadError(ValueError):
    """Sanitized harness failure while loading a trusted temporal corpus."""


class _CorpusPayloadError(ValueError):
    pass


class _DuplicateJsonKey(ValueError):
    pass


class _InvalidJsonConstant(ValueError):
    pass


@dataclass(frozen=True)
class TemporalCorpusRegistry:
    """Immutable corpus models and the exact JSONL bytes that produced them."""

    corpus_id: str
    corpus: TemporalDocumentCorpus
    source_manifest_bytes: bytes = field(repr=False, compare=False)
    document_chunk_bytes: bytes = field(repr=False, compare=False)

    def __post_init__(self) -> None:
        self.validated_corpus()

    def validated_corpus(self) -> TemporalDocumentCorpus:
        """Rebuild and validate the corpus from its exact immutable inputs."""

        if type(self.source_manifest_bytes) is not bytes:
            raise ValueError("source manifest JSONL must be immutable bytes")
        if type(self.document_chunk_bytes) is not bytes:
            raise ValueError("document chunk JSONL must be immutable bytes")
        if not 0 < len(self.source_manifest_bytes) <= MAX_TEMPORAL_CORPUS_FILE_BYTES:
            raise ValueError("source manifest JSONL exceeds its bounded size")
        if not 0 < len(self.document_chunk_bytes) <= MAX_TEMPORAL_CORPUS_FILE_BYTES:
            raise ValueError("document chunk JSONL exceeds its bounded size")
        parsed = _parse_corpus_payloads(
            self.source_manifest_bytes,
            self.document_chunk_bytes,
        )
        if parsed != self.corpus:
            raise ValueError("temporal corpus model differs from its exact JSONL bytes")
        return parsed

    def canonical_descriptor_bytes(self) -> bytes:
        """Serialize complete corpus provenance without paths, URLs, or raw text."""

        corpus = self.validated_corpus()
        descriptor = {
            "corpus_id": self.corpus_id,
            "document_chunks": {
                "byte_size": len(self.document_chunk_bytes),
                "chunk_count": len(corpus.chunks),
                "chunk_ids": sorted(chunk.chunk_id for chunk in corpus.chunks),
                "sha256": hashlib.sha256(self.document_chunk_bytes).hexdigest(),
            },
            "schema_version": "1.0.0",
            "source_manifests": {
                "byte_size": len(self.source_manifest_bytes),
                "sha256": hashlib.sha256(self.source_manifest_bytes).hexdigest(),
                "source_count": len(corpus.sources),
                "source_ids": sorted(source.source_id for source in corpus.sources),
            },
        }
        return json.dumps(
            descriptor,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")

    @property
    def descriptor_sha256(self) -> str:
        """Hash the exact canonical corpus descriptor."""

        return hashlib.sha256(self.canonical_descriptor_bytes()).hexdigest()


def load_temporal_corpus_registry(
    repository_root: Path,
    *,
    corpus_id: str,
    source_manifest_path: Path,
    document_chunk_path: Path,
) -> TemporalCorpusRegistry:
    """Load two explicitly selected, repository-confined JSONL inputs."""

    try:
        root = repository_root.resolve(strict=True)
    except OSError:
        raise TemporalCorpusRegistryLoadError(
            "the trusted repository root could not be resolved"
        ) from None

    required_root = root / "data" / "fixtures" / "retrieval"
    if source_manifest_path == document_chunk_path:
        raise ValueError("trusted temporal corpus roles must use distinct files")
    source_manifest_bytes = _read_trusted_jsonl(
        root,
        source_manifest_path,
        required_root=required_root,
        role="source manifest",
    )
    document_chunk_bytes = _read_trusted_jsonl(
        root,
        document_chunk_path,
        required_root=required_root,
        role="document chunk",
    )
    try:
        corpus = _parse_corpus_payloads(
            source_manifest_bytes,
            document_chunk_bytes,
        )
    except (TypeError, ValueError):
        raise TemporalCorpusRegistryLoadError("the trusted temporal corpus is invalid") from None
    return TemporalCorpusRegistry(
        corpus_id=corpus_id,
        corpus=corpus,
        source_manifest_bytes=source_manifest_bytes,
        document_chunk_bytes=document_chunk_bytes,
    )


def load_committed_temporal_corpus_registry(
    repository_root: Path,
) -> TemporalCorpusRegistry:
    """Load the exact synthetic corpus admitted for the offline baseline."""

    registry = load_temporal_corpus_registry(
        repository_root,
        corpus_id=TEMPORAL_CORPUS_ID,
        source_manifest_path=COMMITTED_SOURCE_MANIFEST_PATH,
        document_chunk_path=COMMITTED_DOCUMENT_CHUNK_PATH,
    )
    if registry.descriptor_sha256 != TEMPORAL_CORPUS_DESCRIPTOR_SHA256:
        raise ValueError("committed temporal corpus changed; preserve v1 and create a new version")
    return registry


def _read_trusted_jsonl(
    root: Path,
    relative_path: Path,
    *,
    required_root: Path,
    role: str,
) -> bytes:
    path = _resolve_trusted_path(
        root,
        relative_path,
        required_root=required_root,
    )
    if path.suffix != ".jsonl":
        raise ValueError(f"trusted {role} input must be JSONL")
    if not path.is_file():
        raise TemporalCorpusRegistryLoadError(f"the trusted {role} JSONL does not exist")
    try:
        byte_size = path.stat().st_size
    except OSError:
        raise TemporalCorpusRegistryLoadError(
            f"the trusted {role} JSONL could not be inspected"
        ) from None
    if byte_size <= 0 or byte_size > MAX_TEMPORAL_CORPUS_FILE_BYTES:
        raise ValueError(f"trusted {role} JSONL exceeds its bounded size")
    try:
        payload = path.read_bytes()
    except OSError:
        raise TemporalCorpusRegistryLoadError(
            f"the trusted {role} JSONL could not be read"
        ) from None
    if len(payload) != byte_size or len(payload) > MAX_TEMPORAL_CORPUS_FILE_BYTES:
        raise ValueError(f"trusted {role} JSONL changed while it was read")
    return payload


def _resolve_trusted_path(
    root: Path,
    relative_path: Path,
    *,
    required_root: Path,
) -> Path:
    if relative_path.is_absolute():
        raise ValueError("trusted temporal corpus paths must be repository-relative")
    try:
        path = (root / relative_path).resolve(strict=False)
        confined_root = required_root.resolve(strict=True)
    except OSError:
        raise TemporalCorpusRegistryLoadError(
            "the trusted temporal corpus root could not be resolved"
        ) from None
    if not path.is_relative_to(confined_root):
        raise ValueError("trusted temporal corpus path escapes its approved root")
    return path


def _parse_corpus_payloads(
    source_manifest_bytes: bytes,
    document_chunk_bytes: bytes,
) -> TemporalDocumentCorpus:
    source_rows = _parse_jsonl(
        source_manifest_bytes,
        max_records=MAX_TEMPORAL_CORPUS_SOURCES,
    )
    chunk_rows = _parse_jsonl(
        document_chunk_bytes,
        max_records=MAX_TEMPORAL_CORPUS_CHUNKS,
    )
    try:
        sources = tuple(SourceManifest.model_validate(row) for row in source_rows)
        chunks = tuple(DocumentChunk.model_validate(row) for row in chunk_rows)
        return TemporalDocumentCorpus(sources=sources, chunks=chunks)
    except (ValidationError, ValueError):
        raise _CorpusPayloadError("temporal corpus rows do not form a trusted corpus") from None


def _parse_jsonl(
    payload: bytes,
    *,
    max_records: int,
) -> tuple[dict[str, object], ...]:
    try:
        text = payload.decode("utf-8")
    except UnicodeDecodeError:
        raise _CorpusPayloadError("temporal corpus JSONL is not valid UTF-8") from None
    lines = text.splitlines()
    if not lines or len(lines) > max_records or any(not line.strip() for line in lines):
        raise _CorpusPayloadError("temporal corpus JSONL has an invalid record layout")

    records: list[dict[str, object]] = []
    try:
        for line in lines:
            record = json.loads(
                line,
                object_pairs_hook=_unique_object,
                parse_constant=_reject_json_constant,
            )
            if not isinstance(record, dict):
                raise _CorpusPayloadError("temporal corpus JSONL records must be objects")
            records.append(record)
    except (RecursionError, ValueError):
        raise _CorpusPayloadError("temporal corpus JSONL is invalid") from None
    return tuple(records)


def _unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise _DuplicateJsonKey(key)
        result[key] = value
    return result


def _reject_json_constant(value: str) -> object:
    raise _InvalidJsonConstant(value)
