"""Behaviour of the dispatcher, planners, packet assembler, and offline executor."""

import hashlib
from dataclasses import replace
from datetime import UTC, date, datetime

import pytest

from sovereignlab.execution import (
    CallableToolRegistry,
    PlannerError,
    RecordedPlanner,
    ScriptedPlanner,
    dispatch_tool_call,
    execute_offline_request,
    executor_sha256,
)
from sovereignlab.retrieval import TEMPORAL_CORPUS_DESCRIPTOR_SHA256
from sovereignlab.schemas import (
    AbstentionOrigin,
    EvidenceRoute,
    ExecutionRequest,
    ExecutionTrace,
    FailurePhase,
    LanguageCode,
    PacketStatus,
    PlanAbstention,
    PlannerMode,
    RoutePlan,
    SnapshotAsOfArguments,
    SnapshotAsOfCall,
    SnapshotAsOfResult,
    StesAsOfArguments,
    StesAsOfCall,
    StesAsOfResult,
    TemporalDocumentArguments,
    TemporalDocumentCall,
    TemporalDocumentResult,
    ToolOutcomeStatus,
    TraceStatus,
)
from sovereignlab.snapshots import SnapshotRegistry

RECORDED_AT = datetime(2026, 8, 11, 6, 0, tzinfo=UTC)
CAPTURE_DAY = date(2026, 7, 17)
STES_DAY = date(2026, 7, 9)


def _request(as_of: date = CAPTURE_DAY) -> ExecutionRequest:
    return ExecutionRequest(
        request_id="request-01",
        question="Why was the growth outlook revised upward?",
        language=LanguageCode.ENGLISH,
        requested_as_of=as_of,
        effective_as_of=as_of,
    )


def _document_call(request: ExecutionRequest) -> TemporalDocumentCall:
    return TemporalDocumentCall(
        call_id="call-documents",
        tool_name="retrieve_temporal_documents",
        arguments=TemporalDocumentArguments(
            question=request.question,
            language=request.language,
            as_of=request.effective_as_of,
        ),
    )


def _snapshot_call(request: ExecutionRequest) -> SnapshotAsOfCall:
    return SnapshotAsOfCall(
        call_id="call-snapshot",
        tool_name="read_snapshot_as_of",
        arguments=SnapshotAsOfArguments(
            source_system="ecos",
            table_id="200Y108",
            item_id="10601",
            period="2026Q1",
            as_of=request.effective_as_of,
            normalization_rule_id="ecos-200y108-10601-billion-krw-v1",
        ),
    )


def _stes_call(request: ExecutionRequest) -> StesAsOfCall:
    return StesAsOfCall(
        call_id="call-stes",
        tool_name="resolve_stes_as_of",
        arguments=StesAsOfArguments(
            ref_area="KOR",
            freq="M",
            measure="LI_AA",
            unit_measure="IX",
            activity="_T",
            period="2026-05",
            as_of=request.effective_as_of,
            normalization_rule_id="oecd-stes-kor-li-aa-index-v1",
        ),
    )


def _scripted(plan: RoutePlan) -> ScriptedPlanner:
    return ScriptedPlanner(planner_id="test-planner", script_id="test-script", route_plan=plan)


def _execute(
    registry: CallableToolRegistry,
    request: ExecutionRequest,
    planner: ScriptedPlanner | RecordedPlanner,
) -> ExecutionTrace:
    return execute_offline_request(
        trace_id="trace-01",
        recorded_at=RECORDED_AT,
        request=request,
        planner=planner,
        registry=registry,
    )


def _without_snapshots(registry: CallableToolRegistry) -> CallableToolRegistry:
    """A registry whose snapshot tool fails unexpectedly: it has no series at all."""

    empty = SnapshotRegistry(registry_id="empty", entries=(), catalog_artifacts=())
    return replace(registry, snapshot_registry=empty)


# --- dispatcher ---------------------------------------------------------------------------


def test_dispatch_runs_each_call_type_against_its_tool(tool_registry: CallableToolRegistry) -> None:
    documents = dispatch_tool_call(call=_document_call(_request()), registry=tool_registry)
    snapshot = dispatch_tool_call(call=_snapshot_call(_request()), registry=tool_registry)
    stes = dispatch_tool_call(call=_stes_call(_request(STES_DAY)), registry=tool_registry)

    assert isinstance(documents, TemporalDocumentResult)
    assert isinstance(snapshot, SnapshotAsOfResult)
    assert isinstance(stes, StesAsOfResult)
    assert {result.status for result in (documents, snapshot, stes)} == {ToolOutcomeStatus.SUCCESS}
    assert snapshot.payload is not None and snapshot.payload.observation.raw_value == "596692.8"
    assert stes.payload is not None and stes.payload.observation.raw_value == "102.66"


def test_dispatch_reports_an_unexpected_tool_failure_as_an_error_result(
    tool_registry: CallableToolRegistry,
) -> None:
    call = _snapshot_call(_request())

    result = dispatch_tool_call(call=call, registry=_without_snapshots(tool_registry))

    assert result.status is ToolOutcomeStatus.ERROR
    assert result.payload is None
    assert result.error is not None
    assert result.error.phase is FailurePhase.TOOL_EXECUTION
    assert result.error.code == "tool_dispatch_failed"
    assert result.error.call_id == call.call_id


def test_registry_provenance_names_the_three_pinned_evidence_sets(
    tool_registry: CallableToolRegistry,
) -> None:
    provenance = tool_registry.provenance()

    assert provenance.retrieval_corpus_sha256 == TEMPORAL_CORPUS_DESCRIPTOR_SHA256
    # These two digests are recorded in every committed trace.
    assert provenance.tool_registry_sha256 == (
        "cd00b5c543cffc53024f98b9fafa73ed3fecd519fde81a826d060c8af4d2ad91"
    )
    assert provenance.artifact_registry_sha256 == (
        "7b42027c1034789bd46a881fd186f66ba1ba1250d94639ff5eed6c89a3cc2293"
    )


# --- planners -----------------------------------------------------------------------------


def test_scripted_planner_returns_its_plan_with_digest_linked_provenance() -> None:
    request = _request()
    plan = RoutePlan(route=EvidenceRoute.DATA, tool_calls=(_snapshot_call(request),))
    planner = _scripted(plan)

    assert planner.plan(request) == plan
    provenance = planner.provenance
    assert provenance.mode is PlannerMode.SCRIPTED
    assert provenance.recording_id == "test-script"
    assert provenance.output_sha256 == hashlib.sha256(plan.model_dump_json().encode()).hexdigest()
    assert provenance.model_id is None


@pytest.mark.parametrize("mismatch", ["cutoff", "question"])
def test_planner_rejects_a_plan_that_is_not_bound_to_the_request(mismatch: str) -> None:
    request = _request()
    other = (
        _request(date(2026, 7, 18))
        if mismatch == "cutoff"
        else request.model_copy(update={"question": "What is the inflation outlook?"})
    )
    plan = RoutePlan(route=EvidenceRoute.DOCUMENTS, tool_calls=(_document_call(other),))

    with pytest.raises(PlannerError) as raised:
        _scripted(plan).plan(request)
    assert raised.value.code == "plan_validation_failed"


def test_recorded_planner_validates_a_model_response_offline() -> None:
    request = _request()
    plan = RoutePlan(route=EvidenceRoute.DATA, tool_calls=(_snapshot_call(request),))
    recorded = RecordedPlanner(
        planner_id="test-planner",
        recording_id="recording-01",
        model_id="example-model-2026",
        candidate_bytes=plan.model_dump_json().encode("utf-8"),
    )

    assert recorded.plan(request) == plan
    assert recorded.provenance.mode is PlannerMode.RECORDED
    assert recorded.provenance.model_id == "example-model-2026"
    assert replace(recorded, mode=PlannerMode.REPLAY).provenance.mode is PlannerMode.REPLAY


@pytest.mark.parametrize(
    "candidate",
    [
        b"not json",
        b'{"route": "data", "tool_calls": []}',
        b'{"route": "abstain", "abstention": {"reason_code": "none", "message": "x"}, "extra": 1}',
        b'{"route": "data", "tool_calls": [{"call_id": "call-01", "tool_name": "run_sql",'
        b' "arguments": {}}]}',
    ],
    ids=["not-json", "route-without-calls", "undeclared-field", "unknown-tool"],
)
def test_recorded_planner_rejects_an_invalid_model_response(candidate: bytes) -> None:
    recorded = RecordedPlanner(
        planner_id="test-planner",
        recording_id="recording-01",
        model_id="example-model-2026",
        candidate_bytes=candidate,
    )

    with pytest.raises(PlannerError) as raised:
        recorded.plan(_request())
    assert raised.value.code == "plan_validation_failed"


# --- executor and packet assembly ---------------------------------------------------------


def test_complete_execution_assembles_every_successful_result(
    tool_registry: CallableToolRegistry,
) -> None:
    request = _request()
    plan = RoutePlan(
        route=EvidenceRoute.DOCUMENTS_AND_DATA,
        tool_calls=(_document_call(request), _snapshot_call(request)),
    )

    trace = _execute(tool_registry, request, _scripted(plan))

    assert trace.status is TraceStatus.COMPLETE
    assert [result.status for result in trace.tool_results] == [ToolOutcomeStatus.SUCCESS] * 2
    packet = trace.evidence_packet
    assert packet is not None and packet.status is PacketStatus.COMPLETE
    assert packet.documents == trace.tool_results[0].payload.matches
    assert packet.observations == (trace.tool_results[1].payload,)
    assert trace.environment.executor_sha256 == executor_sha256()
    assert trace.planner == _scripted(plan).provenance
    assert ExecutionTrace.model_validate_json(trace.model_dump_json()) == trace


def test_planned_abstention_runs_no_tool(tool_registry: CallableToolRegistry) -> None:
    plan = RoutePlan(
        route=EvidenceRoute.ABSTAIN,
        abstention=PlanAbstention(reason_code="no-safe-route", message="No safe route."),
    )

    trace = _execute(tool_registry, _request(), _scripted(plan))

    assert trace.status is TraceStatus.ABSTAINED
    assert trace.tool_results == ()
    assert trace.evidence_packet is not None
    assert trace.evidence_packet.abstention is not None
    assert trace.evidence_packet.abstention.origin is AbstentionOrigin.PLAN
    assert trace.evidence_packet.abstention.reason_code == "no-safe-route"


def test_tool_abstention_stops_execution_and_exposes_no_partial_evidence(
    tool_registry: CallableToolRegistry,
) -> None:
    # One day before the snapshot capture: documents succeed, the snapshot tool abstains, and
    # the STES call planned after it must not run.
    request = _request(date(2026, 7, 16))
    plan = RoutePlan(
        route=EvidenceRoute.DOCUMENTS_AND_DATA,
        tool_calls=(_document_call(request), _snapshot_call(request), _stes_call(request)),
    )

    trace = _execute(tool_registry, request, _scripted(plan))

    assert trace.status is TraceStatus.ABSTAINED
    assert [result.status for result in trace.tool_results] == [
        ToolOutcomeStatus.SUCCESS,
        ToolOutcomeStatus.ABSTAINED,
    ]
    packet = trace.evidence_packet
    assert packet is not None and packet.status is PacketStatus.ABSTAINED
    assert packet.documents == () and packet.observations == ()
    assert packet.abstention is not None
    assert packet.abstention.origin is AbstentionOrigin.TOOL
    assert packet.abstention.origin_call_id == "call-snapshot"
    assert packet.abstention.reason_code == "no_snapshot_available_by_cutoff"


def test_invalid_recorded_plan_fails_at_plan_validation_without_running_tools(
    tool_registry: CallableToolRegistry,
) -> None:
    recorded = RecordedPlanner(
        planner_id="test-planner",
        recording_id="recording-01",
        model_id="example-model-2026",
        candidate_bytes=b'{"route": "data", "tool_calls": []}',
    )

    trace = _execute(tool_registry, _request(), recorded)

    assert trace.status is TraceStatus.FAILED
    assert trace.plan is None and trace.tool_results == () and trace.evidence_packet is None
    assert trace.failure is not None
    assert trace.failure.phase is FailurePhase.PLAN_VALIDATION
    assert trace.failure.code == "plan_validation_failed"
    assert trace.planner.output_sha256 == hashlib.sha256(recorded.candidate_bytes).hexdigest()


def test_tool_error_fails_the_trace_without_an_evidence_packet(
    tool_registry: CallableToolRegistry,
) -> None:
    request = _request()
    plan = RoutePlan(
        route=EvidenceRoute.DOCUMENTS_AND_DATA,
        tool_calls=(_document_call(request), _snapshot_call(request)),
    )

    trace = _execute(_without_snapshots(tool_registry), request, _scripted(plan))

    assert trace.status is TraceStatus.FAILED
    assert trace.evidence_packet is None
    assert [result.status for result in trace.tool_results] == [
        ToolOutcomeStatus.SUCCESS,
        ToolOutcomeStatus.ERROR,
    ]
    assert trace.failure == trace.tool_results[-1].error
    assert trace.failure is not None and trace.failure.phase is FailurePhase.TOOL_EXECUTION
