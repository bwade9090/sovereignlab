"""Verify committed real-digest traces against fresh offline executor replay."""

from __future__ import annotations

import hashlib
import inspect
import json
from pathlib import Path

import pytest
import scripts.export_execution_replay_traces as replay_exporter
from pydantic import ValidationError

import sovereignlab.execution.executor as executor_module
from sovereignlab.execution import (
    CALLABLE_TOOL_REGISTRY_DESCRIPTOR_SHA256,
    EXECUTION_ARTIFACT_REGISTRY_DESCRIPTOR_SHA256,
    load_committed_callable_tool_registry,
)
from sovereignlab.retrieval.registry import TEMPORAL_CORPUS_DESCRIPTOR_SHA256
from sovereignlab.schemas import (
    AbstentionOrigin,
    EvidenceRoute,
    ExecutionTrace,
    LanguageCode,
    PacketStatus,
    ToolName,
    ToolOutcomeStatus,
    TraceStatus,
)

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
TRACE_DIRECTORY = REPOSITORY_ROOT / replay_exporter.TRACE_DIRECTORY
TRACE_README = REPOSITORY_ROOT / "traces" / "README.md"
EXPECTED_FILENAMES = (
    "001-documents-complete-ko-explicit.json",
    "002-data-stes-complete-en-explicit.json",
    "003-documents-and-data-complete-en-implicit.json",
    "004-planned-abstention-ko-implicit.json",
    "005-tool-abstention-en-explicit.json",
)


@pytest.fixture(scope="module")
def rendered_runs() -> tuple[dict[str, bytes], dict[str, bytes]]:
    first = dict(replay_exporter._render_replay_traces(REPOSITORY_ROOT))
    second = dict(replay_exporter._render_replay_traces(REPOSITORY_ROOT))
    return first, second


@pytest.fixture(scope="module")
def committed_traces() -> dict[str, ExecutionTrace]:
    return {
        name: ExecutionTrace.model_validate_json(
            (TRACE_DIRECTORY / name).read_bytes(),
            strict=True,
        )
        for name in EXPECTED_FILENAMES
    }


def test_committed_trace_inventory_is_exact() -> None:
    assert TRACE_DIRECTORY.is_dir()
    assert tuple(sorted(path.name for path in TRACE_DIRECTORY.glob("*.json"))) == (
        EXPECTED_FILENAMES
    )


@pytest.mark.parametrize("filename", EXPECTED_FILENAMES)
def test_committed_trace_exact_bytes_match_fresh_executor_replay(
    filename: str,
    rendered_runs: tuple[dict[str, bytes], dict[str, bytes]],
) -> None:
    first, second = rendered_runs
    committed = (TRACE_DIRECTORY / filename).read_bytes()

    assert committed == first[filename] == second[filename]
    trace = ExecutionTrace.model_validate_json(committed, strict=True)
    assert (trace.model_dump_json(indent=2, warnings="error") + "\n").encode("utf-8") == committed


def test_trace_matrix_covers_routes_tools_languages_and_cutoff_forms(
    committed_traces: dict[str, ExecutionTrace],
) -> None:
    traces = tuple(committed_traces.values())
    assert {trace.plan.route for trace in traces if trace.plan is not None} == set(EvidenceRoute)
    assert {
        call.tool_name
        for trace in traces
        if trace.plan is not None
        for call in trace.plan.tool_calls
    } == set(ToolName)
    assert {trace.request.language for trace in traces} == {
        LanguageCode.KOREAN,
        LanguageCode.ENGLISH,
    }
    assert {trace.request.requested_as_of is None for trace in traces} == {False, True}
    assert {trace.status for trace in traces} == {TraceStatus.COMPLETE, TraceStatus.ABSTAINED}
    assert {
        trace.evidence_packet.abstention.origin
        for trace in traces
        if trace.evidence_packet is not None and trace.evidence_packet.abstention is not None
    } == {AbstentionOrigin.PLAN, AbstentionOrigin.TOOL}


def test_trace_environment_and_planner_digests_are_recomputed_from_real_boundaries(
    committed_traces: dict[str, ExecutionTrace],
) -> None:
    registry = load_committed_callable_tool_registry(REPOSITORY_ROOT)
    provenance = registry.provenance()
    executor_sha256 = executor_module._executor_descriptor_sha256()

    for trace in committed_traces.values():
        assert trace.environment.executor_id == "sovereignlab-offline-executor-v1"
        assert trace.environment.executor_sha256 == executor_sha256
        assert trace.environment.tool_registry_id == provenance.tool_registry_id
        assert (
            trace.environment.tool_registry_sha256
            == provenance.tool_registry_sha256
            == CALLABLE_TOOL_REGISTRY_DESCRIPTOR_SHA256
        )
        assert trace.environment.artifact_registry_id == provenance.artifact_registry_id
        assert (
            trace.environment.artifact_registry_sha256
            == provenance.artifact_registry_sha256
            == EXECUTION_ARTIFACT_REGISTRY_DESCRIPTOR_SHA256
        )
        assert trace.environment.retrieval_corpus_id == provenance.retrieval_corpus_id
        assert (
            trace.environment.retrieval_corpus_sha256
            == provenance.retrieval_corpus_sha256
            == TEMPORAL_CORPUS_DESCRIPTOR_SHA256
        )
        assert trace.plan is not None
        expected_plan_sha256 = hashlib.sha256(
            trace.plan.model_dump_json(warnings="error").encode("utf-8")
        ).hexdigest()
        assert trace.planner.mode.value == "scripted"
        assert trace.planner.recording_id is not None
        assert trace.planner.output_sha256 == expected_plan_sha256
        assert trace.planner.model_id is None


def test_committed_success_evidence_uses_real_cutoff_safe_results(
    committed_traces: dict[str, ExecutionTrace],
) -> None:
    documents = committed_traces[EXPECTED_FILENAMES[0]]
    assert documents.evidence_packet is not None
    assert {item.source_id for item in documents.evidence_packet.documents} == {
        "synthetic-outlook-2024-05-ko"
    }
    assert "2024-08" not in documents.model_dump_json(warnings="error")

    stes = committed_traces[EXPECTED_FILENAMES[1]]
    assert stes.evidence_packet is not None
    vintage = stes.evidence_packet.observations[0]
    assert vintage.evidence_kind == "vintage_observation"
    assert vintage.selected_edition == "202607"
    assert vintage.observation.raw_value == "102.66"

    combined = committed_traces[EXPECTED_FILENAMES[2]]
    assert combined.evidence_packet is not None
    snapshot = combined.evidence_packet.observations[0]
    assert snapshot.evidence_kind == "latest_snapshot"
    assert snapshot.observation.raw_value == "596692.8"


def test_committed_abstentions_preserve_terminal_prefix_without_partial_packet_evidence(
    committed_traces: dict[str, ExecutionTrace],
) -> None:
    planned = committed_traces[EXPECTED_FILENAMES[3]]
    assert planned.tool_results == ()
    assert planned.evidence_packet is not None
    assert planned.evidence_packet.status is PacketStatus.ABSTAINED
    assert planned.evidence_packet.abstention.origin is AbstentionOrigin.PLAN

    terminal = committed_traces[EXPECTED_FILENAMES[4]]
    assert terminal.plan is not None
    assert tuple(call.tool_name for call in terminal.plan.tool_calls) == (
        ToolName.RETRIEVE_TEMPORAL_DOCUMENTS,
        ToolName.READ_SNAPSHOT_AS_OF,
        ToolName.RESOLVE_STES_AS_OF,
    )
    assert tuple(result.status for result in terminal.tool_results) == (
        ToolOutcomeStatus.SUCCESS,
        ToolOutcomeStatus.ABSTAINED,
    )
    assert len(terminal.tool_results) < len(terminal.plan.tool_calls)
    assert terminal.plan.tool_calls[-1].call_id not in {
        result.call_id for result in terminal.tool_results
    }
    assert terminal.evidence_packet is not None
    assert terminal.evidence_packet.status is PacketStatus.ABSTAINED
    assert terminal.evidence_packet.documents == ()
    assert terminal.evidence_packet.observations == ()
    assert terminal.evidence_packet.abstention.origin is AbstentionOrigin.TOOL
    assert terminal.evidence_packet.abstention.origin_call_id == terminal.tool_results[-1].call_id
    assert terminal.evidence_packet.abstention.reason_code == (
        terminal.tool_results[-1].abstention.reason_code
    )


def test_committed_trace_rejects_invalid_call_and_post_cutoff_result_mutation(
    committed_traces: dict[str, ExecutionTrace],
) -> None:
    trace = committed_traces[EXPECTED_FILENAMES[0]]
    payload = json.loads(trace.model_dump_json(warnings="error"))
    payload["plan"]["tool_calls"][0]["tool_name"] = "read_arbitrary_file"
    with pytest.raises(ValidationError):
        ExecutionTrace.model_validate(payload)

    payload = json.loads(trace.model_dump_json(warnings="error"))
    payload["tool_results"][0]["payload"]["matches"][0]["published_on"] = "2024-08-22"
    with pytest.raises(ValidationError, match="post-cutoff"):
        ExecutionTrace.model_validate(payload)


def test_exporter_uses_unmodified_private_executor_without_fault_injection() -> None:
    source = inspect.getsource(replay_exporter)

    assert "_execute_offline_request" in source
    assert "load_committed_callable_tool_registry" in source
    assert "ExecutionTrace(" not in source
    for forbidden in (
        "monkeypatch",
        "mistralai",
        "httpx",
        "requests",
        "provider_envelope",
        "datetime.now",
    ):
        assert forbidden not in source


def test_replay_slice_preserves_executor_and_public_schema_surfaces(
    committed_traces: dict[str, ExecutionTrace],
) -> None:
    descriptor = json.loads(executor_module._canonical_executor_descriptor_bytes())
    assert len(descriptor["source_files"]) == 32
    assert executor_module._executor_descriptor_sha256() == (
        "08f45dab6a36a49cb7d0b588a69236942cd61534540bd4de0772010402dada64"
    )
    assert len(tuple((REPOSITORY_ROOT / "data" / "schemas").glob("*.schema.json"))) == 13
    assert all(trace.failure is None for trace in committed_traces.values())
    serialized = b"".join((TRACE_DIRECTORY / name).read_bytes() for name in EXPECTED_FILENAMES)
    lowered = serialized.lower()
    for forbidden in (
        str(REPOSITORY_ROOT).encode("utf-8").lower(),
        b"provider_envelope",
        b"credential",
        b"api_key",
        b"api-key",
        b"authorization",
        b"bearer ",
        b"password",
        b"access_token",
        b"access-token",
        b"refresh_token",
        b"refresh-token",
        b"private_key",
        b"private-key",
        b"client_secret",
        b"client-secret",
        b"secret",
        b".env",
    ):
        assert forbidden not in lowered
    for absolute_path_prefix in (
        b"c:" + bytes((92,)),
        b"c:/",
        b"/users/",
        b"/home/",
        b"/root/",
        b"/tmp/",
        b"/workspace/",
        b"/var/tmp/",
    ):
        assert absolute_path_prefix not in lowered
    for drive_letter in range(ord("a"), ord("z") + 1):
        drive_prefix = bytes((drive_letter, ord(":")))
        assert drive_prefix + bytes((92,)) not in lowered
        assert drive_prefix + b"/" not in lowered
    assert bytes((92, 92)) not in lowered


def test_trace_readme_preserves_required_attribution_and_noncommercial_profile() -> None:
    readme = TRACE_README.read_text(encoding="utf-8")
    rendered = readme.replace("\n> ", " ")

    assert (
        "출처: ECOS(한국은행; 작성기관: 한국은행; 국내총생산에 대한 지출; "
        "표 200Y108/항목 10601), 조회일 2026-07-17. KOR-RTD에서 빈티지 구조로 가공함."
    ) in rendered
    assert (
        "Source: OECD; original producer: OECD; statistic: Composite leading indicator (CLI) "
        "amplitude adjusted — Korea; retrieved 2026-07-17;"
    ) in rendered
    assert "KOR-RTD preserves the captured vintage; no OECD endorsement is implied." in readme
    assert (
        "https://ecos.bok.or.kr/api/StatisticSearch/%7Bapi-key%7D/json/kr/1/1000/"
        "200Y108/Q/1960Q1/2026Q3/10601"
    ) in readme
    assert (
        "https://sdmx.oecd.org/public/rest/data/"
        "OECD.SDD.STES,DSD_STES_REVISIONS%40DF_STES_REVISIONS,4.0/"
        "KOR.M.LI_AA...?format=csvfilewithlabels"
    ) in readme
    assert "non-commercial public-research profile" in readme
    assert "2026-07-08T09:33:35.737Z" in readme
