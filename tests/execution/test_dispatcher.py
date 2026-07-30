"""Focused tests for the frozen three-tool registry and dispatcher."""

import hashlib
import inspect
import json
from datetime import date, timedelta
from pathlib import Path
from typing import Any

import pytest

import sovereignlab.execution.dispatcher as dispatcher_module
from sovereignlab.execution import (
    CALLABLE_TOOL_DEFINITIONS,
    CALLABLE_TOOL_REGISTRY_DESCRIPTOR_SHA256,
    CALLABLE_TOOL_REGISTRY_ID,
    EXECUTION_ARTIFACT_REGISTRY_DESCRIPTOR_SHA256,
    EXECUTION_ARTIFACT_REGISTRY_ID,
    CallableRegistryLoadError,
    CallableToolRegistry,
    ToolDispatchError,
    dispatch_tool_call,
    load_committed_callable_tool_registry,
)
from sovereignlab.retrieval.registry import (
    TEMPORAL_CORPUS_DESCRIPTOR_SHA256,
    TEMPORAL_CORPUS_ID,
    TemporalCorpusRegistry,
)
from sovereignlab.schemas import (
    DocumentRetrievalPayload,
    LanguageCode,
    SnapshotAsOfArguments,
    SnapshotAsOfCall,
    SnapshotAsOfResult,
    StesAsOfArguments,
    StesAsOfCall,
    StesAsOfResult,
    TemporalDocumentArguments,
    TemporalDocumentCall,
    TemporalDocumentResult,
    ToolCall,
    ToolName,
    ToolOutcomeStatus,
    ToolResult,
)
from sovereignlab.snapshots import (
    ECOS_GDP_BINDING,
    SNAPSHOT_REGISTRY_DESCRIPTOR_SHA256,
    SNAPSHOT_REGISTRY_ID,
    SnapshotArtifact,
    SnapshotRegistry,
    SnapshotRegistryEntry,
)
from sovereignlab.vintage import (
    CLI_STES_BINDING,
    STES_REGISTRY_DESCRIPTOR_SHA256,
    STES_REGISTRY_ID,
    StesRegistry,
)

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
EXPORTED_SCHEMA_PATHS = {
    ToolName.RETRIEVE_TEMPORAL_DOCUMENTS: (
        REPOSITORY_ROOT
        / "data"
        / "schemas"
        / "retrieve-temporal-documents-arguments-v1.schema.json"
    ),
    ToolName.RESOLVE_STES_AS_OF: (
        REPOSITORY_ROOT / "data" / "schemas" / "resolve-stes-as-of-arguments-v1.schema.json"
    ),
    ToolName.READ_SNAPSHOT_AS_OF: (
        REPOSITORY_ROOT / "data" / "schemas" / "read-snapshot-as-of-arguments-v1.schema.json"
    ),
}
ADAPTER_ATTRIBUTES = {
    ToolName.RETRIEVE_TEMPORAL_DOCUMENTS: "_execute_temporal_document_call",
    ToolName.RESOLVE_STES_AS_OF: "_execute_stes_as_of_call",
    ToolName.READ_SNAPSHOT_AS_OF: "_read_snapshot_as_of",
}


@pytest.fixture(scope="module")
def committed_registry() -> CallableToolRegistry:
    return load_committed_callable_tool_registry(REPOSITORY_ROOT)


@pytest.fixture(scope="module")
def calls() -> dict[ToolName, TemporalDocumentCall | StesAsOfCall | SnapshotAsOfCall]:
    return {
        ToolName.RETRIEVE_TEMPORAL_DOCUMENTS: TemporalDocumentCall(
            call_id="dispatcher-document-call-01",
            tool_name=ToolName.RETRIEVE_TEMPORAL_DOCUMENTS,
            arguments=TemporalDocumentArguments(
                question="Why was the growth outlook revised upward?",
                language=LanguageCode.ENGLISH,
                as_of=date(2024, 5, 31),
                top_k=5,
            ),
        ),
        ToolName.RESOLVE_STES_AS_OF: StesAsOfCall(
            call_id="dispatcher-stes-call-01",
            tool_name=ToolName.RESOLVE_STES_AS_OF,
            arguments=StesAsOfArguments(
                ref_area="KOR",
                freq="M",
                measure="LI_AA",
                unit_measure="IX",
                activity="_T",
                period="2026-05",
                as_of=date(2026, 7, 9),
                normalization_rule_id=CLI_STES_BINDING.normalization_rule_id,
            ),
        ),
        ToolName.READ_SNAPSHOT_AS_OF: SnapshotAsOfCall(
            call_id="dispatcher-snapshot-call-01",
            tool_name=ToolName.READ_SNAPSHOT_AS_OF,
            arguments=SnapshotAsOfArguments(
                source_system=ECOS_GDP_BINDING.source_system,
                table_id=ECOS_GDP_BINDING.table_id,
                item_id=ECOS_GDP_BINDING.item_id,
                period="2026Q1",
                as_of=date(2026, 7, 17),
                normalization_rule_id=ECOS_GDP_BINDING.normalization_rule_id,
            ),
        ),
    }


@pytest.fixture(scope="module")
def real_results(
    committed_registry: CallableToolRegistry,
    calls: dict[ToolName, TemporalDocumentCall | StesAsOfCall | SnapshotAsOfCall],
) -> dict[ToolName, TemporalDocumentResult | StesAsOfResult | SnapshotAsOfResult]:
    return {
        tool_name: dispatch_tool_call(call=call, registry=committed_registry)
        for tool_name, call in calls.items()
    }


def _adapter_result(
    real_results: dict[ToolName, TemporalDocumentResult | StesAsOfResult | SnapshotAsOfResult],
    tool_name: ToolName,
) -> TemporalDocumentResult | StesAsOfResult | SnapshotAsOfResult:
    return real_results[tool_name].model_copy(deep=True)


def _patch_adapter_result(
    monkeypatch: pytest.MonkeyPatch,
    *,
    tool_name: ToolName,
    result: object,
) -> None:
    monkeypatch.setattr(
        dispatcher_module,
        ADAPTER_ATTRIBUTES[tool_name],
        lambda **_: result,
    )


def test_real_adapters_smoke_once_each(
    calls: dict[ToolName, TemporalDocumentCall | StesAsOfCall | SnapshotAsOfCall],
    real_results: dict[ToolName, TemporalDocumentResult | StesAsOfResult | SnapshotAsOfResult],
) -> None:
    document_result = real_results[ToolName.RETRIEVE_TEMPORAL_DOCUMENTS]
    assert isinstance(document_result, TemporalDocumentResult)
    assert document_result.status is ToolOutcomeStatus.SUCCESS
    assert document_result.payload is not None
    assert document_result.payload.matches
    assert document_result.call_id == calls[ToolName.RETRIEVE_TEMPORAL_DOCUMENTS].call_id

    stes_result = real_results[ToolName.RESOLVE_STES_AS_OF]
    assert isinstance(stes_result, StesAsOfResult)
    assert stes_result.status is ToolOutcomeStatus.SUCCESS
    assert stes_result.payload is not None
    assert stes_result.payload.selected_edition == "202607"
    assert stes_result.payload.observation.raw_value == "102.66"

    snapshot_result = real_results[ToolName.READ_SNAPSHOT_AS_OF]
    assert isinstance(snapshot_result, SnapshotAsOfResult)
    assert snapshot_result.status is ToolOutcomeStatus.SUCCESS
    assert snapshot_result.payload is not None
    assert snapshot_result.payload.observation.raw_value == "596692.8"


def test_surface_is_exactly_three_explicit_typed_adapters(
    committed_registry: CallableToolRegistry,
) -> None:
    assert committed_registry.tool_names == (
        ToolName.RETRIEVE_TEMPORAL_DOCUMENTS,
        ToolName.RESOLVE_STES_AS_OF,
        ToolName.READ_SNAPSHOT_AS_OF,
    )
    assert tuple(definition.tool_name for definition in CALLABLE_TOOL_DEFINITIONS) == (
        ToolName.RETRIEVE_TEMPORAL_DOCUMENTS,
        ToolName.RESOLVE_STES_AS_OF,
        ToolName.READ_SNAPSHOT_AS_OF,
    )
    assert {
        definition.tool_name: (
            definition.adapter_id,
            definition.arguments_model_id,
            definition.call_model_id,
            definition.result_model_id,
            definition.dependency_role,
        )
        for definition in CALLABLE_TOOL_DEFINITIONS
    } == {
        ToolName.RETRIEVE_TEMPORAL_DOCUMENTS: (
            "sovereignlab-temporal-document-adapter-v1",
            "TemporalDocumentArguments@1.0.0",
            "TemporalDocumentCall@1.0.0",
            "TemporalDocumentResult@1.0.0",
            "retrieval_corpus",
        ),
        ToolName.RESOLVE_STES_AS_OF: (
            "sovereignlab-stes-as-of-adapter-v1",
            "StesAsOfArguments@1.0.0",
            "StesAsOfCall@1.0.0",
            "StesAsOfResult@1.0.0",
            "historical_stes",
        ),
        ToolName.READ_SNAPSHOT_AS_OF: (
            "sovereignlab-snapshot-as-of-adapter-v1",
            "SnapshotAsOfArguments@1.0.0",
            "SnapshotAsOfCall@1.0.0",
            "SnapshotAsOfResult@1.0.0",
            "latest_only_snapshots",
        ),
    }
    assert dispatcher_module._execute_temporal_document_call is (
        dispatcher_module._reference_execute_temporal_document_call
    )
    assert dispatcher_module._execute_stes_as_of_call is (
        dispatcher_module._reference_execute_stes_as_of_call
    )
    assert dispatcher_module._read_snapshot_as_of is (
        dispatcher_module._reference_read_snapshot_as_of
    )


def test_callable_and_artifact_descriptors_are_frozen_and_data_free(
    committed_registry: CallableToolRegistry,
) -> None:
    callable_bytes = committed_registry.canonical_descriptor_bytes()
    artifact_bytes = committed_registry.canonical_artifact_descriptor_bytes()
    callable_descriptor = json.loads(callable_bytes)
    artifact_descriptor = json.loads(artifact_bytes)

    assert committed_registry.registry_id == CALLABLE_TOOL_REGISTRY_ID
    assert committed_registry.descriptor_sha256 == CALLABLE_TOOL_REGISTRY_DESCRIPTOR_SHA256
    assert (
        committed_registry.artifact_registry_sha256 == EXECUTION_ARTIFACT_REGISTRY_DESCRIPTOR_SHA256
    )
    assert callable_descriptor["registry_id"] == CALLABLE_TOOL_REGISTRY_ID
    assert len(callable_descriptor["tools"]) == 3
    assert artifact_descriptor == {
        "registries": [
            {
                "registry_id": STES_REGISTRY_ID,
                "role": "historical_stes",
                "sha256": STES_REGISTRY_DESCRIPTOR_SHA256,
            },
            {
                "registry_id": SNAPSHOT_REGISTRY_ID,
                "role": "latest_only_snapshots",
                "sha256": SNAPSHOT_REGISTRY_DESCRIPTOR_SHA256,
            },
        ],
        "registry_id": EXECUTION_ARTIFACT_REGISTRY_ID,
        "schema_version": "1.0.0",
    }
    serialized = f"{callable_bytes!r}{artifact_bytes!r}"
    for forbidden in (
        str(REPOSITORY_ROOT),
        "archive_bytes",
        "manifest_bytes",
        "canonical_url",
        "596692.8",
        "102.66",
    ):
        assert forbidden not in serialized


def test_provenance_exposes_all_real_registry_digests(
    committed_registry: CallableToolRegistry,
) -> None:
    provenance = committed_registry.provenance()

    assert provenance.tool_registry_id == CALLABLE_TOOL_REGISTRY_ID
    assert provenance.tool_registry_sha256 == CALLABLE_TOOL_REGISTRY_DESCRIPTOR_SHA256
    assert provenance.artifact_registry_id == EXECUTION_ARTIFACT_REGISTRY_ID
    assert provenance.artifact_registry_sha256 == EXECUTION_ARTIFACT_REGISTRY_DESCRIPTOR_SHA256
    assert provenance.retrieval_corpus_id == TEMPORAL_CORPUS_ID
    assert provenance.retrieval_corpus_sha256 == TEMPORAL_CORPUS_DESCRIPTOR_SHA256
    assert committed_registry.retrieval_corpus_id == TEMPORAL_CORPUS_ID
    assert committed_registry.retrieval_corpus_sha256 == TEMPORAL_CORPUS_DESCRIPTOR_SHA256


def test_provenance_rejects_callable_and_composite_descriptor_drift(
    committed_registry: CallableToolRegistry,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    definition = CALLABLE_TOOL_DEFINITIONS[0]
    original_adapter_id = definition.adapter_id
    try:
        object.__setattr__(definition, "adapter_id", "mutated-adapter-v1")
        with pytest.raises(ValueError, match="descriptor drift"):
            committed_registry.provenance()
    finally:
        object.__setattr__(definition, "adapter_id", original_adapter_id)

    monkeypatch.setattr(
        dispatcher_module,
        "_canonical_artifact_descriptor_bytes",
        lambda **_: b"drifted composite descriptor",
    )
    with pytest.raises(CallableRegistryLoadError, match="frozen callable"):
        committed_registry.provenance()


@pytest.mark.parametrize(
    ("tool_name", "model"),
    [
        (ToolName.RETRIEVE_TEMPORAL_DOCUMENTS, TemporalDocumentArguments),
        (ToolName.RESOLVE_STES_AS_OF, StesAsOfArguments),
        (ToolName.READ_SNAPSHOT_AS_OF, SnapshotAsOfArguments),
    ],
)
def test_argument_schemas_match_fresh_models_and_exported_schemas(
    committed_registry: CallableToolRegistry,
    tool_name: ToolName,
    model: type[Any],
) -> None:
    first = committed_registry.argument_schema(tool_name)
    first["test_mutation"] = True
    second = committed_registry.argument_schema(tool_name)
    exported = json.loads(EXPORTED_SCHEMA_PATHS[tool_name].read_text(encoding="utf-8"))
    definition = next(
        candidate for candidate in CALLABLE_TOOL_DEFINITIONS if candidate.tool_name is tool_name
    )
    canonical = json.dumps(
        second,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode()

    assert "test_mutation" not in second
    assert second == model.model_json_schema()
    assert second == exported
    assert hashlib.sha256(canonical).hexdigest() == definition.arguments_schema_sha256


def test_argument_schema_rejects_non_enum_and_missing_registration(
    committed_registry: CallableToolRegistry,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with pytest.raises(ToolDispatchError, match="not registered") as string_error:
        committed_registry.argument_schema("retrieve_temporal_documents")  # type: ignore[arg-type]
    assert string_error.value.code == "unknown_tool"

    class MissingSnapshotLookup(dict[ToolName, object]):
        def get(self, key: ToolName, default: object = None) -> object:
            if key is ToolName.READ_SNAPSHOT_AS_OF:
                return None
            return super().get(key, default)

    monkeypatch.setattr(
        dispatcher_module,
        "_BINDINGS_BY_NAME",
        MissingSnapshotLookup(dispatcher_module._BINDINGS_BY_NAME),
    )
    with pytest.raises(ValueError, match="frozen surface"):
        committed_registry.argument_schema(ToolName.READ_SNAPSHOT_AS_OF)


def test_registry_rechecks_live_argument_schema_hashes(
    committed_registry: CallableToolRegistry,
    calls: dict[ToolName, TemporalDocumentCall | StesAsOfCall | SnapshotAsOfCall],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        TemporalDocumentArguments,
        "model_json_schema",
        classmethod(lambda cls, *args, **kwargs: StesAsOfArguments.model_json_schema()),
    )
    with pytest.raises(ValueError, match="frozen surface"):
        committed_registry.argument_schema(ToolName.RETRIEVE_TEMPORAL_DOCUMENTS)
    with pytest.raises(ToolDispatchError) as dispatch_error:
        dispatch_tool_call(
            call=calls[ToolName.RETRIEVE_TEMPORAL_DOCUMENTS],
            registry=committed_registry,
        )
    assert dispatch_error.value.code == "tool_registry_misconfigured"

    monkeypatch.undo()

    def fail_schema(*args: object, **kwargs: object) -> dict[str, object]:
        del args, kwargs
        raise RuntimeError("private schema failure")

    monkeypatch.setattr(
        TemporalDocumentArguments,
        "model_json_schema",
        classmethod(fail_schema),
    )
    with pytest.raises(ValueError, match="frozen surface") as schema_error:
        committed_registry.argument_schema(ToolName.RETRIEVE_TEMPORAL_DOCUMENTS)
    assert "private schema failure" not in str(schema_error.value)


def test_argument_schema_rechecks_the_exact_returned_dictionary(
    committed_registry: CallableToolRegistry,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original_schema = TemporalDocumentArguments.model_json_schema
    call_count = 0

    def alternate_schema(*args: object, **kwargs: object) -> dict[str, object]:
        nonlocal call_count
        del args
        call_count += 1
        if call_count == 1:
            return original_schema(**kwargs)
        return StesAsOfArguments.model_json_schema()

    monkeypatch.setattr(
        TemporalDocumentArguments,
        "model_json_schema",
        classmethod(alternate_schema),
    )
    with pytest.raises(ValueError, match="argument schema drift"):
        committed_registry.argument_schema(ToolName.RETRIEVE_TEMPORAL_DOCUMENTS)


def test_registry_rejects_binding_map_value_substitution_before_schema_or_dispatch(
    committed_registry: CallableToolRegistry,
    calls: dict[ToolName, TemporalDocumentCall | StesAsOfCall | SnapshotAsOfCall],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    bindings = dict(dispatcher_module._BINDINGS_BY_NAME)
    bindings[ToolName.RETRIEVE_TEMPORAL_DOCUMENTS] = bindings[ToolName.RESOLVE_STES_AS_OF]
    monkeypatch.setattr(dispatcher_module, "_BINDINGS_BY_NAME", bindings)

    with pytest.raises(ValueError, match="frozen surface"):
        committed_registry.argument_schema(ToolName.RETRIEVE_TEMPORAL_DOCUMENTS)
    with pytest.raises(ToolDispatchError) as dispatch_error:
        dispatch_tool_call(
            call=calls[ToolName.RETRIEVE_TEMPORAL_DOCUMENTS],
            registry=committed_registry,
        )
    assert dispatch_error.value.code == "tool_registry_misconfigured"


def test_registry_constructor_sanitizes_wrong_identity_and_dependency_types(
    committed_registry: CallableToolRegistry,
) -> None:
    class EqualRegistryId(str):
        def __eq__(self, other: object) -> bool:
            return other == CALLABLE_TOOL_REGISTRY_ID

        def __ne__(self, other: object) -> bool:
            return not self == other

    with pytest.raises(CallableRegistryLoadError, match="frozen callable") as identity_error:
        CallableToolRegistry(
            snapshot_registry=committed_registry.snapshot_registry,
            temporal_corpus_registry=committed_registry.temporal_corpus_registry,
            stes_registry=committed_registry.stes_registry,
            registry_id="wrong-callable-registry-v1",
        )
    assert str(identity_error.value) == "the frozen callable tool registry is invalid"

    with pytest.raises(CallableRegistryLoadError, match="frozen callable"):
        CallableToolRegistry(
            snapshot_registry=committed_registry.snapshot_registry,
            temporal_corpus_registry=committed_registry.temporal_corpus_registry,
            stes_registry=committed_registry.stes_registry,
            registry_id=EqualRegistryId("attacker-registry-v1"),
        )

    with pytest.raises(CallableRegistryLoadError, match="frozen callable") as dependency_error:
        CallableToolRegistry(
            snapshot_registry=object(),  # type: ignore[arg-type]
            temporal_corpus_registry=committed_registry.temporal_corpus_registry,
            stes_registry=committed_registry.stes_registry,
        )
    assert "object" not in str(dependency_error.value)


def test_registry_constructor_rejects_callable_and_artifact_digest_drift(
    committed_registry: CallableToolRegistry,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        CallableToolRegistry,
        "_validate_all_dependencies",
        lambda self: (
            SNAPSHOT_REGISTRY_DESCRIPTOR_SHA256,
            TEMPORAL_CORPUS_DESCRIPTOR_SHA256,
            STES_REGISTRY_DESCRIPTOR_SHA256,
        ),
    )
    monkeypatch.setattr(
        dispatcher_module,
        "CALLABLE_TOOL_REGISTRY_DESCRIPTOR_SHA256",
        "0" * 64,
    )
    with pytest.raises(CallableRegistryLoadError, match="frozen callable"):
        CallableToolRegistry(
            snapshot_registry=committed_registry.snapshot_registry,
            temporal_corpus_registry=committed_registry.temporal_corpus_registry,
            stes_registry=committed_registry.stes_registry,
        )

    monkeypatch.setattr(
        dispatcher_module,
        "CALLABLE_TOOL_REGISTRY_DESCRIPTOR_SHA256",
        CALLABLE_TOOL_REGISTRY_DESCRIPTOR_SHA256,
    )
    monkeypatch.setattr(
        dispatcher_module,
        "EXECUTION_ARTIFACT_REGISTRY_DESCRIPTOR_SHA256",
        "0" * 64,
    )
    with pytest.raises(CallableRegistryLoadError, match="frozen callable"):
        CallableToolRegistry(
            snapshot_registry=committed_registry.snapshot_registry,
            temporal_corpus_registry=committed_registry.temporal_corpus_registry,
            stes_registry=committed_registry.stes_registry,
        )


def test_registry_methods_fail_closed_if_surface_or_descriptor_drifts(
    committed_registry: CallableToolRegistry,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(dispatcher_module, "_TOOL_BINDINGS", ())
    with pytest.raises(ValueError, match="frozen surface"):
        _ = committed_registry.tool_names

    monkeypatch.undo()
    monkeypatch.setattr(
        dispatcher_module,
        "CALLABLE_TOOL_REGISTRY_DESCRIPTOR_SHA256",
        "0" * 64,
    )
    with pytest.raises(ValueError, match="descriptor drift"):
        _ = committed_registry.tool_names


def test_committed_loader_sanitizes_internal_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    secret = r"C:\private\raw.json contains 999"

    def fail_snapshot_loader(_: Path) -> SnapshotRegistry:
        raise RuntimeError(secret)

    monkeypatch.setattr(
        dispatcher_module,
        "load_committed_snapshot_registry",
        fail_snapshot_loader,
    )
    with pytest.raises(CallableRegistryLoadError) as exc_info:
        load_committed_callable_tool_registry(REPOSITORY_ROOT)

    assert str(exc_info.value) == "the committed callable tool registry could not be loaded"
    assert secret not in str(exc_info.value)


@pytest.mark.parametrize("tool_name", tuple(ToolName))
def test_dispatch_routes_only_the_matching_dependency(
    committed_registry: CallableToolRegistry,
    calls: dict[ToolName, TemporalDocumentCall | StesAsOfCall | SnapshotAsOfCall],
    real_results: dict[ToolName, TemporalDocumentResult | StesAsOfResult | SnapshotAsOfResult],
    monkeypatch: pytest.MonkeyPatch,
    tool_name: ToolName,
) -> None:
    expected_dependency = {
        ToolName.RETRIEVE_TEMPORAL_DOCUMENTS: committed_registry.temporal_corpus_registry,
        ToolName.RESOLVE_STES_AS_OF: committed_registry.stes_registry,
        ToolName.READ_SNAPSHOT_AS_OF: committed_registry.snapshot_registry,
    }[tool_name]
    received: list[tuple[object, object]] = []

    def adapter(*, call: object, registry: object) -> object:
        received.append((call, registry))
        return _adapter_result(real_results, tool_name)

    monkeypatch.setattr(dispatcher_module, ADAPTER_ATTRIBUTES[tool_name], adapter)
    result = dispatch_tool_call(call=calls[tool_name], registry=committed_registry)

    assert result == real_results[tool_name]
    assert received == [(calls[tool_name], expected_dependency)]
    assert received[0][0] is not calls[tool_name]


@pytest.mark.parametrize(
    ("candidate", "expected_code"),
    [
        ({"tool_name": "unknown_tool"}, "unknown_tool"),
        ({"tool_name": "read_snapshot_as_of"}, "tool_call_type_mismatch"),
        ({"tool_name": []}, "unknown_tool"),
        ({"tool_name": {}}, "unknown_tool"),
        ({"tool_name": None}, "unknown_tool"),
        ({"tool_name": 7}, "unknown_tool"),
        (object(), "unknown_tool"),
    ],
)
def test_dispatch_rejects_unknown_or_unvalidated_calls_without_execution(
    committed_registry: CallableToolRegistry,
    monkeypatch: pytest.MonkeyPatch,
    candidate: object,
    expected_code: str,
) -> None:
    invoked = False

    def forbidden_adapter(**_: object) -> None:
        nonlocal invoked
        invoked = True

    for attribute in ADAPTER_ATTRIBUTES.values():
        monkeypatch.setattr(dispatcher_module, attribute, forbidden_adapter)

    with pytest.raises(ToolDispatchError) as exc_info:
        dispatch_tool_call(call=candidate, registry=committed_registry)  # type: ignore[arg-type]

    assert exc_info.value.code == expected_code
    assert invoked is False


def test_dispatch_rejects_call_subclasses(
    committed_registry: CallableToolRegistry,
    calls: dict[ToolName, TemporalDocumentCall | StesAsOfCall | SnapshotAsOfCall],
) -> None:
    class TemporalDocumentCallSubclass(TemporalDocumentCall):
        pass

    base = calls[ToolName.RETRIEVE_TEMPORAL_DOCUMENTS]
    candidate = TemporalDocumentCallSubclass.model_validate(base.model_dump())

    with pytest.raises(ToolDispatchError) as exc_info:
        dispatch_tool_call(call=candidate, registry=committed_registry)

    assert exc_info.value.code == "tool_call_type_mismatch"


@pytest.mark.parametrize(
    ("mutated_name", "expected_code"),
    [
        (ToolName.READ_SNAPSHOT_AS_OF, "tool_call_type_mismatch"),
        ("unregistered_tool", "unknown_tool"),
        ([], "unknown_tool"),
        ({}, "unknown_tool"),
        (None, "unknown_tool"),
        (7, "unknown_tool"),
    ],
)
def test_dispatch_rejects_mutated_call_names(
    committed_registry: CallableToolRegistry,
    calls: dict[ToolName, TemporalDocumentCall | StesAsOfCall | SnapshotAsOfCall],
    mutated_name: object,
    expected_code: str,
) -> None:
    candidate = calls[ToolName.RETRIEVE_TEMPORAL_DOCUMENTS].model_copy(deep=True)
    object.__setattr__(candidate, "tool_name", mutated_name)

    with pytest.raises(ToolDispatchError) as exc_info:
        dispatch_tool_call(call=candidate, registry=committed_registry)

    assert exc_info.value.code == expected_code


def test_dispatch_rejects_invalid_mutated_call_round_trip(
    committed_registry: CallableToolRegistry,
    calls: dict[ToolName, TemporalDocumentCall | StesAsOfCall | SnapshotAsOfCall],
) -> None:
    candidate = calls[ToolName.RETRIEVE_TEMPORAL_DOCUMENTS].model_copy(deep=True)
    object.__setattr__(candidate, "call_id", f" {candidate.call_id} ")

    with pytest.raises(ToolDispatchError) as exc_info:
        dispatch_tool_call(call=candidate, registry=committed_registry)

    assert exc_info.value.code == "invalid_tool_call"


def test_dispatch_rejects_wrong_or_mutated_registry_before_execution(
    committed_registry: CallableToolRegistry,
    calls: dict[ToolName, TemporalDocumentCall | StesAsOfCall | SnapshotAsOfCall],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    invoked = False

    def forbidden_adapter(**_: object) -> None:
        nonlocal invoked
        invoked = True

    monkeypatch.setattr(
        dispatcher_module,
        "_execute_temporal_document_call",
        forbidden_adapter,
    )
    with pytest.raises(ToolDispatchError) as wrong_type:
        dispatch_tool_call(
            call=calls[ToolName.RETRIEVE_TEMPORAL_DOCUMENTS],
            registry=object(),  # type: ignore[arg-type]
        )
    assert wrong_type.value.code == "tool_registry_misconfigured"

    mutated = object.__new__(CallableToolRegistry)
    object.__setattr__(mutated, "snapshot_registry", committed_registry.snapshot_registry)
    object.__setattr__(
        mutated,
        "temporal_corpus_registry",
        committed_registry.temporal_corpus_registry,
    )
    object.__setattr__(mutated, "stes_registry", committed_registry.stes_registry)
    object.__setattr__(mutated, "registry_id", "mutated-registry-v1")
    with pytest.raises(ToolDispatchError) as wrong_identity:
        dispatch_tool_call(
            call=calls[ToolName.RETRIEVE_TEMPORAL_DOCUMENTS],
            registry=mutated,
        )
    assert wrong_identity.value.code == "tool_registry_misconfigured"
    assert invoked is False


@pytest.mark.parametrize("tool_name", tuple(ToolName))
def test_adapter_exception_becomes_sanitized_typed_error(
    committed_registry: CallableToolRegistry,
    calls: dict[ToolName, TemporalDocumentCall | StesAsOfCall | SnapshotAsOfCall],
    monkeypatch: pytest.MonkeyPatch,
    tool_name: ToolName,
) -> None:
    secret = rf"C:\private\{tool_name.value}.json raw-row=999"

    def fail_adapter(**_: object) -> None:
        raise RuntimeError(secret)

    monkeypatch.setattr(dispatcher_module, ADAPTER_ATTRIBUTES[tool_name], fail_adapter)
    result = dispatch_tool_call(call=calls[tool_name], registry=committed_registry)

    assert result.status is ToolOutcomeStatus.ERROR
    assert result.call_id == calls[tool_name].call_id
    assert result.tool_name is tool_name
    assert result.error is not None
    assert result.error.code == "tool_dispatch_failed"
    assert result.error.message == "The deterministic tool adapter failed unexpectedly."
    assert secret not in result.model_dump_json()


@pytest.mark.parametrize("tool_name", tuple(ToolName))
def test_wrong_result_type_becomes_typed_invalid_result(
    committed_registry: CallableToolRegistry,
    calls: dict[ToolName, TemporalDocumentCall | StesAsOfCall | SnapshotAsOfCall],
    real_results: dict[ToolName, TemporalDocumentResult | StesAsOfResult | SnapshotAsOfResult],
    monkeypatch: pytest.MonkeyPatch,
    tool_name: ToolName,
) -> None:
    wrong_name = next(candidate for candidate in ToolName if candidate is not tool_name)
    _patch_adapter_result(
        monkeypatch,
        tool_name=tool_name,
        result=_adapter_result(real_results, wrong_name),
    )

    result = dispatch_tool_call(call=calls[tool_name], registry=committed_registry)

    assert result.status is ToolOutcomeStatus.ERROR
    assert result.error is not None
    assert result.error.code == "tool_result_invalid"
    assert result.call_id == calls[tool_name].call_id
    assert result.tool_name is tool_name


@pytest.mark.parametrize("tool_name", tuple(ToolName))
def test_wrong_result_identity_becomes_typed_invalid_result(
    committed_registry: CallableToolRegistry,
    calls: dict[ToolName, TemporalDocumentCall | StesAsOfCall | SnapshotAsOfCall],
    real_results: dict[ToolName, TemporalDocumentResult | StesAsOfResult | SnapshotAsOfResult],
    monkeypatch: pytest.MonkeyPatch,
    tool_name: ToolName,
) -> None:
    wrong_id = _adapter_result(real_results, tool_name).model_copy(
        update={"call_id": "different-call-id"}
    )
    _patch_adapter_result(monkeypatch, tool_name=tool_name, result=wrong_id)
    id_result = dispatch_tool_call(call=calls[tool_name], registry=committed_registry)
    assert id_result.error is not None
    assert id_result.error.code == "tool_result_invalid"

    wrong_name = _adapter_result(real_results, tool_name)
    object.__setattr__(
        wrong_name,
        "tool_name",
        next(candidate for candidate in ToolName if candidate is not tool_name),
    )
    _patch_adapter_result(monkeypatch, tool_name=tool_name, result=wrong_name)
    name_result = dispatch_tool_call(call=calls[tool_name], registry=committed_registry)
    assert name_result.error is not None
    assert name_result.error.code == "tool_result_invalid"


@pytest.mark.parametrize("tool_name", tuple(ToolName))
def test_success_fact_drift_becomes_typed_invalid_result(
    committed_registry: CallableToolRegistry,
    calls: dict[ToolName, TemporalDocumentCall | StesAsOfCall | SnapshotAsOfCall],
    real_results: dict[ToolName, TemporalDocumentResult | StesAsOfResult | SnapshotAsOfResult],
    monkeypatch: pytest.MonkeyPatch,
    tool_name: ToolName,
) -> None:
    result = _adapter_result(real_results, tool_name)
    assert result.payload is not None
    if isinstance(result, TemporalDocumentResult):
        first = result.payload.matches[0]
        drifted_match = first.model_copy(
            update={"published_on": calls[tool_name].arguments.as_of + timedelta(days=1)}
        )
        result = result.model_copy(
            update={"payload": DocumentRetrievalPayload(matches=(drifted_match,))}
        )
    elif isinstance(result, StesAsOfResult):
        result = result.model_copy(
            update={
                "payload": result.payload.model_copy(
                    update={"period": "2026-04"},
                )
            }
        )
    else:
        result = result.model_copy(
            update={
                "payload": result.payload.model_copy(
                    update={"period": "2025Q4"},
                )
            }
        )
    _patch_adapter_result(monkeypatch, tool_name=tool_name, result=result)

    dispatched = dispatch_tool_call(call=calls[tool_name], registry=committed_registry)

    assert dispatched.status is ToolOutcomeStatus.ERROR
    assert dispatched.error is not None
    assert dispatched.error.code == "tool_result_invalid"


def test_temporal_success_validation_rejects_limit_duplicate_and_order_drift(
    committed_registry: CallableToolRegistry,
    calls: dict[ToolName, TemporalDocumentCall | StesAsOfCall | SnapshotAsOfCall],
    real_results: dict[ToolName, TemporalDocumentResult | StesAsOfResult | SnapshotAsOfResult],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    tool_name = ToolName.RETRIEVE_TEMPORAL_DOCUMENTS
    base_call = calls[tool_name]
    base_result = _adapter_result(real_results, tool_name)
    assert isinstance(base_call, TemporalDocumentCall)
    assert isinstance(base_result, TemporalDocumentResult)
    assert base_result.payload is not None
    first = base_result.payload.matches[0]

    limited_call = base_call.model_copy(
        update={"arguments": base_call.arguments.model_copy(update={"top_k": 1})}
    )
    too_many = base_result.model_copy(
        update={"payload": DocumentRetrievalPayload(matches=(first, first.model_copy()))}
    )
    _patch_adapter_result(monkeypatch, tool_name=tool_name, result=too_many)
    limited = dispatch_tool_call(call=limited_call, registry=committed_registry)
    assert limited.error is not None
    assert limited.error.code == "tool_result_invalid"

    duplicate = base_result.model_copy(
        update={"payload": DocumentRetrievalPayload(matches=(first, first))}
    )
    _patch_adapter_result(monkeypatch, tool_name=tool_name, result=duplicate)
    duplicated = dispatch_tool_call(call=base_call, registry=committed_registry)
    assert duplicated.error is not None
    assert duplicated.error.code == "tool_result_invalid"

    lower_score = first.model_copy(
        update={
            "chunk_id": "dispatcher-lower-score-chunk",
            "score": max(first.score / 2, 1e-12),
        }
    )
    reversed_order = base_result.model_copy(
        update={"payload": DocumentRetrievalPayload(matches=(lower_score, first))}
    )
    _patch_adapter_result(monkeypatch, tool_name=tool_name, result=reversed_order)
    unordered = dispatch_tool_call(call=base_call, registry=committed_registry)
    assert unordered.error is not None
    assert unordered.error.code == "tool_result_invalid"


def test_caller_owned_call_is_isolated_from_adapter_mutation(
    committed_registry: CallableToolRegistry,
    calls: dict[ToolName, TemporalDocumentCall | StesAsOfCall | SnapshotAsOfCall],
    real_results: dict[ToolName, TemporalDocumentResult | StesAsOfResult | SnapshotAsOfResult],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    tool_name = ToolName.RETRIEVE_TEMPORAL_DOCUMENTS
    caller_call = calls[tool_name].model_copy(deep=True)
    before = caller_call.model_dump_json()

    def mutating_adapter(*, call: TemporalDocumentCall, registry: object) -> TemporalDocumentResult:
        del registry
        object.__setattr__(call, "call_id", "adapter-mutated-call")
        result = _adapter_result(real_results, tool_name)
        assert isinstance(result, TemporalDocumentResult)
        return result

    monkeypatch.setattr(
        dispatcher_module,
        "_execute_temporal_document_call",
        mutating_adapter,
    )
    result = dispatch_tool_call(call=caller_call, registry=committed_registry)

    assert caller_call.model_dump_json() == before
    assert result.status is ToolOutcomeStatus.ERROR
    assert result.error is not None
    assert result.error.code == "tool_result_invalid"
    assert result.call_id == caller_call.call_id


def test_private_call_argument_mutation_cannot_change_real_temporal_evidence(
    committed_registry: CallableToolRegistry,
    calls: dict[ToolName, TemporalDocumentCall | StesAsOfCall | SnapshotAsOfCall],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    caller_call = calls[ToolName.RETRIEVE_TEMPORAL_DOCUMENTS].model_copy(deep=True)
    original_question = caller_call.arguments.question

    def mutate_then_execute(
        *,
        call: TemporalDocumentCall,
        registry: TemporalCorpusRegistry,
    ) -> TemporalDocumentResult:
        original = call.arguments.question
        try:
            object.__setattr__(
                call.arguments,
                "question",
                "Why was consumer price inflation expected to moderate?",
            )
            changed = dispatcher_module._reference_execute_temporal_document_call(
                call=call,
                registry=registry,
            )
        finally:
            object.__setattr__(call.arguments, "question", original)
        assert changed.payload is not None
        assert changed.payload.matches[0].chunk_id == "synthetic-2024-05-en-prices"
        return changed

    monkeypatch.setattr(
        dispatcher_module,
        "_execute_temporal_document_call",
        mutate_then_execute,
    )
    result = dispatch_tool_call(call=caller_call, registry=committed_registry)

    assert caller_call.arguments.question == original_question
    assert result.status is ToolOutcomeStatus.ERROR
    assert result.error is not None
    assert result.error.code == "tool_result_invalid"
    assert "synthetic-2024-05-en-prices" not in result.model_dump_json()


@pytest.mark.parametrize(
    ("tool_name", "mutated_as_of"),
    [
        (ToolName.RESOLVE_STES_AS_OF, date(2026, 6, 30)),
        (ToolName.READ_SNAPSHOT_AS_OF, date(2026, 7, 16)),
    ],
)
def test_private_data_call_mutation_cannot_create_false_abstention(
    committed_registry: CallableToolRegistry,
    calls: dict[ToolName, TemporalDocumentCall | StesAsOfCall | SnapshotAsOfCall],
    monkeypatch: pytest.MonkeyPatch,
    tool_name: ToolName,
    mutated_as_of: date,
) -> None:
    caller_call = calls[tool_name].model_copy(deep=True)
    reference_adapter = {
        ToolName.RESOLVE_STES_AS_OF: dispatcher_module._reference_execute_stes_as_of_call,
        ToolName.READ_SNAPSHOT_AS_OF: dispatcher_module._reference_read_snapshot_as_of,
    }[tool_name]

    def mutate_then_execute(*, call: ToolCall, registry: object) -> ToolResult:
        original = call.arguments.as_of
        try:
            object.__setattr__(call.arguments, "as_of", mutated_as_of)
            changed = reference_adapter(call=call, registry=registry)
        finally:
            object.__setattr__(call.arguments, "as_of", original)
        assert changed.status is ToolOutcomeStatus.ABSTAINED
        return changed

    monkeypatch.setattr(
        dispatcher_module,
        ADAPTER_ATTRIBUTES[tool_name],
        mutate_then_execute,
    )
    result = dispatch_tool_call(call=caller_call, registry=committed_registry)

    assert caller_call.arguments.as_of == calls[tool_name].arguments.as_of
    assert result.status is ToolOutcomeStatus.ERROR
    assert result.error is not None
    assert result.error.code == "tool_result_invalid"


def test_trusted_temporal_replay_failure_is_sanitized_before_candidate_execution(
    committed_registry: CallableToolRegistry,
    calls: dict[ToolName, TemporalDocumentCall | StesAsOfCall | SnapshotAsOfCall],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    candidate_invoked = False
    secret = r"C:\private\trusted-replay.json raw=999"

    def fail_trusted_replay(**_: object) -> None:
        raise RuntimeError(secret)

    def candidate_adapter(**_: object) -> None:
        nonlocal candidate_invoked
        candidate_invoked = True

    monkeypatch.setattr(
        dispatcher_module,
        "_reference_execute_temporal_document_call",
        fail_trusted_replay,
    )
    monkeypatch.setattr(
        dispatcher_module,
        "_execute_temporal_document_call",
        candidate_adapter,
    )
    result = dispatch_tool_call(
        call=calls[ToolName.RETRIEVE_TEMPORAL_DOCUMENTS],
        registry=committed_registry,
    )

    assert result.status is ToolOutcomeStatus.ERROR
    assert result.error is not None
    assert result.error.code == "tool_dispatch_failed"
    assert secret not in result.model_dump_json()
    assert candidate_invoked is False


def test_trusted_snapshot_replay_failure_is_sanitized_before_candidate_execution(
    committed_registry: CallableToolRegistry,
    calls: dict[ToolName, TemporalDocumentCall | StesAsOfCall | SnapshotAsOfCall],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    call = calls[ToolName.READ_SNAPSHOT_AS_OF]
    assert isinstance(call, SnapshotAsOfCall)
    secret = r"C:\private\conditional-replay.json raw=999"
    candidate_invoked = False

    def candidate_adapter(**_: object) -> None:
        nonlocal candidate_invoked
        candidate_invoked = True

    def fail_trusted_replay(**_: object) -> None:
        raise RuntimeError(secret)

    monkeypatch.setattr(
        dispatcher_module,
        "_read_snapshot_as_of",
        candidate_adapter,
    )
    monkeypatch.setattr(
        dispatcher_module,
        "_reference_read_snapshot_as_of",
        fail_trusted_replay,
    )
    result = dispatch_tool_call(call=call, registry=committed_registry)

    assert result.status is ToolOutcomeStatus.ERROR
    assert result.error is not None
    assert result.error.code == "tool_dispatch_failed"
    assert secret not in result.model_dump_json()
    assert candidate_invoked is False


def test_dispatch_is_byte_deterministic(
    committed_registry: CallableToolRegistry,
    calls: dict[ToolName, TemporalDocumentCall | StesAsOfCall | SnapshotAsOfCall],
    real_results: dict[ToolName, TemporalDocumentResult | StesAsOfResult | SnapshotAsOfResult],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    tool_name = ToolName.READ_SNAPSHOT_AS_OF
    _patch_adapter_result(
        monkeypatch,
        tool_name=tool_name,
        result=_adapter_result(real_results, tool_name),
    )

    first = dispatch_tool_call(call=calls[tool_name], registry=committed_registry)
    second = dispatch_tool_call(call=calls[tool_name], registry=committed_registry)

    assert first.model_dump_json() == second.model_dump_json()


def test_dispatch_signature_rejects_model_supplied_artifacts(
    committed_registry: CallableToolRegistry,
    calls: dict[ToolName, TemporalDocumentCall | StesAsOfCall | SnapshotAsOfCall],
) -> None:
    signature = inspect.signature(dispatch_tool_call)
    assert tuple(signature.parameters) == ("call", "registry")
    assert all(
        parameter.kind is inspect.Parameter.KEYWORD_ONLY
        for parameter in signature.parameters.values()
    )
    with pytest.raises(TypeError, match="unexpected keyword"):
        dispatch_tool_call(
            call=calls[ToolName.READ_SNAPSHOT_AS_OF],
            registry=committed_registry,
            archive_bytes=b"model supplied",  # type: ignore[call-arg]
        )


def test_internal_dependency_validation_rejects_unregistered_name(
    committed_registry: CallableToolRegistry,
) -> None:
    with pytest.raises(ValueError, match="no registered dependency"):
        dispatcher_module._validated_dependency(
            committed_registry,
            "unregistered",  # type: ignore[arg-type]
        )


def test_internal_dependency_validation_rejects_callable_descriptor_drift(
    committed_registry: CallableToolRegistry,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        dispatcher_module,
        "_canonical_callable_descriptor_bytes",
        lambda: b"drifted callable descriptor",
    )

    with pytest.raises(ValueError, match="descriptor drift"):
        dispatcher_module._validated_dependency(
            committed_registry,
            ToolName.RETRIEVE_TEMPORAL_DOCUMENTS,
        )


@pytest.mark.parametrize(
    ("validator_name", "registry_type", "expected_digest"),
    [
        (
            "_validated_snapshot_registry",
            SnapshotRegistry,
            SNAPSHOT_REGISTRY_DESCRIPTOR_SHA256,
        ),
        (
            "_validated_temporal_registry",
            TemporalCorpusRegistry,
            TEMPORAL_CORPUS_DESCRIPTOR_SHA256,
        ),
        (
            "_validated_stes_registry",
            StesRegistry,
            STES_REGISTRY_DESCRIPTOR_SHA256,
        ),
    ],
)
def test_component_validators_reject_identity_and_digest_drift(
    committed_registry: CallableToolRegistry,
    monkeypatch: pytest.MonkeyPatch,
    validator_name: str,
    registry_type: type[Any],
    expected_digest: str,
) -> None:
    validator = getattr(dispatcher_module, validator_name)
    component = {
        SnapshotRegistry: committed_registry.snapshot_registry,
        TemporalCorpusRegistry: committed_registry.temporal_corpus_registry,
        StesRegistry: committed_registry.stes_registry,
    }[registry_type]
    assert validator(component) == expected_digest

    with pytest.raises(ValueError, match="identity differs"):
        validator(object())

    monkeypatch.setattr(
        registry_type,
        "descriptor_sha256",
        property(lambda self: "0" * 64),
    )
    with pytest.raises(ValueError, match="descriptor differs"):
        validator(component)


def test_validated_result_rejects_round_trip_mutation(
    calls: dict[ToolName, TemporalDocumentCall | StesAsOfCall | SnapshotAsOfCall],
    real_results: dict[ToolName, TemporalDocumentResult | StesAsOfResult | SnapshotAsOfResult],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    binding = dispatcher_module._BINDINGS_BY_NAME[ToolName.RETRIEVE_TEMPORAL_DOCUMENTS]
    call = calls[ToolName.RETRIEVE_TEMPORAL_DOCUMENTS]
    result = _adapter_result(real_results, ToolName.RETRIEVE_TEMPORAL_DOCUMENTS)

    monkeypatch.setattr(
        TemporalDocumentResult,
        "model_validate",
        classmethod(lambda cls, payload: None),
    )
    with pytest.raises(ValueError, match="round trip changed"):
        dispatcher_module._validated_result(binding, call, result)


def test_adapter_call_revalidation_rejects_wrong_registered_model(
    calls: dict[ToolName, TemporalDocumentCall | StesAsOfCall | SnapshotAsOfCall],
) -> None:
    binding = dispatcher_module._BINDINGS_BY_NAME[ToolName.RETRIEVE_TEMPORAL_DOCUMENTS]
    with pytest.raises(ValueError, match="wrong registered model"):
        dispatcher_module._validate_adapter_call_unchanged(
            binding,
            calls[ToolName.RETRIEVE_TEMPORAL_DOCUMENTS],
            calls[ToolName.RESOLVE_STES_AS_OF],
        )


def test_validated_result_accepts_non_success_without_success_mapping(
    calls: dict[ToolName, TemporalDocumentCall | StesAsOfCall | SnapshotAsOfCall],
) -> None:
    call = calls[ToolName.RETRIEVE_TEMPORAL_DOCUMENTS]
    binding = dispatcher_module._BINDINGS_BY_NAME[ToolName.RETRIEVE_TEMPORAL_DOCUMENTS]
    result = dispatcher_module._dispatch_error(
        call,
        code="test_failure",
        message="A stable test failure.",
    )

    assert dispatcher_module._validated_result(binding, call, result) == result


def test_success_validator_rejects_wrong_payload_models(
    calls: dict[ToolName, TemporalDocumentCall | StesAsOfCall | SnapshotAsOfCall],
    real_results: dict[ToolName, TemporalDocumentResult | StesAsOfResult | SnapshotAsOfResult],
) -> None:
    temporal_call = calls[ToolName.RETRIEVE_TEMPORAL_DOCUMENTS]
    stes_call = calls[ToolName.RESOLVE_STES_AS_OF]
    snapshot_call = calls[ToolName.READ_SNAPSHOT_AS_OF]

    with pytest.raises(ValueError, match="temporal result payload"):
        dispatcher_module._validate_success_result(
            temporal_call,
            real_results[ToolName.RESOLVE_STES_AS_OF],
        )
    with pytest.raises(ValueError, match="STES result payload"):
        dispatcher_module._validate_success_result(
            stes_call,
            real_results[ToolName.READ_SNAPSHOT_AS_OF],
        )
    with pytest.raises(ValueError, match="snapshot result payload"):
        dispatcher_module._validate_success_result(
            snapshot_call,
            real_results[ToolName.RETRIEVE_TEMPORAL_DOCUMENTS],
        )


def test_candidate_temporary_coherent_snapshot_registry_drift_is_rejected(
    committed_registry: CallableToolRegistry,
    calls: dict[ToolName, TemporalDocumentCall | StesAsOfCall | SnapshotAsOfCall],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    snapshot_registry = committed_registry.snapshot_registry
    original_entries = snapshot_registry.entries
    target = snapshot_registry.entry_for(*ECOS_GDP_BINDING.scope)
    assert target is not None
    assert len(target.artifacts) == 1
    artifact = target.artifacts[0]
    original_raw = b'"DATA_VALUE":"596692.8"'
    forged_raw = b'"DATA_VALUE":"696692.8"'
    assert artifact.archive_bytes.count(original_raw) == 1
    forged_archive = artifact.archive_bytes.replace(original_raw, forged_raw, 1)
    forged_manifest = artifact.manifest.model_copy(
        update={
            "byte_size": len(forged_archive),
            "content_sha256": hashlib.sha256(forged_archive).hexdigest(),
        }
    )
    forged_artifact = SnapshotArtifact(
        manifest=forged_manifest,
        manifest_bytes=forged_manifest.model_dump_json(exclude_none=True).encode("utf-8"),
        archive_bytes=forged_archive,
    )
    forged_entry = SnapshotRegistryEntry(
        binding=target.binding,
        artifacts=(forged_artifact,),
    )
    forged_entries = tuple(forged_entry if entry is target else entry for entry in original_entries)

    def execute_with_temporary_registry_drift(
        *,
        call: SnapshotAsOfCall,
        registry: SnapshotRegistry,
    ) -> SnapshotAsOfResult:
        try:
            object.__setattr__(registry, "entries", forged_entries)
            changed = dispatcher_module._reference_read_snapshot_as_of(
                call=call,
                registry=registry,
            )
        finally:
            object.__setattr__(registry, "entries", original_entries)
        assert changed.payload is not None
        assert changed.payload.observation.raw_value == "696692.8"
        return changed

    monkeypatch.setattr(
        dispatcher_module,
        "_read_snapshot_as_of",
        execute_with_temporary_registry_drift,
    )
    call = calls[ToolName.READ_SNAPSHOT_AS_OF]
    assert isinstance(call, SnapshotAsOfCall)

    result = dispatch_tool_call(call=call, registry=committed_registry)

    assert snapshot_registry.entries is original_entries
    assert snapshot_registry.descriptor_sha256 == SNAPSHOT_REGISTRY_DESCRIPTOR_SHA256
    assert result.status is ToolOutcomeStatus.ERROR
    assert result.error is not None
    assert result.error.code == "tool_result_invalid"
    assert "696692.8" not in result.model_dump_json()


def test_candidate_post_call_dependency_corruption_is_rejected(
    committed_registry: CallableToolRegistry,
    calls: dict[ToolName, TemporalDocumentCall | StesAsOfCall | SnapshotAsOfCall],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    call = calls[ToolName.READ_SNAPSHOT_AS_OF]
    dependency = committed_registry.snapshot_registry
    original_registry_id = dependency.registry_id

    def corrupt_after_execution(
        *,
        call: SnapshotAsOfCall,
        registry: SnapshotRegistry,
    ) -> SnapshotAsOfResult:
        result = dispatcher_module._reference_read_snapshot_as_of(
            call=call,
            registry=registry,
        )
        object.__setattr__(registry, "registry_id", "poisoned-snapshot-registry")
        return result

    monkeypatch.setattr(
        dispatcher_module,
        "_read_snapshot_as_of",
        corrupt_after_execution,
    )
    try:
        result = dispatch_tool_call(call=call, registry=committed_registry)
    finally:
        object.__setattr__(dependency, "registry_id", original_registry_id)

    assert result.status is ToolOutcomeStatus.ERROR
    assert result.error is not None
    assert result.error.code == "tool_result_invalid"
    assert dependency.registry_id == SNAPSHOT_REGISTRY_ID


def test_candidate_post_call_dependency_replacement_is_rejected(
    committed_registry: CallableToolRegistry,
    calls: dict[ToolName, TemporalDocumentCall | StesAsOfCall | SnapshotAsOfCall],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    call = calls[ToolName.READ_SNAPSHOT_AS_OF]
    original_dependency = committed_registry.snapshot_registry
    replacement = load_committed_callable_tool_registry(REPOSITORY_ROOT).snapshot_registry
    assert replacement is not original_dependency

    def replace_after_execution(
        *,
        call: SnapshotAsOfCall,
        registry: SnapshotRegistry,
    ) -> SnapshotAsOfResult:
        result = dispatcher_module._reference_read_snapshot_as_of(
            call=call,
            registry=registry,
        )
        object.__setattr__(committed_registry, "snapshot_registry", replacement)
        return result

    monkeypatch.setattr(
        dispatcher_module,
        "_read_snapshot_as_of",
        replace_after_execution,
    )
    try:
        result = dispatch_tool_call(call=call, registry=committed_registry)
    finally:
        object.__setattr__(
            committed_registry,
            "snapshot_registry",
            original_dependency,
        )

    assert result.status is ToolOutcomeStatus.ERROR
    assert result.error is not None
    assert result.error.code == "tool_result_invalid"
    assert committed_registry.snapshot_registry is original_dependency


def test_result_comparison_side_effect_cannot_escape_final_dependency_check(
    committed_registry: CallableToolRegistry,
    calls: dict[ToolName, TemporalDocumentCall | StesAsOfCall | SnapshotAsOfCall],
    real_results: dict[ToolName, TemporalDocumentResult | StesAsOfResult | SnapshotAsOfResult],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    tool_name = ToolName.READ_SNAPSHOT_AS_OF
    candidate = _adapter_result(real_results, tool_name)
    assert isinstance(candidate, SnapshotAsOfResult)
    assert candidate.payload is not None
    dependency = committed_registry.snapshot_registry
    original_registry_id = dependency.registry_id

    class RegistryPoisoningStr(str):
        __hash__ = str.__hash__

        def _poison(self) -> None:
            object.__setattr__(dependency, "registry_id", "poisoned-during-result-compare")

        def __eq__(self, other: object) -> bool:
            self._poison()
            return super().__eq__(other)

        def __ne__(self, other: object) -> bool:
            self._poison()
            return super().__ne__(other)

    object.__setattr__(
        candidate.payload.observation,
        "raw_value",
        RegistryPoisoningStr(candidate.payload.observation.raw_value),
    )
    _patch_adapter_result(
        monkeypatch,
        tool_name=tool_name,
        result=candidate,
    )
    try:
        result = dispatch_tool_call(call=calls[tool_name], registry=committed_registry)
    finally:
        object.__setattr__(dependency, "registry_id", original_registry_id)

    assert result.status is ToolOutcomeStatus.ERROR
    assert result.error is not None
    assert result.error.code == "tool_result_invalid"
    assert dependency.registry_id == SNAPSHOT_REGISTRY_ID
