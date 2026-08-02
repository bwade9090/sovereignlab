"""Offline one-shot planners over exact scripted or recorded candidate bytes."""

import hashlib
import json
from dataclasses import dataclass, field
from typing import ClassVar, Protocol, runtime_checkable

from sovereignlab.schemas import (
    ExecutionRequest,
    PlannerMode,
    PlannerProvenance,
    RoutePlan,
    TemporalDocumentCall,
)

_MAX_CANDIDATE_BYTES = 1_000_000


class PlannerError(ValueError):
    """Sanitized planner rejection with optional audit-ready candidate provenance."""

    def __init__(
        self,
        code: str,
        message: str,
        *,
        provenance: PlannerProvenance | None = None,
    ) -> None:
        self.code = code
        self.provenance = provenance
        super().__init__(message)


@runtime_checkable
class Planner(Protocol):
    """The one-shot boundary consumed by the later offline executor."""

    @property
    def provenance(self) -> PlannerProvenance:
        """Return immutable metadata describing the candidate source."""

    def plan(self, request: ExecutionRequest) -> RoutePlan:
        """Return one request-bound, validated single-shot route plan."""


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _validate_candidate_bytes(candidate_bytes: object) -> bytes:
    if type(candidate_bytes) is not bytes:
        raise ValueError("planner candidate must use exact immutable bytes")
    if not candidate_bytes or len(candidate_bytes) > _MAX_CANDIDATE_BYTES:
        raise ValueError("planner candidate size is outside the trusted bound")
    return candidate_bytes


def _unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    output: dict[str, object] = {}
    for key, value in pairs:
        if key in output:
            raise ValueError("planner candidate contains a duplicate JSON key")
        output[key] = value
    return output


def _reject_json_constant(value: str) -> None:
    raise ValueError(f"unsupported JSON constant: {value}")


def _parse_route_plan(candidate_bytes: bytes) -> RoutePlan:
    candidate_bytes = _validate_candidate_bytes(candidate_bytes)
    decoded = candidate_bytes.decode("utf-8")
    parsed = json.loads(
        decoded,
        object_pairs_hook=_unique_object,
        parse_constant=_reject_json_constant,
    )
    if type(parsed) is not dict:
        raise ValueError("planner candidate must be one JSON object")
    plan = RoutePlan.model_validate_json(candidate_bytes, strict=True)
    if type(plan) is not RoutePlan:
        raise ValueError("planner candidate did not produce the exact route-plan model")
    return plan


def _validated_request_copy(request: object) -> ExecutionRequest:
    if type(request) is not ExecutionRequest:
        raise ValueError("planner request must be the exact validated model")
    payload = request.model_dump_json(warnings="error")
    rebuilt = ExecutionRequest.model_validate_json(payload, strict=True)
    if type(rebuilt) is not ExecutionRequest or rebuilt != request:
        raise ValueError("planner request changed during strict round trip")
    return rebuilt


def _bind_plan_to_request(plan: RoutePlan, request: ExecutionRequest) -> None:
    for call in plan.tool_calls:
        if call.arguments.as_of != request.effective_as_of:
            raise ValueError("planner call cutoff differs from the request cutoff")
        if isinstance(call, TemporalDocumentCall) and (
            call.arguments.question != request.question
            or call.arguments.language != request.language
        ):
            raise ValueError("planner document call differs from the request question or language")


def _validated_plan_for_request(
    *,
    candidate_bytes: bytes,
    request: object,
    provenance: PlannerProvenance,
) -> RoutePlan:
    try:
        validated_request = _validated_request_copy(request)
    except Exception:
        raise PlannerError(
            "invalid_request",
            "The planner requires an already validated execution request.",
            provenance=provenance,
        ) from None
    try:
        plan = _parse_route_plan(candidate_bytes)
        _bind_plan_to_request(plan, validated_request)
        return plan
    except Exception:
        raise PlannerError(
            "plan_validation_failed",
            "The planner candidate did not validate against the execution request.",
            provenance=provenance,
        ) from None


@dataclass(frozen=True)
class ScriptedPlanner:
    """Deterministically replay one harness-owned validated plan template."""

    planner_id: str
    script_id: str
    route_plan: RoutePlan = field(repr=False)
    _candidate_bytes: bytes = field(init=False, repr=False)
    _candidate_sha256: str = field(init=False, repr=False)

    def __post_init__(self) -> None:
        try:
            if type(self.route_plan) is not RoutePlan:
                raise ValueError("scripted route plan must use the exact model")
            candidate_bytes = self.route_plan.model_dump_json(warnings="error").encode("utf-8")
            candidate_bytes = _validate_candidate_bytes(candidate_bytes)
            candidate_sha256 = _sha256(candidate_bytes)
            PlannerProvenance(
                planner_id=self.planner_id,
                mode=PlannerMode.SCRIPTED,
                recording_id=self.script_id,
                output_sha256=candidate_sha256,
            )
        except Exception:
            raise PlannerError(
                "planner_misconfigured",
                "The scripted planner is misconfigured.",
            ) from None
        object.__setattr__(self, "_candidate_bytes", candidate_bytes)
        object.__setattr__(self, "_candidate_sha256", candidate_sha256)

    @property
    def provenance(self) -> PlannerProvenance:
        """Return digest-linked scripted provenance without a model ID."""

        return PlannerProvenance(
            planner_id=self.planner_id,
            mode=PlannerMode.SCRIPTED,
            recording_id=self.script_id,
            output_sha256=self._candidate_sha256,
        )

    def plan(self, request: ExecutionRequest) -> RoutePlan:
        """Reparse and request-bind a fresh plan from the frozen script bytes."""

        provenance = self.provenance
        try:
            candidate_bytes = _validate_candidate_bytes(self._candidate_bytes)
            if _sha256(candidate_bytes) != self._candidate_sha256:
                raise ValueError("scripted candidate digest drift")
        except Exception:
            raise PlannerError(
                "planner_misconfigured",
                "The scripted planner candidate is no longer immutable.",
                provenance=provenance,
            ) from None
        return _validated_plan_for_request(
            candidate_bytes=candidate_bytes,
            request=request,
            provenance=provenance,
        )


@dataclass(frozen=True)
class _PlannerRecording:
    recording_id: str
    model_id: str
    candidate_bytes: bytes = field(repr=False)
    output_sha256: str

    def validate(self) -> None:
        candidate_bytes = _validate_candidate_bytes(self.candidate_bytes)
        if _sha256(candidate_bytes) != self.output_sha256:
            raise ValueError("planner recording digest mismatch")
        PlannerProvenance(
            planner_id="recording-metadata-validator",
            mode=PlannerMode.RECORDED,
            recording_id=self.recording_id,
            output_sha256=self.output_sha256,
            model_id=self.model_id,
        )


class _RecordingRegistryError(ValueError):
    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__("the immutable planner recording registry is invalid")


@dataclass(frozen=True)
class _ImmutablePlannerRecordingRegistry:
    entries: tuple[_PlannerRecording, ...]

    def __post_init__(self) -> None:
        self._validate()

    def _validate(self) -> None:
        try:
            if (
                type(self) is not _ImmutablePlannerRecordingRegistry
                or type(self.entries) is not tuple
            ):
                raise ValueError("recording registry has the wrong immutable shape")
            if any(type(entry) is not _PlannerRecording for entry in self.entries):
                raise ValueError("recording registry contains an invalid entry")
            recording_ids = tuple(entry.recording_id for entry in self.entries)
            if len(recording_ids) != len(set(recording_ids)):
                raise ValueError("recording registry IDs must be unique")
            for entry in self.entries:
                entry.validate()
        except Exception:
            raise _RecordingRegistryError("recording_registry_invalid") from None

    def resolve(self, recording_id: str) -> _PlannerRecording:
        self._validate()
        matches = tuple(entry for entry in self.entries if entry.recording_id == recording_id)
        if not matches:
            raise _RecordingRegistryError("recording_missing")
        return matches[0]


class _RecordingBackedPlanner:
    _mode: ClassVar[PlannerMode]

    def __init__(
        self,
        *,
        planner_id: str,
        recording_id: str,
        registry: _ImmutablePlannerRecordingRegistry,
    ) -> None:
        try:
            if type(registry) is not _ImmutablePlannerRecordingRegistry:
                raise _RecordingRegistryError("recording_registry_invalid")
            entry = registry.resolve(recording_id)
            provenance = PlannerProvenance(
                planner_id=planner_id,
                mode=self._mode,
                recording_id=entry.recording_id,
                output_sha256=entry.output_sha256,
                model_id=entry.model_id,
            )
        except _RecordingRegistryError as error:
            raise PlannerError(
                error.code,
                "The requested immutable planner recording is unavailable.",
            ) from None
        except Exception:
            raise PlannerError(
                "planner_misconfigured",
                "The recording-backed planner is misconfigured.",
            ) from None
        self._registry = registry
        self._recording_id = entry.recording_id
        self._provenance = provenance

    @property
    def provenance(self) -> PlannerProvenance:
        """Return the complete immutable recording and model metadata."""

        return PlannerProvenance.model_validate_json(
            self._provenance.model_dump_json(warnings="error"),
            strict=True,
        )

    def plan(self, request: ExecutionRequest) -> RoutePlan:
        """Resolve, hash-verify, parse, and request-bind the recorded candidate."""

        provenance = self.provenance
        try:
            entry = self._registry.resolve(self._recording_id)
            if (
                entry.recording_id != provenance.recording_id
                or entry.output_sha256 != provenance.output_sha256
                or entry.model_id != provenance.model_id
            ):
                raise ValueError("planner recording metadata drift")
            candidate_bytes = _validate_candidate_bytes(entry.candidate_bytes)
            if _sha256(candidate_bytes) != provenance.output_sha256:
                raise ValueError("planner recording digest drift")
        except Exception:
            raise PlannerError(
                "recording_integrity_failed",
                "The immutable planner recording failed its integrity check.",
                provenance=provenance,
            ) from None
        return _validated_plan_for_request(
            candidate_bytes=candidate_bytes,
            request=request,
            provenance=provenance,
        )


class RecordedPlanner(_RecordingBackedPlanner):
    """Validate an immutable previously recorded model candidate without a provider call."""

    _mode = PlannerMode.RECORDED


class ReplayPlanner(_RecordingBackedPlanner):
    """Deterministically replay the same exact recorded candidate bytes."""

    _mode = PlannerMode.REPLAY
