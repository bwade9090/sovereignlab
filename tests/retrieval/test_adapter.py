"""Offline regression tests for the typed temporal-document adapter."""

import shutil
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

import pytest

import sovereignlab.retrieval.adapter as adapter_module
import sovereignlab.retrieval.registry as registry_module
from sovereignlab.retrieval import (
    COMMITTED_DOCUMENT_CHUNK_PATH,
    COMMITTED_SOURCE_MANIFEST_PATH,
    MAX_TEMPORAL_CORPUS_FILE_BYTES,
    TEMPORAL_CORPUS_DESCRIPTOR_SHA256,
    TEMPORAL_CORPUS_ID,
    DocumentChunk,
    RetrievedDocumentChunk,
    TemporalCorpusRegistry,
    TemporalCorpusRegistryLoadError,
    TemporalDocumentAbstentionReason,
    TemporalDocumentCorpus,
    TemporalDocumentQuery,
    TemporalDocumentRetrievalResult,
    execute_temporal_document_call,
    load_committed_temporal_corpus_registry,
    load_temporal_corpus_registry,
)
from sovereignlab.schemas import (
    EvidenceRoute,
    ExecutionEnvironmentProvenance,
    ExecutionEvidencePacket,
    ExecutionRequest,
    ExecutionTrace,
    LanguageCode,
    PacketStatus,
    PlannerMode,
    PlannerProvenance,
    RoutePlan,
    TemporalDocumentArguments,
    TemporalDocumentCall,
    ToolOutcomeStatus,
    TraceStatus,
)

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
AS_OF = date(2024, 5, 31)


class _DecodeOverridingBytes(bytes):
    decoded_text: str

    def __new__(cls, payload: bytes, decoded_text: str) -> "_DecodeOverridingBytes":
        instance = super().__new__(cls, payload)
        instance.decoded_text = decoded_text
        return instance

    def decode(self, *args: object, **kwargs: object) -> str:
        return self.decoded_text


ENGLISH_QUESTION = "Why was the growth outlook revised upward?"
KOREAN_QUESTION = "GDP 성장 전망의 상향 배경은 수출과 내수 중 무엇인가?"


@pytest.fixture(scope="module")
def committed_registry() -> TemporalCorpusRegistry:
    return load_committed_temporal_corpus_registry(REPOSITORY_ROOT)


def _call(
    *,
    language: LanguageCode = LanguageCode.ENGLISH,
    question: str | None = None,
    as_of: date = AS_OF,
    top_k: int = 5,
    call_id: str = "temporal-document-call-01",
) -> TemporalDocumentCall:
    return TemporalDocumentCall(
        call_id=call_id,
        tool_name="retrieve_temporal_documents",
        arguments=TemporalDocumentArguments(
            question=question
            or {
                LanguageCode.KOREAN: KOREAN_QUESTION,
                LanguageCode.ENGLISH: ENGLISH_QUESTION,
            }[language],
            language=language,
            as_of=as_of,
            top_k=top_k,
        ),
    )


def _jsonl_bytes(models: tuple[Any, ...]) -> bytes:
    return b"".join(f"{model.model_dump_json(exclude_none=True)}\n".encode() for model in models)


def _registry_from_corpus(
    corpus: TemporalDocumentCorpus,
    *,
    corpus_id: str = "test-temporal-corpus-v1",
) -> TemporalCorpusRegistry:
    return TemporalCorpusRegistry(
        corpus_id=corpus_id,
        corpus=corpus,
        source_manifest_bytes=_jsonl_bytes(corpus.sources),
        document_chunk_bytes=_jsonl_bytes(corpus.chunks),
    )


def _write_corpus_files(
    root: Path,
    *,
    source_bytes: bytes | None = None,
    chunk_bytes: bytes | None = None,
) -> None:
    fixture_root = root / "data" / "fixtures" / "retrieval"
    fixture_root.mkdir(parents=True, exist_ok=True)
    (root / COMMITTED_SOURCE_MANIFEST_PATH).write_bytes(
        source_bytes
        if source_bytes is not None
        else (REPOSITORY_ROOT / COMMITTED_SOURCE_MANIFEST_PATH).read_bytes()
    )
    (root / COMMITTED_DOCUMENT_CHUNK_PATH).write_bytes(
        chunk_bytes
        if chunk_bytes is not None
        else (REPOSITORY_ROOT / COMMITTED_DOCUMENT_CHUNK_PATH).read_bytes()
    )


def _query_for(call: TemporalDocumentCall) -> TemporalDocumentQuery:
    return TemporalDocumentQuery.model_validate(call.arguments.model_dump())


def _match(
    *,
    chunk_id: str,
    score: float,
    language: LanguageCode = LanguageCode.ENGLISH,
    published_on: date = date(2024, 5, 23),
) -> RetrievedDocumentChunk:
    return RetrievedDocumentChunk(
        chunk_id=chunk_id,
        source_id=f"source-{chunk_id}",
        source_sha256="a" * 64,
        language=language,
        published_on=published_on,
        locator={"page": 1, "section": "Synthetic match"},
        text=f"Synthetic text for {chunk_id}.",
        score=score,
    )


def test_committed_registry_freezes_the_complete_synthetic_corpus(
    committed_registry: TemporalCorpusRegistry,
) -> None:
    assert committed_registry.corpus_id == TEMPORAL_CORPUS_ID
    assert committed_registry.descriptor_sha256 == TEMPORAL_CORPUS_DESCRIPTOR_SHA256
    assert len(committed_registry.corpus.sources) == 4
    assert len(committed_registry.corpus.chunks) == 6
    assert (
        registry_module.hashlib.sha256(committed_registry.source_manifest_bytes).hexdigest()
        == "cc25ae9085518af89032b9b3bd29aeb56f1d0b15051c51e4d7070a9088b4d8a6"
    )
    assert (
        registry_module.hashlib.sha256(committed_registry.document_chunk_bytes).hexdigest()
        == "c22018874c54fb2b6c98df4c816375fbc610102fbbd629542a57734c9ad5b7ee"
    )

    descriptor = committed_registry.canonical_descriptor_bytes().decode("utf-8")
    assert "example.org" not in descriptor
    assert "exact future answer" not in descriptor
    assert "data/fixtures" not in descriptor


def test_committed_paths_cover_every_jsonl_in_the_synthetic_fixture_directory() -> None:
    fixture_root = REPOSITORY_ROOT / "data" / "fixtures" / "retrieval"
    discovered = {path.relative_to(REPOSITORY_ROOT) for path in fixture_root.glob("*.jsonl")}

    assert discovered == {
        COMMITTED_SOURCE_MANIFEST_PATH,
        COMMITTED_DOCUMENT_CHUNK_PATH,
    }


def test_generic_loader_matches_the_committed_loader(
    committed_registry: TemporalCorpusRegistry,
) -> None:
    generic = load_temporal_corpus_registry(
        REPOSITORY_ROOT,
        corpus_id=TEMPORAL_CORPUS_ID,
        source_manifest_path=COMMITTED_SOURCE_MANIFEST_PATH,
        document_chunk_path=COMMITTED_DOCUMENT_CHUNK_PATH,
    )

    assert generic == committed_registry
    assert generic.canonical_descriptor_bytes() == (committed_registry.canonical_descriptor_bytes())


def test_committed_corpus_id_is_pinned_to_one_descriptor(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        registry_module,
        "TEMPORAL_CORPUS_DESCRIPTOR_SHA256",
        "0" * 64,
    )

    with pytest.raises(ValueError, match="preserve v1"):
        load_committed_temporal_corpus_registry(REPOSITORY_ROOT)


@pytest.mark.parametrize(
    ("language", "expected_source", "expected_text"),
    [
        (
            LanguageCode.KOREAN,
            "synthetic-outlook-2024-05-ko",
            "수출 증가",
        ),
        (
            LanguageCode.ENGLISH,
            "synthetic-outlook-2024-05-en",
            "Stronger exports",
        ),
    ],
    ids=("ko", "en"),
)
def test_adapter_maps_bilingual_matches_to_typed_selected_evidence(
    committed_registry: TemporalCorpusRegistry,
    language: LanguageCode,
    expected_source: str,
    expected_text: str,
) -> None:
    call = _call(language=language)

    result = execute_temporal_document_call(
        call=call,
        registry=committed_registry,
    )

    assert result.call_id == call.call_id
    assert result.tool_name.value == "retrieve_temporal_documents"
    assert result.status is ToolOutcomeStatus.SUCCESS
    assert result.abstention is None
    assert result.error is None
    assert result.payload is not None
    assert result.payload.matches[0].source_id == expected_source
    assert expected_text in result.payload.matches[0].text
    assert all(match.language is language for match in result.payload.matches)
    assert all(match.published_on <= call.arguments.as_of for match in result.payload.matches)
    serialized = result.model_dump_json()
    assert "synthetic-outlook-2024-08" not in serialized
    assert "exact future answer" not in serialized
    assert "canonical_url" not in serialized
    assert "retrieved_at" not in serialized
    assert "data/fixtures" not in serialized


def test_inclusive_cutoff_and_top_k_are_preserved(
    committed_registry: TemporalCorpusRegistry,
) -> None:
    call = _call(as_of=date(2024, 5, 23), top_k=1)

    result = execute_temporal_document_call(
        call=call,
        registry=committed_registry,
    )

    assert result.payload is not None
    assert len(result.payload.matches) == 1
    assert result.payload.matches[0].published_on == call.arguments.as_of


def test_adapter_preserves_stable_tie_order_and_the_top_k_20_boundary(
    committed_registry: TemporalCorpusRegistry,
) -> None:
    source = next(
        source
        for source in committed_registry.corpus.sources
        if source.source_id == "synthetic-outlook-2024-05-en"
    )
    original = next(
        chunk
        for chunk in committed_registry.corpus.chunks
        if chunk.chunk_id == "synthetic-2024-05-en-growth"
    )
    tie_b = DocumentChunk.model_validate(
        {
            **original.model_dump(mode="python"),
            "chunk_id": "tie-b",
        }
    )
    tie_a = DocumentChunk.model_validate(
        {
            **original.model_dump(mode="python"),
            "chunk_id": "tie-a",
        }
    )
    registry = _registry_from_corpus(
        TemporalDocumentCorpus(
            sources=(source,),
            chunks=(tie_b, tie_a),
        )
    )

    wide = execute_temporal_document_call(
        call=_call(top_k=20, call_id="tie-wide"),
        registry=registry,
    )
    narrow = execute_temporal_document_call(
        call=_call(top_k=1, call_id="tie-narrow"),
        registry=registry,
    )

    assert wide.payload is not None
    assert narrow.payload is not None
    assert tuple(match.chunk_id for match in wide.payload.matches) == ("tie-a", "tie-b")
    assert tuple(match.chunk_id for match in narrow.payload.matches) == ("tie-a",)


def test_adapter_result_round_trips_in_a_complete_execution_trace(
    committed_registry: TemporalCorpusRegistry,
) -> None:
    call = _call(top_k=1)
    result = execute_temporal_document_call(
        call=call,
        registry=committed_registry,
    )
    assert result.payload is not None
    request = ExecutionRequest(
        request_id="temporal-request-01",
        question=call.arguments.question,
        language=call.arguments.language,
        requested_as_of=call.arguments.as_of,
        effective_as_of=call.arguments.as_of,
    )
    trace = ExecutionTrace(
        trace_id="temporal-trace-01",
        recorded_at=datetime(2026, 7, 29, tzinfo=UTC),
        request=request,
        environment=ExecutionEnvironmentProvenance(
            executor_id="test-executor-v1",
            executor_sha256="a" * 64,
            tool_registry_id="test-tool-registry-v1",
            tool_registry_sha256="b" * 64,
            artifact_registry_id="test-artifact-registry-v1",
            artifact_registry_sha256="c" * 64,
            retrieval_corpus_id=committed_registry.corpus_id,
            retrieval_corpus_sha256=committed_registry.descriptor_sha256,
        ),
        planner=PlannerProvenance(
            planner_id="test-scripted-planner-v1",
            mode=PlannerMode.SCRIPTED,
        ),
        status=TraceStatus.COMPLETE,
        plan=RoutePlan(
            route=EvidenceRoute.DOCUMENTS,
            tool_calls=(call,),
        ),
        tool_results=(result,),
        evidence_packet=ExecutionEvidencePacket(
            request=request,
            planned_route=EvidenceRoute.DOCUMENTS,
            status=PacketStatus.COMPLETE,
            documents=result.payload.matches,
        ),
    )

    assert ExecutionTrace.model_validate_json(trace.model_dump_json()) == trace


@pytest.mark.parametrize(
    ("question", "as_of"),
    [
        (ENGLISH_QUESTION, date(2024, 5, 22)),
        ("?!?!?!", AS_OF),
        ("Quasar zephyr nebula", AS_OF),
    ],
    ids=("before-publication", "punctuation", "no-overlap"),
)
def test_empty_low_level_results_become_sanitized_abstentions(
    committed_registry: TemporalCorpusRegistry,
    question: str,
    as_of: date,
) -> None:
    call = _call(question=question, as_of=as_of, call_id="empty-document-call")

    result = execute_temporal_document_call(
        call=call,
        registry=committed_registry,
    )

    assert result.status is ToolOutcomeStatus.ABSTAINED
    assert result.payload is None
    assert result.error is None
    assert result.abstention is not None
    assert (
        result.abstention.reason_code
        == TemporalDocumentAbstentionReason.NO_TEMPORAL_DOCUMENT_MATCH.value
    )
    serialized = result.model_dump_json()
    assert "synthetic-outlook-2024-08" not in serialized
    assert "exact future answer" not in serialized


def test_future_and_other_language_inputs_cannot_change_the_typed_result(
    committed_registry: TemporalCorpusRegistry,
) -> None:
    call = _call()
    eligible_sources = tuple(
        source
        for source in committed_registry.corpus.sources
        if source.language is call.arguments.language
        and source.published_on <= call.arguments.as_of
    )
    eligible_ids = {source.source_id for source in eligible_sources}
    physically_filtered = TemporalDocumentCorpus(
        sources=eligible_sources,
        chunks=tuple(
            chunk for chunk in committed_registry.corpus.chunks if chunk.source_id in eligible_ids
        ),
    )

    full_result = execute_temporal_document_call(
        call=call,
        registry=committed_registry,
    )
    filtered_result = execute_temporal_document_call(
        call=call,
        registry=_registry_from_corpus(physically_filtered),
    )

    assert full_result == filtered_result
    assert full_result.model_dump_json() == filtered_result.model_dump_json()


def test_nonreturned_future_chunk_changes_the_digest_but_not_the_cutoff_result(
    committed_registry: TemporalCorpusRegistry,
) -> None:
    future_chunk = next(
        chunk
        for chunk in committed_registry.corpus.chunks
        if chunk.chunk_id == "synthetic-2024-08-en-growth"
    )
    changed_chunk = DocumentChunk.model_validate(
        {
            **future_chunk.model_dump(mode="python"),
            "text": f"{future_chunk.text} One-byte-equivalent drift.",
        }
    )
    changed_corpus = TemporalDocumentCorpus(
        sources=committed_registry.corpus.sources,
        chunks=tuple(
            changed_chunk if chunk.chunk_id == changed_chunk.chunk_id else chunk
            for chunk in committed_registry.corpus.chunks
        ),
    )
    changed_registry = _registry_from_corpus(
        changed_corpus,
        corpus_id=TEMPORAL_CORPUS_ID,
    )
    call = _call()

    assert changed_registry.descriptor_sha256 != committed_registry.descriptor_sha256
    assert execute_temporal_document_call(
        call=call,
        registry=changed_registry,
    ) == execute_temporal_document_call(
        call=call,
        registry=committed_registry,
    )


def test_repeated_load_and_call_are_byte_identical() -> None:
    first_registry = load_committed_temporal_corpus_registry(REPOSITORY_ROOT)
    second_registry = load_committed_temporal_corpus_registry(REPOSITORY_ROOT)
    call = _call(top_k=1)

    first = execute_temporal_document_call(call=call, registry=first_registry)
    second = execute_temporal_document_call(call=call, registry=second_registry)

    assert first_registry.canonical_descriptor_bytes() == (
        second_registry.canonical_descriptor_bytes()
    )
    assert first.model_dump_json() == second.model_dump_json()


def test_registry_constructor_rejects_byte_and_model_mismatches(
    committed_registry: TemporalCorpusRegistry,
) -> None:
    with pytest.raises(ValueError, match="source manifest JSONL"):
        TemporalCorpusRegistry(
            corpus_id="invalid-source-bytes",
            corpus=committed_registry.corpus,
            source_manifest_bytes="not bytes",  # type: ignore[arg-type]
            document_chunk_bytes=committed_registry.document_chunk_bytes,
        )
    with pytest.raises(ValueError, match="document chunk JSONL"):
        TemporalCorpusRegistry(
            corpus_id="invalid-chunk-bytes",
            corpus=committed_registry.corpus,
            source_manifest_bytes=committed_registry.source_manifest_bytes,
            document_chunk_bytes="not bytes",  # type: ignore[arg-type]
        )
    with pytest.raises(ValueError, match="model differs"):
        TemporalCorpusRegistry(
            corpus_id="mismatched-model",
            corpus=TemporalDocumentCorpus(),
            source_manifest_bytes=committed_registry.source_manifest_bytes,
            document_chunk_bytes=committed_registry.document_chunk_bytes,
        )
    with pytest.raises(ValueError):
        TemporalCorpusRegistry(
            corpus_id="swapped-bytes",
            corpus=committed_registry.corpus,
            source_manifest_bytes=committed_registry.document_chunk_bytes,
            document_chunk_bytes=committed_registry.source_manifest_bytes,
        )


def test_registry_constructor_rejects_nonexact_and_unbounded_bytes(
    committed_registry: TemporalCorpusRegistry,
) -> None:
    changed_text = committed_registry.document_chunk_bytes.decode("utf-8").replace(
        "Stronger exports",
        "The exact future answer",
        1,
    )
    deceptive_bytes = _DecodeOverridingBytes(
        committed_registry.document_chunk_bytes,
        changed_text,
    )
    with pytest.raises(ValueError, match="immutable bytes"):
        TemporalCorpusRegistry(
            corpus_id="decode-overriding-bytes",
            corpus=committed_registry.corpus,
            source_manifest_bytes=committed_registry.source_manifest_bytes,
            document_chunk_bytes=deceptive_bytes,
        )

    for role in ("source_manifest_bytes", "document_chunk_bytes"):
        for payload in (b"", b"X" * (MAX_TEMPORAL_CORPUS_FILE_BYTES + 1)):
            inputs = {
                "source_manifest_bytes": committed_registry.source_manifest_bytes,
                "document_chunk_bytes": committed_registry.document_chunk_bytes,
            }
            inputs[role] = payload
            with pytest.raises(ValueError, match="bounded size"):
                TemporalCorpusRegistry(
                    corpus_id=f"unbounded-{role}",
                    corpus=committed_registry.corpus,
                    **inputs,
                )


def test_adapter_rejects_missing_or_corrupted_registry(
    committed_registry: TemporalCorpusRegistry,
) -> None:
    call = _call(call_id="corrupt-registry-call")
    missing = execute_temporal_document_call(
        call=call,
        registry=object(),  # type: ignore[arg-type]
    )

    corrupt_registry = load_committed_temporal_corpus_registry(REPOSITORY_ROOT)
    object.__setattr__(corrupt_registry, "corpus", "not a corpus")
    corrupt = execute_temporal_document_call(
        call=call,
        registry=corrupt_registry,
    )

    deleted_registry = load_committed_temporal_corpus_registry(REPOSITORY_ROOT)
    object.__delattr__(deleted_registry, "corpus")
    deleted = execute_temporal_document_call(
        call=call,
        registry=deleted_registry,
    )

    original_chunk = committed_registry.corpus.chunks[0]
    changed_chunk = DocumentChunk.model_validate(
        {
            **original_chunk.model_dump(mode="python"),
            "text": "The exact future answer leaked into a registered old chunk.",
        }
    )
    changed_corpus = TemporalDocumentCorpus(
        sources=committed_registry.corpus.sources,
        chunks=tuple(
            changed_chunk if chunk.chunk_id == changed_chunk.chunk_id else chunk
            for chunk in committed_registry.corpus.chunks
        ),
    )
    byte_model_mismatch = load_committed_temporal_corpus_registry(REPOSITORY_ROOT)
    object.__setattr__(byte_model_mismatch, "corpus", changed_corpus)
    with pytest.raises(ValueError, match="model differs"):
        _ = byte_model_mismatch.descriptor_sha256
    mismatched = execute_temporal_document_call(
        call=call,
        registry=byte_model_mismatch,
    )

    deceptive_registry = load_committed_temporal_corpus_registry(REPOSITORY_ROOT)
    changed_text = deceptive_registry.document_chunk_bytes.decode("utf-8").replace(
        "Stronger exports",
        "The exact future answer",
        1,
    )
    object.__setattr__(
        deceptive_registry,
        "document_chunk_bytes",
        _DecodeOverridingBytes(
            deceptive_registry.document_chunk_bytes,
            changed_text,
        ),
    )
    deceptive = execute_temporal_document_call(
        call=call,
        registry=deceptive_registry,
    )

    oversized_registry = load_committed_temporal_corpus_registry(REPOSITORY_ROOT)
    object.__setattr__(
        oversized_registry,
        "document_chunk_bytes",
        b"X" * (MAX_TEMPORAL_CORPUS_FILE_BYTES + 1),
    )
    oversized = execute_temporal_document_call(
        call=call,
        registry=oversized_registry,
    )

    for result in (missing, corrupt, deleted, mismatched, deceptive, oversized):
        assert result.status is ToolOutcomeStatus.ERROR
        assert result.error is not None
        assert result.error.code == "temporal_corpus_misconfigured"
        assert result.error.call_id == call.call_id
        assert "exact future answer" not in result.model_dump_json()


def test_unexpected_query_or_retriever_failure_is_sanitized(
    committed_registry: TemporalCorpusRegistry,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    call = _call(call_id="retriever-failure-call")

    def fail_retrieval(*args: Any, **kwargs: Any) -> Any:
        raise RuntimeError("private future text and local path")

    monkeypatch.setattr(adapter_module, "_retrieve_temporal_documents", fail_retrieval)
    result = execute_temporal_document_call(
        call=call,
        registry=committed_registry,
    )

    assert result.error is not None
    assert result.error.code == "temporal_retrieval_failed"
    assert result.error.call_id == call.call_id
    assert "private future text" not in result.error.message
    assert "local path" not in result.error.message


@pytest.mark.parametrize(
    "case",
    (
        "wrong-type",
        "wrong-query",
        "too-many",
        "duplicate",
        "out-of-order",
        "wrong-language",
        "future",
    ),
)
def test_invalid_internal_results_become_sanitized_errors(
    committed_registry: TemporalCorpusRegistry,
    monkeypatch: pytest.MonkeyPatch,
    case: str,
) -> None:
    call = _call(top_k=2, call_id=f"invalid-result-{case}")
    query = _query_for(call)
    high = _match(chunk_id="high", score=2.0)
    low = _match(chunk_id="low", score=1.0)
    if case == "wrong-type":
        invalid: Any = object()
    elif case == "wrong-query":
        invalid = TemporalDocumentRetrievalResult(
            query=query.model_copy(update={"top_k": 1}),
            matches=(high,),
        )
    elif case == "too-many":
        invalid = TemporalDocumentRetrievalResult(
            query=query,
            matches=(high, low, _match(chunk_id="third", score=0.5)),
        )
    elif case == "duplicate":
        invalid = TemporalDocumentRetrievalResult(
            query=query,
            matches=(high, high),
        )
    elif case == "out-of-order":
        invalid = TemporalDocumentRetrievalResult(
            query=query,
            matches=(low, high),
        )
    elif case == "wrong-language":
        invalid = TemporalDocumentRetrievalResult(
            query=query,
            matches=(
                _match(
                    chunk_id="korean",
                    score=1.0,
                    language=LanguageCode.KOREAN,
                ),
            ),
        )
    else:
        invalid = TemporalDocumentRetrievalResult(
            query=query,
            matches=(
                _match(
                    chunk_id="future",
                    score=1.0,
                    published_on=date(2024, 8, 22),
                ),
            ),
        )

    monkeypatch.setattr(
        adapter_module,
        "_retrieve_temporal_documents",
        lambda **kwargs: invalid,
    )
    result = execute_temporal_document_call(
        call=call,
        registry=committed_registry,
    )

    assert result.status is ToolOutcomeStatus.ERROR
    assert result.error is not None
    assert result.error.code == "temporal_retrieval_failed"
    assert result.error.call_id == call.call_id


def test_unregistered_internal_match_becomes_a_sanitized_error(
    committed_registry: TemporalCorpusRegistry,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    call = _call(top_k=1, call_id="unregistered-result")
    query = _query_for(call)
    expected = adapter_module._reference_retrieve_temporal_documents(
        corpus=committed_registry.corpus,
        query=query,
    )
    trusted = expected.matches[0]
    forged = RetrievedDocumentChunk.model_validate(
        {
            **trusted.model_dump(mode="python"),
            "chunk_id": "fabricated-chunk",
            "text": "Private fabricated evidence.",
        }
    )
    monkeypatch.setattr(
        adapter_module,
        "_retrieve_temporal_documents",
        lambda **kwargs: TemporalDocumentRetrievalResult(
            query=query,
            matches=(forged,),
        ),
    )

    result = execute_temporal_document_call(call=call, registry=committed_registry)

    assert result.status is ToolOutcomeStatus.ERROR
    assert result.error is not None
    assert result.error.code == "temporal_retrieval_failed"
    assert "fabricated" not in result.model_dump_json().lower()


@pytest.mark.parametrize(
    ("field", "replacement"),
    (
        ("source_id", "fabricated-source"),
        ("source_sha256", "f" * 64),
        ("published_on", date(2024, 5, 22)),
        ("locator", {"page": 999, "section": "Fabricated"}),
        ("text", "Private fabricated evidence."),
    ),
)
def test_registered_internal_match_field_drift_becomes_a_sanitized_error(
    committed_registry: TemporalCorpusRegistry,
    monkeypatch: pytest.MonkeyPatch,
    field: str,
    replacement: object,
) -> None:
    call = _call(top_k=1, call_id=f"field-drift-{field}")
    query = _query_for(call)
    expected = adapter_module._reference_retrieve_temporal_documents(
        corpus=committed_registry.corpus,
        query=query,
    )
    trusted = expected.matches[0]
    drifted = RetrievedDocumentChunk.model_validate(
        {
            **trusted.model_dump(mode="python"),
            field: replacement,
        }
    )
    monkeypatch.setattr(
        adapter_module,
        "_retrieve_temporal_documents",
        lambda **kwargs: TemporalDocumentRetrievalResult(
            query=query,
            matches=(drifted,),
        ),
    )

    result = execute_temporal_document_call(call=call, registry=committed_registry)

    assert result.status is ToolOutcomeStatus.ERROR
    assert result.error is not None
    assert result.error.code == "temporal_retrieval_failed"
    assert "fabricated" not in result.model_dump_json().lower()


def test_noncanonical_internal_score_becomes_a_sanitized_error(
    committed_registry: TemporalCorpusRegistry,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    call = _call(top_k=1, call_id="noncanonical-score")
    query = _query_for(call)
    expected = adapter_module._reference_retrieve_temporal_documents(
        corpus=committed_registry.corpus,
        query=query,
    )
    trusted = expected.matches[0]
    drifted = RetrievedDocumentChunk.model_validate(
        {
            **trusted.model_dump(mode="python"),
            "score": trusted.score + 1e-13,
        }
    )
    assert drifted.score != trusted.score
    monkeypatch.setattr(
        adapter_module,
        "_retrieve_temporal_documents",
        lambda **kwargs: TemporalDocumentRetrievalResult(
            query=query,
            matches=(drifted,),
        ),
    )

    result = execute_temporal_document_call(call=call, registry=committed_registry)

    assert result.status is ToolOutcomeStatus.ERROR
    assert result.error is not None
    assert result.error.code == "temporal_retrieval_failed"


@pytest.mark.parametrize("exception", (ValueError("model detail"), RuntimeError("private detail")))
def test_evidence_mapping_failures_are_sanitized(
    committed_registry: TemporalCorpusRegistry,
    monkeypatch: pytest.MonkeyPatch,
    exception: Exception,
) -> None:
    def fail_evidence(**kwargs: Any) -> Any:
        raise exception

    monkeypatch.setattr(adapter_module, "DocumentMatchEvidence", fail_evidence)
    result = execute_temporal_document_call(
        call=_call(call_id="mapping-failure-call"),
        registry=committed_registry,
    )

    assert result.error is not None
    assert result.error.code == "temporal_retrieval_failed"
    assert "detail" not in result.error.message


def test_loader_sanitizes_missing_repository_and_fixture_roots(tmp_path: Path) -> None:
    missing_root = tmp_path / "private-missing-repository"
    with pytest.raises(
        TemporalCorpusRegistryLoadError,
        match="repository root could not be resolved",
    ) as repository_error:
        load_temporal_corpus_registry(
            missing_root,
            corpus_id="missing-repository",
            source_manifest_path=COMMITTED_SOURCE_MANIFEST_PATH,
            document_chunk_path=COMMITTED_DOCUMENT_CHUNK_PATH,
        )
    assert str(missing_root) not in str(repository_error.value)

    with pytest.raises(
        TemporalCorpusRegistryLoadError,
        match="corpus root could not be resolved",
    ) as fixture_error:
        load_temporal_corpus_registry(
            tmp_path,
            corpus_id="missing-fixture-root",
            source_manifest_path=COMMITTED_SOURCE_MANIFEST_PATH,
            document_chunk_path=COMMITTED_DOCUMENT_CHUNK_PATH,
        )
    assert str(tmp_path) not in str(fixture_error.value)


def test_loader_rejects_untrusted_paths_and_roles(tmp_path: Path) -> None:
    _write_corpus_files(tmp_path)
    fixture_root = tmp_path / "data" / "fixtures" / "retrieval"
    wrong_suffix = fixture_root / "sources.txt"
    shutil.copyfile(tmp_path / COMMITTED_SOURCE_MANIFEST_PATH, wrong_suffix)

    with pytest.raises(ValueError, match="distinct files"):
        load_temporal_corpus_registry(
            tmp_path,
            corpus_id="same-role-file",
            source_manifest_path=COMMITTED_SOURCE_MANIFEST_PATH,
            document_chunk_path=COMMITTED_SOURCE_MANIFEST_PATH,
        )
    with pytest.raises(ValueError, match="repository-relative"):
        load_temporal_corpus_registry(
            tmp_path,
            corpus_id="absolute-path",
            source_manifest_path=(tmp_path / COMMITTED_SOURCE_MANIFEST_PATH).resolve(),
            document_chunk_path=COMMITTED_DOCUMENT_CHUNK_PATH,
        )
    with pytest.raises(ValueError, match="escapes"):
        load_temporal_corpus_registry(
            tmp_path,
            corpus_id="escaped-path",
            source_manifest_path=Path("data/fixtures/retrieval/../../../outside.jsonl"),
            document_chunk_path=COMMITTED_DOCUMENT_CHUNK_PATH,
        )
    with pytest.raises(ValueError, match="must be JSONL"):
        load_temporal_corpus_registry(
            tmp_path,
            corpus_id="wrong-suffix",
            source_manifest_path=wrong_suffix.relative_to(tmp_path),
            document_chunk_path=COMMITTED_DOCUMENT_CHUNK_PATH,
        )
    with pytest.raises(TemporalCorpusRegistryLoadError, match="does not exist"):
        load_temporal_corpus_registry(
            tmp_path,
            corpus_id="missing-file",
            source_manifest_path=Path("data/fixtures/retrieval/missing.jsonl"),
            document_chunk_path=COMMITTED_DOCUMENT_CHUNK_PATH,
        )


@pytest.mark.parametrize(
    "source_bytes",
    (
        b"\xff",
        b"\n",
        b'{"schema_version":"2.0.0","schema_version":"2.0.0"}\n',
        b'{"value":NaN}\n',
        b"[]\n",
        b"{\n",
        b"[" * 1_100 + b"]" * 1_100 + b"\n",
    ),
    ids=(
        "invalid-utf8",
        "blank-record",
        "duplicate-key",
        "nonfinite-constant",
        "nonobject",
        "invalid-json",
        "recursive-json",
    ),
)
def test_loader_sanitizes_invalid_jsonl(
    tmp_path: Path,
    source_bytes: bytes,
) -> None:
    _write_corpus_files(tmp_path, source_bytes=source_bytes)

    with pytest.raises(TemporalCorpusRegistryLoadError, match="corpus is invalid"):
        load_temporal_corpus_registry(
            tmp_path,
            corpus_id="invalid-jsonl",
            source_manifest_path=COMMITTED_SOURCE_MANIFEST_PATH,
            document_chunk_path=COMMITTED_DOCUMENT_CHUNK_PATH,
        )


def test_loader_rejects_record_count_and_corpus_binding_drift(tmp_path: Path) -> None:
    source_line = (REPOSITORY_ROOT / COMMITTED_SOURCE_MANIFEST_PATH).read_bytes().splitlines()[0]
    too_many_sources = b"\n".join(
        source_line for _ in range(registry_module.MAX_TEMPORAL_CORPUS_SOURCES + 1)
    )
    _write_corpus_files(tmp_path, source_bytes=too_many_sources)
    with pytest.raises(TemporalCorpusRegistryLoadError, match="corpus is invalid"):
        load_temporal_corpus_registry(
            tmp_path,
            corpus_id="too-many-sources",
            source_manifest_path=COMMITTED_SOURCE_MANIFEST_PATH,
            document_chunk_path=COMMITTED_DOCUMENT_CHUNK_PATH,
        )

    valid_chunks = (REPOSITORY_ROOT / COMMITTED_DOCUMENT_CHUNK_PATH).read_text(encoding="utf-8")
    unknown_source = valid_chunks.replace(
        '"source_id":"synthetic-outlook-2024-05-ko"',
        '"source_id":"unknown-synthetic-source"',
        1,
    ).encode("utf-8")
    _write_corpus_files(tmp_path, chunk_bytes=unknown_source)
    with pytest.raises(TemporalCorpusRegistryLoadError, match="corpus is invalid"):
        load_temporal_corpus_registry(
            tmp_path,
            corpus_id="binding-drift",
            source_manifest_path=COMMITTED_SOURCE_MANIFEST_PATH,
            document_chunk_path=COMMITTED_DOCUMENT_CHUNK_PATH,
        )


@pytest.mark.parametrize("size", (0, MAX_TEMPORAL_CORPUS_FILE_BYTES + 1))
def test_loader_rejects_empty_or_oversized_files(
    tmp_path: Path,
    size: int,
) -> None:
    _write_corpus_files(tmp_path, source_bytes=b"X" * size)

    with pytest.raises(ValueError, match="bounded size"):
        load_temporal_corpus_registry(
            tmp_path,
            corpus_id="invalid-size",
            source_manifest_path=COMMITTED_SOURCE_MANIFEST_PATH,
            document_chunk_path=COMMITTED_DOCUMENT_CHUNK_PATH,
        )


def test_loader_sanitizes_stat_and_read_failures(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _write_corpus_files(tmp_path)
    source_path = (tmp_path / COMMITTED_SOURCE_MANIFEST_PATH).resolve()
    original_is_file = Path.is_file
    original_stat = Path.stat
    original_read_bytes = Path.read_bytes

    def controlled_is_file(path: Path) -> bool:
        if path == source_path:
            return True
        return original_is_file(path)

    def fail_stat(path: Path, *args: object, **kwargs: object) -> Any:
        if path == source_path:
            raise OSError("private source path")
        return original_stat(path, *args, **kwargs)

    monkeypatch.setattr(Path, "is_file", controlled_is_file)
    monkeypatch.setattr(Path, "stat", fail_stat)
    with pytest.raises(
        TemporalCorpusRegistryLoadError,
        match="could not be inspected",
    ):
        load_temporal_corpus_registry(
            tmp_path,
            corpus_id="stat-failure",
            source_manifest_path=COMMITTED_SOURCE_MANIFEST_PATH,
            document_chunk_path=COMMITTED_DOCUMENT_CHUNK_PATH,
        )

    monkeypatch.undo()
    original_read_bytes = Path.read_bytes

    def fail_read(path: Path) -> bytes:
        if path == source_path:
            raise OSError("private source path")
        return original_read_bytes(path)

    monkeypatch.setattr(Path, "read_bytes", fail_read)
    with pytest.raises(
        TemporalCorpusRegistryLoadError,
        match="could not be read",
    ):
        load_temporal_corpus_registry(
            tmp_path,
            corpus_id="read-failure",
            source_manifest_path=COMMITTED_SOURCE_MANIFEST_PATH,
            document_chunk_path=COMMITTED_DOCUMENT_CHUNK_PATH,
        )


def test_loader_rejects_file_change_between_stat_and_read(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _write_corpus_files(tmp_path)
    source_path = (tmp_path / COMMITTED_SOURCE_MANIFEST_PATH).resolve()
    original_read_bytes = Path.read_bytes

    def change_after_stat(path: Path) -> bytes:
        payload = original_read_bytes(path)
        if path == source_path:
            return payload[:-1]
        return payload

    monkeypatch.setattr(Path, "read_bytes", change_after_stat)
    with pytest.raises(ValueError, match="changed while"):
        load_temporal_corpus_registry(
            tmp_path,
            corpus_id="read-race",
            source_manifest_path=COMMITTED_SOURCE_MANIFEST_PATH,
            document_chunk_path=COMMITTED_DOCUMENT_CHUNK_PATH,
        )


def test_changed_committed_bytes_require_a_new_corpus_version(tmp_path: Path) -> None:
    chunk_bytes = (
        (REPOSITORY_ROOT / COMMITTED_DOCUMENT_CHUNK_PATH)
        .read_bytes()
        .replace(b"exact future answer", b"exact future output", 1)
    )
    _write_corpus_files(tmp_path, chunk_bytes=chunk_bytes)

    with pytest.raises(ValueError, match="preserve v1"):
        load_committed_temporal_corpus_registry(tmp_path)
