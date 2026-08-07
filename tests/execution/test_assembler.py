"""Focused tests for private deterministic evidence-packet assembly."""

import inspect
from datetime import UTC, date, datetime
from typing import Any

import pytest

import sovereignlab.execution as execution_package
import sovereignlab.execution.assembler as assembler_module
from sovereignlab.schemas import (
    AbstentionOrigin,
    DocumentMatchEvidence,
    DocumentRetrievalPayload,
    EvidenceLocator,
    EvidenceRoute,
    ExecutionEvidencePacket,
    ExecutionFailure,
    ExecutionRequest,
    FailurePhase,
    NormalizedObservation,
    PacketStatus,
    PlanAbstention,
    RoutePlan,
    SnapshotAsOfArguments,
    SnapshotAsOfCall,
    SnapshotAsOfResult,
    SnapshotObservationEvidence,
    StesAsOfArguments,
    StesAsOfCall,
    StesAsOfResult,
    TemporalDocumentArguments,
    TemporalDocumentCall,
    TemporalDocumentResult,
    ToolAbstention,
    ToolName,
    ToolOutcomeStatus,
    VintageObservationEvidence,
)

CUTOFF = date(2026, 7, 17)
QUESTION_KO = "기준일 당시 한국의 성장 흐름을 설명해줘."
QUESTION_EN = "Explain Korea's growth conditions as of the cutoff."
SHA_A = "a" * 64
SHA_B = "b" * 64


def _request(
    *,
    language: str = "ko",
    question: str | None = None,
    requested_as_of: date | None = CUTOFF,
    effective_as_of: date = CUTOFF,
) -> ExecutionRequest:
    return ExecutionRequest(
        request_id=f"assembler-request-{language}",
        question=question or (QUESTION_KO if language == "ko" else QUESTION_EN),
        language=language,
        requested_as_of=requested_as_of,
        effective_as_of=effective_as_of,
    )


def _document_call(
    request: ExecutionRequest,
    *,
    call_id: str = "assembler-call-doc-001",
    question: str | None = None,
    language: str | None = None,
    as_of: date | None = None,
    top_k: int = 5,
) -> TemporalDocumentCall:
    return TemporalDocumentCall(
        call_id=call_id,
        tool_name=ToolName.RETRIEVE_TEMPORAL_DOCUMENTS,
        arguments=TemporalDocumentArguments(
            question=question or request.question,
            language=language or request.language,
            as_of=as_of or request.effective_as_of,
            top_k=top_k,
        ),
    )


def _snapshot_call(
    request: ExecutionRequest,
    *,
    call_id: str = "assembler-call-snapshot-001",
    as_of: date | None = None,
) -> SnapshotAsOfCall:
    return SnapshotAsOfCall(
        call_id=call_id,
        tool_name=ToolName.READ_SNAPSHOT_AS_OF,
        arguments=SnapshotAsOfArguments(
            source_system="ecos",
            table_id="200Y108",
            item_id="10601",
            period="2026Q1",
            as_of=as_of or request.effective_as_of,
            normalization_rule_id="ecos-200y108-10601-billion-krw-v1",
        ),
    )


def _stes_call(
    request: ExecutionRequest,
    *,
    call_id: str = "assembler-call-stes-001",
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


def _plan(
    route: EvidenceRoute,
    request: ExecutionRequest,
    *,
    calls: tuple[Any, ...] | None = None,
) -> RoutePlan:
    selected_calls = calls
    if selected_calls is None:
        selected_calls = {
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
        tool_calls=selected_calls,
        abstention=(
            PlanAbstention(
                reason_code="planned-no-safe-route",
                message="No cutoff-safe evidence route is available.",
            )
            if route is EvidenceRoute.ABSTAIN
            else None
        ),
    )


def _document_evidence(
    *,
    chunk_id: str = "assembler-chunk-001",
    source_id: str = "assembler-source-001",
    language: str = "ko",
    published_on: date = date(2026, 5, 28),
    score: float = 3.0,
) -> DocumentMatchEvidence:
    return DocumentMatchEvidence(
        chunk_id=chunk_id,
        source_id=source_id,
        source_sha256=SHA_A,
        language=language,
        published_on=published_on,
        locator=EvidenceLocator(page=7, section="Synthetic evidence"),
        text=f"Synthetic cutoff-safe evidence for {chunk_id}.",
        score=score,
    )


def _document_result(
    *,
    call_id: str = "assembler-call-doc-001",
    matches: tuple[DocumentMatchEvidence, ...] | None = None,
) -> TemporalDocumentResult:
    return TemporalDocumentResult(
        call_id=call_id,
        tool_name=ToolName.RETRIEVE_TEMPORAL_DOCUMENTS,
        status=ToolOutcomeStatus.SUCCESS,
        payload=DocumentRetrievalPayload(
            matches=matches or (_document_evidence(),),
        ),
    )


def _normalization(
    *,
    raw_value: str = "596692.8",
    normalization_rule_id: str = "ecos-200y108-10601-billion-krw-v1",
    normalized_value: str = "596692.8",
    canonical_unit: str = "billion_krw",
    display_places: int = 1,
    display_value: str = "596692.8",
) -> NormalizedObservation:
    return NormalizedObservation(
        raw_value=raw_value,
        normalization_rule_id=normalization_rule_id,
        normalized_value=normalized_value,
        canonical_unit=canonical_unit,
        display_places=display_places,
        display_value=display_value,
    )


def _snapshot_evidence(
    *,
    period: str = "2026Q1",
    as_of: date = CUTOFF,
) -> SnapshotObservationEvidence:
    return SnapshotObservationEvidence(
        evidence_kind="latest_snapshot",
        source_id="assembler-ecos-gdp-snapshot",
        source_sha256=SHA_B,
        source_system="ecos",
        source_published_on=CUTOFF,
        source_retrieved_at=datetime(2026, 7, 17, 11, 52, 43, tzinfo=UTC),
        rights_catalog_id="assembler-rights-catalog",
        rights_decision_id="assembler-ecos-gdp-rights",
        as_of=as_of,
        table_id="200Y108",
        item_id="10601",
        period=period,
        observation=_normalization(),
    )


def _snapshot_result(
    *,
    call_id: str = "assembler-call-snapshot-001",
    evidence: SnapshotObservationEvidence | None = None,
) -> SnapshotAsOfResult:
    return SnapshotAsOfResult(
        call_id=call_id,
        tool_name=ToolName.READ_SNAPSHOT_AS_OF,
        status=ToolOutcomeStatus.SUCCESS,
        payload=evidence or _snapshot_evidence(),
    )


def _vintage_evidence(*, period: str = "2026-05") -> VintageObservationEvidence:
    return VintageObservationEvidence(
        evidence_kind="vintage_observation",
        source_id="assembler-oecd-cli-archive",
        source_sha256=SHA_A,
        source_published_on=CUTOFF,
        source_retrieved_at=datetime(2026, 7, 17, 11, 53, 2, tzinfo=UTC),
        rights_catalog_id="assembler-rights-catalog",
        rights_decision_id="assembler-oecd-cli-rights",
        ledger_id="assembler-edition-ledger",
        dataflow_id="DSD_STES_REVISIONS@DF_STES_REVISIONS",
        dataflow_version="4.0",
        as_of=CUTOFF,
        ref_area="KOR",
        freq="M",
        measure="LI_AA",
        unit_measure="IX",
        activity="_T",
        selected_edition="202607",
        period=period,
        observation=_normalization(
            raw_value="102.66",
            normalization_rule_id="oecd-stes-kor-li-aa-index-v1",
            normalized_value="102.66",
            canonical_unit="oecd_amplitude_adjusted_index",
            display_places=2,
            display_value="102.66",
        ),
    )


def _stes_result(
    *,
    call_id: str = "assembler-call-stes-001",
    evidence: VintageObservationEvidence | None = None,
) -> StesAsOfResult:
    return StesAsOfResult(
        call_id=call_id,
        tool_name=ToolName.RESOLVE_STES_AS_OF,
        status=ToolOutcomeStatus.SUCCESS,
        payload=evidence or _vintage_evidence(),
    )


def _document_abstention(
    *,
    call_id: str = "assembler-call-doc-001",
) -> TemporalDocumentResult:
    return TemporalDocumentResult(
        call_id=call_id,
        tool_name=ToolName.RETRIEVE_TEMPORAL_DOCUMENTS,
        status=ToolOutcomeStatus.ABSTAINED,
        abstention=ToolAbstention(
            reason_code="no-temporal-document-match",
            message="No cutoff-safe document matched the request.",
        ),
    )


def _snapshot_abstention(
    *,
    call_id: str = "assembler-call-snapshot-001",
) -> SnapshotAsOfResult:
    return SnapshotAsOfResult(
        call_id=call_id,
        tool_name=ToolName.READ_SNAPSHOT_AS_OF,
        status=ToolOutcomeStatus.ABSTAINED,
        abstention=ToolAbstention(
            reason_code="no-snapshot-available-by-cutoff",
            message="No eligible snapshot exists by the cutoff.",
        ),
    )


def _snapshot_error(
    *,
    call_id: str = "assembler-call-snapshot-001",
) -> SnapshotAsOfResult:
    failure = ExecutionFailure(
        phase=FailurePhase.TOOL_EXECUTION,
        code="snapshot-invalid",
        message="Snapshot execution failed safely.",
        call_id=call_id,
    )
    return SnapshotAsOfResult(
        call_id=call_id,
        tool_name=ToolName.READ_SNAPSHOT_AS_OF,
        status=ToolOutcomeStatus.ERROR,
        error=failure,
    )


@pytest.mark.parametrize(
    ("language", "requested_as_of"),
    [("ko", CUTOFF), ("en", None)],
)
def test_planned_abstention_reproduces_exact_reason_without_results(
    language: str,
    requested_as_of: date | None,
) -> None:
    request = _request(language=language, requested_as_of=requested_as_of)
    plan = _plan(EvidenceRoute.ABSTAIN, request)

    packet = assembler_module._assemble_evidence_packet(
        request=request,
        plan=plan,
        tool_results=(),
    )

    assert packet.status is PacketStatus.ABSTAINED
    assert packet.planned_route is EvidenceRoute.ABSTAIN
    assert packet.abstention is not None
    assert packet.abstention.origin is AbstentionOrigin.PLAN
    assert packet.abstention.origin_call_id is None
    assert plan.abstention is not None
    assert packet.abstention.reason_code == plan.abstention.reason_code
    assert packet.abstention.message == plan.abstention.message
    assert not packet.documents
    assert not packet.observations
    assert (
        ExecutionEvidencePacket.model_validate_json(packet.model_dump_json(), strict=True) == packet
    )


def test_complete_document_packet_preserves_call_and_match_order_and_is_fresh() -> None:
    request = _request()
    calls = (
        _document_call(request, call_id="assembler-call-doc-001"),
        _document_call(request, call_id="assembler-call-doc-002"),
    )
    high = _document_evidence(chunk_id="assembler-chunk-high", score=4.0)
    low = _document_evidence(chunk_id="assembler-chunk-low", score=2.0)
    last = _document_evidence(
        chunk_id="assembler-chunk-last",
        source_id="assembler-source-002",
        score=1.0,
    )
    results = (
        _document_result(call_id=calls[0].call_id, matches=(high, low)),
        _document_result(call_id=calls[1].call_id, matches=(last,)),
    )
    plan = _plan(EvidenceRoute.DOCUMENTS, request, calls=calls)

    first = assembler_module._assemble_evidence_packet(
        request=request,
        plan=plan,
        tool_results=results,
    )
    second = assembler_module._assemble_evidence_packet(
        request=request,
        plan=plan,
        tool_results=results,
    )

    assert first.status is PacketStatus.COMPLETE
    assert tuple(item.chunk_id for item in first.documents) == (
        "assembler-chunk-high",
        "assembler-chunk-low",
        "assembler-chunk-last",
    )
    assert not first.observations
    assert first.request is not request
    assert results[0].payload is not None
    assert first.documents[0] is not results[0].payload.matches[0]
    assert first.model_dump_json() == second.model_dump_json()


def test_complete_data_packet_preserves_typed_observation_order() -> None:
    request = _request()
    calls = (_stes_call(request), _snapshot_call(request))
    results = (_stes_result(), _snapshot_result())
    plan = _plan(EvidenceRoute.DATA, request, calls=calls)

    packet = assembler_module._assemble_evidence_packet(
        request=request,
        plan=plan,
        tool_results=results,
    )

    assert packet.status is PacketStatus.COMPLETE
    assert not packet.documents
    assert tuple(item.evidence_kind for item in packet.observations) == (
        "vintage_observation",
        "latest_snapshot",
    )
    assert results[0].payload is not None
    assert packet.observations[0] is not results[0].payload


def test_complete_documents_and_data_packet_exposes_exact_success_payloads() -> None:
    request = _request(language="en")
    document = _document_evidence(language="en")
    calls = (_document_call(request), _snapshot_call(request))
    results = (
        _document_result(matches=(document,)),
        _snapshot_result(),
    )

    packet = assembler_module._assemble_evidence_packet(
        request=request,
        plan=_plan(EvidenceRoute.DOCUMENTS_AND_DATA, request, calls=calls),
        tool_results=results,
    )

    assert packet.status is PacketStatus.COMPLETE
    assert packet.documents == (document,)
    assert packet.observations == (_snapshot_evidence(),)


def test_cross_call_duplicates_are_preserved_without_global_deduplication() -> None:
    request = _request()
    document = _document_evidence()
    observation = _snapshot_evidence()
    calls = (
        _document_call(request, call_id="assembler-call-doc-001"),
        _document_call(request, call_id="assembler-call-doc-002"),
        _snapshot_call(request, call_id="assembler-call-snapshot-001"),
        _snapshot_call(request, call_id="assembler-call-snapshot-002"),
    )
    results = (
        _document_result(call_id=calls[0].call_id, matches=(document,)),
        _document_result(call_id=calls[1].call_id, matches=(document,)),
        _snapshot_result(call_id=calls[2].call_id, evidence=observation),
        _snapshot_result(call_id=calls[3].call_id, evidence=observation),
    )

    packet = assembler_module._assemble_evidence_packet(
        request=request,
        plan=_plan(EvidenceRoute.DOCUMENTS_AND_DATA, request, calls=calls),
        tool_results=results,
    )

    assert packet.documents == (document, document)
    assert packet.observations == (observation, observation)


@pytest.mark.parametrize("terminal_position", [0, 1])
def test_tool_abstention_returns_empty_packet_for_terminal_success_prefix(
    terminal_position: int,
) -> None:
    request = _request()
    calls = (_document_call(request), _snapshot_call(request))
    if terminal_position == 0:
        results = (_document_abstention(),)
        expected_call_id = calls[0].call_id
        expected_code = "no-temporal-document-match"
    else:
        results = (_document_result(), _snapshot_abstention())
        expected_call_id = calls[1].call_id
        expected_code = "no-snapshot-available-by-cutoff"

    packet = assembler_module._assemble_evidence_packet(
        request=request,
        plan=_plan(EvidenceRoute.DOCUMENTS_AND_DATA, request, calls=calls),
        tool_results=results,
    )

    assert packet.status is PacketStatus.ABSTAINED
    assert packet.abstention is not None
    assert packet.abstention.origin is AbstentionOrigin.TOOL
    assert packet.abstention.origin_call_id == expected_call_id
    assert packet.abstention.reason_code == expected_code
    expected_message = (
        "No cutoff-safe document matched the request."
        if terminal_position == 0
        else "No eligible snapshot exists by the cutoff."
    )
    assert packet.abstention.message == expected_message
    assert not packet.documents
    assert not packet.observations


@pytest.mark.parametrize(
    ("route", "results", "expected_code"),
    [
        (EvidenceRoute.DOCUMENTS, (), "incomplete_result_sequence"),
        (
            EvidenceRoute.DOCUMENTS_AND_DATA,
            (_document_result(),),
            "incomplete_result_sequence",
        ),
    ],
)
def test_non_abstain_routes_reject_missing_or_incomplete_success(
    route: EvidenceRoute,
    results: tuple[Any, ...],
    expected_code: str,
) -> None:
    request = _request()

    with pytest.raises(assembler_module._PacketAssemblyError) as exc_info:
        assembler_module._assemble_evidence_packet(
            request=request,
            plan=_plan(route, request),
            tool_results=results,
        )

    assert exc_info.value.code == expected_code


def test_planned_abstention_rejects_any_tool_result() -> None:
    request = _request()

    with pytest.raises(assembler_module._PacketAssemblyError) as exc_info:
        assembler_module._assemble_evidence_packet(
            request=request,
            plan=_plan(EvidenceRoute.ABSTAIN, request),
            tool_results=(_snapshot_result(),),
        )

    assert exc_info.value.code == "invalid_result_sequence"


@pytest.mark.parametrize(
    "results",
    [
        (_snapshot_result(), _document_result()),
        (_snapshot_result(call_id="assembler-call-doc-001"),),
        (_document_result(call_id="wrong-call-id"),),
    ],
)
def test_reordered_non_prefix_or_mismatched_results_fail_closed(
    results: tuple[Any, ...],
) -> None:
    request = _request()
    calls = (_document_call(request), _snapshot_call(request))

    with pytest.raises(assembler_module._PacketAssemblyError) as exc_info:
        assembler_module._assemble_evidence_packet(
            request=request,
            plan=_plan(EvidenceRoute.DOCUMENTS_AND_DATA, request, calls=calls),
            tool_results=results,
        )

    assert exc_info.value.code == "invalid_result_sequence"


def test_result_sequence_longer_than_plan_is_rejected() -> None:
    request = _request()

    with pytest.raises(assembler_module._PacketAssemblyError) as exc_info:
        assembler_module._assemble_evidence_packet(
            request=request,
            plan=_plan(EvidenceRoute.DOCUMENTS, request),
            tool_results=(
                _document_result(),
                _document_result(call_id="assembler-call-doc-002"),
            ),
        )

    assert exc_info.value.code == "invalid_result_sequence"


def test_tool_error_cannot_be_presented_as_packet_evidence() -> None:
    request = _request()
    calls = (_document_call(request), _snapshot_call(request))

    with pytest.raises(assembler_module._PacketAssemblyError) as exc_info:
        assembler_module._assemble_evidence_packet(
            request=request,
            plan=_plan(EvidenceRoute.DOCUMENTS_AND_DATA, request, calls=calls),
            tool_results=(_document_result(), _snapshot_error()),
        )

    assert exc_info.value.code == "tool_error_not_evidence"


@pytest.mark.parametrize(
    "results",
    [
        (_document_abstention(), _snapshot_result()),
        (_document_abstention(), _snapshot_abstention()),
    ],
)
def test_abstention_must_be_the_only_terminal_non_success(
    results: tuple[Any, ...],
) -> None:
    request = _request()
    calls = (_document_call(request), _snapshot_call(request))

    with pytest.raises(assembler_module._PacketAssemblyError) as exc_info:
        assembler_module._assemble_evidence_packet(
            request=request,
            plan=_plan(EvidenceRoute.DOCUMENTS_AND_DATA, request, calls=calls),
            tool_results=results,
        )

    assert exc_info.value.code == "invalid_result_sequence"


@pytest.mark.parametrize("field", ["cutoff", "question", "language"])
def test_request_plan_binding_drift_is_rejected(field: str) -> None:
    request = _request()
    if field == "cutoff":
        calls = (_snapshot_call(request, as_of=date(2026, 7, 16)),)
        route = EvidenceRoute.DATA
    else:
        calls = (
            _document_call(
                request,
                question="This is a different question." if field == "question" else None,
                language="en" if field == "language" else None,
            ),
        )
        route = EvidenceRoute.DOCUMENTS

    with pytest.raises(assembler_module._PacketAssemblyError) as exc_info:
        assembler_module._assemble_evidence_packet(
            request=request,
            plan=_plan(route, request, calls=calls),
            tool_results=(),
        )

    assert exc_info.value.code == "request_plan_drift"


@pytest.mark.parametrize(
    "result",
    [
        _document_result(matches=(_document_evidence(published_on=date(2026, 7, 18)),)),
        _document_result(matches=(_document_evidence(language="en"),)),
        _document_result(
            matches=(
                _document_evidence(chunk_id="assembler-low", score=1.0),
                _document_evidence(chunk_id="assembler-high", score=2.0),
            )
        ),
    ],
)
def test_document_payload_cutoff_language_and_order_drift_are_rejected(
    result: TemporalDocumentResult,
) -> None:
    request = _request()

    with pytest.raises(assembler_module._PacketAssemblyError) as exc_info:
        assembler_module._assemble_evidence_packet(
            request=request,
            plan=_plan(EvidenceRoute.DOCUMENTS, request),
            tool_results=(result,),
        )

    assert exc_info.value.code == "invalid_result_sequence"


@pytest.mark.parametrize(
    ("call", "result"),
    [
        (_stes_call(_request()), _stes_result(evidence=_vintage_evidence(period="2026-04"))),
        (
            _snapshot_call(_request()),
            _snapshot_result(evidence=_snapshot_evidence(period="2025Q4")),
        ),
    ],
)
def test_data_payload_scope_or_period_drift_is_rejected(
    call: Any,
    result: Any,
) -> None:
    request = _request()

    with pytest.raises(assembler_module._PacketAssemblyError) as exc_info:
        assembler_module._assemble_evidence_packet(
            request=request,
            plan=_plan(EvidenceRoute.DATA, request, calls=(call,)),
            tool_results=(result,),
        )

    assert exc_info.value.code == "invalid_result_sequence"


@pytest.mark.parametrize("value", [{"request_id": "raw"}, object()])
def test_request_must_be_the_exact_validated_model(value: object) -> None:
    request = _request()

    with pytest.raises(assembler_module._PacketAssemblyError) as exc_info:
        assembler_module._assemble_evidence_packet(
            request=value,  # type: ignore[arg-type]
            plan=_plan(EvidenceRoute.ABSTAIN, request),
            tool_results=(),
        )

    assert exc_info.value.code == "invalid_request"


def test_mutated_request_and_plan_fail_their_strict_round_trips() -> None:
    request = _request()
    changed_request = request.model_copy(deep=True)
    object.__setattr__(changed_request, "effective_as_of", date(2026, 7, 18))
    plan = _plan(EvidenceRoute.DATA, request)

    with pytest.raises(assembler_module._PacketAssemblyError) as request_error:
        assembler_module._assemble_evidence_packet(
            request=changed_request,
            plan=plan,
            tool_results=(_snapshot_result(),),
        )
    assert request_error.value.code == "invalid_request"

    changed_plan = plan.model_copy(deep=True)
    object.__setattr__(changed_plan, "route", EvidenceRoute.DOCUMENTS)
    with pytest.raises(assembler_module._PacketAssemblyError) as plan_error:
        assembler_module._assemble_evidence_packet(
            request=request,
            plan=changed_plan,
            tool_results=(_snapshot_result(),),
        )
    assert plan_error.value.code == "invalid_plan"


def test_plan_must_be_the_exact_route_plan_model() -> None:
    request = _request()

    with pytest.raises(assembler_module._PacketAssemblyError) as exc_info:
        assembler_module._assemble_evidence_packet(
            request=request,
            plan={"route": "abstain"},  # type: ignore[arg-type]
            tool_results=(),
        )

    assert exc_info.value.code == "invalid_plan"


def test_result_sequence_requires_exact_tuple_and_exact_result_models() -> None:
    request = _request()
    plan = _plan(EvidenceRoute.DATA, request)

    with pytest.raises(assembler_module._PacketAssemblyError) as list_error:
        assembler_module._assemble_evidence_packet(
            request=request,
            plan=plan,
            tool_results=[_snapshot_result()],  # type: ignore[arg-type]
        )
    assert list_error.value.code == "invalid_result_sequence"

    class ResultSubclass(SnapshotAsOfResult):
        pass

    subclassed = ResultSubclass.model_validate(_snapshot_result().model_dump(mode="python"))
    with pytest.raises(assembler_module._PacketAssemblyError) as subclass_error:
        assembler_module._assemble_evidence_packet(
            request=request,
            plan=plan,
            tool_results=(subclassed,),
        )
    assert subclass_error.value.code == "invalid_tool_result"


def test_mutated_tool_result_is_rejected_before_evidence_use() -> None:
    request = _request()
    result = _snapshot_result().model_copy(deep=True)
    object.__setattr__(result, "status", ToolOutcomeStatus.ABSTAINED)

    with pytest.raises(assembler_module._PacketAssemblyError) as exc_info:
        assembler_module._assemble_evidence_packet(
            request=request,
            plan=_plan(EvidenceRoute.DATA, request),
            tool_results=(result,),
        )

    assert exc_info.value.code == "invalid_tool_result"


def test_strict_round_trip_rejects_changed_exact_models(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    request = _request()
    plan = _plan(EvidenceRoute.DATA, request)
    result = _snapshot_result()

    changed_request = request.model_copy(
        update={"request_id": "assembler-request-changed"},
    )
    monkeypatch.setattr(
        ExecutionRequest,
        "model_validate_json",
        classmethod(lambda cls, *args, **kwargs: changed_request),
    )
    with pytest.raises(assembler_module._PacketAssemblyError) as request_error:
        assembler_module._assemble_evidence_packet(
            request=request,
            plan=plan,
            tool_results=(result,),
        )
    assert request_error.value.code == "invalid_request"
    monkeypatch.undo()

    changed_plan = _plan(
        EvidenceRoute.DATA,
        request,
        calls=(_stes_call(request),),
    )
    monkeypatch.setattr(
        RoutePlan,
        "model_validate_json",
        classmethod(lambda cls, *args, **kwargs: changed_plan),
    )
    with pytest.raises(assembler_module._PacketAssemblyError) as plan_error:
        assembler_module._assemble_evidence_packet(
            request=request,
            plan=plan,
            tool_results=(result,),
        )
    assert plan_error.value.code == "invalid_plan"
    monkeypatch.undo()

    changed_result = _snapshot_result(call_id="assembler-call-changed")
    monkeypatch.setattr(
        SnapshotAsOfResult,
        "model_validate_json",
        classmethod(lambda cls, *args, **kwargs: changed_result),
    )
    with pytest.raises(assembler_module._PacketAssemblyError) as result_error:
        assembler_module._assemble_evidence_packet(
            request=request,
            plan=plan,
            tool_results=(result,),
        )
    assert result_error.value.code == "invalid_tool_result"
    monkeypatch.undo()

    packet = assembler_module._assemble_evidence_packet(
        request=request,
        plan=plan,
        tool_results=(result,),
    )
    changed_packet = packet.model_copy(
        update={
            "request": request.model_copy(
                update={"request_id": "assembler-request-changed"},
            )
        }
    )
    monkeypatch.setattr(
        ExecutionEvidencePacket,
        "model_validate_json",
        classmethod(lambda cls, *args, **kwargs: changed_packet),
    )
    with pytest.raises(assembler_module._PacketAssemblyError) as packet_error:
        assembler_module._assemble_evidence_packet(
            request=request,
            plan=plan,
            tool_results=(result,),
        )
    assert packet_error.value.code == "packet_validation_failed"


def test_packet_round_trip_failure_is_sanitized(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    request = _request()
    secret = r"C:\private\packet.json raw=999"

    def fail_round_trip(*_: object, **__: object) -> None:
        raise RuntimeError(secret)

    monkeypatch.setattr(
        ExecutionEvidencePacket,
        "model_validate_json",
        classmethod(fail_round_trip),
    )

    with pytest.raises(assembler_module._PacketAssemblyError) as exc_info:
        assembler_module._assemble_evidence_packet(
            request=request,
            plan=_plan(EvidenceRoute.DATA, request),
            tool_results=(_snapshot_result(),),
        )

    assert exc_info.value.code == "packet_validation_failed"
    assert secret not in str(exc_info.value)


def test_unexpected_internal_failure_is_sanitized(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    request = _request()
    secret = r"C:\private\internal.json raw=999"

    def fail_unexpectedly(_: object) -> None:
        raise RuntimeError(secret)

    monkeypatch.setattr(assembler_module, "_validated_request", fail_unexpectedly)

    with pytest.raises(assembler_module._PacketAssemblyError) as exc_info:
        assembler_module._assemble_evidence_packet(
            request=request,
            plan=_plan(EvidenceRoute.DATA, request),
            tool_results=(_snapshot_result(),),
        )

    assert exc_info.value.code == "packet_assembly_failed"
    assert secret not in str(exc_info.value)


def test_defensive_private_helpers_reject_impossible_missing_payloads() -> None:
    request = _request()
    data_plan = _plan(EvidenceRoute.DATA, request)
    missing_data = _snapshot_result().model_copy(deep=True)
    object.__setattr__(missing_data, "payload", None)
    with pytest.raises(assembler_module._PacketAssemblyError) as data_error:
        assembler_module._complete_packet(
            request=request,
            plan=data_plan,
            results=(missing_data,),
        )
    assert data_error.value.code == "invalid_tool_result"

    document_plan = _plan(EvidenceRoute.DOCUMENTS, request)
    missing_document = _document_result().model_copy(deep=True)
    object.__setattr__(missing_document, "payload", None)
    with pytest.raises(assembler_module._PacketAssemblyError) as document_error:
        assembler_module._complete_packet(
            request=request,
            plan=document_plan,
            results=(missing_document,),
        )
    assert document_error.value.code == "invalid_tool_result"

    with pytest.raises(assembler_module._PacketAssemblyError) as type_error:
        assembler_module._complete_packet(
            request=request,
            plan=data_plan,
            results=(object(),),  # type: ignore[arg-type]
        )
    assert type_error.value.code == "invalid_tool_result"


def test_defensive_abstention_helpers_require_validated_reasons() -> None:
    request = _request()
    plan = _plan(EvidenceRoute.ABSTAIN, request).model_copy(deep=True)
    object.__setattr__(plan, "abstention", None)
    with pytest.raises(assembler_module._PacketAssemblyError) as plan_error:
        assembler_module._planned_abstention_packet(request=request, plan=plan)
    assert plan_error.value.code == "invalid_plan"

    result = _snapshot_abstention().model_copy(deep=True)
    object.__setattr__(result, "abstention", None)
    with pytest.raises(assembler_module._PacketAssemblyError) as result_error:
        assembler_module._tool_abstention_packet(
            request=request,
            plan=_plan(EvidenceRoute.DATA, request),
            result=result,
        )
    assert result_error.value.code == "invalid_tool_result"


def test_unsupported_terminal_status_fails_closed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    request = _request()
    result = _snapshot_result().model_copy(deep=True)
    object.__setattr__(result, "status", "unknown-terminal-status")
    monkeypatch.setattr(
        assembler_module,
        "_validated_results",
        lambda tool_results: (result,),
    )

    with pytest.raises(assembler_module._PacketAssemblyError) as exc_info:
        assembler_module._assemble_evidence_packet(
            request=request,
            plan=_plan(EvidenceRoute.DATA, request),
            tool_results=(_snapshot_result(),),
        )

    assert exc_info.value.code == "invalid_result_sequence"


@pytest.mark.parametrize("case", ["top_k", "duplicate_chunk"])
def test_document_top_k_and_intra_result_duplicates_are_rejected(case: str) -> None:
    request = _request()
    first = _document_evidence(chunk_id="assembler-chunk-first", score=3.0)
    if case == "top_k":
        call = _document_call(request, top_k=1)
        matches = (
            first,
            _document_evidence(chunk_id="assembler-chunk-second", score=2.0),
        )
    else:
        call = _document_call(request)
        matches = (first, first)

    with pytest.raises(assembler_module._PacketAssemblyError) as exc_info:
        assembler_module._assemble_evidence_packet(
            request=request,
            plan=_plan(EvidenceRoute.DOCUMENTS, request, calls=(call,)),
            tool_results=(_document_result(matches=matches),),
        )

    assert exc_info.value.code == "invalid_result_sequence"


def test_data_payload_cutoff_drift_is_rejected() -> None:
    request = _request()

    with pytest.raises(assembler_module._PacketAssemblyError) as exc_info:
        assembler_module._assemble_evidence_packet(
            request=request,
            plan=_plan(EvidenceRoute.DATA, request),
            tool_results=(
                _snapshot_result(
                    evidence=_snapshot_evidence(as_of=date(2026, 7, 18)),
                ),
            ),
        )

    assert exc_info.value.code == "invalid_result_sequence"


def test_assembler_signature_and_package_exports_keep_boundary_private() -> None:
    signature = inspect.signature(assembler_module._assemble_evidence_packet)

    assert tuple(signature.parameters) == ("request", "plan", "tool_results")
    assert all(
        parameter.kind is inspect.Parameter.KEYWORD_ONLY
        for parameter in signature.parameters.values()
    )
    for public_name in (
        "assemble_evidence_packet",
        "PacketAssembler",
        "AssemblerResult",
        "AssemblerOutput",
    ):
        assert not hasattr(assembler_module, public_name)
        assert public_name not in execution_package.__all__

    source = inspect.getsource(assembler_module)
    for forbidden_dependency in (
        "sovereignlab.execution.planner",
        "sovereignlab.execution.dispatcher",
        "ExecutionTrace",
        "dispatch_tool_call",
    ):
        assert forbidden_dependency not in source
    assert "_assemble_evidence_packet" not in execution_package.__all__
    assert "_PacketAssemblyError" not in execution_package.__all__
