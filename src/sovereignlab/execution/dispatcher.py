"""The three-tool callable registry and its dispatcher."""

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

from pydantic import BaseModel

from sovereignlab.artifacts import canonical_sha256
from sovereignlab.retrieval.adapter import execute_temporal_document_call
from sovereignlab.retrieval.registry import (
    TemporalCorpusRegistry,
    load_committed_temporal_corpus_registry,
)
from sovereignlab.schemas import (
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
from sovereignlab.snapshots.reader import read_snapshot_as_of
from sovereignlab.snapshots.registry import SnapshotRegistry, load_committed_snapshot_registry
from sovereignlab.vintage.adapter import execute_stes_as_of_call
from sovereignlab.vintage.registry import StesRegistry, load_committed_stes_registry

CALLABLE_TOOL_REGISTRY_ID = "sovereignlab-deterministic-tool-registry-v1"
EXECUTION_ARTIFACT_REGISTRY_ID = "kor-rtd-execution-artifact-registry-v1"


def _schema_sha256(model: type[BaseModel]) -> str:
    canonical = json.dumps(
        model.model_json_schema(),
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class CallableToolDefinition:
    """Model-visible metadata for one deterministic tool."""

    tool_name: ToolName
    adapter_id: str
    arguments_model: type[BaseModel]
    call_model: type[BaseModel]
    result_model: type[BaseModel]
    dependency_role: str

    def descriptor(self) -> dict[str, str]:
        """Return the tool's registry-digest material."""

        return {
            "adapter_id": self.adapter_id,
            "arguments_model_id": f"{self.arguments_model.__name__}@1.0.0",
            "arguments_schema_sha256": _schema_sha256(self.arguments_model),
            "call_model_id": f"{self.call_model.__name__}@1.0.0",
            "dependency_role": self.dependency_role,
            "result_model_id": f"{self.result_model.__name__}@1.0.0",
            "tool_name": self.tool_name.value,
        }


CALLABLE_TOOL_DEFINITIONS = (
    CallableToolDefinition(
        tool_name=ToolName.RETRIEVE_TEMPORAL_DOCUMENTS,
        adapter_id="sovereignlab-temporal-document-adapter-v1",
        arguments_model=TemporalDocumentArguments,
        call_model=TemporalDocumentCall,
        result_model=TemporalDocumentResult,
        dependency_role="retrieval_corpus",
    ),
    CallableToolDefinition(
        tool_name=ToolName.RESOLVE_STES_AS_OF,
        adapter_id="sovereignlab-stes-as-of-adapter-v1",
        arguments_model=StesAsOfArguments,
        call_model=StesAsOfCall,
        result_model=StesAsOfResult,
        dependency_role="historical_stes",
    ),
    CallableToolDefinition(
        tool_name=ToolName.READ_SNAPSHOT_AS_OF,
        adapter_id="sovereignlab-snapshot-as-of-adapter-v1",
        arguments_model=SnapshotAsOfArguments,
        call_model=SnapshotAsOfCall,
        result_model=SnapshotAsOfResult,
        dependency_role="latest_only_snapshots",
    ),
)
_RESULT_MODELS = {
    definition.call_model: definition.result_model for definition in CALLABLE_TOOL_DEFINITIONS
}


def tool_registry_sha256() -> str:
    """Hash the model-visible tool surface: names, adapters, and argument schemas."""

    return canonical_sha256(
        {
            "execution_contract_version": "1.0.0",
            "registry_id": CALLABLE_TOOL_REGISTRY_ID,
            "schema_version": "1.0.0",
            "tools": sorted(
                (definition.descriptor() for definition in CALLABLE_TOOL_DEFINITIONS),
                key=lambda item: item["tool_name"],
            ),
        }
    )


@dataclass(frozen=True)
class ToolRegistryProvenance:
    """Registry identifiers and digests recorded in every execution trace."""

    tool_registry_id: str
    tool_registry_sha256: str
    artifact_registry_id: str
    artifact_registry_sha256: str
    retrieval_corpus_id: str
    retrieval_corpus_sha256: str


@dataclass(frozen=True)
class CallableToolRegistry:
    """The evidence registries behind the three offline tools."""

    snapshot_registry: SnapshotRegistry
    temporal_corpus_registry: TemporalCorpusRegistry
    stes_registry: StesRegistry

    def argument_schema(self, tool_name: ToolName) -> dict[str, object]:
        """Return the provider-facing JSON Schema for one tool's arguments."""

        for definition in CALLABLE_TOOL_DEFINITIONS:
            if definition.tool_name is tool_name:
                return definition.arguments_model.model_json_schema()
        raise KeyError(f"unknown tool {tool_name!r}")

    def provenance(self) -> ToolRegistryProvenance:
        """Return the identifiers and digests that pin this registry's inputs."""

        return ToolRegistryProvenance(
            tool_registry_id=CALLABLE_TOOL_REGISTRY_ID,
            tool_registry_sha256=tool_registry_sha256(),
            artifact_registry_id=EXECUTION_ARTIFACT_REGISTRY_ID,
            artifact_registry_sha256=canonical_sha256(
                {
                    "registries": [
                        {
                            "registry_id": self.stes_registry.registry_id,
                            "role": "historical_stes",
                            "sha256": self.stes_registry.descriptor_sha256,
                        },
                        {
                            "registry_id": self.snapshot_registry.registry_id,
                            "role": "latest_only_snapshots",
                            "sha256": self.snapshot_registry.descriptor_sha256,
                        },
                    ],
                    "registry_id": EXECUTION_ARTIFACT_REGISTRY_ID,
                    "schema_version": "1.0.0",
                }
            ),
            retrieval_corpus_id=self.temporal_corpus_registry.corpus_id,
            retrieval_corpus_sha256=self.temporal_corpus_registry.descriptor_sha256,
        )


def load_committed_callable_tool_registry(repository_root: Path) -> CallableToolRegistry:
    """Load the three committed v1 evidence registries."""

    return CallableToolRegistry(
        snapshot_registry=load_committed_snapshot_registry(repository_root),
        temporal_corpus_registry=load_committed_temporal_corpus_registry(repository_root),
        stes_registry=load_committed_stes_registry(repository_root),
    )


def dispatch_tool_call(*, call: ToolCall, registry: CallableToolRegistry) -> ToolResult:
    """Run one typed call against its tool; an unexpected failure becomes an error result."""

    try:
        if isinstance(call, TemporalDocumentCall):
            return execute_temporal_document_call(
                call=call,
                registry=registry.temporal_corpus_registry,
            )
        if isinstance(call, StesAsOfCall):
            return execute_stes_as_of_call(call=call, registry=registry.stes_registry)
        if isinstance(call, SnapshotAsOfCall):
            return read_snapshot_as_of(call=call, registry=registry.snapshot_registry)
    except Exception:
        return _RESULT_MODELS[type(call)](
            call_id=call.call_id,
            tool_name=call.tool_name,
            status=ToolOutcomeStatus.ERROR,
            error=ExecutionFailure(
                phase=FailurePhase.TOOL_EXECUTION,
                code="tool_dispatch_failed",
                message="The deterministic tool adapter failed unexpectedly.",
                call_id=call.call_id,
            ),
        )
    raise TypeError(f"unsupported tool call type: {type(call).__name__}")
