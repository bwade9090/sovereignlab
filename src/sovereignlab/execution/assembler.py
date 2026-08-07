"""Private deterministic assembly of validated execution evidence packets."""

from sovereignlab.schemas import (
    AbstentionOrigin,
    EvidenceRoute,
    ExecutionEvidencePacket,
    ExecutionRequest,
    ObservationEvidence,
    PacketAbstention,
    PacketStatus,
    RoutePlan,
    SnapshotAsOfResult,
    StesAsOfResult,
    TemporalDocumentCall,
    TemporalDocumentResult,
    ToolOutcomeStatus,
    ToolResult,
)
from sovereignlab.schemas.execution import _validate_result_against_call

_RESULT_MODELS = (
    TemporalDocumentResult,
    StesAsOfResult,
    SnapshotAsOfResult,
)


class _PacketAssemblyError(ValueError):
    """Sanitized private rejection from the packet-assembly boundary."""

    def __init__(self, code: str, message: str) -> None:
        self.code = code
        super().__init__(message)


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
        raise _PacketAssemblyError(
            "invalid_request",
            "Packet assembly requires an exact validated execution request.",
        ) from None


def _validated_plan(plan: object) -> RoutePlan:
    try:
        if type(plan) is not RoutePlan:
            raise ValueError("plan must use the exact route-plan model")
        rebuilt = RoutePlan.model_validate_json(
            plan.model_dump_json(warnings="error"),
            strict=True,
        )
        if type(rebuilt) is not RoutePlan or rebuilt != plan:
            raise ValueError("plan changed during strict round trip")
        return rebuilt
    except Exception:
        raise _PacketAssemblyError(
            "invalid_plan",
            "Packet assembly requires an exact validated route plan.",
        ) from None


def _validated_result(result: object) -> ToolResult:
    model_type = type(result)
    try:
        if model_type not in _RESULT_MODELS:
            raise ValueError("result must use an exact registered result model")
        rebuilt = model_type.model_validate_json(
            result.model_dump_json(warnings="error"),
            strict=True,
        )
        if type(rebuilt) is not model_type or rebuilt != result:
            raise ValueError("result changed during strict round trip")
        return rebuilt
    except Exception:
        raise _PacketAssemblyError(
            "invalid_tool_result",
            "Packet assembly received an invalid typed tool result.",
        ) from None


def _validated_results(tool_results: object) -> tuple[ToolResult, ...]:
    if type(tool_results) is not tuple:
        raise _PacketAssemblyError(
            "invalid_result_sequence",
            "Packet assembly requires one immutable ordered result sequence.",
        )
    return tuple(_validated_result(result) for result in tool_results)


def _bind_plan_to_request(plan: RoutePlan, request: ExecutionRequest) -> None:
    for call in plan.tool_calls:
        if call.arguments.as_of != request.effective_as_of:
            raise _PacketAssemblyError(
                "request_plan_drift",
                "The route plan cutoff differs from the execution request.",
            )
        if type(call) is TemporalDocumentCall and (
            call.arguments.question != request.question
            or call.arguments.language != request.language
        ):
            raise _PacketAssemblyError(
                "request_plan_drift",
                "The document plan differs from the execution request.",
            )


def _validate_result_sequence(
    plan: RoutePlan,
    results: tuple[ToolResult, ...],
) -> None:
    if len(results) > len(plan.tool_calls):
        raise _PacketAssemblyError(
            "invalid_result_sequence",
            "Tool results are not an ordered prefix of the route plan.",
        )
    for call, result in zip(plan.tool_calls, results, strict=False):
        try:
            _validate_result_against_call(call, result)
        except Exception:
            raise _PacketAssemblyError(
                "invalid_result_sequence",
                "Tool results differ from the ordered route-plan calls.",
            ) from None


def _validated_packet(packet: ExecutionEvidencePacket) -> ExecutionEvidencePacket:
    try:
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


def _planned_abstention_packet(
    *,
    request: ExecutionRequest,
    plan: RoutePlan,
) -> ExecutionEvidencePacket:
    if plan.abstention is None:
        raise _PacketAssemblyError(
            "invalid_plan",
            "The planned abstention is missing its validated reason.",
        )
    return _validated_packet(
        ExecutionEvidencePacket(
            request=request,
            planned_route=plan.route,
            status=PacketStatus.ABSTAINED,
            abstention=PacketAbstention(
                origin=AbstentionOrigin.PLAN,
                reason_code=plan.abstention.reason_code,
                message=plan.abstention.message,
            ),
        )
    )


def _tool_abstention_packet(
    *,
    request: ExecutionRequest,
    plan: RoutePlan,
    result: ToolResult,
) -> ExecutionEvidencePacket:
    if result.abstention is None:
        raise _PacketAssemblyError(
            "invalid_tool_result",
            "The terminal tool abstention is missing its validated reason.",
        )
    return _validated_packet(
        ExecutionEvidencePacket(
            request=request,
            planned_route=plan.route,
            status=PacketStatus.ABSTAINED,
            abstention=PacketAbstention(
                origin=AbstentionOrigin.TOOL,
                origin_call_id=result.call_id,
                reason_code=result.abstention.reason_code,
                message=result.abstention.message,
            ),
        )
    )


def _complete_packet(
    *,
    request: ExecutionRequest,
    plan: RoutePlan,
    results: tuple[ToolResult, ...],
) -> ExecutionEvidencePacket:
    documents = []
    observations: list[ObservationEvidence] = []
    for result in results:
        if type(result) is TemporalDocumentResult:
            if result.payload is None:
                raise _PacketAssemblyError(
                    "invalid_tool_result",
                    "A successful document result is missing its typed payload.",
                )
            documents.extend(result.payload.matches)
        elif type(result) in {StesAsOfResult, SnapshotAsOfResult}:
            if result.payload is None:
                raise _PacketAssemblyError(
                    "invalid_tool_result",
                    "A successful data result is missing its typed payload.",
                )
            observations.append(result.payload)
        else:
            raise _PacketAssemblyError(
                "invalid_tool_result",
                "Packet assembly received an unregistered result model.",
            )
    return _validated_packet(
        ExecutionEvidencePacket(
            request=request,
            planned_route=plan.route,
            status=PacketStatus.COMPLETE,
            documents=tuple(documents),
            observations=tuple(observations),
        )
    )


def _assemble_evidence_packet(
    *,
    request: ExecutionRequest,
    plan: RoutePlan,
    tool_results: tuple[ToolResult, ...],
) -> ExecutionEvidencePacket:
    """Assemble one fail-closed packet without planning, dispatch, or trace work."""

    try:
        validated_request = _validated_request(request)
        validated_plan = _validated_plan(plan)
        validated_results = _validated_results(tool_results)
        _bind_plan_to_request(validated_plan, validated_request)

        if validated_plan.route is EvidenceRoute.ABSTAIN:
            if validated_results:
                raise _PacketAssemblyError(
                    "invalid_result_sequence",
                    "A planned abstention cannot contain tool results.",
                )
            return _planned_abstention_packet(
                request=validated_request,
                plan=validated_plan,
            )

        _validate_result_sequence(validated_plan, validated_results)

        if not validated_results:
            raise _PacketAssemblyError(
                "incomplete_result_sequence",
                "A non-abstain route requires its ordered tool results.",
            )
        if any(result.status is ToolOutcomeStatus.ERROR for result in validated_results):
            raise _PacketAssemblyError(
                "tool_error_not_evidence",
                "A tool execution error cannot be assembled as packet evidence.",
            )

        abstained_positions = tuple(
            index
            for index, result in enumerate(validated_results)
            if result.status is ToolOutcomeStatus.ABSTAINED
        )
        if abstained_positions:
            if abstained_positions != (len(validated_results) - 1,) or any(
                result.status is not ToolOutcomeStatus.SUCCESS for result in validated_results[:-1]
            ):
                raise _PacketAssemblyError(
                    "invalid_result_sequence",
                    "A tool abstention must terminate a successful result prefix.",
                )
            return _tool_abstention_packet(
                request=validated_request,
                plan=validated_plan,
                result=validated_results[-1],
            )

        if any(result.status is not ToolOutcomeStatus.SUCCESS for result in validated_results):
            raise _PacketAssemblyError(
                "invalid_result_sequence",
                "Tool results contain an unsupported terminal state.",
            )
        if len(validated_results) != len(validated_plan.tool_calls):
            raise _PacketAssemblyError(
                "incomplete_result_sequence",
                "Complete packet assembly requires every planned successful result.",
            )
        return _complete_packet(
            request=validated_request,
            plan=validated_plan,
            results=validated_results,
        )
    except _PacketAssemblyError:
        raise
    except Exception:
        raise _PacketAssemblyError(
            "packet_assembly_failed",
            "The evidence packet could not be assembled safely.",
        ) from None
