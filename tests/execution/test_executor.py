"""Focused tests for the private deterministic offline executor."""

from __future__ import annotations

import inspect
import json
from datetime import UTC, date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import pytest

import sovereignlab.execution as execution_package
import sovereignlab.execution.executor as executor_module
from sovereignlab.execution import (
    CallableToolRegistry,
    Planner,
    PlannerError,
    ScriptedPlanner,
    ToolDispatchError,
    load_committed_callable_tool_registry,
)
from sovereignlab.schemas import (
    EvidenceRoute,
    ExecutionEnvironmentProvenance,
    ExecutionEvidencePacket,
    ExecutionFailure,
    ExecutionRequest,
    ExecutionTrace,
    FailurePhase,
    PacketStatus,
    PlanAbstention,
    PlannerMode,
    PlannerProvenance,
    RoutePlan,
    SnapshotAsOfArguments,
    SnapshotAsOfCall,
    SnapshotAsOfResult,
    StesAsOfArguments,
    StesAsOfCall,
    TemporalDocumentArguments,
    TemporalDocumentCall,
    ToolAbstention,
    ToolName,
    ToolOutcomeStatus,
    TraceStatus,
)
from sovereignlab.snapshots import ECOS_GDP_BINDING
from sovereignlab.vintage import CLI_STES_BINDING

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
CUTOFF = date(2026, 7, 17)
RECORDED_AT = datetime(2026, 8, 11, 3, 0, tzinfo=UTC)
QUESTION_EN = "Why was the growth outlook revised upward?"
QUESTION_KO = "기준일 현재 성장 전망이 상향 조정된 이유는 무엇인가요?"
SHA_A = "a" * 64
SHA_B = "b" * 64


@pytest.fixture(scope="module")
def committed_registry() -> CallableToolRegistry:
    return load_committed_callable_tool_registry(REPOSITORY_ROOT)


def _request(
    *,
    language: str = "en",
    requested_as_of: date | None = CUTOFF,
    effective_as_of: date = CUTOFF,
    question: str | None = None,
) -> ExecutionRequest:
    return ExecutionRequest(
        request_id=f"executor-request-{language}",
        question=question or (QUESTION_EN if language == "en" else QUESTION_KO),
        language=language,
        requested_as_of=requested_as_of,
        effective_as_of=effective_as_of,
    )


def _document_call(request: ExecutionRequest) -> TemporalDocumentCall:
    return TemporalDocumentCall(
        call_id="executor-call-document",
        tool_name=ToolName.RETRIEVE_TEMPORAL_DOCUMENTS,
        arguments=TemporalDocumentArguments(
            question=request.question,
            language=request.language,
            as_of=request.effective_as_of,
            top_k=5,
        ),
    )


def _stes_call(request: ExecutionRequest) -> StesAsOfCall:
    return StesAsOfCall(
        call_id="executor-call-stes",
        tool_name=ToolName.RESOLVE_STES_AS_OF,
        arguments=StesAsOfArguments(
            ref_area="KOR",
            freq="M",
            measure="LI_AA",
            unit_measure="IX",
            activity="_T",
            period="2026-05",
            as_of=request.effective_as_of,
            normalization_rule_id=CLI_STES_BINDING.normalization_rule_id,
        ),
    )


def _snapshot_call(request: ExecutionRequest) -> SnapshotAsOfCall:
    return SnapshotAsOfCall(
        call_id="executor-call-snapshot",
        tool_name=ToolName.READ_SNAPSHOT_AS_OF,
        arguments=SnapshotAsOfArguments(
            source_system=ECOS_GDP_BINDING.source_system,
            table_id=ECOS_GDP_BINDING.table_id,
            item_id=ECOS_GDP_BINDING.item_id,
            period="2026Q1",
            as_of=request.effective_as_of,
            normalization_rule_id=ECOS_GDP_BINDING.normalization_rule_id,
        ),
    )


def _plan(
    route: EvidenceRoute,
    request: ExecutionRequest,
    *,
    calls: tuple[Any, ...] | None = None,
) -> RoutePlan:
    selected = (
        {
            EvidenceRoute.DOCUMENTS: (_document_call(request),),
            EvidenceRoute.DATA: (_snapshot_call(request),),
            EvidenceRoute.DOCUMENTS_AND_DATA: (
                _document_call(request),
                _snapshot_call(request),
            ),
            EvidenceRoute.ABSTAIN: (),
        }[route]
        if calls is None
        else calls
    )
    return RoutePlan(
        route=route,
        tool_calls=selected,
        abstention=(
            PlanAbstention(
                reason_code="unsupported-request",
                message="No cutoff-safe evidence route is available.",
            )
            if route is EvidenceRoute.ABSTAIN
            else None
        ),
    )


def _provenance(
    *,
    planner_id: str = "executor-test-planner-v1",
    digest_linked: bool = True,
) -> PlannerProvenance:
    return PlannerProvenance(
        planner_id=planner_id,
        mode=PlannerMode.SCRIPTED,
        recording_id="executor-script-001" if digest_linked else None,
        output_sha256=SHA_A if digest_linked else None,
    )


def _environment(*, executor_sha256: str = SHA_A) -> ExecutionEnvironmentProvenance:
    return ExecutionEnvironmentProvenance(
        executor_id="sovereignlab-offline-executor-v1",
        executor_sha256=executor_sha256,
        tool_registry_id="sovereignlab-deterministic-tool-registry-v1",
        tool_registry_sha256=SHA_A,
        artifact_registry_id="kor-rtd-execution-artifact-registry-v1",
        artifact_registry_sha256=SHA_A,
        retrieval_corpus_id="synthetic-temporal-retrieval-corpus-v1",
        retrieval_corpus_sha256=SHA_A,
    )


class _FakePlanner:
    def __init__(
        self,
        *,
        plan: object,
        provenance: PlannerProvenance | object | None = None,
        error: BaseException | None = None,
        mutate_request: bool = False,
    ) -> None:
        self._plan = plan
        self._provenance = provenance or _provenance()
        self._error = error
        self._mutate_request = mutate_request
        self.calls = 0

    @property
    def provenance(self) -> Any:
        value = self._provenance
        if type(value) is PlannerProvenance:
            return value.model_copy(deep=True)
        return value

    def plan(self, request: ExecutionRequest) -> Any:
        self.calls += 1
        if self._mutate_request:
            object.__setattr__(request, "request_id", "executor-mutated-request")
        if self._error is not None:
            raise self._error
        return self._plan


@pytest.fixture
def isolated_environment(monkeypatch: pytest.MonkeyPatch) -> ExecutionEnvironmentProvenance:
    environment = _environment()
    monkeypatch.setattr(
        executor_module,
        "_validated_environment",
        lambda registry: environment.model_copy(deep=True),
    )
    monkeypatch.setattr(
        executor_module,
        "_require_stable_environment",
        lambda **kwargs: None,
    )
    return environment


def _execute(
    *,
    planner: Planner,
    registry: object = None,
    trace_id: str = "executor-trace-001",
    recorded_at: datetime = RECORDED_AT,
    request: ExecutionRequest | None = None,
) -> ExecutionTrace:
    return executor_module._execute_offline_request(
        trace_id=trace_id,
        recorded_at=recorded_at,
        request=request or _request(),
        planner=planner,
        registry=registry,  # type: ignore[arg-type]
    )


def _tool_abstention(call: SnapshotAsOfCall) -> SnapshotAsOfResult:
    return SnapshotAsOfResult(
        call_id=call.call_id,
        tool_name=ToolName.READ_SNAPSHOT_AS_OF,
        status=ToolOutcomeStatus.ABSTAINED,
        abstention=ToolAbstention(
            reason_code="no-snapshot-by-cutoff",
            message="No eligible snapshot exists by the cutoff.",
        ),
    )


def _tool_error(call: SnapshotAsOfCall) -> SnapshotAsOfResult:
    failure = ExecutionFailure(
        phase=FailurePhase.TOOL_EXECUTION,
        code="snapshot-failed",
        message="The snapshot failed safely.",
        call_id=call.call_id,
    )
    return SnapshotAsOfResult(
        call_id=call.call_id,
        tool_name=ToolName.READ_SNAPSHOT_AS_OF,
        status=ToolOutcomeStatus.ERROR,
        error=failure,
    )


def test_real_executor_runs_all_three_tools_and_is_byte_deterministic(
    committed_registry: CallableToolRegistry,
) -> None:
    request = _request(requested_as_of=None)
    plan = _plan(EvidenceRoute.DOCUMENTS_AND_DATA, request)
    planner = ScriptedPlanner(
        planner_id="executor-real-scripted-planner-v1",
        script_id="executor-real-script-001",
        route_plan=plan,
    )

    first = _execute(planner=planner, registry=committed_registry, request=request)
    second = _execute(planner=planner, registry=committed_registry, request=request)

    stes_cutoff = date(2026, 7, 9)
    stes_request = _request(
        requested_as_of=stes_cutoff,
        effective_as_of=stes_cutoff,
    )
    stes_plan = _plan(
        EvidenceRoute.DATA,
        stes_request,
        calls=(_stes_call(stes_request),),
    )
    stes_trace = _execute(
        planner=ScriptedPlanner(
            planner_id="executor-real-stes-planner-v1",
            script_id="executor-real-stes-script-001",
            route_plan=stes_plan,
        ),
        registry=committed_registry,
        request=stes_request,
        trace_id="executor-trace-stes-001",
    )

    assert first == second
    assert first is not second
    assert first.model_dump_json(warnings="error") == second.model_dump_json(warnings="error")
    assert first.status is TraceStatus.COMPLETE
    assert tuple(result.tool_name for result in first.tool_results) == (
        ToolName.RETRIEVE_TEMPORAL_DOCUMENTS,
        ToolName.READ_SNAPSHOT_AS_OF,
    )
    assert first.tool_results[1].payload.observation.raw_value == "596692.8"
    assert stes_trace.status is TraceStatus.COMPLETE
    assert stes_trace.tool_results[0].tool_name is ToolName.RESOLVE_STES_AS_OF
    assert stes_trace.tool_results[0].payload.selected_edition == "202607"
    assert stes_trace.tool_results[0].payload.observation.raw_value == "102.66"
    assert first.environment.tool_registry_id == committed_registry.provenance().tool_registry_id
    assert first.environment.artifact_registry_sha256 == (
        committed_registry.provenance().artifact_registry_sha256
    )
    assert first.environment.retrieval_corpus_sha256 == (
        committed_registry.provenance().retrieval_corpus_sha256
    )
    assert first.environment.executor_id == "sovereignlab-offline-executor-v1"
    assert first.environment.executor_sha256 == executor_module._executor_descriptor_sha256()
    assert (
        ExecutionTrace.model_validate_json(
            first.model_dump_json(warnings="error"),
            strict=True,
        )
        == first
    )


@pytest.mark.parametrize(
    ("language", "question", "requested_as_of"),
    [
        (
            "ko",
            "GDP 성장 전망의 상향 배경은 수출과 내수 중 무엇인가?",
            date(2024, 5, 31),
        ),
        ("en", QUESTION_EN, None),
    ],
)
def test_real_bilingual_document_execution_excludes_post_cutoff_sources(
    language: str,
    question: str,
    requested_as_of: date | None,
    committed_registry: CallableToolRegistry,
) -> None:
    cutoff = date(2024, 5, 31)
    request = _request(
        language=language,
        question=question,
        requested_as_of=requested_as_of,
        effective_as_of=cutoff,
    )
    plan = _plan(EvidenceRoute.DOCUMENTS, request)
    trace = _execute(
        planner=ScriptedPlanner(
            planner_id=f"executor-real-{language}-documents-planner-v1",
            script_id=f"executor-real-{language}-documents-script-001",
            route_plan=plan,
        ),
        registry=committed_registry,
        request=request,
        trace_id=f"executor-trace-{language}-documents-001",
    )

    assert trace.status is TraceStatus.COMPLETE
    assert trace.evidence_packet is not None
    assert {document.source_id for document in trace.evidence_packet.documents} == {
        f"synthetic-outlook-2024-05-{language}"
    }
    assert "2024-08" not in trace.model_dump_json(warnings="error")


@pytest.mark.parametrize(
    "route",
    [EvidenceRoute.DOCUMENTS, EvidenceRoute.DATA, EvidenceRoute.DOCUMENTS_AND_DATA],
)
def test_complete_routes_preserve_planned_order_and_call_once(
    route: EvidenceRoute,
    committed_registry: CallableToolRegistry,
    isolated_environment: ExecutionEnvironmentProvenance,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    request = _request()
    plan = _plan(route, request)
    planner = _FakePlanner(plan=plan)
    real_results = {
        call.call_id: executor_module.dispatch_tool_call(call=call, registry=committed_registry)
        for call in plan.tool_calls
    }
    observed: list[str] = []

    def dispatch(*, call: Any, registry: object) -> Any:
        assert registry is None
        observed.append(call.call_id)
        return real_results[call.call_id].model_copy(deep=True)

    monkeypatch.setattr(executor_module, "dispatch_tool_call", dispatch)

    trace = _execute(planner=planner, request=request)

    assert trace.status is TraceStatus.COMPLETE
    assert planner.calls == 1
    assert observed == [call.call_id for call in plan.tool_calls]
    assert tuple(result.call_id for result in trace.tool_results) == tuple(observed)
    assert trace.evidence_packet is not None
    assert trace.evidence_packet.status is PacketStatus.COMPLETE


@pytest.mark.parametrize("language", ["ko", "en"])
def test_planned_abstention_is_bilingual_and_never_dispatches(
    language: str,
    isolated_environment: ExecutionEnvironmentProvenance,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    request = _request(language=language, requested_as_of=None)
    plan = _plan(EvidenceRoute.ABSTAIN, request)
    planner = _FakePlanner(plan=plan)
    monkeypatch.setattr(
        executor_module,
        "dispatch_tool_call",
        lambda **kwargs: pytest.fail("planned abstention must not dispatch"),
    )

    trace = _execute(planner=planner, request=request)

    assert trace.status is TraceStatus.ABSTAINED
    assert trace.tool_results == ()
    assert trace.evidence_packet is not None
    assert trace.evidence_packet.documents == ()
    assert trace.evidence_packet.observations == ()
    assert trace.evidence_packet.abstention.reason_code == plan.abstention.reason_code
    assert trace.evidence_packet.abstention.message == plan.abstention.message


def test_tool_abstention_stops_after_successful_prefix_and_hides_partial_evidence(
    committed_registry: CallableToolRegistry,
    isolated_environment: ExecutionEnvironmentProvenance,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    request = _request()
    calls = (_document_call(request), _snapshot_call(request), _stes_call(request))
    plan = _plan(EvidenceRoute.DOCUMENTS_AND_DATA, request, calls=calls)
    document_result = executor_module.dispatch_tool_call(
        call=calls[0],
        registry=committed_registry,
    )
    observed: list[str] = []

    def dispatch(*, call: Any, registry: object) -> Any:
        observed.append(call.call_id)
        if call.call_id == calls[0].call_id:
            return document_result.model_copy(deep=True)
        return _tool_abstention(calls[1])

    monkeypatch.setattr(executor_module, "dispatch_tool_call", dispatch)

    trace = _execute(planner=_FakePlanner(plan=plan), request=request)

    assert observed == [calls[0].call_id, calls[1].call_id]
    assert trace.status is TraceStatus.ABSTAINED
    assert tuple(result.status for result in trace.tool_results) == (
        ToolOutcomeStatus.SUCCESS,
        ToolOutcomeStatus.ABSTAINED,
    )
    assert trace.evidence_packet is not None
    assert trace.evidence_packet.documents == ()
    assert trace.evidence_packet.observations == ()
    assert trace.evidence_packet.abstention.origin_call_id == calls[1].call_id


def test_typed_tool_error_stops_and_skips_assembler(
    isolated_environment: ExecutionEnvironmentProvenance,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    request = _request()
    calls = (_snapshot_call(request), _stes_call(request))
    plan = _plan(EvidenceRoute.DATA, request, calls=calls)
    monkeypatch.setattr(
        executor_module,
        "dispatch_tool_call",
        lambda **kwargs: _tool_error(calls[0]),
    )
    monkeypatch.setattr(
        executor_module,
        "_assemble_evidence_packet",
        lambda **kwargs: pytest.fail("tool error must not be assembled"),
    )

    trace = _execute(planner=_FakePlanner(plan=plan), request=request)

    assert trace.status is TraceStatus.FAILED
    assert len(trace.tool_results) == 1
    assert trace.failure == trace.tool_results[0].error
    assert trace.failure.phase is FailurePhase.TOOL_EXECUTION
    assert trace.evidence_packet is None


def test_tool_error_after_successful_prefix_stops_and_skips_assembler(
    committed_registry: CallableToolRegistry,
    isolated_environment: ExecutionEnvironmentProvenance,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    request = _request()
    calls = (_document_call(request), _snapshot_call(request), _stes_call(request))
    plan = _plan(EvidenceRoute.DOCUMENTS_AND_DATA, request, calls=calls)
    document_result = executor_module.dispatch_tool_call(
        call=calls[0],
        registry=committed_registry,
    )
    observed: list[str] = []

    def dispatch(*, call: Any, registry: object) -> Any:
        observed.append(call.call_id)
        if call.call_id == calls[0].call_id:
            return document_result.model_copy(deep=True)
        if call.call_id == calls[1].call_id:
            return _tool_error(calls[1])
        pytest.fail("execution continued after a terminal tool error")

    monkeypatch.setattr(executor_module, "dispatch_tool_call", dispatch)
    monkeypatch.setattr(
        executor_module,
        "_assemble_evidence_packet",
        lambda **kwargs: pytest.fail("tool error must not be assembled"),
    )

    trace = _execute(planner=_FakePlanner(plan=plan), request=request)

    assert observed == [calls[0].call_id, calls[1].call_id]
    assert tuple(result.status for result in trace.tool_results) == (
        ToolOutcomeStatus.SUCCESS,
        ToolOutcomeStatus.ERROR,
    )
    assert trace.status is TraceStatus.FAILED
    assert trace.failure == trace.tool_results[-1].error
    assert trace.evidence_packet is None


@pytest.mark.parametrize(
    ("failure_kind", "expected_code", "expected_message"),
    [
        (
            "known",
            "tool_registry_misconfigured",
            "The frozen callable tool registry is misconfigured.",
        ),
        (
            "unknown",
            "tool_dispatch_failed",
            "The deterministic tool dispatcher failed safely.",
        ),
        (
            "unexpected",
            "tool_dispatch_failed",
            "The deterministic tool dispatcher failed unexpectedly.",
        ),
    ],
)
def test_dispatch_exceptions_become_sanitized_typed_failures(
    failure_kind: str,
    expected_code: str,
    expected_message: str,
    isolated_environment: ExecutionEnvironmentProvenance,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    request = _request()
    plan = _plan(EvidenceRoute.DATA, request)
    secret = r"C:\private\provider.json raw=999"

    def fail(**kwargs: object) -> None:
        if failure_kind == "unexpected":
            raise RuntimeError(secret)
        code = "tool_registry_misconfigured" if failure_kind == "known" else "provider_raw"
        raise ToolDispatchError(code, secret)

    monkeypatch.setattr(executor_module, "dispatch_tool_call", fail)

    trace = _execute(planner=_FakePlanner(plan=plan), request=request)

    assert trace.status is TraceStatus.FAILED
    assert trace.failure.phase is FailurePhase.TOOL_EXECUTION
    assert trace.failure.code == expected_code
    assert trace.failure.message == expected_message
    assert trace.failure == trace.tool_results[-1].error
    assert secret not in trace.model_dump_json()


def test_invalid_or_mutated_dispatch_result_becomes_terminal_tool_error(
    isolated_environment: ExecutionEnvironmentProvenance,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    request = _request()
    plan = _plan(EvidenceRoute.DATA, request)
    monkeypatch.setattr(executor_module, "dispatch_tool_call", lambda **kwargs: object())

    trace = _execute(planner=_FakePlanner(plan=plan), request=request)

    assert trace.status is TraceStatus.FAILED
    assert trace.failure.code == "tool_result_invalid"
    assert trace.tool_results[-1].status is ToolOutcomeStatus.ERROR


def test_dispatcher_call_mutation_becomes_terminal_tool_error(
    isolated_environment: ExecutionEnvironmentProvenance,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    request = _request()
    call = _snapshot_call(request)
    plan = _plan(EvidenceRoute.DATA, request, calls=(call,))

    def mutate(*, call: SnapshotAsOfCall, registry: object) -> object:
        object.__setattr__(call, "call_id", "executor-mutated-call")
        return object()

    monkeypatch.setattr(executor_module, "dispatch_tool_call", mutate)

    trace = _execute(planner=_FakePlanner(plan=plan), request=request)

    assert trace.status is TraceStatus.FAILED
    assert trace.failure.code == "tool_result_invalid"
    assert trace.failure.call_id == "executor-call-snapshot"


@pytest.mark.parametrize("typed", [False, True])
def test_dispatcher_call_mutation_before_exception_uses_planned_call(
    typed: bool,
    isolated_environment: ExecutionEnvironmentProvenance,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    request = _request()
    planned_call = _snapshot_call(request)
    plan = _plan(EvidenceRoute.DATA, request, calls=(planned_call,))
    secret = r"C:\private\provider.json raw=999"

    def mutate_and_fail(*, call: SnapshotAsOfCall, registry: object) -> None:
        object.__setattr__(call, "call_id", "executor-mutated-call")
        if typed:
            raise ToolDispatchError("tool_registry_misconfigured", secret)
        raise RuntimeError(secret)

    monkeypatch.setattr(executor_module, "dispatch_tool_call", mutate_and_fail)

    trace = _execute(planner=_FakePlanner(plan=plan), request=request)

    assert trace.status is TraceStatus.FAILED
    assert trace.failure.code == "tool_result_invalid"
    assert trace.failure.call_id == planned_call.call_id
    assert trace.tool_results[-1].call_id == planned_call.call_id
    assert secret not in trace.model_dump_json(warnings="error")


def test_post_dispatch_environment_drift_is_rejected_privately(
    committed_registry: CallableToolRegistry,
    isolated_environment: ExecutionEnvironmentProvenance,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    request = _request()
    plan = _plan(EvidenceRoute.DATA, request)
    result = executor_module.dispatch_tool_call(
        call=plan.tool_calls[0],
        registry=committed_registry,
    )
    calls = 0

    def require_stable(**kwargs: object) -> None:
        nonlocal calls
        calls += 1
        if calls == 2:
            raise executor_module._OfflineExecutorError(
                "execution_environment_drift",
                "The environment drifted safely.",
            )

    monkeypatch.setattr(executor_module, "_require_stable_environment", require_stable)
    monkeypatch.setattr(
        executor_module,
        "dispatch_tool_call",
        lambda **kwargs: result.model_copy(deep=True),
    )

    with pytest.raises(executor_module._OfflineExecutorError) as exc_info:
        _execute(planner=_FakePlanner(plan=plan), request=request)

    assert exc_info.value.code == "execution_environment_drift"


@pytest.mark.parametrize("planned_abstention", [False, True])
def test_packet_assembly_failure_returns_failed_trace_without_evidence(
    planned_abstention: bool,
    committed_registry: CallableToolRegistry,
    isolated_environment: ExecutionEnvironmentProvenance,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    request = _request()
    route = EvidenceRoute.ABSTAIN if planned_abstention else EvidenceRoute.DATA
    plan = _plan(route, request)
    if not planned_abstention:
        result = executor_module.dispatch_tool_call(
            call=plan.tool_calls[0],
            registry=committed_registry,
        )
        monkeypatch.setattr(
            executor_module,
            "dispatch_tool_call",
            lambda **kwargs: result.model_copy(deep=True),
        )

    def fail(**kwargs: object) -> None:
        raise executor_module._PacketAssemblyError(
            "packet_validation_failed",
            r"C:\private\packet.json raw=999",
        )

    monkeypatch.setattr(executor_module, "_assemble_evidence_packet", fail)

    trace = _execute(planner=_FakePlanner(plan=plan), request=request)

    assert trace.status is TraceStatus.FAILED
    assert trace.failure.phase is FailurePhase.PACKET_ASSEMBLY
    assert trace.failure.code == "packet_validation_failed"
    assert trace.failure.message == "The evidence packet could not be assembled safely."
    assert "private" not in trace.model_dump_json(warnings="error")
    assert trace.evidence_packet is None
    assert all(result.status is ToolOutcomeStatus.SUCCESS for result in trace.tool_results)


def test_tool_abstention_assembly_fault_is_private_and_exposes_no_trace(
    isolated_environment: ExecutionEnvironmentProvenance,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    request = _request()
    call = _snapshot_call(request)
    plan = _plan(EvidenceRoute.DATA, request, calls=(call,))
    monkeypatch.setattr(
        executor_module,
        "dispatch_tool_call",
        lambda **kwargs: _tool_abstention(call),
    )
    monkeypatch.setattr(
        executor_module,
        "_assemble_evidence_packet",
        lambda **kwargs: (_ for _ in ()).throw(
            executor_module._PacketAssemblyError("packet-invalid", "Packet failed safely.")
        ),
    )

    with pytest.raises(executor_module._OfflineExecutorError) as exc_info:
        _execute(planner=_FakePlanner(plan=plan), request=request)

    assert exc_info.value.code == "untraceable_packet_assembly_failure"


@pytest.mark.parametrize(
    ("error", "expected_phase", "expected_code", "expected_message"),
    [
        (
            PlannerError(
                "plan_validation_failed",
                r"C:\private\planner-candidate.json raw=999",
                provenance=_provenance(),
            ),
            FailurePhase.PLAN_VALIDATION,
            "plan_validation_failed",
            "The planner candidate did not validate against the execution request.",
        ),
        (
            PlannerError(
                "recording_integrity_failed",
                r"C:\private\planner-recording.json raw=999",
                provenance=_provenance(),
            ),
            FailurePhase.PLANNER,
            "recording_integrity_failed",
            "The immutable planner recording failed its integrity check.",
        ),
        (
            PlannerError(
                "provider_raw",
                r"C:\private\planner-provider.json raw=999",
                provenance=_provenance(),
            ),
            FailurePhase.PLANNER,
            "planner_failed",
            "The offline planner failed safely.",
        ),
        (
            RuntimeError(r"C:\private\planner.json raw=999"),
            FailurePhase.PLANNER,
            "planner_failed",
            "The offline planner failed unexpectedly.",
        ),
    ],
)
def test_planner_failures_are_sanitized_and_have_no_execution_data(
    error: BaseException,
    expected_phase: FailurePhase,
    expected_code: str,
    expected_message: str,
    isolated_environment: ExecutionEnvironmentProvenance,
) -> None:
    planner = _FakePlanner(plan=object(), error=error)

    trace = _execute(planner=planner)

    assert trace.status is TraceStatus.FAILED
    assert trace.failure.phase is expected_phase
    assert trace.failure.code == expected_code
    assert trace.failure.message == expected_message
    assert trace.plan is None
    assert trace.tool_results == ()
    assert trace.evidence_packet is None
    assert "private" not in trace.model_dump_json(warnings="error")


@pytest.mark.parametrize(
    "error",
    [
        PlannerError(
            "recording_integrity_failed",
            r"C:\private\planner-recording.json raw=999",
            provenance=_provenance(),
        ),
        RuntimeError(r"C:\private\planner.json raw=999"),
    ],
)
def test_planner_request_mutation_with_failure_maps_to_planner_result_invalid(
    error: BaseException,
    isolated_environment: ExecutionEnvironmentProvenance,
) -> None:
    trace = _execute(
        planner=_FakePlanner(
            plan=object(),
            error=error,
            mutate_request=True,
        )
    )

    assert trace.status is TraceStatus.FAILED
    assert trace.failure.phase is FailurePhase.PLANNER
    assert trace.failure.code == "planner_result_invalid"
    assert trace.failure.message == (
        "The planner result did not validate against the execution request."
    )
    assert trace.plan is None
    assert trace.tool_results == ()
    assert trace.evidence_packet is None
    assert "private" not in trace.model_dump_json(warnings="error")


def test_digestless_plan_validation_failure_is_rejected_privately(
    isolated_environment: ExecutionEnvironmentProvenance,
) -> None:
    provenance = _provenance(digest_linked=False)
    error = PlannerError(
        "plan_validation_failed",
        "Candidate plan failed safely.",
        provenance=provenance,
    )

    with pytest.raises(executor_module._OfflineExecutorError) as exc_info:
        _execute(planner=_FakePlanner(plan=object(), provenance=provenance, error=error))

    assert exc_info.value.code == "invalid_planner_provenance"


@pytest.mark.parametrize("invalid_kind", ["raw", "mutated", "request_mutated"])
def test_invalid_planner_results_map_to_existing_failure_phases(
    invalid_kind: str,
    isolated_environment: ExecutionEnvironmentProvenance,
) -> None:
    request = _request()
    if invalid_kind == "raw":
        candidate: object = {"route": "data"}
    else:
        candidate = _plan(EvidenceRoute.DATA, request).model_copy(deep=True)
        if invalid_kind == "mutated":
            object.__setattr__(candidate, "route", EvidenceRoute.DOCUMENTS)
    planner = _FakePlanner(
        plan=candidate,
        mutate_request=invalid_kind == "request_mutated",
    )

    trace = _execute(planner=planner, request=request)

    assert trace.status is TraceStatus.FAILED
    assert trace.failure.phase is FailurePhase.PLANNER
    assert trace.failure.code == "planner_result_invalid"
    assert trace.plan is None


def test_digestless_invalid_planner_result_maps_to_planner_failure(
    isolated_environment: ExecutionEnvironmentProvenance,
) -> None:
    provenance = _provenance(digest_linked=False)
    trace = _execute(
        planner=_FakePlanner(plan=object(), provenance=provenance),
    )

    assert trace.failure.phase is FailurePhase.PLANNER
    assert trace.failure.code == "planner_result_invalid"


@pytest.mark.parametrize(
    ("trace_id", "recorded_at"),
    [
        ("INVALID TRACE", RECORDED_AT),
        ("executor-trace-001", datetime(2026, 8, 11, 12, 0)),
        (
            "executor-trace-001",
            datetime(2026, 8, 11, 12, 0, tzinfo=timezone(timedelta(hours=9))),
        ),
    ],
)
def test_invalid_trace_metadata_is_rejected_before_planning(
    trace_id: str,
    recorded_at: datetime,
    isolated_environment: ExecutionEnvironmentProvenance,
) -> None:
    planner = _FakePlanner(plan=_plan(EvidenceRoute.ABSTAIN, _request()))

    with pytest.raises(executor_module._OfflineExecutorError) as exc_info:
        _execute(planner=planner, trace_id=trace_id, recorded_at=recorded_at)

    assert exc_info.value.code == "invalid_trace_metadata"
    assert planner.calls == 0


def test_request_must_be_an_exact_unchanged_model() -> None:
    with pytest.raises(executor_module._OfflineExecutorError, match="exact validated"):
        executor_module._validated_request({"request_id": "raw"})

    request = _request().model_copy(deep=True)
    object.__setattr__(request, "effective_as_of", date(2026, 7, 18))
    with pytest.raises(executor_module._OfflineExecutorError) as exc_info:
        executor_module._validated_request(request)
    assert exc_info.value.code == "invalid_request"
    assert not executor_module._planner_request_is_stable(
        candidate=object(),
        expected=_request(),
    )


def test_planner_and_provenance_must_implement_exact_fresh_boundary() -> None:
    assert isinstance(_FakePlanner(plan=object()), Planner)
    with pytest.raises(executor_module._OfflineExecutorError) as wrong_planner:
        executor_module._planner_provenance(object())
    assert wrong_planner.value.code == "invalid_planner"

    with pytest.raises(executor_module._OfflineExecutorError) as wrong_provenance:
        executor_module._validated_planner_provenance(object())
    assert wrong_provenance.value.code == "invalid_planner_provenance"

    with pytest.raises(executor_module._OfflineExecutorError) as property_failure:
        executor_module._planner_provenance(
            _FakePlanner(plan=object(), provenance=object()),
        )
    assert property_failure.value.code == "invalid_planner_provenance"


def test_stability_guards_reject_planner_and_environment_drift(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    planner = _FakePlanner(plan=object())
    with pytest.raises(executor_module._OfflineExecutorError) as planner_drift:
        executor_module._require_stable_planner(
            planner=planner,
            expected=_provenance(planner_id="different-planner-v1"),
        )
    assert planner_drift.value.code == "planner_provenance_drift"

    monkeypatch.setattr(
        executor_module,
        "_validated_environment",
        lambda registry: _environment(executor_sha256=SHA_B),
    )
    with pytest.raises(executor_module._OfflineExecutorError) as environment_drift:
        executor_module._require_stable_environment(
            registry=object(),
            expected=_environment(),
        )
    assert environment_drift.value.code == "execution_environment_drift"


def test_registry_and_environment_provenance_are_exact(
    committed_registry: CallableToolRegistry,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    provenance = executor_module._validated_registry_provenance(committed_registry)
    environment = executor_module._validated_environment(committed_registry)
    assert environment.tool_registry_id == provenance.tool_registry_id
    assert environment.tool_registry_sha256 == provenance.tool_registry_sha256
    assert environment.artifact_registry_id == provenance.artifact_registry_id
    assert environment.retrieval_corpus_sha256 == provenance.retrieval_corpus_sha256

    with pytest.raises(executor_module._OfflineExecutorError) as wrong_registry:
        executor_module._validated_registry_provenance(object())
    assert wrong_registry.value.code == "invalid_execution_environment"

    monkeypatch.setattr(
        CallableToolRegistry,
        "provenance",
        lambda self: object(),
    )
    with pytest.raises(executor_module._OfflineExecutorError) as wrong_output:
        executor_module._validated_registry_provenance(committed_registry)
    assert wrong_output.value.code == "invalid_execution_environment"


def test_plan_call_and_result_strict_revalidation(
    committed_registry: CallableToolRegistry,
) -> None:
    request = _request()
    plan = _plan(EvidenceRoute.DATA, request)
    rebuilt_plan = executor_module._validated_plan(plan, request)
    call = executor_module._validated_call_copy(rebuilt_plan.tool_calls[0])
    result = executor_module.dispatch_tool_call(call=call, registry=committed_registry)
    rebuilt_result = executor_module._validated_result(call, result)

    assert rebuilt_plan == plan and rebuilt_plan is not plan
    assert call == plan.tool_calls[0] and call is not plan.tool_calls[0]
    assert rebuilt_result == result and rebuilt_result is not result

    with pytest.raises(executor_module._OfflineExecutorError) as wrong_plan:
        executor_module._validated_plan(object(), request)
    assert wrong_plan.value.code == "invalid_route_plan"

    with pytest.raises(executor_module._OfflineExecutorError) as wrong_call:
        executor_module._validated_call_copy(object())
    assert wrong_call.value.code == "invalid_tool_call"

    with pytest.raises(executor_module._OfflineExecutorError) as wrong_result:
        executor_module._validated_result(call, object())
    assert wrong_result.value.code == "invalid_tool_result"


@pytest.mark.parametrize("kind", ["cutoff", "question", "language"])
def test_executor_plan_revalidation_rejects_request_binding_drift(kind: str) -> None:
    request = _request()
    if kind == "cutoff":
        call = _snapshot_call(request).model_copy(deep=True)
        arguments = call.arguments.model_copy(update={"as_of": date(2026, 7, 16)})
    else:
        call = _document_call(request).model_copy(deep=True)
        arguments = call.arguments.model_copy(
            update={
                "question": "This is a different question."
                if kind == "question"
                else call.arguments.question,
                "language": "ko" if kind == "language" else call.arguments.language,
            }
        )
    object.__setattr__(call, "arguments", arguments)
    route = EvidenceRoute.DATA if kind == "cutoff" else EvidenceRoute.DOCUMENTS
    plan = RoutePlan(route=route, tool_calls=(call,))

    with pytest.raises(executor_module._OfflineExecutorError) as exc_info:
        executor_module._validated_plan(plan, request)

    assert exc_info.value.code == "invalid_route_plan"


@pytest.mark.parametrize(
    "call",
    [_document_call(_request()), _stes_call(_request()), _snapshot_call(_request())],
)
def test_dispatch_exception_mapping_supports_each_exact_call(call: Any) -> None:
    result = executor_module._tool_error_result(
        call,
        code="tool_dispatch_failed",
        message="The tool failed safely.",
    )
    assert result.call_id == call.call_id
    assert result.tool_name is call.tool_name
    assert result.status is ToolOutcomeStatus.ERROR
    assert result.error.call_id == call.call_id


def test_invalid_tool_failure_mapping_is_private() -> None:
    with pytest.raises(executor_module._OfflineExecutorError) as wrong_call:
        executor_module._tool_error_result(
            object(),  # type: ignore[arg-type]
            code="tool-failed",
            message="The tool failed safely.",
        )
    assert wrong_call.value.code == "tool_failure_mapping_failed"

    with pytest.raises(executor_module._OfflineExecutorError) as invalid_code:
        executor_module._tool_error_result(
            _snapshot_call(_request()),
            code="INVALID CODE",
            message="The tool failed safely.",
        )
    assert invalid_code.value.code == "tool_failure_mapping_failed"


def test_packet_and_trace_helpers_return_fresh_strict_models(
    committed_registry: CallableToolRegistry,
) -> None:
    request = _request()
    plan = _plan(EvidenceRoute.DATA, request)
    result = executor_module.dispatch_tool_call(
        call=plan.tool_calls[0],
        registry=committed_registry,
    )
    packet = executor_module._assemble_packet(
        request=request,
        plan=plan,
        tool_results=(result,),
    )
    rebuilt_packet = executor_module._validated_packet(packet)
    trace = executor_module._trace(
        trace_id="executor-helper-trace",
        recorded_at=RECORDED_AT,
        request=request,
        environment=_environment(),
        planner=_provenance(),
        status=TraceStatus.COMPLETE,
        plan=plan,
        tool_results=(result,),
        evidence_packet=packet,
    )
    rebuilt_trace = executor_module._validated_trace(trace)

    assert rebuilt_packet == packet and rebuilt_packet is not packet
    assert rebuilt_trace == trace and rebuilt_trace is not trace

    with pytest.raises(executor_module._PacketAssemblyError) as wrong_packet:
        executor_module._validated_packet(object())
    assert wrong_packet.value.code == "packet_validation_failed"

    with pytest.raises(executor_module._OfflineExecutorError) as wrong_trace:
        executor_module._validated_trace(object())
    assert wrong_trace.value.code == "trace_validation_failed"


def test_trace_and_failure_mapping_helpers_sanitize_invalid_models() -> None:
    request = _request()
    with pytest.raises(executor_module._OfflineExecutorError) as invalid_trace:
        executor_module._trace(
            trace_id="INVALID TRACE",
            recorded_at=RECORDED_AT,
            request=request,
            environment=_environment(),
            planner=_provenance(),
            status=TraceStatus.FAILED,
            failure=ExecutionFailure(
                phase=FailurePhase.PLANNER,
                code="planner-failed",
                message="Planner failed safely.",
            ),
        )
    assert invalid_trace.value.code == "trace_validation_failed"

    with pytest.raises(executor_module._OfflineExecutorError) as planner_mapping:
        executor_module._planner_failure(
            trace_id="executor-helper-trace",
            recorded_at=RECORDED_AT,
            request=request,
            environment=_environment(),
            provenance=_provenance(),
            phase=FailurePhase.PLANNER,
            code="INVALID CODE",
            message="Planner failed safely.",
        )
    assert planner_mapping.value.code == "planner_failure_mapping_failed"

    packet_trace = executor_module._packet_failure_trace(
        trace_id="executor-helper-trace",
        recorded_at=RECORDED_AT,
        request=request,
        environment=_environment(),
        planner=_provenance(),
        plan=_plan(EvidenceRoute.ABSTAIN, request),
        tool_results=(),
        error=executor_module._PacketAssemblyError(
            "INVALID CODE",
            r"C:\private\packet.json raw=999",
        ),
    )
    assert packet_trace.failure.code == "packet_assembly_failed"
    assert packet_trace.failure.message == ("The evidence packet could not be assembled safely.")
    assert "private" not in packet_trace.model_dump_json(warnings="error")


def test_packet_failure_mapping_failure_is_private(monkeypatch: pytest.MonkeyPatch) -> None:
    request = _request()
    monkeypatch.setattr(
        executor_module,
        "_sanitized_packet_failure",
        lambda error: ("INVALID CODE", "Packet failed safely."),
    )

    with pytest.raises(executor_module._OfflineExecutorError) as exc_info:
        executor_module._packet_failure_trace(
            trace_id="executor-helper-trace",
            recorded_at=RECORDED_AT,
            request=request,
            environment=_environment(),
            planner=_provenance(),
            plan=_plan(EvidenceRoute.ABSTAIN, request),
            tool_results=(),
            error=executor_module._PacketAssemblyError(
                "packet_assembly_failed",
                "Packet failed safely.",
            ),
        )

    assert exc_info.value.code == "packet_failure_mapping_failed"


def test_typed_failure_sanitizers_reject_non_string_codes() -> None:
    secret = r"C:\private\typed-error.json raw=999"
    planner_error = PlannerError("recording_missing", secret)
    dispatch_error = ToolDispatchError("unknown_tool", secret)
    packet_error = executor_module._PacketAssemblyError("invalid_request", secret)
    for error in (planner_error, dispatch_error, packet_error):
        object.__setattr__(error, "code", object())

    planner_code, planner_message = executor_module._sanitized_planner_failure(planner_error)
    dispatch_code, dispatch_message = executor_module._sanitized_dispatch_failure(dispatch_error)
    packet_code, packet_message = executor_module._sanitized_packet_failure(packet_error)

    assert (planner_code, planner_message) == (
        "planner_failed",
        "The offline planner failed safely.",
    )
    assert (dispatch_code, dispatch_message) == (
        "tool_dispatch_failed",
        "The deterministic tool dispatcher failed safely.",
    )
    assert (packet_code, packet_message) == (
        "packet_assembly_failed",
        "The evidence packet could not be assembled safely.",
    )
    assert all(
        secret not in message for message in (planner_message, dispatch_message, packet_message)
    )


def test_generic_assembler_failure_is_sanitized(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    secret = r"C:\private\packet.json raw=999"
    monkeypatch.setattr(
        executor_module,
        "_assemble_evidence_packet",
        lambda **kwargs: (_ for _ in ()).throw(RuntimeError(secret)),
    )

    with pytest.raises(executor_module._PacketAssemblyError) as exc_info:
        executor_module._assemble_packet(
            request=_request(),
            plan=_plan(EvidenceRoute.ABSTAIN, _request()),
            tool_results=(),
        )

    assert exc_info.value.code == "packet_assembly_failed"
    assert secret not in str(exc_info.value)


def test_executor_descriptor_binds_canonical_source_tree_without_local_paths() -> None:
    descriptor_bytes = executor_module._canonical_executor_descriptor_bytes()
    descriptor = json.loads(descriptor_bytes)
    paths = tuple(item["path"] for item in descriptor["source_files"])

    assert descriptor["executor_id"] == "sovereignlab-offline-executor-v1"
    assert descriptor["execution_contract_version"] == "1.0.0"
    assert descriptor["tool_registry_id"] == "sovereignlab-deterministic-tool-registry-v1"
    assert "execution/executor.py" in paths
    assert "execution/dispatcher.py" in paths
    assert "execution/planner.py" in paths
    assert "execution/assembler.py" in paths
    assert "schemas/execution.py" in paths
    assert len(paths) == len(set(paths)) == 32
    assert str(REPOSITORY_ROOT).encode() not in descriptor_bytes
    assert executor_module._executor_descriptor_sha256() == (
        "08f45dab6a36a49cb7d0b588a69236942cd61534540bd4de0772010402dada64"
    )


def test_source_canonicalization_and_empty_descriptor_fail_closed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = tmp_path / "module.py"
    source.write_bytes(b"first\r\nsecond\rthird\n")
    assert executor_module._canonical_source_bytes(source) == b"first\nsecond\nthird\n"

    original_is_symlink = Path.is_symlink
    with monkeypatch.context() as patch:
        patch.setattr(
            Path,
            "is_symlink",
            lambda self: self == source or original_is_symlink(self),
        )
        with pytest.raises(ValueError, match="regular file"):
            executor_module._canonical_source_bytes(source)

    empty = tmp_path / "empty.py"
    empty.write_bytes(b"")
    with pytest.raises(ValueError, match="non-empty"):
        executor_module._canonical_source_bytes(empty)

    with pytest.raises(ValueError, match="regular file"):
        executor_module._canonical_source_bytes(tmp_path)

    empty_root = tmp_path / "empty-root"
    empty_root.mkdir()
    monkeypatch.setattr(executor_module, "_SOURCE_ROOT", empty_root)
    with pytest.raises(ValueError, match="incomplete"):
        executor_module._canonical_executor_descriptor_bytes()


def test_executor_descriptor_rejects_lexical_source_symlink(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source_root = tmp_path / "source-root"
    source_root.mkdir()
    source = source_root / "module.py"
    source.write_text("VALUE = 1\n", encoding="utf-8")
    original_is_symlink = Path.is_symlink
    monkeypatch.setattr(executor_module, "_SOURCE_ROOT", source_root)
    monkeypatch.setattr(
        Path,
        "is_symlink",
        lambda self: self == source or original_is_symlink(self),
    )

    with pytest.raises(ValueError, match="symbolic links"):
        executor_module._canonical_executor_descriptor_bytes()


def test_signature_exports_and_dependencies_keep_executor_private() -> None:
    signature = inspect.signature(executor_module._execute_offline_request)
    assert tuple(signature.parameters) == (
        "trace_id",
        "recorded_at",
        "request",
        "planner",
        "registry",
    )
    assert all(
        parameter.kind is inspect.Parameter.KEYWORD_ONLY
        for parameter in signature.parameters.values()
    )
    for public_name in (
        "execute_offline_request",
        "OfflineExecutor",
        "ExecutorResult",
        "ExecutorOutput",
    ):
        assert not hasattr(executor_module, public_name)
        assert public_name not in execution_package.__all__
    assert "_execute_offline_request" not in execution_package.__all__
    assert "_OfflineExecutorError" not in execution_package.__all__

    source = inspect.getsource(executor_module)
    for forbidden_dependency in (
        "mistralai",
        "httpx",
        "requests",
        "provider",
        "bounded_loop",
    ):
        assert forbidden_dependency not in source


def test_round_trip_drift_guards_reject_changed_models(
    committed_registry: CallableToolRegistry,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    request = _request()
    plan = _plan(EvidenceRoute.DATA, request)
    call = plan.tool_calls[0]
    result = executor_module.dispatch_tool_call(call=call, registry=committed_registry)
    packet = executor_module._assemble_packet(
        request=request,
        plan=plan,
        tool_results=(result,),
    )
    trace = executor_module._trace(
        trace_id="executor-round-trip-trace",
        recorded_at=RECORDED_AT,
        request=request,
        environment=_environment(),
        planner=_provenance(),
        status=TraceStatus.COMPLETE,
        plan=plan,
        tool_results=(result,),
        evidence_packet=packet,
    )

    changed_request = request.model_copy(update={"request_id": "executor-request-changed"})
    with monkeypatch.context() as patch:
        patch.setattr(
            ExecutionRequest,
            "model_validate_json",
            classmethod(lambda cls, *args, **kwargs: changed_request),
        )
        with pytest.raises(executor_module._OfflineExecutorError) as request_error:
            executor_module._validated_request(request)
        assert request_error.value.code == "invalid_request"

    changed_provenance = _provenance(planner_id="executor-planner-changed-v1")
    with monkeypatch.context() as patch:
        patch.setattr(
            PlannerProvenance,
            "model_validate_json",
            classmethod(lambda cls, *args, **kwargs: changed_provenance),
        )
        with pytest.raises(executor_module._OfflineExecutorError) as provenance_error:
            executor_module._validated_planner_provenance(_provenance())
        assert provenance_error.value.code == "invalid_planner_provenance"

    changed_plan = _plan(EvidenceRoute.ABSTAIN, request)
    with monkeypatch.context() as patch:
        patch.setattr(
            RoutePlan,
            "model_validate_json",
            classmethod(lambda cls, *args, **kwargs: changed_plan),
        )
        with pytest.raises(executor_module._OfflineExecutorError) as plan_error:
            executor_module._validated_plan(plan, request)
        assert plan_error.value.code == "invalid_route_plan"

    changed_call = call.model_copy(update={"call_id": "executor-call-changed"})
    with monkeypatch.context() as patch:
        patch.setattr(
            SnapshotAsOfCall,
            "model_validate_json",
            classmethod(lambda cls, *args, **kwargs: changed_call),
        )
        with pytest.raises(executor_module._OfflineExecutorError) as call_error:
            executor_module._validated_call_copy(call)
        assert call_error.value.code == "invalid_tool_call"

    changed_result = result.model_copy(update={"call_id": "executor-call-changed"})
    with monkeypatch.context() as patch:
        patch.setattr(
            SnapshotAsOfResult,
            "model_validate_json",
            classmethod(lambda cls, *args, **kwargs: changed_result),
        )
        with pytest.raises(executor_module._OfflineExecutorError) as result_error:
            executor_module._validated_result(call, result)
        assert result_error.value.code == "invalid_tool_result"

    changed_packet = packet.model_copy(
        update={"request": request.model_copy(update={"request_id": "packet-request-changed"})}
    )
    with monkeypatch.context() as patch:
        patch.setattr(
            ExecutionEvidencePacket,
            "model_validate_json",
            classmethod(lambda cls, *args, **kwargs: changed_packet),
        )
        with pytest.raises(executor_module._PacketAssemblyError) as packet_error:
            executor_module._validated_packet(packet)
        assert packet_error.value.code == "packet_validation_failed"

    changed_trace = trace.model_copy(update={"trace_id": "executor-trace-changed"})
    with monkeypatch.context() as patch:
        patch.setattr(
            ExecutionTrace,
            "model_validate_json",
            classmethod(lambda cls, *args, **kwargs: changed_trace),
        )
        with pytest.raises(executor_module._OfflineExecutorError) as trace_error:
            executor_module._validated_trace(trace)
        assert trace_error.value.code == "trace_validation_failed"


def test_environment_round_trip_and_internal_failures_are_sanitized(
    committed_registry: CallableToolRegistry,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with pytest.raises(executor_module._OfflineExecutorError) as propagated:
        executor_module._validated_environment(object())
    assert propagated.value.code == "invalid_execution_environment"

    with monkeypatch.context() as patch:
        patch.setattr(
            ExecutionEnvironmentProvenance,
            "model_validate_json",
            classmethod(lambda cls, *args, **kwargs: _environment(executor_sha256=SHA_B)),
        )
        with pytest.raises(executor_module._OfflineExecutorError) as changed:
            executor_module._validated_environment(committed_registry)
        assert changed.value.code == "invalid_execution_environment"

    secret = r"C:\private\executor-source.py raw=999"
    with monkeypatch.context() as patch:
        patch.setattr(
            executor_module,
            "_executor_descriptor_sha256",
            lambda: (_ for _ in ()).throw(RuntimeError(secret)),
        )
        with pytest.raises(executor_module._OfflineExecutorError) as internal:
            executor_module._validated_environment(committed_registry)
        assert internal.value.code == "invalid_execution_environment"
        assert secret not in str(internal.value)


def test_trace_metadata_rejects_non_string_identifier() -> None:
    with pytest.raises(executor_module._OfflineExecutorError) as exc_info:
        executor_module._validated_trace_metadata(
            trace_id=123,
            recorded_at=RECORDED_AT,
        )
    assert exc_info.value.code == "invalid_trace_metadata"


def test_planner_error_provenance_drift_is_private(
    isolated_environment: ExecutionEnvironmentProvenance,
) -> None:
    initial = _provenance()
    drifted = _provenance(planner_id="executor-drifted-planner-v1")
    error = PlannerError(
        "recording_integrity_failed",
        "Recording failed safely.",
        provenance=drifted,
    )

    with pytest.raises(executor_module._OfflineExecutorError) as exc_info:
        _execute(
            planner=_FakePlanner(
                plan=object(),
                provenance=initial,
                error=error,
            )
        )

    assert exc_info.value.code == "planner_provenance_drift"


def test_unexpected_planner_failure_mapping_is_private(
    isolated_environment: ExecutionEnvironmentProvenance,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    error = PlannerError(
        "recording_integrity_failed",
        "Recording failed safely.",
        provenance=_provenance(),
    )
    monkeypatch.setattr(
        executor_module,
        "_planner_failure",
        lambda **kwargs: (_ for _ in ()).throw(RuntimeError("private mapping detail")),
    )

    with pytest.raises(executor_module._OfflineExecutorError) as exc_info:
        _execute(planner=_FakePlanner(plan=object(), error=error))

    assert exc_info.value.code == "planner_failure_mapping_failed"
    assert "private mapping detail" not in str(exc_info.value)


def test_post_plan_provenance_failure_is_rethrown_privately(
    isolated_environment: ExecutionEnvironmentProvenance,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    request = _request()
    monkeypatch.setattr(
        executor_module,
        "_require_stable_planner",
        lambda **kwargs: (_ for _ in ()).throw(
            executor_module._OfflineExecutorError(
                "planner_provenance_drift",
                "Planner drifted safely.",
            )
        ),
    )

    with pytest.raises(executor_module._OfflineExecutorError) as exc_info:
        _execute(
            planner=_FakePlanner(plan=_plan(EvidenceRoute.DATA, request)),
            request=request,
        )

    assert exc_info.value.code == "planner_provenance_drift"


def test_defensive_terminal_error_requires_failure_metadata(
    isolated_environment: ExecutionEnvironmentProvenance,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    request = _request()
    call = _snapshot_call(request)
    missing_failure = _tool_error(call).model_copy(deep=True)
    object.__setattr__(missing_failure, "error", None)
    monkeypatch.setattr(executor_module, "dispatch_tool_call", lambda **kwargs: object())
    monkeypatch.setattr(
        executor_module,
        "_validated_result",
        lambda call, result: missing_failure,
    )

    with pytest.raises(executor_module._OfflineExecutorError) as exc_info:
        _execute(
            planner=_FakePlanner(plan=_plan(EvidenceRoute.DATA, request, calls=(call,))),
            request=request,
        )

    assert exc_info.value.code == "tool_failure_mapping_failed"


def test_unknown_call_like_object_reaches_defensive_mapping_branch() -> None:
    class CallLike:
        call_id = "executor-call-like"

    with pytest.raises(executor_module._OfflineExecutorError) as exc_info:
        executor_module._tool_error_result(
            CallLike(),  # type: ignore[arg-type]
            code="tool-failed",
            message="The tool failed safely.",
        )

    assert exc_info.value.code == "tool_failure_mapping_failed"


def test_public_schema_count_remains_thirteen() -> None:
    assert len(tuple((REPOSITORY_ROOT / "data" / "schemas").glob("*.schema.json"))) == 13
