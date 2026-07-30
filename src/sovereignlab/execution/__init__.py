"""Frozen callable registry and deterministic tool dispatcher."""

from sovereignlab.execution.dispatcher import (
    CALLABLE_TOOL_DEFINITIONS,
    CALLABLE_TOOL_REGISTRY_DESCRIPTOR_SHA256,
    CALLABLE_TOOL_REGISTRY_ID,
    EXECUTION_ARTIFACT_REGISTRY_DESCRIPTOR_SHA256,
    EXECUTION_ARTIFACT_REGISTRY_ID,
    CallableRegistryLoadError,
    CallableToolDefinition,
    CallableToolRegistry,
    ToolDispatchError,
    ToolRegistryProvenance,
    dispatch_tool_call,
    load_committed_callable_tool_registry,
)

__all__ = [
    "CALLABLE_TOOL_DEFINITIONS",
    "CALLABLE_TOOL_REGISTRY_DESCRIPTOR_SHA256",
    "CALLABLE_TOOL_REGISTRY_ID",
    "EXECUTION_ARTIFACT_REGISTRY_DESCRIPTOR_SHA256",
    "EXECUTION_ARTIFACT_REGISTRY_ID",
    "CallableRegistryLoadError",
    "CallableToolDefinition",
    "CallableToolRegistry",
    "ToolDispatchError",
    "ToolRegistryProvenance",
    "dispatch_tool_call",
    "load_committed_callable_tool_registry",
]
