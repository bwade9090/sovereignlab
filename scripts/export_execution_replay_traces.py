"""Write or check the committed offline execution replay traces.

Run with ``--write`` after changing anything under ``src/`` (every trace records a digest of
the source tree) and with ``--check`` to confirm the committed traces are reproducible.
"""

import argparse
import sys
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from sovereignlab.execution import (  # noqa: E402
    ScriptedPlanner,
    execute_offline_request,
    load_committed_callable_tool_registry,
)
from sovereignlab.schemas import (  # noqa: E402
    EvidenceRoute,
    ExecutionRequest,
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
    TraceStatus,
)

TRACE_DIRECTORY = ROOT / "traces" / "replay" / "v1"
_RECORDED_AT = datetime(2026, 8, 11, 6, 0, tzinfo=UTC)
_PLANNER_ID = "committed-replay-scripted-planner-v1"


@dataclass(frozen=True)
class ReplayScenario:
    """One fixed request, scripted plan, and the terminal status it must reach."""

    number: int
    slug: str
    request: ExecutionRequest
    plan: RoutePlan
    expected_status: TraceStatus

    @property
    def filename(self) -> str:
        return f"{self.number:03d}-{self.slug}.json"


def _request(
    slug: str,
    question: str,
    language: LanguageCode,
    effective_as_of: date,
    *,
    explicit: bool,
) -> ExecutionRequest:
    return ExecutionRequest(
        request_id=f"replay-request-{slug}-v1",
        question=question,
        language=language,
        requested_as_of=effective_as_of if explicit else None,
        effective_as_of=effective_as_of,
    )


def _document_call(request: ExecutionRequest, call_id: str) -> TemporalDocumentCall:
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


def _stes_call(request: ExecutionRequest, call_id: str) -> StesAsOfCall:
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


def _snapshot_call(request: ExecutionRequest, call_id: str) -> SnapshotAsOfCall:
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


def replay_scenarios() -> tuple[ReplayScenario, ...]:
    """Return the five scenarios: every route and tool, both languages, both cutoff forms."""

    documents_ko = _request(
        "documents-ko-explicit",
        "성장 전망 상향 배경은 수출 증가와 내수 회복 중 무엇인가요?",
        LanguageCode.KOREAN,
        date(2024, 5, 31),
        explicit=True,
    )
    data_en = _request(
        "data-stes-en-explicit",
        "What was Korea's May 2026 CLI at the cutoff?",
        LanguageCode.ENGLISH,
        date(2026, 7, 9),
        explicit=True,
    )
    combined_en = _request(
        "documents-data-en-implicit",
        "Why was the growth outlook revised upward?",
        LanguageCode.ENGLISH,
        date(2026, 7, 17),
        explicit=False,
    )
    abstain_ko = _request(
        "planned-abstention-ko-implicit",
        "검증 가능한 근거가 없는 요청에는 어떻게 답해야 하나요?",
        LanguageCode.KOREAN,
        date(2026, 7, 17),
        explicit=False,
    )
    # One day before the snapshot capture: the snapshot tool abstains and the STES call
    # planned after it never runs.
    tool_abstention_en = _request(
        "tool-abstention-en-explicit",
        "Why was the growth outlook revised upward?",
        LanguageCode.ENGLISH,
        date(2026, 7, 16),
        explicit=True,
    )
    return (
        ReplayScenario(
            number=1,
            slug="documents-complete-ko-explicit",
            request=documents_ko,
            plan=RoutePlan(
                route=EvidenceRoute.DOCUMENTS,
                tool_calls=(_document_call(documents_ko, "replay-call-documents-ko-explicit-v1"),),
            ),
            expected_status=TraceStatus.COMPLETE,
        ),
        ReplayScenario(
            number=2,
            slug="data-stes-complete-en-explicit",
            request=data_en,
            plan=RoutePlan(
                route=EvidenceRoute.DATA,
                tool_calls=(_stes_call(data_en, "replay-call-data-stes-en-explicit-v1"),),
            ),
            expected_status=TraceStatus.COMPLETE,
        ),
        ReplayScenario(
            number=3,
            slug="documents-and-data-complete-en-implicit",
            request=combined_en,
            plan=RoutePlan(
                route=EvidenceRoute.DOCUMENTS_AND_DATA,
                tool_calls=(
                    _document_call(combined_en, "replay-call-documents-data-doc-en-implicit-v1"),
                    _snapshot_call(
                        combined_en,
                        "replay-call-documents-data-snapshot-en-implicit-v1",
                    ),
                ),
            ),
            expected_status=TraceStatus.COMPLETE,
        ),
        ReplayScenario(
            number=4,
            slug="planned-abstention-ko-implicit",
            request=abstain_ko,
            plan=RoutePlan(
                route=EvidenceRoute.ABSTAIN,
                abstention=PlanAbstention(
                    reason_code="no-cutoff-safe-route",
                    message="No cutoff-safe evidence route is available for this request.",
                ),
            ),
            expected_status=TraceStatus.ABSTAINED,
        ),
        ReplayScenario(
            number=5,
            slug="tool-abstention-en-explicit",
            request=tool_abstention_en,
            plan=RoutePlan(
                route=EvidenceRoute.DOCUMENTS_AND_DATA,
                tool_calls=(
                    _document_call(
                        tool_abstention_en,
                        "replay-call-tool-abstention-doc-en-explicit-v1",
                    ),
                    _snapshot_call(
                        tool_abstention_en,
                        "replay-call-tool-abstention-snapshot-en-explicit-v1",
                    ),
                    _stes_call(
                        tool_abstention_en,
                        "replay-call-tool-abstention-stes-not-run-en-explicit-v1",
                    ),
                ),
            ),
            expected_status=TraceStatus.ABSTAINED,
        ),
    )


def render_replay_traces(repository_root: Path = ROOT) -> dict[str, bytes]:
    """Execute every scenario and return its trace file bytes by filename."""

    registry = load_committed_callable_tool_registry(repository_root)
    rendered: dict[str, bytes] = {}
    for scenario in replay_scenarios():
        trace = execute_offline_request(
            trace_id=f"e2e-{scenario.slug}-v1",
            recorded_at=_RECORDED_AT + timedelta(minutes=scenario.number - 1),
            request=scenario.request,
            planner=ScriptedPlanner(
                planner_id=_PLANNER_ID,
                script_id=f"committed-replay-{scenario.slug}-v1",
                route_plan=scenario.plan,
            ),
            registry=registry,
        )
        if trace.status is not scenario.expected_status:
            raise RuntimeError(f"{scenario.filename} reached {trace.status.value}")
        rendered[scenario.filename] = (trace.model_dump_json(indent=2) + "\n").encode("utf-8")
    return rendered


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true", help="write the committed traces")
    mode.add_argument("--check", action="store_true", help="fail if a committed trace differs")
    arguments = parser.parse_args()

    rendered = render_replay_traces()
    committed = {path.name for path in TRACE_DIRECTORY.glob("*.json")}
    if committed - set(rendered):
        raise SystemExit(f"unexpected trace files: {sorted(committed - set(rendered))}")
    for name, payload in rendered.items():
        path = TRACE_DIRECTORY / name
        if arguments.write:
            path.write_bytes(payload)
        elif not path.is_file() or path.read_bytes() != payload:
            raise SystemExit(f"committed replay trace drift: {path.relative_to(ROOT)}")
        print(path.relative_to(ROOT))


if __name__ == "__main__":
    main()
