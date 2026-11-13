"""Assemble the evidence packet for one executed route plan."""

from sovereignlab.schemas import (
    AbstentionOrigin,
    EvidenceRoute,
    ExecutionEvidencePacket,
    ExecutionRequest,
    PacketAbstention,
    PacketStatus,
    RoutePlan,
    TemporalDocumentResult,
    ToolOutcomeStatus,
    ToolResult,
)


def assemble_evidence_packet(
    *,
    request: ExecutionRequest,
    plan: RoutePlan,
    tool_results: tuple[ToolResult, ...],
) -> ExecutionEvidencePacket:
    """Return a complete packet, or an abstained one that exposes no partial evidence.

    ``tool_results`` are the results of the plan's calls in order, stopping at the first
    abstention. The packet model itself rejects any shape that contradicts the route.
    """

    if plan.route is EvidenceRoute.ABSTAIN:
        assert plan.abstention is not None  # guaranteed by the route-plan model
        return ExecutionEvidencePacket(
            request=request,
            planned_route=plan.route,
            status=PacketStatus.ABSTAINED,
            abstention=PacketAbstention(
                origin=AbstentionOrigin.PLAN,
                reason_code=plan.abstention.reason_code,
                message=plan.abstention.message,
            ),
        )

    last = tool_results[-1]
    if last.status is ToolOutcomeStatus.ABSTAINED:
        assert last.abstention is not None  # guaranteed by the tool-result models
        return ExecutionEvidencePacket(
            request=request,
            planned_route=plan.route,
            status=PacketStatus.ABSTAINED,
            abstention=PacketAbstention(
                origin=AbstentionOrigin.TOOL,
                origin_call_id=last.call_id,
                reason_code=last.abstention.reason_code,
                message=last.abstention.message,
            ),
        )

    documents = []
    observations = []
    for result in tool_results:
        if isinstance(result, TemporalDocumentResult):
            documents.extend(result.payload.matches)
        else:
            observations.append(result.payload)
    return ExecutionEvidencePacket(
        request=request,
        planned_route=plan.route,
        status=PacketStatus.COMPLETE,
        documents=tuple(documents),
        observations=tuple(observations),
    )
