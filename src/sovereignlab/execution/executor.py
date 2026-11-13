"""Offline executor: plan once, call the tools in order, and return one trace."""

from datetime import datetime
from pathlib import Path

from sovereignlab.artifacts import canonical_sha256, sha256_hex
from sovereignlab.execution.assembler import assemble_evidence_packet
from sovereignlab.execution.dispatcher import (
    CALLABLE_TOOL_REGISTRY_ID,
    CallableToolRegistry,
    dispatch_tool_call,
    tool_registry_sha256,
)
from sovereignlab.execution.planner import Planner, PlannerError
from sovereignlab.schemas import (
    ExecutionEnvironmentProvenance,
    ExecutionFailure,
    ExecutionRequest,
    ExecutionTrace,
    FailurePhase,
    PacketStatus,
    ToolOutcomeStatus,
    ToolResult,
    TraceStatus,
)

OFFLINE_EXECUTOR_ID = "sovereignlab-offline-executor-v1"
_SOURCE_ROOT = Path(__file__).resolve().parents[1]


def executor_sha256() -> str:
    """Hash every source file of the package, so a trace names the code that produced it."""

    return canonical_sha256(
        {
            "execution_contract_version": "1.0.0",
            "executor_id": OFFLINE_EXECUTOR_ID,
            "source_files": [
                {
                    "path": path.relative_to(_SOURCE_ROOT).as_posix(),
                    # Line endings are normalized so a Windows checkout hashes identically.
                    "sha256": sha256_hex(
                        path.read_bytes().replace(b"\r\n", b"\n").replace(b"\r", b"\n")
                    ),
                }
                for path in sorted(_SOURCE_ROOT.rglob("*.py"))
            ],
            "tool_registry_id": CALLABLE_TOOL_REGISTRY_ID,
            "tool_registry_sha256": tool_registry_sha256(),
        }
    )


def execution_environment(registry: CallableToolRegistry) -> ExecutionEnvironmentProvenance:
    """Return the code and evidence digests recorded in a trace."""

    provenance = registry.provenance()
    return ExecutionEnvironmentProvenance(
        executor_id=OFFLINE_EXECUTOR_ID,
        executor_sha256=executor_sha256(),
        tool_registry_id=provenance.tool_registry_id,
        tool_registry_sha256=provenance.tool_registry_sha256,
        artifact_registry_id=provenance.artifact_registry_id,
        artifact_registry_sha256=provenance.artifact_registry_sha256,
        retrieval_corpus_id=provenance.retrieval_corpus_id,
        retrieval_corpus_sha256=provenance.retrieval_corpus_sha256,
    )


def execute_offline_request(
    *,
    trace_id: str,
    recorded_at: datetime,
    request: ExecutionRequest,
    planner: Planner,
    registry: CallableToolRegistry,
) -> ExecutionTrace:
    """Run one request to a terminal trace: complete, abstained, or failed.

    Execution stops at the first tool result that is not a success. An abstention yields an
    abstained packet with no partial evidence; an error yields a failed trace with no packet.
    The trace model validates the final shape.
    """

    def trace(status: TraceStatus, **fields: object) -> ExecutionTrace:
        return ExecutionTrace(
            trace_id=trace_id,
            recorded_at=recorded_at,
            request=request,
            environment=execution_environment(registry),
            planner=planner.provenance,
            status=status,
            **fields,
        )

    try:
        plan = planner.plan(request)
    except PlannerError as error:
        phase = (
            FailurePhase.PLAN_VALIDATION
            if error.code == "plan_validation_failed"
            else FailurePhase.PLANNER
        )
        return trace(
            TraceStatus.FAILED,
            failure=ExecutionFailure(phase=phase, code=error.code, message=str(error)),
        )

    results: list[ToolResult] = []
    for call in plan.tool_calls:
        result = dispatch_tool_call(call=call, registry=registry)
        results.append(result)
        if result.status is not ToolOutcomeStatus.SUCCESS:
            break
    tool_results = tuple(results)

    if tool_results and tool_results[-1].status is ToolOutcomeStatus.ERROR:
        return trace(
            TraceStatus.FAILED,
            plan=plan,
            tool_results=tool_results,
            failure=tool_results[-1].error,
        )

    packet = assemble_evidence_packet(request=request, plan=plan, tool_results=tool_results)
    return trace(
        TraceStatus.COMPLETE if packet.status is PacketStatus.COMPLETE else TraceStatus.ABSTAINED,
        plan=plan,
        tool_results=tool_results,
        evidence_packet=packet,
    )
