"""Focused tests for the offline scripted and immutable recording planners."""

import hashlib
import inspect
import json
from datetime import date

import pytest

import sovereignlab.execution.planner as planner_module
from sovereignlab.execution import (
    Planner,
    PlannerError,
    RecordedPlanner,
    ReplayPlanner,
    ScriptedPlanner,
)
from sovereignlab.schemas import (
    EvidenceRoute,
    ExecutionRequest,
    PlanAbstention,
    PlannerMode,
    RoutePlan,
    SnapshotAsOfArguments,
    SnapshotAsOfCall,
    TemporalDocumentArguments,
    TemporalDocumentCall,
    ToolName,
)

CUTOFF = date(2026, 7, 17)
QUESTION_KO = "기준일 현재 성장 전망의 상향 조정 이유는 무엇인가?"
QUESTION_EN = "Why was the growth outlook revised upward as of the cutoff?"


def _request(
    *,
    language: str = "ko",
    requested_as_of: date | None = CUTOFF,
    effective_as_of: date = CUTOFF,
    question: str | None = None,
) -> ExecutionRequest:
    return ExecutionRequest(
        request_id=f"planner-request-{language}",
        question=question or (QUESTION_KO if language == "ko" else QUESTION_EN),
        language=language,
        requested_as_of=requested_as_of,
        effective_as_of=effective_as_of,
    )


def _document_call(
    request: ExecutionRequest,
    *,
    call_id: str = "planner-call-doc",
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


def _snapshot_call(
    request: ExecutionRequest,
    *,
    call_id: str = "planner-call-snapshot",
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


def _plan(route: EvidenceRoute, request: ExecutionRequest) -> RoutePlan:
    calls = {
        EvidenceRoute.DOCUMENTS: (_document_call(request),),
        EvidenceRoute.DATA: (_snapshot_call(request),),
        EvidenceRoute.DOCUMENTS_AND_DATA: (
            _document_call(request),
            _snapshot_call(request),
        ),
        EvidenceRoute.ABSTAIN: (),
    }[route]
    return RoutePlan(
        route=route,
        tool_calls=calls,
        abstention=(
            PlanAbstention(
                reason_code="unsupported-request",
                message="No cutoff-safe evidence route is available.",
            )
            if route is EvidenceRoute.ABSTAIN
            else None
        ),
    )


def _candidate_bytes(plan: RoutePlan) -> bytes:
    return plan.model_dump_json(warnings="error").encode("utf-8")


def _registry(
    candidate_bytes: bytes,
    *,
    recording_id: str = "planner-recording-001",
    model_id: str = "recorded-model/checkpoint-v1",
    output_sha256: str | None = None,
) -> planner_module._ImmutablePlannerRecordingRegistry:
    return planner_module._ImmutablePlannerRecordingRegistry(
        entries=(
            planner_module._PlannerRecording(
                recording_id=recording_id,
                model_id=model_id,
                candidate_bytes=candidate_bytes,
                output_sha256=output_sha256 or hashlib.sha256(candidate_bytes).hexdigest(),
            ),
        )
    )


@pytest.mark.parametrize(
    ("route", "language", "requested_as_of"),
    [
        (EvidenceRoute.DOCUMENTS, "ko", CUTOFF),
        (EvidenceRoute.DATA, "en", None),
        (EvidenceRoute.DOCUMENTS_AND_DATA, "en", CUTOFF),
        (EvidenceRoute.ABSTAIN, "ko", None),
    ],
)
def test_scripted_planner_covers_all_routes_languages_and_cutoff_forms(
    route: EvidenceRoute,
    language: str,
    requested_as_of: date | None,
) -> None:
    request = _request(language=language, requested_as_of=requested_as_of)
    expected = _plan(route, request)
    planner = ScriptedPlanner(
        planner_id="scripted-planner-v1",
        script_id=f"script-{route.value.replace('_', '-')}-{language}",
        route_plan=expected,
    )

    first = planner.plan(request)
    second = planner.plan(request)

    assert isinstance(planner, Planner)
    assert first == expected == second
    assert first is not second
    assert planner.provenance.mode is PlannerMode.SCRIPTED
    assert planner.provenance.model_id is None
    assert planner.provenance.recording_id is not None
    assert (
        planner.provenance.output_sha256 == hashlib.sha256(_candidate_bytes(expected)).hexdigest()
    )


def test_scripted_planner_freezes_the_template_at_construction() -> None:
    request = _request()
    template = _plan(EvidenceRoute.DATA, request)
    planner = ScriptedPlanner(
        planner_id="scripted-planner-v1",
        script_id="script-frozen-template",
        route_plan=template,
    )
    object.__setattr__(template, "route", EvidenceRoute.DOCUMENTS)

    assert planner.plan(request).route is EvidenceRoute.DATA


@pytest.mark.parametrize("planner_type", [RecordedPlanner, ReplayPlanner])
def test_recorded_and_replay_planners_verify_identical_candidate_bytes(
    planner_type: type[RecordedPlanner] | type[ReplayPlanner],
) -> None:
    request = _request(language="en", requested_as_of=None)
    expected = _plan(EvidenceRoute.DOCUMENTS_AND_DATA, request)
    candidate_bytes = _candidate_bytes(expected)
    registry = _registry(candidate_bytes)
    planner = planner_type(
        planner_id=f"{planner_type.__name__.lower()}-v1",
        recording_id="planner-recording-001",
        registry=registry,
    )

    first = planner.plan(request)
    second = planner.plan(request)

    assert isinstance(planner, Planner)
    assert first == expected == second
    assert first is not second
    assert planner.provenance.mode is (
        PlannerMode.RECORDED if planner_type is RecordedPlanner else PlannerMode.REPLAY
    )
    assert planner.provenance.recording_id == "planner-recording-001"
    assert planner.provenance.model_id == "recorded-model/checkpoint-v1"
    assert planner.provenance.output_sha256 == hashlib.sha256(candidate_bytes).hexdigest()


def test_recording_planner_returns_a_fresh_provenance_model() -> None:
    request = _request()
    planner = ReplayPlanner(
        planner_id="replay-planner-v1",
        recording_id="planner-recording-001",
        registry=_registry(_candidate_bytes(_plan(EvidenceRoute.DATA, request))),
    )
    returned = planner.provenance
    object.__setattr__(returned, "model_id", "caller-mutated-model")

    assert planner.provenance.model_id == "recorded-model/checkpoint-v1"
    assert planner.plan(request).route is EvidenceRoute.DATA


def _invalid_candidate_cases() -> list[tuple[str, bytes]]:
    request = _request()
    data_payload = _plan(EvidenceRoute.DATA, request).model_dump(mode="json")
    both_payload = _plan(EvidenceRoute.DOCUMENTS_AND_DATA, request).model_dump(mode="json")

    extra_root = dict(data_payload)
    extra_root["provider_envelope"] = {"hidden": True}

    unknown_tool = json.loads(json.dumps(data_payload))
    unknown_tool["tool_calls"][0]["tool_name"] = "read_arbitrary_file"

    mismatched_tool = json.loads(json.dumps(data_payload))
    mismatched_tool["tool_calls"][0]["tool_name"] = "retrieve_temporal_documents"

    duplicate_ids = json.loads(json.dumps(both_payload))
    duplicate_ids["tool_calls"][1]["call_id"] = duplicate_ids["tool_calls"][0]["call_id"]

    inconsistent_route = json.loads(json.dumps(data_payload))
    inconsistent_route["route"] = "documents"

    extra_argument = json.loads(json.dumps(data_payload))
    extra_argument["tool_calls"][0]["arguments"]["path"] = "/private/source.json"

    return [
        ("malformed-json", b"{"),
        ("non-object", b"[]"),
        ("extra-root", json.dumps(extra_root).encode()),
        ("unknown-tool", json.dumps(unknown_tool).encode()),
        ("mismatched-tool", json.dumps(mismatched_tool).encode()),
        ("duplicate-call-ids", json.dumps(duplicate_ids).encode()),
        ("inconsistent-route", json.dumps(inconsistent_route).encode()),
        ("extra-argument", json.dumps(extra_argument).encode()),
        (
            "duplicate-json-key",
            b'{"schema_version":"1.0.0","schema_version":"1.0.0","route":"data",'
            b'"tool_calls":[],"abstention":null}',
        ),
        (
            "non-finite-json",
            b'{"schema_version":"1.0.0","route":"documents","tool_calls":['
            b'{"call_id":"planner-call-doc","tool_name":"retrieve_temporal_documents",'
            b'"arguments":{"question":"A valid recorded question?","language":"en",'
            b'"as_of":"2026-07-17","top_k":NaN}}],"abstention":null}',
        ),
    ]


@pytest.mark.parametrize(("case_name", "candidate_bytes"), _invalid_candidate_cases())
def test_recorded_candidate_validation_fails_closed_with_digest_metadata(
    case_name: str,
    candidate_bytes: bytes,
) -> None:
    request = _request()
    planner = ReplayPlanner(
        planner_id="replay-planner-v1",
        recording_id="planner-recording-001",
        registry=_registry(candidate_bytes),
    )

    with pytest.raises(PlannerError) as exc_info:
        planner.plan(request)

    assert case_name
    assert exc_info.value.code == "plan_validation_failed"
    assert str(exc_info.value) == (
        "The planner candidate did not validate against the execution request."
    )
    assert exc_info.value.provenance == planner.provenance
    assert exc_info.value.provenance is not None
    assert exc_info.value.provenance.output_sha256 == hashlib.sha256(candidate_bytes).hexdigest()


@pytest.mark.parametrize(
    "drift",
    ["cutoff", "question", "language"],
)
def test_planner_rejects_request_binding_drift_before_dispatch(drift: str) -> None:
    request = _request(language="ko")
    arguments = _document_call(request).arguments.model_dump(mode="python")
    if drift == "cutoff":
        arguments["as_of"] = date(2026, 7, 16)
    elif drift == "question":
        arguments["question"] = "이 질문은 원래 요청과 다릅니다."
    else:
        arguments["language"] = "en"
    drifted_plan = RoutePlan(
        route=EvidenceRoute.DOCUMENTS,
        tool_calls=(
            TemporalDocumentCall(
                call_id="planner-call-doc",
                tool_name=ToolName.RETRIEVE_TEMPORAL_DOCUMENTS,
                arguments=TemporalDocumentArguments.model_validate(arguments),
            ),
        ),
    )
    planner = RecordedPlanner(
        planner_id="recorded-planner-v1",
        recording_id="planner-recording-001",
        registry=_registry(_candidate_bytes(drifted_plan)),
    )

    with pytest.raises(PlannerError) as exc_info:
        planner.plan(request)

    assert exc_info.value.code == "plan_validation_failed"
    assert exc_info.value.provenance == planner.provenance


def test_planner_rejects_missing_recording_and_wrong_registry_type() -> None:
    registry = _registry(_candidate_bytes(_plan(EvidenceRoute.ABSTAIN, _request())))

    with pytest.raises(PlannerError) as missing:
        ReplayPlanner(
            planner_id="replay-planner-v1",
            recording_id="missing-recording",
            registry=registry,
        )
    assert missing.value.code == "recording_missing"
    assert missing.value.provenance is None

    with pytest.raises(PlannerError) as wrong_registry:
        RecordedPlanner(
            planner_id="recorded-planner-v1",
            recording_id="planner-recording-001",
            registry=object(),  # type: ignore[arg-type]
        )
    assert wrong_registry.value.code == "recording_registry_invalid"


def test_recording_registry_rejects_duplicates_wrong_hash_and_mutable_bytes() -> None:
    candidate_bytes = _candidate_bytes(_plan(EvidenceRoute.ABSTAIN, _request()))
    valid = planner_module._PlannerRecording(
        recording_id="duplicate-recording",
        model_id="recorded-model/checkpoint-v1",
        candidate_bytes=candidate_bytes,
        output_sha256=hashlib.sha256(candidate_bytes).hexdigest(),
    )
    duplicate = planner_module._PlannerRecording(
        recording_id="duplicate-recording",
        model_id="recorded-model/checkpoint-v1",
        candidate_bytes=candidate_bytes,
        output_sha256=hashlib.sha256(candidate_bytes).hexdigest(),
    )
    with pytest.raises(planner_module._RecordingRegistryError) as duplicates:
        planner_module._ImmutablePlannerRecordingRegistry(entries=(valid, duplicate))
    assert duplicates.value.code == "recording_registry_invalid"

    with pytest.raises(planner_module._RecordingRegistryError):
        _registry(candidate_bytes, output_sha256="0" * 64)

    class BytesSubclass(bytes):
        pass

    with pytest.raises(planner_module._RecordingRegistryError):
        _registry(BytesSubclass(candidate_bytes))

    for invalid_size in (b"", b"x" * (planner_module._MAX_CANDIDATE_BYTES + 1)):
        with pytest.raises(planner_module._RecordingRegistryError):
            _registry(invalid_size)


def test_recording_registry_rejects_mutable_shape_invalid_entries_and_subclass() -> None:
    with pytest.raises(planner_module._RecordingRegistryError):
        planner_module._ImmutablePlannerRecordingRegistry(entries=[])  # type: ignore[arg-type]

    with pytest.raises(planner_module._RecordingRegistryError):
        planner_module._ImmutablePlannerRecordingRegistry(
            entries=(object(),),  # type: ignore[arg-type]
        )

    class RegistrySubclass(planner_module._ImmutablePlannerRecordingRegistry):
        pass

    with pytest.raises(planner_module._RecordingRegistryError):
        RegistrySubclass(entries=())


def test_recording_integrity_and_metadata_are_rechecked_on_every_plan() -> None:
    request = _request()
    candidate_bytes = _candidate_bytes(_plan(EvidenceRoute.DATA, request))
    registry = _registry(candidate_bytes)
    planner = ReplayPlanner(
        planner_id="replay-planner-v1",
        recording_id="planner-recording-001",
        registry=registry,
    )
    entry = registry.entries[0]
    original_bytes = entry.candidate_bytes
    try:
        object.__setattr__(entry, "candidate_bytes", candidate_bytes + b" ")
        with pytest.raises(PlannerError) as tampered:
            planner.plan(request)
        assert tampered.value.code == "recording_integrity_failed"
        assert tampered.value.provenance == planner.provenance
    finally:
        object.__setattr__(entry, "candidate_bytes", original_bytes)

    original_model_id = entry.model_id
    try:
        object.__setattr__(entry, "model_id", "recorded-model/changed-checkpoint")
        with pytest.raises(PlannerError) as drifted:
            planner.plan(request)
        assert drifted.value.code == "recording_integrity_failed"
    finally:
        object.__setattr__(entry, "model_id", original_model_id)


def test_recording_planner_independently_rechecks_the_resolved_byte_digest(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    request = _request()
    candidate_bytes = _candidate_bytes(_plan(EvidenceRoute.DATA, request))
    registry = _registry(candidate_bytes)
    planner = ReplayPlanner(
        planner_id="replay-planner-v1",
        recording_id="planner-recording-001",
        registry=registry,
    )
    entry = registry.entries[0]
    drifted = planner_module._PlannerRecording(
        recording_id=entry.recording_id,
        model_id=entry.model_id,
        candidate_bytes=entry.candidate_bytes + b" ",
        output_sha256=entry.output_sha256,
    )
    monkeypatch.setattr(
        planner_module._ImmutablePlannerRecordingRegistry,
        "resolve",
        lambda self, recording_id: drifted,
    )

    with pytest.raises(PlannerError) as exc_info:
        planner.plan(request)

    assert exc_info.value.code == "recording_integrity_failed"


def test_invalid_request_is_sanitized_and_bound_to_candidate_provenance() -> None:
    request = _request()
    planner = ScriptedPlanner(
        planner_id="scripted-planner-v1",
        script_id="script-invalid-request",
        route_plan=_plan(EvidenceRoute.DATA, request),
    )

    with pytest.raises(PlannerError) as raw_mapping:
        planner.plan(request.model_dump(mode="python"))  # type: ignore[arg-type]
    assert raw_mapping.value.code == "invalid_request"
    assert raw_mapping.value.provenance == planner.provenance

    mutated = request.model_copy(deep=True)
    object.__setattr__(mutated, "effective_as_of", date(2026, 7, 18))
    with pytest.raises(PlannerError) as invalid_model:
        planner.plan(mutated)
    assert invalid_model.value.code == "invalid_request"


def test_request_and_plan_round_trip_model_identity_is_enforced(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    request = _request()
    planner = ScriptedPlanner(
        planner_id="scripted-planner-v1",
        script_id="script-round-trip-check",
        route_plan=_plan(EvidenceRoute.DATA, request),
    )
    changed_request = request.model_copy(update={"request_id": "changed-request-id"})
    monkeypatch.setattr(
        ExecutionRequest,
        "model_validate_json",
        classmethod(lambda cls, payload, strict: changed_request),
    )
    with pytest.raises(PlannerError) as request_error:
        planner.plan(request)
    assert request_error.value.code == "invalid_request"

    monkeypatch.undo()
    monkeypatch.setattr(
        RoutePlan,
        "model_validate_json",
        classmethod(lambda cls, payload, strict: object()),
    )
    with pytest.raises(PlannerError) as plan_error:
        planner.plan(request)
    assert plan_error.value.code == "plan_validation_failed"


def test_scripted_and_recording_planner_configuration_failures_are_sanitized() -> None:
    with pytest.raises(PlannerError) as wrong_plan:
        ScriptedPlanner(
            planner_id="scripted-planner-v1",
            script_id="script-wrong-plan",
            route_plan=object(),  # type: ignore[arg-type]
        )
    assert wrong_plan.value.code == "planner_misconfigured"

    candidate_bytes = _candidate_bytes(_plan(EvidenceRoute.ABSTAIN, _request()))
    with pytest.raises(PlannerError) as bad_id:
        RecordedPlanner(
            planner_id=" INVALID ",
            recording_id="planner-recording-001",
            registry=_registry(candidate_bytes),
        )
    assert bad_id.value.code == "planner_misconfigured"


def test_scripted_candidate_digest_is_rechecked_and_failure_is_sanitized() -> None:
    request = _request()
    planner = ScriptedPlanner(
        planner_id="scripted-planner-v1",
        script_id="script-tamper-check",
        route_plan=_plan(EvidenceRoute.DATA, request),
    )
    original = planner._candidate_bytes
    try:
        object.__setattr__(planner, "_candidate_bytes", original + b" ")
        with pytest.raises(PlannerError) as exc_info:
            planner.plan(request)
        assert exc_info.value.code == "planner_misconfigured"
        assert exc_info.value.provenance == planner.provenance
    finally:
        object.__setattr__(planner, "_candidate_bytes", original)


def test_planner_boundary_has_no_dispatch_or_provider_dependency() -> None:
    source = inspect.getsource(planner_module)

    assert "dispatch_tool_call" not in source
    assert "mistral" not in source.lower()
    assert not hasattr(planner_module, "PlannerResult")
    assert not hasattr(planner_module, "PlannerOutput")
