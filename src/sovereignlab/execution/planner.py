"""Offline one-shot planners: a scripted plan or a recorded model response."""

import hashlib
from dataclasses import dataclass, field
from typing import Protocol

from sovereignlab.schemas import (
    ExecutionRequest,
    PlannerMode,
    PlannerProvenance,
    RoutePlan,
    TemporalDocumentCall,
)


class PlannerError(ValueError):
    """A planner could not produce a plan that is valid for the request."""

    def __init__(self, code: str, message: str) -> None:
        self.code = code
        super().__init__(message)


class Planner(Protocol):
    """The one-shot planning boundary consumed by the offline executor."""

    @property
    def provenance(self) -> PlannerProvenance:
        """Describe where the plan comes from."""

    def plan(self, request: ExecutionRequest) -> RoutePlan:
        """Return one route plan bound to the request, or raise ``PlannerError``."""


def bind_plan_to_request(plan: RoutePlan, request: ExecutionRequest) -> None:
    """Reject a plan whose calls use another cutoff, question, or language."""

    for call in plan.tool_calls:
        if call.arguments.as_of != request.effective_as_of:
            raise ValueError("a planned call's cutoff differs from the request cutoff")
        if isinstance(call, TemporalDocumentCall) and (
            call.arguments.question != request.question
            or call.arguments.language != request.language
        ):
            raise ValueError("a planned document call differs from the request")


def _validated_plan(candidate_bytes: bytes, request: ExecutionRequest) -> RoutePlan:
    try:
        plan = RoutePlan.model_validate_json(candidate_bytes, strict=True)
        bind_plan_to_request(plan, request)
    except ValueError:
        raise PlannerError(
            "plan_validation_failed",
            "The planner candidate did not validate against the execution request.",
        ) from None
    return plan


@dataclass(frozen=True)
class ScriptedPlanner:
    """Replay one harness-authored route plan."""

    planner_id: str
    script_id: str
    route_plan: RoutePlan = field(repr=False)

    def _candidate_bytes(self) -> bytes:
        return self.route_plan.model_dump_json(warnings="error").encode("utf-8")

    @property
    def provenance(self) -> PlannerProvenance:
        """Return scripted provenance linked to the plan's digest."""

        return PlannerProvenance(
            planner_id=self.planner_id,
            mode=PlannerMode.SCRIPTED,
            recording_id=self.script_id,
            output_sha256=hashlib.sha256(self._candidate_bytes()).hexdigest(),
        )

    def plan(self, request: ExecutionRequest) -> RoutePlan:
        """Return the scripted plan after binding it to the request."""

        return _validated_plan(self._candidate_bytes(), request)


@dataclass(frozen=True)
class RecordedPlanner:
    """Validate one recorded model response offline, without a provider call.

    Use ``mode=PlannerMode.REPLAY`` when re-running a recording that was already validated.
    """

    planner_id: str
    recording_id: str
    model_id: str
    candidate_bytes: bytes = field(repr=False)
    mode: PlannerMode = PlannerMode.RECORDED

    @property
    def provenance(self) -> PlannerProvenance:
        """Return recording provenance linked to the exact response bytes."""

        return PlannerProvenance(
            planner_id=self.planner_id,
            mode=self.mode,
            recording_id=self.recording_id,
            output_sha256=hashlib.sha256(self.candidate_bytes).hexdigest(),
            model_id=self.model_id,
        )

    def plan(self, request: ExecutionRequest) -> RoutePlan:
        """Parse the recorded bytes strictly and bind the plan to the request."""

        return _validated_plan(self.candidate_bytes, request)
