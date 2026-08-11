"""Private offline coordination of one validated request into an execution trace."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timedelta
from pathlib import Path

from pydantic import TypeAdapter

from sovereignlab.execution.assembler import (
    _assemble_evidence_packet,
    _PacketAssemblyError,
)
from sovereignlab.execution.dispatcher import (
    CALLABLE_TOOL_REGISTRY_DESCRIPTOR_SHA256,
    CALLABLE_TOOL_REGISTRY_ID,
    CallableToolRegistry,
    ToolDispatchError,
    ToolRegistryProvenance,
    dispatch_tool_call,
)
from sovereignlab.execution.planner import Planner, PlannerError
from sovereignlab.schemas import (
    ExecutionEnvironmentProvenance,
    ExecutionEvidencePacket,
    ExecutionFailure,
    ExecutionRequest,
    ExecutionTrace,
    FailurePhase,
    PacketStatus,
    PlannerProvenance,
    RoutePlan,
    SnapshotAsOfCall,
    SnapshotAsOfResult,
    StesAsOfCall,
    StesAsOfResult,
    TemporalDocumentCall,
    TemporalDocumentResult,
    ToolName,
    ToolOutcomeStatus,
    ToolResult,
    TraceStatus,
)
from sovereignlab.schemas.common import Identifier
from sovereignlab.schemas.execution import _validate_result_against_call

_OFFLINE_EXECUTOR_ID = "sovereignlab-offline-executor-v1"
_SOURCE_ROOT = Path(__file__).resolve().parents[1]
_IDENTIFIER_ADAPTER = TypeAdapter(Identifier)
_RESULT_MODELS = (
    TemporalDocumentResult,
    StesAsOfResult,
    SnapshotAsOfResult,
)
_PLANNER_FAILURE_MESSAGES = {
    "invalid_request": "The planner rejected the execution request safely.",
    "planner_misconfigured": "The offline planner is misconfigured.",
    "recording_registry_invalid": "The immutable planner recording registry is unavailable.",
    "recording_missing": "The requested immutable planner recording is unavailable.",
    "recording_integrity_failed": "The immutable planner recording failed its integrity check.",
    "plan_validation_failed": (
        "The planner candidate did not validate against the execution request."
    ),
}
_DISPATCH_FAILURE_MESSAGES = {
    "unknown_tool": "The requested tool is not registered.",
    "tool_call_type_mismatch": "The tool call does not match its registered model.",
    "invalid_tool_call": "The registered tool call is invalid.",
    "tool_registry_misconfigured": "The frozen callable tool registry is misconfigured.",
}
_PACKET_FAILURE_CODES = frozenset(
    {
        "invalid_request",
        "invalid_plan",
        "invalid_tool_result",
        "invalid_result_sequence",
        "request_plan_drift",
        "incomplete_result_sequence",
        "tool_error_not_evidence",
        "packet_validation_failed",
        "packet_assembly_failed",
    }
)


class _OfflineExecutorError(ValueError):
    """Sanitized private rejection when no valid execution trace can be returned."""

    def __init__(self, code: str, message: str) -> None:
        self.code = code
        super().__init__(message)


def _sanitized_planner_failure(error: PlannerError) -> tuple[str, str]:
    code = error.code if type(error.code) is str else "planner_failed"
    message = _PLANNER_FAILURE_MESSAGES.get(code)
    if message is None:
        return "planner_failed", "The offline planner failed safely."
    return code, message


def _sanitized_dispatch_failure(error: ToolDispatchError) -> tuple[str, str]:
    code = error.code if type(error.code) is str else "tool_dispatch_failed"
    message = _DISPATCH_FAILURE_MESSAGES.get(code)
    if message is None:
        return "tool_dispatch_failed", "The deterministic tool dispatcher failed safely."
    return code, message


def _sanitized_packet_failure(error: _PacketAssemblyError) -> tuple[str, str]:
    code = error.code if type(error.code) is str else "packet_assembly_failed"
    if code not in _PACKET_FAILURE_CODES:
        code = "packet_assembly_failed"
    return code, "The evidence packet could not be assembled safely."


def _canonical_source_bytes(path: Path) -> bytes:
    if path.is_symlink() or not path.is_file():
        raise ValueError("executor source entry is not one regular file")
    payload = path.read_bytes()
    if type(payload) is not bytes or not payload:
        raise ValueError("executor source entry is not exact non-empty bytes")
    return payload.replace(b"\r\n", b"\n").replace(b"\r", b"\n")


def _canonical_executor_descriptor_bytes() -> bytes:
    """Bind the complete importable SovereignLab source tree without local paths."""

    source_files = []
    for path in sorted(_SOURCE_ROOT.rglob("*.py")):
        if path.is_symlink():
            raise ValueError("executor source tree cannot contain symbolic links")
        resolved = path.resolve()
        resolved.relative_to(_SOURCE_ROOT)
        relative = path.relative_to(_SOURCE_ROOT).as_posix()
        source_files.append(
            {
                "path": relative,
                "sha256": hashlib.sha256(_canonical_source_bytes(path)).hexdigest(),
            }
        )
    if not source_files or len({item["path"] for item in source_files}) != len(source_files):
        raise ValueError("executor source descriptor is incomplete or ambiguous")
    descriptor = {
        "execution_contract_version": "1.0.0",
        "executor_id": _OFFLINE_EXECUTOR_ID,
        "source_files": source_files,
        "tool_registry_id": CALLABLE_TOOL_REGISTRY_ID,
        "tool_registry_sha256": CALLABLE_TOOL_REGISTRY_DESCRIPTOR_SHA256,
    }
    return json.dumps(
        descriptor,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def _executor_descriptor_sha256() -> str:
    return hashlib.sha256(_canonical_executor_descriptor_bytes()).hexdigest()


def _validated_request(request: object) -> ExecutionRequest:
    try:
        if type(request) is not ExecutionRequest:
            raise ValueError("request must use the exact execution model")
        rebuilt = ExecutionRequest.model_validate_json(
            request.model_dump_json(warnings="error"),
            strict=True,
        )
        if type(rebuilt) is not ExecutionRequest or rebuilt != request:
            raise ValueError("request changed during strict round trip")
        return rebuilt
    except Exception:
        raise _OfflineExecutorError(
            "invalid_request",
            "Offline execution requires an exact validated execution request.",
        ) from None


def _validated_trace_metadata(*, trace_id: object, recorded_at: object) -> tuple[str, datetime]:
    try:
        if type(trace_id) is not str:
            raise ValueError("trace ID must use an exact string")
        validated_trace_id = _IDENTIFIER_ADAPTER.validate_python(trace_id, strict=True)
        if type(recorded_at) is not datetime or recorded_at.utcoffset() != timedelta(0):
            raise ValueError("recorded_at must be an exact UTC datetime")
        return validated_trace_id, recorded_at
    except Exception:
        raise _OfflineExecutorError(
            "invalid_trace_metadata",
            "Offline execution requires a valid trace ID and explicit UTC recording instant.",
        ) from None


def _validated_planner_provenance(value: object) -> PlannerProvenance:
    try:
        if type(value) is not PlannerProvenance:
            raise ValueError("planner provenance must use the exact model")
        rebuilt = PlannerProvenance.model_validate_json(
            value.model_dump_json(warnings="error"),
            strict=True,
        )
        if type(rebuilt) is not PlannerProvenance or rebuilt != value:
            raise ValueError("planner provenance changed during strict round trip")
        return rebuilt
    except Exception:
        raise _OfflineExecutorError(
            "invalid_planner_provenance",
            "The offline planner provenance could not be validated safely.",
        ) from None


def _planner_provenance(planner: object) -> PlannerProvenance:
    try:
        if not isinstance(planner, Planner):
            raise ValueError("planner does not implement the one-shot protocol")
        return _validated_planner_provenance(planner.provenance)
    except _OfflineExecutorError:
        raise
    except Exception:
        raise _OfflineExecutorError(
            "invalid_planner",
            "Offline execution requires a valid one-shot planner.",
        ) from None


def _validated_registry_provenance(registry: object) -> ToolRegistryProvenance:
    try:
        if type(registry) is not CallableToolRegistry:
            raise ValueError("registry must use the exact callable registry")
        provenance = registry.provenance()
        if type(provenance) is not ToolRegistryProvenance:
            raise ValueError("registry provenance has the wrong exact type")
        return provenance
    except Exception:
        raise _OfflineExecutorError(
            "invalid_execution_environment",
            "The offline execution environment could not be validated safely.",
        ) from None


def _validated_environment(registry: object) -> ExecutionEnvironmentProvenance:
    try:
        provenance = _validated_registry_provenance(registry)
        environment = ExecutionEnvironmentProvenance(
            executor_id=_OFFLINE_EXECUTOR_ID,
            executor_sha256=_executor_descriptor_sha256(),
            tool_registry_id=provenance.tool_registry_id,
            tool_registry_sha256=provenance.tool_registry_sha256,
            artifact_registry_id=provenance.artifact_registry_id,
            artifact_registry_sha256=provenance.artifact_registry_sha256,
            retrieval_corpus_id=provenance.retrieval_corpus_id,
            retrieval_corpus_sha256=provenance.retrieval_corpus_sha256,
        )
        rebuilt = ExecutionEnvironmentProvenance.model_validate_json(
            environment.model_dump_json(warnings="error"),
            strict=True,
        )
        if type(rebuilt) is not ExecutionEnvironmentProvenance or rebuilt != environment:
            raise ValueError("environment changed during strict round trip")
        return rebuilt
    except _OfflineExecutorError:
        raise
    except Exception:
        raise _OfflineExecutorError(
            "invalid_execution_environment",
            "The offline execution environment could not be validated safely.",
        ) from None


def _require_stable_environment(
    *,
    registry: object,
    expected: ExecutionEnvironmentProvenance,
) -> None:
    if _validated_environment(registry) != expected:
        raise _OfflineExecutorError(
            "execution_environment_drift",
            "The offline execution environment changed during execution.",
        )


def _require_stable_planner(
    *,
    planner: object,
    expected: PlannerProvenance,
) -> None:
    if _planner_provenance(planner) != expected:
        raise _OfflineExecutorError(
            "planner_provenance_drift",
            "The offline planner provenance changed during execution.",
        )


def _planner_request_is_stable(
    *,
    candidate: object,
    expected: ExecutionRequest,
) -> bool:
    try:
        return _validated_request(candidate) == expected
    except _OfflineExecutorError:
        return False


def _validated_plan(plan: object, request: ExecutionRequest) -> RoutePlan:
    try:
        if type(plan) is not RoutePlan:
            raise ValueError("planner result must use the exact route-plan model")
        rebuilt = RoutePlan.model_validate_json(
            plan.model_dump_json(warnings="error"),
            strict=True,
        )
        if type(rebuilt) is not RoutePlan or rebuilt != plan:
            raise ValueError("route plan changed during strict round trip")
        for call in rebuilt.tool_calls:
            if call.arguments.as_of != request.effective_as_of:
                raise ValueError("route plan cutoff differs from request")
            if type(call) is TemporalDocumentCall and (
                call.arguments.question != request.question
                or call.arguments.language != request.language
            ):
                raise ValueError("document call differs from request")
        return rebuilt
    except Exception:
        raise _OfflineExecutorError(
            "invalid_route_plan",
            "The planner did not return a request-bound validated route plan.",
        ) from None


def _validated_call_copy(call: object) -> TemporalDocumentCall | StesAsOfCall | SnapshotAsOfCall:
    model_type = type(call)
    try:
        if model_type not in {TemporalDocumentCall, StesAsOfCall, SnapshotAsOfCall}:
            raise ValueError("call must use an exact registered model")
        rebuilt = model_type.model_validate_json(
            call.model_dump_json(warnings="error"),
            strict=True,
        )
        if type(rebuilt) is not model_type or rebuilt != call:
            raise ValueError("call changed during strict round trip")
        return rebuilt
    except Exception:
        raise _OfflineExecutorError(
            "invalid_tool_call",
            "The validated route plan contained an invalid tool call.",
        ) from None


def _validated_result(call: object, result: object) -> ToolResult:
    model_type = type(result)
    try:
        if model_type not in _RESULT_MODELS:
            raise ValueError("result must use an exact registered model")
        rebuilt = model_type.model_validate_json(
            result.model_dump_json(warnings="error"),
            strict=True,
        )
        if type(rebuilt) is not model_type or rebuilt != result:
            raise ValueError("tool result changed during strict round trip")
        _validate_result_against_call(call, rebuilt)
        return rebuilt
    except Exception:
        raise _OfflineExecutorError(
            "invalid_tool_result",
            "The dispatcher returned an invalid typed tool result.",
        ) from None


def _tool_error_result(
    call: TemporalDocumentCall | StesAsOfCall | SnapshotAsOfCall,
    *,
    code: str,
    message: str,
) -> ToolResult:
    try:
        failure = ExecutionFailure(
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
                error=failure,
            )
        if type(call) is StesAsOfCall:
            return StesAsOfResult(
                call_id=call.call_id,
                tool_name=ToolName.RESOLVE_STES_AS_OF,
                status=ToolOutcomeStatus.ERROR,
                error=failure,
            )
        if type(call) is SnapshotAsOfCall:
            return SnapshotAsOfResult(
                call_id=call.call_id,
                tool_name=ToolName.READ_SNAPSHOT_AS_OF,
                status=ToolOutcomeStatus.ERROR,
                error=failure,
            )
        raise ValueError("call has no typed error result")
    except Exception:
        raise _OfflineExecutorError(
            "tool_failure_mapping_failed",
            "A tool failure could not be represented safely.",
        ) from None


def _validated_packet(packet: object) -> ExecutionEvidencePacket:
    try:
        if type(packet) is not ExecutionEvidencePacket:
            raise ValueError("assembler output must use the exact packet model")
        rebuilt = ExecutionEvidencePacket.model_validate_json(
            packet.model_dump_json(warnings="error"),
            strict=True,
        )
        if type(rebuilt) is not ExecutionEvidencePacket or rebuilt != packet:
            raise ValueError("packet changed during strict round trip")
        return rebuilt
    except Exception:
        raise _PacketAssemblyError(
            "packet_validation_failed",
            "The assembled evidence packet did not pass strict validation.",
        ) from None


def _validated_trace(trace: object) -> ExecutionTrace:
    try:
        if type(trace) is not ExecutionTrace:
            raise ValueError("trace must use the exact execution model")
        rebuilt = ExecutionTrace.model_validate_json(
            trace.model_dump_json(warnings="error"),
            strict=True,
        )
        if type(rebuilt) is not ExecutionTrace or rebuilt != trace:
            raise ValueError("trace changed during strict round trip")
        return rebuilt
    except Exception:
        raise _OfflineExecutorError(
            "trace_validation_failed",
            "The terminal execution trace could not be validated safely.",
        ) from None


def _trace(
    *,
    trace_id: str,
    recorded_at: datetime,
    request: ExecutionRequest,
    environment: ExecutionEnvironmentProvenance,
    planner: PlannerProvenance,
    status: TraceStatus,
    plan: RoutePlan | None = None,
    tool_results: tuple[ToolResult, ...] = (),
    evidence_packet: ExecutionEvidencePacket | None = None,
    failure: ExecutionFailure | None = None,
) -> ExecutionTrace:
    try:
        candidate = ExecutionTrace(
            trace_id=trace_id,
            recorded_at=recorded_at,
            request=request,
            environment=environment,
            planner=planner,
            status=status,
            plan=plan,
            tool_results=tool_results,
            evidence_packet=evidence_packet,
            failure=failure,
        )
    except Exception:
        raise _OfflineExecutorError(
            "trace_validation_failed",
            "The terminal execution trace could not be validated safely.",
        ) from None
    return _validated_trace(candidate)


def _planner_failure(
    *,
    trace_id: str,
    recorded_at: datetime,
    request: ExecutionRequest,
    environment: ExecutionEnvironmentProvenance,
    provenance: PlannerProvenance,
    phase: FailurePhase,
    code: str,
    message: str,
) -> ExecutionTrace:
    try:
        failure = ExecutionFailure(phase=phase, code=code, message=message)
    except Exception:
        raise _OfflineExecutorError(
            "planner_failure_mapping_failed",
            "A planner failure could not be represented safely.",
        ) from None
    return _trace(
        trace_id=trace_id,
        recorded_at=recorded_at,
        request=request,
        environment=environment,
        planner=provenance,
        status=TraceStatus.FAILED,
        failure=failure,
    )


def _assemble_packet(
    *,
    request: ExecutionRequest,
    plan: RoutePlan,
    tool_results: tuple[ToolResult, ...],
) -> ExecutionEvidencePacket:
    try:
        packet = _assemble_evidence_packet(
            request=request,
            plan=plan,
            tool_results=tool_results,
        )
        return _validated_packet(packet)
    except _PacketAssemblyError:
        raise
    except Exception:
        raise _PacketAssemblyError(
            "packet_assembly_failed",
            "The evidence packet could not be assembled safely.",
        ) from None


def _packet_failure_trace(
    *,
    trace_id: str,
    recorded_at: datetime,
    request: ExecutionRequest,
    environment: ExecutionEnvironmentProvenance,
    planner: PlannerProvenance,
    plan: RoutePlan,
    tool_results: tuple[ToolResult, ...],
    error: _PacketAssemblyError,
) -> ExecutionTrace:
    code, message = _sanitized_packet_failure(error)
    try:
        failure = ExecutionFailure(
            phase=FailurePhase.PACKET_ASSEMBLY,
            code=code,
            message=message,
        )
    except Exception:
        raise _OfflineExecutorError(
            "packet_failure_mapping_failed",
            "A packet-assembly failure could not be represented safely.",
        ) from None
    return _trace(
        trace_id=trace_id,
        recorded_at=recorded_at,
        request=request,
        environment=environment,
        planner=planner,
        status=TraceStatus.FAILED,
        plan=plan,
        tool_results=tool_results,
        failure=failure,
    )


def _execute_offline_request(
    *,
    trace_id: str,
    recorded_at: datetime,
    request: ExecutionRequest,
    planner: Planner,
    registry: CallableToolRegistry,
) -> ExecutionTrace:
    """Plan once, dispatch in order, assemble once, and return one strict terminal trace."""

    validated_trace_id, validated_recorded_at = _validated_trace_metadata(
        trace_id=trace_id,
        recorded_at=recorded_at,
    )
    validated_request = _validated_request(request)
    environment = _validated_environment(registry)
    planner_provenance = _planner_provenance(planner)
    planner_request = _validated_request(validated_request)

    try:
        candidate_plan = planner.plan(planner_request)
    except PlannerError as error:
        try:
            error_provenance = (
                planner_provenance
                if error.provenance is None
                else _validated_planner_provenance(error.provenance)
            )
            request_is_stable = _planner_request_is_stable(
                candidate=planner_request,
                expected=validated_request,
            )
            _require_stable_planner(planner=planner, expected=planner_provenance)
            _require_stable_environment(registry=registry, expected=environment)
            if error_provenance != planner_provenance:
                raise _OfflineExecutorError(
                    "planner_provenance_drift",
                    "The offline planner provenance changed during execution.",
                )
            if request_is_stable:
                failure_code, failure_message = _sanitized_planner_failure(error)
            else:
                failure_code = "planner_result_invalid"
                failure_message = (
                    "The planner result did not validate against the execution request."
                )
            phase = (
                FailurePhase.PLAN_VALIDATION
                if failure_code == "plan_validation_failed"
                else FailurePhase.PLANNER
            )
            if phase is FailurePhase.PLAN_VALIDATION and (
                error_provenance.recording_id is None or error_provenance.output_sha256 is None
            ):
                raise _OfflineExecutorError(
                    "invalid_planner_provenance",
                    "A rejected planner candidate requires digest-linked provenance.",
                )
            return _planner_failure(
                trace_id=validated_trace_id,
                recorded_at=validated_recorded_at,
                request=validated_request,
                environment=environment,
                provenance=error_provenance,
                phase=phase,
                code=failure_code,
                message=failure_message,
            )
        except _OfflineExecutorError:
            raise
        except Exception:
            raise _OfflineExecutorError(
                "planner_failure_mapping_failed",
                "A planner failure could not be represented safely.",
            ) from None
    except Exception:
        request_is_stable = _planner_request_is_stable(
            candidate=planner_request,
            expected=validated_request,
        )
        _require_stable_planner(planner=planner, expected=planner_provenance)
        _require_stable_environment(registry=registry, expected=environment)
        failure_code = "planner_failed" if request_is_stable else "planner_result_invalid"
        failure_message = (
            "The offline planner failed unexpectedly."
            if request_is_stable
            else "The planner result did not validate against the execution request."
        )
        return _planner_failure(
            trace_id=validated_trace_id,
            recorded_at=validated_recorded_at,
            request=validated_request,
            environment=environment,
            provenance=planner_provenance,
            phase=FailurePhase.PLANNER,
            code=failure_code,
            message=failure_message,
        )

    try:
        if not _planner_request_is_stable(
            candidate=planner_request,
            expected=validated_request,
        ):
            raise _OfflineExecutorError(
                "planner_request_drift",
                "The offline planner changed its private request copy.",
            )
        _require_stable_planner(planner=planner, expected=planner_provenance)
        _require_stable_environment(registry=registry, expected=environment)
        plan = _validated_plan(candidate_plan, validated_request)
    except _OfflineExecutorError as error:
        if error.code in {
            "invalid_route_plan",
            "planner_request_drift",
        }:
            return _planner_failure(
                trace_id=validated_trace_id,
                recorded_at=validated_recorded_at,
                request=validated_request,
                environment=environment,
                provenance=planner_provenance,
                phase=FailurePhase.PLANNER,
                code="planner_result_invalid",
                message="The planner result did not validate against the execution request.",
            )
        raise

    results: list[ToolResult] = []
    for planned_call in plan.tool_calls:
        call = _validated_call_copy(planned_call)
        try:
            raw_result = dispatch_tool_call(call=call, registry=registry)
        except ToolDispatchError as error:
            try:
                if _validated_call_copy(call) != planned_call:
                    raise _OfflineExecutorError(
                        "invalid_tool_call",
                        "The dispatcher changed its private tool-call copy.",
                    )
            except _OfflineExecutorError:
                result = _tool_error_result(
                    planned_call,
                    code="tool_result_invalid",
                    message="The deterministic tool dispatcher returned an invalid result.",
                )
            else:
                failure_code, failure_message = _sanitized_dispatch_failure(error)
                result = _tool_error_result(
                    planned_call,
                    code=failure_code,
                    message=failure_message,
                )
        except Exception:
            try:
                if _validated_call_copy(call) != planned_call:
                    raise _OfflineExecutorError(
                        "invalid_tool_call",
                        "The dispatcher changed its private tool-call copy.",
                    )
            except _OfflineExecutorError:
                result = _tool_error_result(
                    planned_call,
                    code="tool_result_invalid",
                    message="The deterministic tool dispatcher returned an invalid result.",
                )
            else:
                result = _tool_error_result(
                    planned_call,
                    code="tool_dispatch_failed",
                    message="The deterministic tool dispatcher failed unexpectedly.",
                )
        else:
            try:
                if _validated_call_copy(call) != planned_call:
                    raise _OfflineExecutorError(
                        "invalid_tool_call",
                        "The dispatcher changed its private tool-call copy.",
                    )
                result = _validated_result(planned_call, raw_result)
            except _OfflineExecutorError:
                result = _tool_error_result(
                    planned_call,
                    code="tool_result_invalid",
                    message="The deterministic tool dispatcher returned an invalid result.",
                )
        _require_stable_environment(registry=registry, expected=environment)
        results.append(result)
        if result.status is not ToolOutcomeStatus.SUCCESS:
            break

    tool_results = tuple(results)
    if tool_results and tool_results[-1].status is ToolOutcomeStatus.ERROR:
        terminal = tool_results[-1]
        if terminal.error is None:
            raise _OfflineExecutorError(
                "tool_failure_mapping_failed",
                "A tool failure could not be represented safely.",
            )
        _require_stable_planner(planner=planner, expected=planner_provenance)
        _require_stable_environment(registry=registry, expected=environment)
        return _trace(
            trace_id=validated_trace_id,
            recorded_at=validated_recorded_at,
            request=validated_request,
            environment=environment,
            planner=planner_provenance,
            status=TraceStatus.FAILED,
            plan=plan,
            tool_results=tool_results,
            failure=terminal.error,
        )

    try:
        packet = _assemble_packet(
            request=validated_request,
            plan=plan,
            tool_results=tool_results,
        )
    except _PacketAssemblyError as error:
        if tool_results and tool_results[-1].status is ToolOutcomeStatus.ABSTAINED:
            raise _OfflineExecutorError(
                "untraceable_packet_assembly_failure",
                "A terminal tool abstention could not be assembled safely.",
            ) from None
        _require_stable_planner(planner=planner, expected=planner_provenance)
        _require_stable_environment(registry=registry, expected=environment)
        return _packet_failure_trace(
            trace_id=validated_trace_id,
            recorded_at=validated_recorded_at,
            request=validated_request,
            environment=environment,
            planner=planner_provenance,
            plan=plan,
            tool_results=tool_results,
            error=error,
        )

    _require_stable_planner(planner=planner, expected=planner_provenance)
    _require_stable_environment(registry=registry, expected=environment)
    status = (
        TraceStatus.COMPLETE if packet.status is PacketStatus.COMPLETE else TraceStatus.ABSTAINED
    )
    return _trace(
        trace_id=validated_trace_id,
        recorded_at=validated_recorded_at,
        request=validated_request,
        environment=environment,
        planner=planner_provenance,
        status=status,
        plan=plan,
        tool_results=tool_results,
        evidence_packet=packet,
    )
