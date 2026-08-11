"""Write or check committed real-digest offline execution replay traces."""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from sovereignlab.execution import (  # noqa: E402
    CallableToolRegistry,
    ScriptedPlanner,
    load_committed_callable_tool_registry,
)
from sovereignlab.execution.executor import _execute_offline_request  # noqa: E402
from sovereignlab.schemas import (  # noqa: E402
    EvidenceRoute,
    ExecutionRequest,
    ExecutionTrace,
    LanguageCode,
    PlanAbstention,
    RoutePlan,
    SnapshotAsOfArguments,
    SnapshotAsOfCall,
    StesAsOfArguments,
    StesAsOfCall,
    TemporalDocumentArguments,
    TemporalDocumentCall,
    ToolName,
    ToolOutcomeStatus,
    TraceStatus,
)

TRACE_DIRECTORY = Path("traces/replay/v1")
_RECORDED_AT = datetime(2026, 8, 11, 6, 0, tzinfo=UTC)
_PLANNER_ID = "committed-replay-scripted-planner-v1"


@dataclass(frozen=True)
class _ReplayScenario:
    filename: str
    trace_id: str
    recorded_at: datetime
    request: ExecutionRequest
    plan: RoutePlan
    script_id: str
    expected_status: TraceStatus
    expected_tools: tuple[ToolName, ...]
    expected_outcomes: tuple[ToolOutcomeStatus, ...]


def _request(
    *,
    request_id: str,
    question: str,
    language: LanguageCode,
    requested_as_of: date | None,
    effective_as_of: date,
) -> ExecutionRequest:
    return ExecutionRequest(
        request_id=request_id,
        question=question,
        language=language,
        requested_as_of=requested_as_of,
        effective_as_of=effective_as_of,
    )


def _document_call(
    request: ExecutionRequest,
    *,
    call_id: str,
) -> TemporalDocumentCall:
    return TemporalDocumentCall(
        call_id=call_id,
        tool_name=ToolName.RETRIEVE_TEMPORAL_DOCUMENTS,
        arguments=TemporalDocumentArguments(
            question=request.question,
            language=request.language,
            as_of=request.effective_as_of,
            top_k=5,
        ),
    )


def _stes_call(
    request: ExecutionRequest,
    *,
    call_id: str,
) -> StesAsOfCall:
    return StesAsOfCall(
        call_id=call_id,
        tool_name=ToolName.RESOLVE_STES_AS_OF,
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


def _snapshot_call(
    request: ExecutionRequest,
    *,
    call_id: str,
) -> SnapshotAsOfCall:
    return SnapshotAsOfCall(
        call_id=call_id,
        tool_name=ToolName.READ_SNAPSHOT_AS_OF,
        arguments=SnapshotAsOfArguments(
            source_system="ecos",
            table_id="200Y108",
            item_id="10601",
            period="2026Q1",
            as_of=request.effective_as_of,
            normalization_rule_id="ecos-200y108-10601-billion-krw-v1",
        ),
    )


def _scenario(
    *,
    number: int,
    slug: str,
    request: ExecutionRequest,
    plan: RoutePlan,
    expected_status: TraceStatus,
    expected_tools: tuple[ToolName, ...],
    expected_outcomes: tuple[ToolOutcomeStatus, ...],
) -> _ReplayScenario:
    return _ReplayScenario(
        filename=f"{number:03d}-{slug}.json",
        trace_id=f"e2e-{slug}-v1",
        recorded_at=_RECORDED_AT + timedelta(minutes=number - 1),
        request=request,
        plan=plan,
        script_id=f"committed-replay-{slug}-v1",
        expected_status=expected_status,
        expected_tools=expected_tools,
        expected_outcomes=expected_outcomes,
    )


def _scenarios() -> tuple[_ReplayScenario, ...]:
    document_cutoff = date(2024, 5, 31)
    documents_ko = _request(
        request_id="replay-request-documents-ko-explicit-v1",
        question="성장 전망 상향 배경은 수출 증가와 내수 회복 중 무엇인가요?",
        language=LanguageCode.KOREAN,
        requested_as_of=document_cutoff,
        effective_as_of=document_cutoff,
    )
    documents_ko_plan = RoutePlan(
        route=EvidenceRoute.DOCUMENTS,
        tool_calls=(
            _document_call(
                documents_ko,
                call_id="replay-call-documents-ko-explicit-v1",
            ),
        ),
    )

    stes_cutoff = date(2026, 7, 9)
    data_en = _request(
        request_id="replay-request-data-stes-en-explicit-v1",
        question="What was Korea's May 2026 CLI at the cutoff?",
        language=LanguageCode.ENGLISH,
        requested_as_of=stes_cutoff,
        effective_as_of=stes_cutoff,
    )
    data_en_plan = RoutePlan(
        route=EvidenceRoute.DATA,
        tool_calls=(
            _stes_call(
                data_en,
                call_id="replay-call-data-stes-en-explicit-v1",
            ),
        ),
    )

    combined_cutoff = date(2026, 7, 17)
    combined_en = _request(
        request_id="replay-request-documents-data-en-implicit-v1",
        question="Why was the growth outlook revised upward?",
        language=LanguageCode.ENGLISH,
        requested_as_of=None,
        effective_as_of=combined_cutoff,
    )
    combined_en_plan = RoutePlan(
        route=EvidenceRoute.DOCUMENTS_AND_DATA,
        tool_calls=(
            _document_call(
                combined_en,
                call_id="replay-call-documents-data-doc-en-implicit-v1",
            ),
            _snapshot_call(
                combined_en,
                call_id="replay-call-documents-data-snapshot-en-implicit-v1",
            ),
        ),
    )

    abstain_ko = _request(
        request_id="replay-request-planned-abstention-ko-implicit-v1",
        question="검증 가능한 근거가 없는 요청에는 어떻게 답해야 하나요?",
        language=LanguageCode.KOREAN,
        requested_as_of=None,
        effective_as_of=combined_cutoff,
    )
    abstain_ko_plan = RoutePlan(
        route=EvidenceRoute.ABSTAIN,
        abstention=PlanAbstention(
            reason_code="no-cutoff-safe-route",
            message="No cutoff-safe evidence route is available for this request.",
        ),
    )

    abstention_cutoff = date(2026, 7, 16)
    tool_abstention_en = _request(
        request_id="replay-request-tool-abstention-en-explicit-v1",
        question="Why was the growth outlook revised upward?",
        language=LanguageCode.ENGLISH,
        requested_as_of=abstention_cutoff,
        effective_as_of=abstention_cutoff,
    )
    tool_abstention_en_plan = RoutePlan(
        route=EvidenceRoute.DOCUMENTS_AND_DATA,
        tool_calls=(
            _document_call(
                tool_abstention_en,
                call_id="replay-call-tool-abstention-doc-en-explicit-v1",
            ),
            _snapshot_call(
                tool_abstention_en,
                call_id="replay-call-tool-abstention-snapshot-en-explicit-v1",
            ),
            _stes_call(
                tool_abstention_en,
                call_id="replay-call-tool-abstention-stes-not-run-en-explicit-v1",
            ),
        ),
    )

    return (
        _scenario(
            number=1,
            slug="documents-complete-ko-explicit",
            request=documents_ko,
            plan=documents_ko_plan,
            expected_status=TraceStatus.COMPLETE,
            expected_tools=(ToolName.RETRIEVE_TEMPORAL_DOCUMENTS,),
            expected_outcomes=(ToolOutcomeStatus.SUCCESS,),
        ),
        _scenario(
            number=2,
            slug="data-stes-complete-en-explicit",
            request=data_en,
            plan=data_en_plan,
            expected_status=TraceStatus.COMPLETE,
            expected_tools=(ToolName.RESOLVE_STES_AS_OF,),
            expected_outcomes=(ToolOutcomeStatus.SUCCESS,),
        ),
        _scenario(
            number=3,
            slug="documents-and-data-complete-en-implicit",
            request=combined_en,
            plan=combined_en_plan,
            expected_status=TraceStatus.COMPLETE,
            expected_tools=(
                ToolName.RETRIEVE_TEMPORAL_DOCUMENTS,
                ToolName.READ_SNAPSHOT_AS_OF,
            ),
            expected_outcomes=(ToolOutcomeStatus.SUCCESS, ToolOutcomeStatus.SUCCESS),
        ),
        _scenario(
            number=4,
            slug="planned-abstention-ko-implicit",
            request=abstain_ko,
            plan=abstain_ko_plan,
            expected_status=TraceStatus.ABSTAINED,
            expected_tools=(),
            expected_outcomes=(),
        ),
        _scenario(
            number=5,
            slug="tool-abstention-en-explicit",
            request=tool_abstention_en,
            plan=tool_abstention_en_plan,
            expected_status=TraceStatus.ABSTAINED,
            expected_tools=(
                ToolName.RETRIEVE_TEMPORAL_DOCUMENTS,
                ToolName.READ_SNAPSHOT_AS_OF,
            ),
            expected_outcomes=(ToolOutcomeStatus.SUCCESS, ToolOutcomeStatus.ABSTAINED),
        ),
    )


def _render_trace(
    scenario: _ReplayScenario,
    *,
    registry: CallableToolRegistry,
) -> bytes:
    trace = _execute_offline_request(
        trace_id=scenario.trace_id,
        recorded_at=scenario.recorded_at,
        request=scenario.request,
        planner=ScriptedPlanner(
            planner_id=_PLANNER_ID,
            script_id=scenario.script_id,
            route_plan=scenario.plan,
        ),
        registry=registry,
    )
    actual_tools = tuple(result.tool_name for result in trace.tool_results)
    actual_outcomes = tuple(result.status for result in trace.tool_results)
    if (
        trace.status is not scenario.expected_status
        or actual_tools != scenario.expected_tools
        or actual_outcomes != scenario.expected_outcomes
    ):
        raise RuntimeError(f"replay scenario {scenario.filename} reached an unexpected outcome")
    payload = (trace.model_dump_json(indent=2, warnings="error") + "\n").encode("utf-8")
    rebuilt = ExecutionTrace.model_validate_json(payload, strict=True)
    if type(rebuilt) is not ExecutionTrace or rebuilt != trace:
        raise RuntimeError(f"replay scenario {scenario.filename} did not round trip exactly")
    return payload


def _render_replay_traces(repository_root: Path = ROOT) -> tuple[tuple[str, bytes], ...]:
    registry = load_committed_callable_tool_registry(repository_root)
    return tuple(
        (scenario.filename, _render_trace(scenario, registry=registry)) for scenario in _scenarios()
    )


def _validate_inventory(output_directory: Path, expected_names: set[str]) -> None:
    actual_names = {path.name for path in output_directory.glob("*.json")}
    unexpected = actual_names - expected_names
    if unexpected:
        names = ", ".join(sorted(unexpected))
        raise RuntimeError(f"unexpected committed replay trace files: {names}")


def _write_traces(payloads: tuple[tuple[str, bytes], ...]) -> None:
    output_directory = ROOT / TRACE_DIRECTORY
    output_directory.mkdir(parents=True, exist_ok=True)
    _validate_inventory(output_directory, {name for name, _ in payloads})
    for name, payload in payloads:
        path = output_directory / name
        path.write_bytes(payload)
        print(path.relative_to(ROOT))


def _check_traces(payloads: tuple[tuple[str, bytes], ...]) -> None:
    output_directory = ROOT / TRACE_DIRECTORY
    if not output_directory.is_dir():
        raise RuntimeError("the committed replay trace directory is missing")
    expected_names = {name for name, _ in payloads}
    _validate_inventory(output_directory, expected_names)
    for name, payload in payloads:
        path = output_directory / name
        if not path.is_file() or path.read_bytes() != payload:
            raise RuntimeError(f"committed replay trace drift: {path.relative_to(ROOT)}")
        print(path.relative_to(ROOT))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true", help="write the fixed committed traces")
    mode.add_argument("--check", action="store_true", help="check exact committed trace bytes")
    arguments = parser.parse_args()

    payloads = _render_replay_traces()
    if arguments.write:
        _write_traces(payloads)
    else:
        _check_traces(payloads)


if __name__ == "__main__":
    main()
