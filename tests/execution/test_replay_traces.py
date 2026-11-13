"""The committed replay traces are reproducible and cover the whole tool surface."""

from pathlib import Path

import pytest
from scripts.export_execution_replay_traces import TRACE_DIRECTORY, render_replay_traces

from sovereignlab.schemas import (
    EvidenceRoute,
    ExecutionTrace,
    LanguageCode,
    ToolName,
    ToolOutcomeStatus,
    TraceStatus,
)

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(scope="module")
def committed_traces() -> dict[str, ExecutionTrace]:
    return {
        path.name: ExecutionTrace.model_validate_json(path.read_bytes())
        for path in sorted(TRACE_DIRECTORY.glob("*.json"))
    }


def test_committed_traces_match_a_fresh_offline_execution() -> None:
    # A failure here after editing src/ means the traces need regenerating:
    #   python scripts/export_execution_replay_traces.py --write
    rendered = render_replay_traces(REPOSITORY_ROOT)

    assert {path.name for path in TRACE_DIRECTORY.glob("*.json")} == set(rendered)
    for name, payload in rendered.items():
        assert (TRACE_DIRECTORY / name).read_bytes() == payload, name


def test_traces_cover_every_route_tool_language_and_cutoff_form(
    committed_traces: dict[str, ExecutionTrace],
) -> None:
    traces = tuple(committed_traces.values())

    assert {trace.plan.route for trace in traces} == set(EvidenceRoute)
    assert {result.tool_name for trace in traces for result in trace.tool_results} == set(ToolName)
    assert {trace.request.language for trace in traces} == {
        LanguageCode.KOREAN,
        LanguageCode.ENGLISH,
    }
    assert {trace.request.requested_as_of is None for trace in traces} == {True, False}
    assert {trace.status for trace in traces} == {TraceStatus.COMPLETE, TraceStatus.ABSTAINED}


def test_tool_abstention_trace_stops_before_the_remaining_call(
    committed_traces: dict[str, ExecutionTrace],
) -> None:
    trace = committed_traces["005-tool-abstention-en-explicit.json"]

    assert len(trace.plan.tool_calls) == 3
    assert [result.status for result in trace.tool_results] == [
        ToolOutcomeStatus.SUCCESS,
        ToolOutcomeStatus.ABSTAINED,
    ]
    assert trace.evidence_packet.documents == () and trace.evidence_packet.observations == ()


def test_traces_carry_no_credential_or_local_path(
    committed_traces: dict[str, ExecutionTrace],
) -> None:
    for name in committed_traces:
        text = (TRACE_DIRECTORY / name).read_text(encoding="utf-8").lower()
        assert not any(marker in text for marker in ("api_key", "apikey", "/home/", "\\users\\"))
