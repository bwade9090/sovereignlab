"""Frozen three-tool registry and explicit deterministic dispatcher."""

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

from pydantic import BaseModel

from sovereignlab.retrieval.adapter import (
    execute_temporal_document_call as _reference_execute_temporal_document_call,
)
from sovereignlab.retrieval.registry import (
    TEMPORAL_CORPUS_DESCRIPTOR_SHA256,
    TEMPORAL_CORPUS_ID,
    TemporalCorpusRegistry,
    load_committed_temporal_corpus_registry,
)
from sovereignlab.schemas import (
    DocumentRetrievalPayload,
    ExecutionFailure,
    FailurePhase,
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
from sovereignlab.snapshots.reader import read_snapshot_as_of as _reference_read_snapshot_as_of
from sovereignlab.snapshots.registry import (
    SNAPSHOT_REGISTRY_DESCRIPTOR_SHA256,
    SNAPSHOT_REGISTRY_ID,
    SnapshotRegistry,
    load_committed_snapshot_registry,
)
from sovereignlab.vintage.adapter import (
    execute_stes_as_of_call as _reference_execute_stes_as_of_call,
)
from sovereignlab.vintage.registry import (
    STES_REGISTRY_DESCRIPTOR_SHA256,
    STES_REGISTRY_ID,
    StesRegistry,
    load_committed_stes_registry,
)

CALLABLE_TOOL_REGISTRY_ID = "sovereignlab-deterministic-tool-registry-v1"
CALLABLE_TOOL_REGISTRY_DESCRIPTOR_SHA256 = (
    "cd00b5c543cffc53024f98b9fafa73ed3fecd519fde81a826d060c8af4d2ad91"
)
EXECUTION_ARTIFACT_REGISTRY_ID = "kor-rtd-execution-artifact-registry-v1"
EXECUTION_ARTIFACT_REGISTRY_DESCRIPTOR_SHA256 = (
    "7b42027c1034789bd46a881fd186f66ba1ba1250d94639ff5eed6c89a3cc2293"
)

_execute_temporal_document_call = _reference_execute_temporal_document_call
_execute_stes_as_of_call = _reference_execute_stes_as_of_call
_read_snapshot_as_of = _reference_read_snapshot_as_of


class CallableRegistryLoadError(ValueError):
    """Sanitized harness failure while loading the frozen callable registry."""


class ToolDispatchError(ValueError):
    """Sanitized pre-execution rejection that has no valid typed result variant."""

    def __init__(self, code: str, message: str) -> None:
        self.code = code
        super().__init__(message)


@dataclass(frozen=True)
class CallableToolDefinition:
    """Stable model-visible metadata for one deterministic callable."""

    tool_name: ToolName
    adapter_id: str
    arguments_model_id: str
    call_model_id: str
    result_model_id: str
    dependency_role: str
    arguments_schema_sha256: str

    def descriptor(self) -> dict[str, str]:
        """Return canonical callable-registry digest material."""

        return {
            "adapter_id": self.adapter_id,
            "arguments_model_id": self.arguments_model_id,
            "arguments_schema_sha256": self.arguments_schema_sha256,
            "call_model_id": self.call_model_id,
            "dependency_role": self.dependency_role,
            "result_model_id": self.result_model_id,
            "tool_name": self.tool_name.value,
        }


@dataclass(frozen=True)
class _ToolBinding:
    definition: CallableToolDefinition
    arguments_model: type[BaseModel]
    call_model: type[BaseModel]
    result_model: type[BaseModel]


def _canonical_schema_bytes(model: type[BaseModel]) -> bytes:
    return json.dumps(
        model.model_json_schema(),
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def _schema_sha256(model: type[BaseModel]) -> str:
    return hashlib.sha256(_canonical_schema_bytes(model)).hexdigest()


_TOOL_BINDINGS = (
    _ToolBinding(
        definition=CallableToolDefinition(
            tool_name=ToolName.RETRIEVE_TEMPORAL_DOCUMENTS,
            adapter_id="sovereignlab-temporal-document-adapter-v1",
            arguments_model_id="TemporalDocumentArguments@1.0.0",
            call_model_id="TemporalDocumentCall@1.0.0",
            result_model_id="TemporalDocumentResult@1.0.0",
            dependency_role="retrieval_corpus",
            arguments_schema_sha256=_schema_sha256(TemporalDocumentArguments),
        ),
        arguments_model=TemporalDocumentArguments,
        call_model=TemporalDocumentCall,
        result_model=TemporalDocumentResult,
    ),
    _ToolBinding(
        definition=CallableToolDefinition(
            tool_name=ToolName.RESOLVE_STES_AS_OF,
            adapter_id="sovereignlab-stes-as-of-adapter-v1",
            arguments_model_id="StesAsOfArguments@1.0.0",
            call_model_id="StesAsOfCall@1.0.0",
            result_model_id="StesAsOfResult@1.0.0",
            dependency_role="historical_stes",
            arguments_schema_sha256=_schema_sha256(StesAsOfArguments),
        ),
        arguments_model=StesAsOfArguments,
        call_model=StesAsOfCall,
        result_model=StesAsOfResult,
    ),
    _ToolBinding(
        definition=CallableToolDefinition(
            tool_name=ToolName.READ_SNAPSHOT_AS_OF,
            adapter_id="sovereignlab-snapshot-as-of-adapter-v1",
            arguments_model_id="SnapshotAsOfArguments@1.0.0",
            call_model_id="SnapshotAsOfCall@1.0.0",
            result_model_id="SnapshotAsOfResult@1.0.0",
            dependency_role="latest_only_snapshots",
            arguments_schema_sha256=_schema_sha256(SnapshotAsOfArguments),
        ),
        arguments_model=SnapshotAsOfArguments,
        call_model=SnapshotAsOfCall,
        result_model=SnapshotAsOfResult,
    ),
)
CALLABLE_TOOL_DEFINITIONS = tuple(binding.definition for binding in _TOOL_BINDINGS)
_BINDINGS_BY_NAME = {binding.definition.tool_name: binding for binding in _TOOL_BINDINGS}
_BINDINGS_BY_CALL_TYPE = {binding.call_model: binding for binding in _TOOL_BINDINGS}


@dataclass(frozen=True)
class ToolRegistryProvenance:
    """Real registry identifiers and digests needed by later trace assembly."""

    tool_registry_id: str
    tool_registry_sha256: str
    artifact_registry_id: str
    artifact_registry_sha256: str
    retrieval_corpus_id: str
    retrieval_corpus_sha256: str


@dataclass(frozen=True)
class CallableToolRegistry:
    """Harness-owned committed dependencies for exactly three offline tools."""

    snapshot_registry: SnapshotRegistry
    temporal_corpus_registry: TemporalCorpusRegistry
    stes_registry: StesRegistry
    registry_id: str = CALLABLE_TOOL_REGISTRY_ID

    def __post_init__(self) -> None:
        try:
            self._validate_identity()
            snapshot_sha256, _, stes_sha256 = self._validate_all_dependencies()
            _ = self.descriptor_sha256
            artifact_sha256 = hashlib.sha256(
                _canonical_artifact_descriptor_bytes(
                    snapshot_registry_id=self.snapshot_registry.registry_id,
                    snapshot_registry_sha256=snapshot_sha256,
                    stes_registry_id=self.stes_registry.registry_id,
                    stes_registry_sha256=stes_sha256,
                )
            ).hexdigest()
            if artifact_sha256 != EXECUTION_ARTIFACT_REGISTRY_DESCRIPTOR_SHA256:
                raise ValueError("execution artifact registry descriptor drift")
        except Exception:
            raise CallableRegistryLoadError(
                "the frozen callable tool registry is invalid"
            ) from None

    @property
    def tool_names(self) -> tuple[ToolName, ...]:
        """Return the exact registered names in the frozen contract order."""

        self._validate_identity()
        self._validate_frozen_descriptor()
        return tuple(binding.definition.tool_name for binding in _TOOL_BINDINGS)

    def argument_schema(self, tool_name: ToolName) -> dict[str, object]:
        """Return a fresh provider-facing argument schema for one registered tool."""

        self._validate_identity()
        self._validate_frozen_descriptor()
        if type(tool_name) is not ToolName:
            raise ToolDispatchError("unknown_tool", "The requested tool is not registered.")
        binding = _BINDINGS_BY_NAME[tool_name]
        schema = binding.arguments_model.model_json_schema()
        digest = hashlib.sha256(
            json.dumps(
                schema,
                ensure_ascii=False,
                separators=(",", ":"),
                sort_keys=True,
            ).encode("utf-8")
        ).hexdigest()
        if digest != binding.definition.arguments_schema_sha256:
            raise ValueError("callable registry argument schema drift")
        return schema

    def canonical_descriptor_bytes(self) -> bytes:
        """Serialize the callable surface without code objects or trusted data."""

        self._validate_identity()
        descriptor = _canonical_callable_descriptor_bytes()
        if hashlib.sha256(descriptor).hexdigest() != CALLABLE_TOOL_REGISTRY_DESCRIPTOR_SHA256:
            raise ValueError("callable registry descriptor drift")
        return descriptor

    @property
    def descriptor_sha256(self) -> str:
        """Hash the canonical callable descriptor."""

        return hashlib.sha256(self.canonical_descriptor_bytes()).hexdigest()

    def canonical_artifact_descriptor_bytes(self) -> bytes:
        """Serialize the two deterministic data registries as one trace input."""

        snapshot_sha256 = _validated_snapshot_registry(self.snapshot_registry)
        stes_sha256 = _validated_stes_registry(self.stes_registry)
        return _canonical_artifact_descriptor_bytes(
            snapshot_registry_id=self.snapshot_registry.registry_id,
            snapshot_registry_sha256=snapshot_sha256,
            stes_registry_id=self.stes_registry.registry_id,
            stes_registry_sha256=stes_sha256,
        )

    @property
    def artifact_registry_sha256(self) -> str:
        """Hash the canonical composite snapshot/STES artifact descriptor."""

        return hashlib.sha256(self.canonical_artifact_descriptor_bytes()).hexdigest()

    @property
    def retrieval_corpus_id(self) -> str:
        """Return the independently traceable retrieval-corpus ID."""

        _validated_temporal_registry(self.temporal_corpus_registry)
        return self.temporal_corpus_registry.corpus_id

    @property
    def retrieval_corpus_sha256(self) -> str:
        """Return the independently traceable retrieval-corpus digest."""

        return _validated_temporal_registry(self.temporal_corpus_registry)

    def provenance(self) -> ToolRegistryProvenance:
        """Return the six real registry fields used by execution provenance."""

        self._validate_identity()
        self._validate_frozen_descriptor()
        snapshot_sha256, corpus_sha256, stes_sha256 = self._validate_all_dependencies()
        artifact_sha256 = hashlib.sha256(
            _canonical_artifact_descriptor_bytes(
                snapshot_registry_id=self.snapshot_registry.registry_id,
                snapshot_registry_sha256=snapshot_sha256,
                stes_registry_id=self.stes_registry.registry_id,
                stes_registry_sha256=stes_sha256,
            )
        ).hexdigest()
        if artifact_sha256 != EXECUTION_ARTIFACT_REGISTRY_DESCRIPTOR_SHA256:
            raise CallableRegistryLoadError("the frozen callable tool registry is invalid")
        return ToolRegistryProvenance(
            tool_registry_id=self.registry_id,
            tool_registry_sha256=self.descriptor_sha256,
            artifact_registry_id=EXECUTION_ARTIFACT_REGISTRY_ID,
            artifact_registry_sha256=artifact_sha256,
            retrieval_corpus_id=self.temporal_corpus_registry.corpus_id,
            retrieval_corpus_sha256=corpus_sha256,
        )

    def _validate_identity(self) -> None:
        if (
            type(self) is not CallableToolRegistry
            or type(self.registry_id) is not str
            or self.registry_id != CALLABLE_TOOL_REGISTRY_ID
        ):
            raise ValueError("callable registry identity differs from its frozen contract")
        _validate_frozen_bindings()
        if (
            type(self.snapshot_registry) is not SnapshotRegistry
            or self.snapshot_registry.registry_id != SNAPSHOT_REGISTRY_ID
            or type(self.temporal_corpus_registry) is not TemporalCorpusRegistry
            or self.temporal_corpus_registry.corpus_id != TEMPORAL_CORPUS_ID
            or type(self.stes_registry) is not StesRegistry
            or self.stes_registry.registry_id != STES_REGISTRY_ID
        ):
            raise ValueError("callable registry dependencies differ from the frozen surface")

    def _validate_frozen_descriptor(self) -> None:
        digest = hashlib.sha256(_canonical_callable_descriptor_bytes()).hexdigest()
        if digest != CALLABLE_TOOL_REGISTRY_DESCRIPTOR_SHA256:
            raise ValueError("callable registry descriptor drift")

    def _validate_all_dependencies(self) -> tuple[str, str, str]:
        snapshot_sha256 = _validated_snapshot_registry(self.snapshot_registry)
        corpus_sha256 = _validated_temporal_registry(self.temporal_corpus_registry)
        stes_sha256 = _validated_stes_registry(self.stes_registry)
        return snapshot_sha256, corpus_sha256, stes_sha256


def _canonical_callable_descriptor_bytes() -> bytes:
    descriptor = {
        "execution_contract_version": "1.0.0",
        "registry_id": CALLABLE_TOOL_REGISTRY_ID,
        "schema_version": "1.0.0",
        "tools": sorted(
            (definition.descriptor() for definition in CALLABLE_TOOL_DEFINITIONS),
            key=lambda item: item["tool_name"],
        ),
    }
    return json.dumps(
        descriptor,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def _validate_frozen_bindings() -> None:
    expected_shapes = (
        (
            ToolName.RETRIEVE_TEMPORAL_DOCUMENTS,
            TemporalDocumentArguments,
            TemporalDocumentCall,
            TemporalDocumentResult,
        ),
        (
            ToolName.RESOLVE_STES_AS_OF,
            StesAsOfArguments,
            StesAsOfCall,
            StesAsOfResult,
        ),
        (
            ToolName.READ_SNAPSHOT_AS_OF,
            SnapshotAsOfArguments,
            SnapshotAsOfCall,
            SnapshotAsOfResult,
        ),
    )
    invalid = (
        type(_TOOL_BINDINGS) is not tuple
        or len(_TOOL_BINDINGS) != 3
        or any(type(binding) is not _ToolBinding for binding in _TOOL_BINDINGS)
        or type(CALLABLE_TOOL_DEFINITIONS) is not tuple
        or len(CALLABLE_TOOL_DEFINITIONS) != 3
        or type(_BINDINGS_BY_NAME) is not dict
        or type(_BINDINGS_BY_CALL_TYPE) is not dict
        or len(_BINDINGS_BY_NAME) != 3
        or len(_BINDINGS_BY_CALL_TYPE) != 3
        or set(_BINDINGS_BY_NAME) != set(ToolName)
        or tuple(
            (
                binding.definition.tool_name,
                binding.arguments_model,
                binding.call_model,
                binding.result_model,
            )
            for binding in _TOOL_BINDINGS
        )
        != expected_shapes
        or any(
            CALLABLE_TOOL_DEFINITIONS[index] is not binding.definition
            or _BINDINGS_BY_NAME.get(binding.definition.tool_name) is not binding
            or _BINDINGS_BY_CALL_TYPE.get(binding.call_model) is not binding
            for index, binding in enumerate(_TOOL_BINDINGS)
        )
    )
    if not invalid:
        try:
            invalid = any(
                binding.definition.arguments_schema_sha256
                != _schema_sha256(binding.arguments_model)
                for binding in _TOOL_BINDINGS
            )
        except Exception:
            invalid = True
    if invalid:
        raise ValueError("callable registry definitions differ from the frozen surface")


def _canonical_artifact_descriptor_bytes(
    *,
    snapshot_registry_id: str,
    snapshot_registry_sha256: str,
    stes_registry_id: str,
    stes_registry_sha256: str,
) -> bytes:
    descriptor = {
        "registries": sorted(
            (
                {
                    "registry_id": snapshot_registry_id,
                    "role": "latest_only_snapshots",
                    "sha256": snapshot_registry_sha256,
                },
                {
                    "registry_id": stes_registry_id,
                    "role": "historical_stes",
                    "sha256": stes_registry_sha256,
                },
            ),
            key=lambda item: item["role"],
        ),
        "registry_id": EXECUTION_ARTIFACT_REGISTRY_ID,
        "schema_version": "1.0.0",
    }
    return json.dumps(
        descriptor,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def _validated_snapshot_registry(registry: object) -> str:
    if type(registry) is not SnapshotRegistry or registry.registry_id != SNAPSHOT_REGISTRY_ID:
        raise ValueError("snapshot registry identity differs from the committed registry")
    digest = registry.descriptor_sha256
    if digest != SNAPSHOT_REGISTRY_DESCRIPTOR_SHA256:
        raise ValueError("snapshot registry descriptor differs from the committed registry")
    return digest


def _validated_temporal_registry(registry: object) -> str:
    if type(registry) is not TemporalCorpusRegistry or registry.corpus_id != TEMPORAL_CORPUS_ID:
        raise ValueError("temporal corpus identity differs from the committed registry")
    digest = registry.descriptor_sha256
    if digest != TEMPORAL_CORPUS_DESCRIPTOR_SHA256:
        raise ValueError("temporal corpus descriptor differs from the committed registry")
    return digest


def _validated_stes_registry(registry: object) -> str:
    if type(registry) is not StesRegistry or registry.registry_id != STES_REGISTRY_ID:
        raise ValueError("STES registry identity differs from the committed registry")
    digest = registry.descriptor_sha256
    if digest != STES_REGISTRY_DESCRIPTOR_SHA256:
        raise ValueError("STES registry descriptor differs from the committed registry")
    return digest


def load_committed_callable_tool_registry(repository_root: Path) -> CallableToolRegistry:
    """Load the exact three committed deterministic dependencies."""

    try:
        return CallableToolRegistry(
            snapshot_registry=load_committed_snapshot_registry(repository_root),
            temporal_corpus_registry=load_committed_temporal_corpus_registry(repository_root),
            stes_registry=load_committed_stes_registry(repository_root),
        )
    except Exception:
        raise CallableRegistryLoadError(
            "the committed callable tool registry could not be loaded"
        ) from None


def dispatch_tool_call(
    *,
    call: ToolCall,
    registry: CallableToolRegistry,
) -> ToolResult:
    """Dispatch one exact typed call to its explicit trusted offline adapter."""

    binding, reference_call, adapter_call = _validated_call_copies(call)
    try:
        dependency = _validated_dependency(registry, binding.definition.tool_name)
    except Exception:
        raise ToolDispatchError(
            "tool_registry_misconfigured",
            "The frozen callable tool registry is misconfigured.",
        ) from None

    try:
        trusted_result = _trusted_replay(reference_call, dependency)
    except Exception:
        return _dispatch_error(
            reference_call,
            code="tool_dispatch_failed",
            message="The deterministic tool adapter failed unexpectedly.",
        )

    try:
        if type(adapter_call) is TemporalDocumentCall:
            result = _execute_temporal_document_call(
                call=adapter_call,
                registry=dependency,
            )
        elif type(adapter_call) is StesAsOfCall:
            result = _execute_stes_as_of_call(
                call=adapter_call,
                registry=dependency,
            )
        else:
            assert type(adapter_call) is SnapshotAsOfCall
            result = _read_snapshot_as_of(
                call=adapter_call,
                registry=dependency,
            )
    except Exception:
        return _dispatch_error(
            reference_call,
            code="tool_dispatch_failed",
            message="The deterministic tool adapter failed unexpectedly.",
        )

    try:
        _validate_selected_dependency_unchanged(
            registry,
            binding.definition.tool_name,
            dependency,
        )
        _validate_adapter_call_unchanged(binding, reference_call, adapter_call)
        validated = _validated_result(binding, reference_call, result)
    except Exception:
        return _dispatch_error(
            reference_call,
            code="tool_result_invalid",
            message="The deterministic tool adapter returned an invalid result.",
        )

    try:
        trusted = _validated_result(binding, reference_call, trusted_result)
        if validated != trusted:
            raise ValueError("tool result differs from trusted replay")
        _validate_selected_dependency_unchanged(
            registry,
            binding.definition.tool_name,
            dependency,
        )
        return validated
    except Exception:
        return _dispatch_error(
            reference_call,
            code="tool_result_invalid",
            message="The deterministic tool adapter returned an invalid result.",
        )


def _validated_call_copies(
    call: object,
) -> tuple[_ToolBinding, ToolCall, ToolCall]:
    try:
        _validate_frozen_bindings()
    except Exception:
        raise ToolDispatchError(
            "tool_registry_misconfigured",
            "The frozen callable tool registry is misconfigured.",
        ) from None
    binding = _BINDINGS_BY_CALL_TYPE.get(type(call))
    if binding is None:
        if isinstance(call, tuple(_BINDINGS_BY_CALL_TYPE)):
            code = "tool_call_type_mismatch"
            message = "The tool call type is not an exact registered model."
        else:
            raw_name = call.get("tool_name") if type(call) is dict else None
            if type(raw_name) is str and raw_name in {name.value for name in ToolName}:
                code = "tool_call_type_mismatch"
                message = "The tool call must be a validated registered model."
            else:
                code = "unknown_tool"
                message = "The requested tool is not registered."
        raise ToolDispatchError(code, message)

    try:
        tool_name = call.tool_name
        if tool_name is not binding.definition.tool_name:
            known = type(tool_name) is ToolName and tool_name in set(ToolName)
            raise ToolDispatchError(
                "tool_call_type_mismatch" if known else "unknown_tool",
                (
                    "The tool call type does not match its registered name."
                    if known
                    else "The requested tool is not registered."
                ),
            )
        payload = call.model_dump(mode="python", warnings="error")
        reference_call = binding.call_model.model_validate(payload)
        adapter_call = binding.call_model.model_validate(payload)
        if (
            type(reference_call) is not binding.call_model
            or type(adapter_call) is not binding.call_model
            or reference_call != call
            or adapter_call != reference_call
        ):
            raise ValueError("tool call round trip changed")
    except ToolDispatchError:
        raise
    except Exception:
        raise ToolDispatchError(
            "invalid_tool_call",
            "The registered tool call is invalid.",
        ) from None
    return binding, reference_call, adapter_call


def _trusted_replay(
    call: ToolCall,
    dependency: TemporalCorpusRegistry | StesRegistry | SnapshotRegistry,
) -> ToolResult:
    payload = call.model_dump(mode="python", warnings="error")
    if type(call) is TemporalDocumentCall:
        trusted_call = TemporalDocumentCall.model_validate(payload)
        return _reference_execute_temporal_document_call(
            call=trusted_call,
            registry=dependency,
        )
    if type(call) is StesAsOfCall:
        trusted_call = StesAsOfCall.model_validate(payload)
        return _reference_execute_stes_as_of_call(
            call=trusted_call,
            registry=dependency,
        )
    assert type(call) is SnapshotAsOfCall
    trusted_call = SnapshotAsOfCall.model_validate(payload)
    return _reference_read_snapshot_as_of(
        call=trusted_call,
        registry=dependency,
    )


def _validate_adapter_call_unchanged(
    binding: _ToolBinding,
    reference_call: ToolCall,
    adapter_call: ToolCall,
) -> None:
    if type(adapter_call) is not binding.call_model:
        raise ValueError("adapter call has the wrong registered model")
    payload = adapter_call.model_dump(mode="python", warnings="error")
    rebuilt = binding.call_model.model_validate(payload)
    if (
        type(rebuilt) is not binding.call_model
        or rebuilt != adapter_call
        or rebuilt != reference_call
    ):
        raise ValueError("adapter changed its private call")


def _validated_dependency(
    registry: object,
    tool_name: ToolName,
) -> TemporalCorpusRegistry | StesRegistry | SnapshotRegistry:
    if type(registry) is not CallableToolRegistry:
        raise ValueError("callable registry has an invalid type")
    registry._validate_identity()
    _ = registry.descriptor_sha256
    if tool_name is ToolName.RETRIEVE_TEMPORAL_DOCUMENTS:
        _validated_temporal_registry(registry.temporal_corpus_registry)
        return registry.temporal_corpus_registry
    if tool_name is ToolName.RESOLVE_STES_AS_OF:
        _validated_stes_registry(registry.stes_registry)
        return registry.stes_registry
    if tool_name is ToolName.READ_SNAPSHOT_AS_OF:
        _validated_snapshot_registry(registry.snapshot_registry)
        return registry.snapshot_registry
    raise ValueError("tool has no registered dependency")


def _validate_selected_dependency_unchanged(
    registry: CallableToolRegistry,
    tool_name: ToolName,
    dependency: TemporalCorpusRegistry | StesRegistry | SnapshotRegistry,
) -> None:
    if _validated_dependency(registry, tool_name) is not dependency:
        raise ValueError("adapter replaced its selected dependency")


def _validated_result(
    binding: _ToolBinding,
    call: ToolCall,
    result: object,
) -> ToolResult:
    if type(result) is not binding.result_model:
        raise ValueError("tool result has the wrong registered model")
    payload = result.model_dump(mode="python", warnings="error")
    rebuilt = binding.result_model.model_validate(payload)
    if type(rebuilt) is not binding.result_model or rebuilt != result:
        raise ValueError("tool result round trip changed")
    if rebuilt.call_id != call.call_id or rebuilt.tool_name is not call.tool_name:
        raise ValueError("tool result identity differs from its call")
    if rebuilt.status is ToolOutcomeStatus.SUCCESS:
        _validate_success_result(call, rebuilt)
    return rebuilt


def _validate_success_result(call: ToolCall, result: ToolResult) -> None:
    if type(call) is TemporalDocumentCall:
        if type(result) is not TemporalDocumentResult or not isinstance(
            result.payload,
            DocumentRetrievalPayload,
        ):
            raise ValueError("temporal result payload has the wrong type")
        matches = result.payload.matches
        if len(matches) > call.arguments.top_k:
            raise ValueError("temporal result exceeds top_k")
        chunk_ids = tuple(match.chunk_id for match in matches)
        if len(chunk_ids) != len(set(chunk_ids)):
            raise ValueError("temporal result repeats a chunk")
        expected_order = tuple(
            sorted(matches, key=lambda match: (-match.score, match.source_id, match.chunk_id))
        )
        if matches != expected_order or any(
            match.language is not call.arguments.language
            or match.published_on > call.arguments.as_of
            for match in matches
        ):
            raise ValueError("temporal result differs from its call")
        return

    if type(call) is StesAsOfCall:
        if type(result) is not StesAsOfResult or result.payload is None:
            raise ValueError("STES result payload has the wrong type")
        evidence = result.payload
        arguments = call.arguments
        if (
            evidence.as_of,
            evidence.ref_area,
            evidence.freq,
            evidence.measure,
            evidence.unit_measure,
            evidence.activity,
            evidence.period,
            evidence.observation.normalization_rule_id,
        ) != (
            arguments.as_of,
            arguments.ref_area,
            arguments.freq,
            arguments.measure,
            arguments.unit_measure,
            arguments.activity,
            arguments.period,
            arguments.normalization_rule_id,
        ):
            raise ValueError("STES result differs from its call")
        return

    if (
        type(call) is not SnapshotAsOfCall
        or type(result) is not SnapshotAsOfResult
        or result.payload is None
    ):
        raise ValueError("snapshot result payload has the wrong type")
    evidence = result.payload
    arguments = call.arguments
    if (
        evidence.source_system,
        evidence.table_id,
        evidence.item_id,
        evidence.period,
        evidence.as_of,
        evidence.observation.normalization_rule_id,
    ) != (
        arguments.source_system,
        arguments.table_id,
        arguments.item_id,
        arguments.period,
        arguments.as_of,
        arguments.normalization_rule_id,
    ):
        raise ValueError("snapshot result differs from its call")


def _dispatch_error(
    call: ToolCall,
    *,
    code: str,
    message: str,
) -> ToolResult:
    error = ExecutionFailure(
        phase=FailurePhase.TOOL_EXECUTION,
        code=code,
        message=message,
        call_id=call.call_id,
    )
    if type(call) is TemporalDocumentCall:
        return TemporalDocumentResult(
            call_id=call.call_id,
            tool_name=ToolName.RETRIEVE_TEMPORAL_DOCUMENTS,
            status=ToolOutcomeStatus.ERROR,
            error=error,
        )
    if type(call) is StesAsOfCall:
        return StesAsOfResult(
            call_id=call.call_id,
            tool_name=ToolName.RESOLVE_STES_AS_OF,
            status=ToolOutcomeStatus.ERROR,
            error=error,
        )
    assert type(call) is SnapshotAsOfCall
    return SnapshotAsOfResult(
        call_id=call.call_id,
        tool_name=ToolName.READ_SNAPSHOT_AS_OF,
        status=ToolOutcomeStatus.ERROR,
        error=error,
    )
