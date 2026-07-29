"""Freeze the strict ADR 0008 execution and trace contract."""

import json
from datetime import UTC, date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import pytest
from pydantic import ValidationError

from sovereignlab.schemas import (
    AbstentionOrigin,
    DocumentMatchEvidence,
    DocumentRetrievalPayload,
    EvidenceLocator,
    EvidenceRoute,
    ExecutionEnvironmentProvenance,
    ExecutionEvidencePacket,
    ExecutionFailure,
    ExecutionRequest,
    ExecutionTrace,
    FailurePhase,
    NormalizedObservation,
    PacketAbstention,
    PacketStatus,
    PlanAbstention,
    PlannerMode,
    PlannerProvenance,
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
    TraceStatus,
    VintageObservationEvidence,
)

ROOT = Path(__file__).resolve().parents[2]
CUTOFF = date(2026, 7, 17)
QUESTION = "2026년 7월 17일 현재 한국의 실질 GDP는 얼마인가?"
SHA_A = "a" * 64
SHA_B = "b" * 64


def _request(
    *,
    question: str = QUESTION,
    language: str = "ko",
    requested_as_of: date | None = CUTOFF,
    effective_as_of: date = CUTOFF,
) -> ExecutionRequest:
    return ExecutionRequest(
        request_id="request-001",
        question=question,
        language=language,
        requested_as_of=requested_as_of,
        effective_as_of=effective_as_of,
    )


def _document_call(
    *,
    call_id: str = "call-doc-001",
    question: str = QUESTION,
    language: str = "ko",
    as_of: date = CUTOFF,
    top_k: int = 5,
) -> TemporalDocumentCall:
    return TemporalDocumentCall(
        call_id=call_id,
        tool_name=ToolName.RETRIEVE_TEMPORAL_DOCUMENTS,
        arguments=TemporalDocumentArguments(
            question=question,
            language=language,
            as_of=as_of,
            top_k=top_k,
        ),
    )


def _snapshot_arguments(
    *,
    source_system: str = "ecos",
    table_id: str = "200Y108",
    item_id: str = "10601",
    period: str = "2026Q1",
    as_of: date = CUTOFF,
    normalization_rule_id: str = "ecos-200y108-10601-billion-krw-v1",
) -> SnapshotAsOfArguments:
    return SnapshotAsOfArguments(
        source_system=source_system,
        table_id=table_id,
        item_id=item_id,
        period=period,
        as_of=as_of,
        normalization_rule_id=normalization_rule_id,
    )


def _snapshot_call(
    *,
    call_id: str = "call-snapshot-001",
    arguments: SnapshotAsOfArguments | None = None,
) -> SnapshotAsOfCall:
    return SnapshotAsOfCall(
        call_id=call_id,
        tool_name=ToolName.READ_SNAPSHOT_AS_OF,
        arguments=arguments or _snapshot_arguments(),
    )


def _stes_arguments(
    *,
    as_of: date = CUTOFF,
    period: str = "2026-05",
) -> StesAsOfArguments:
    return StesAsOfArguments(
        ref_area="KOR",
        freq="M",
        measure="LI_AA",
        unit_measure="IX",
        activity="_T",
        period=period,
        as_of=as_of,
        normalization_rule_id="oecd-stes-kor-li-aa-index-v1",
    )


def _stes_call(
    *,
    call_id: str = "call-stes-001",
    arguments: StesAsOfArguments | None = None,
) -> StesAsOfCall:
    return StesAsOfCall(
        call_id=call_id,
        tool_name=ToolName.RESOLVE_STES_AS_OF,
        arguments=arguments or _stes_arguments(),
    )


def _normalization(
    *,
    raw_value: str = "123.45",
    normalization_rule_id: str = "ecos-200y108-10601-billion-krw-v1",
    normalized_value: str = "123.45",
    canonical_unit: str = "billion_krw",
    display_places: int = 1,
    display_value: str = "123.5",
) -> NormalizedObservation:
    return NormalizedObservation(
        raw_value=raw_value,
        normalization_rule_id=normalization_rule_id,
        normalized_value=normalized_value,
        canonical_unit=canonical_unit,
        display_places=display_places,
        display_value=display_value,
    )


def _document_evidence(
    *,
    chunk_id: str = "chunk-ko-001",
    source_id: str = "synthetic-doc-ko",
    language: str = "ko",
    published_on: date = date(2026, 5, 28),
    text: str = "합성 문서 근거입니다.",
    score: float = 2.5,
) -> DocumentMatchEvidence:
    return DocumentMatchEvidence(
        chunk_id=chunk_id,
        source_id=source_id,
        source_sha256=SHA_A,
        language=language,
        published_on=published_on,
        locator=EvidenceLocator(page=7, section="합성 전망"),
        text=text,
        score=score,
    )


def _snapshot_evidence(
    *,
    source_system: str = "ecos",
    table_id: str = "200Y108",
    item_id: str = "10601",
    period: str = "2026Q1",
    as_of: date = CUTOFF,
    source_published_on: date = CUTOFF,
    source_retrieved_at: datetime = datetime(2026, 7, 17, 11, 52, 43, tzinfo=UTC),
    observation: NormalizedObservation | None = None,
) -> SnapshotObservationEvidence:
    return SnapshotObservationEvidence(
        evidence_kind="latest_snapshot",
        source_id="ecos-gdp-snapshot-001",
        source_sha256=SHA_B,
        source_system=source_system,
        source_published_on=source_published_on,
        source_retrieved_at=source_retrieved_at,
        rights_catalog_id="rights-catalog-001",
        rights_decision_id="ecos-gdp-rights-v1",
        as_of=as_of,
        table_id=table_id,
        item_id=item_id,
        period=period,
        observation=observation or _normalization(),
    )


def _vintage_evidence(
    *,
    as_of: date = CUTOFF,
    period: str = "2026-05",
) -> VintageObservationEvidence:
    return VintageObservationEvidence(
        evidence_kind="vintage_observation",
        source_id="oecd-stes-cli-snapshot-001",
        source_sha256=SHA_A,
        source_published_on=date(2026, 7, 17),
        source_retrieved_at=datetime(2026, 7, 17, 11, 53, 2, tzinfo=UTC),
        rights_catalog_id="rights-catalog-001",
        rights_decision_id="oecd-cli-rights-v1",
        ledger_id="oecd-stes-ledger-001",
        dataflow_id="DSD_STES_REVISIONS@DF_STES_REVISIONS",
        dataflow_version="1.0",
        as_of=as_of,
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


def _document_result(
    *,
    call_id: str = "call-doc-001",
    evidence: DocumentMatchEvidence | None = None,
) -> TemporalDocumentResult:
    return TemporalDocumentResult(
        call_id=call_id,
        tool_name=ToolName.RETRIEVE_TEMPORAL_DOCUMENTS,
        status=ToolOutcomeStatus.SUCCESS,
        payload=DocumentRetrievalPayload(matches=(evidence or _document_evidence(),)),
    )


def _snapshot_result(
    *,
    call_id: str = "call-snapshot-001",
    evidence: SnapshotObservationEvidence | None = None,
) -> SnapshotAsOfResult:
    return SnapshotAsOfResult(
        call_id=call_id,
        tool_name=ToolName.READ_SNAPSHOT_AS_OF,
        status=ToolOutcomeStatus.SUCCESS,
        payload=evidence or _snapshot_evidence(),
    )


def _stes_result(
    *,
    call_id: str = "call-stes-001",
    evidence: VintageObservationEvidence | None = None,
) -> StesAsOfResult:
    return StesAsOfResult(
        call_id=call_id,
        tool_name=ToolName.RESOLVE_STES_AS_OF,
        status=ToolOutcomeStatus.SUCCESS,
        payload=evidence or _vintage_evidence(),
    )


def _plan(route: EvidenceRoute) -> RoutePlan:
    calls = {
        EvidenceRoute.DOCUMENTS: (_document_call(),),
        EvidenceRoute.DATA: (_snapshot_call(),),
        EvidenceRoute.DOCUMENTS_AND_DATA: (_document_call(), _snapshot_call()),
        EvidenceRoute.ABSTAIN: (),
    }[route]
    return RoutePlan(
        route=route,
        tool_calls=calls,
        abstention=PlanAbstention(
            reason_code="planned-abstention",
            message="질문에 검증 가능한 근거가 없습니다.",
        )
        if route is EvidenceRoute.ABSTAIN
        else None,
    )


def _packet(
    route: EvidenceRoute,
    *,
    request: ExecutionRequest | None = None,
) -> ExecutionEvidencePacket:
    documents = {
        EvidenceRoute.DOCUMENTS: (_document_evidence(),),
        EvidenceRoute.DATA: (),
        EvidenceRoute.DOCUMENTS_AND_DATA: (_document_evidence(),),
    }.get(route, ())
    observations = {
        EvidenceRoute.DOCUMENTS: (),
        EvidenceRoute.DATA: (_snapshot_evidence(),),
        EvidenceRoute.DOCUMENTS_AND_DATA: (_snapshot_evidence(),),
    }.get(route, ())
    if route is EvidenceRoute.ABSTAIN:
        return ExecutionEvidencePacket(
            request=request or _request(),
            planned_route=route,
            status=PacketStatus.ABSTAINED,
            abstention=PacketAbstention(
                origin=AbstentionOrigin.PLAN,
                reason_code="planned-abstention",
                message="질문에 검증 가능한 근거가 없습니다.",
            ),
        )
    return ExecutionEvidencePacket(
        request=request or _request(),
        planned_route=route,
        status=PacketStatus.COMPLETE,
        documents=documents,
        observations=observations,
    )


def _environment() -> ExecutionEnvironmentProvenance:
    return ExecutionEnvironmentProvenance(
        executor_id="sovereignlab-executor-v1",
        executor_sha256="c" * 64,
        tool_registry_id="tool-registry-v1",
        tool_registry_sha256="d" * 64,
        artifact_registry_id="artifact-registry-v1",
        artifact_registry_sha256="e" * 64,
        retrieval_corpus_id="retrieval-corpus-v1",
        retrieval_corpus_sha256="f" * 64,
    )


def _trace(
    route: EvidenceRoute = EvidenceRoute.DOCUMENTS_AND_DATA,
) -> ExecutionTrace:
    results = {
        EvidenceRoute.DOCUMENTS: (_document_result(),),
        EvidenceRoute.DATA: (_snapshot_result(),),
        EvidenceRoute.DOCUMENTS_AND_DATA: (_document_result(), _snapshot_result()),
        EvidenceRoute.ABSTAIN: (),
    }[route]
    return ExecutionTrace(
        trace_id=f"trace-{route.value.replace('_', '-')}",
        recorded_at=datetime(2026, 7, 29, 3, 0, tzinfo=UTC),
        request=_request(),
        environment=_environment(),
        planner=PlannerProvenance(planner_id="scripted-planner-v1", mode=PlannerMode.SCRIPTED),
        status=TraceStatus.ABSTAINED if route is EvidenceRoute.ABSTAIN else TraceStatus.COMPLETE,
        plan=_plan(route),
        tool_results=results,
        evidence_packet=_packet(route),
    )


def _as_payload(model: Any, **updates: Any) -> dict[str, Any]:
    payload = model.model_dump(mode="python")
    payload.update(updates)
    return payload


def test_request_records_an_effective_cutoff_when_as_of_is_omitted() -> None:
    request = _request(requested_as_of=None)

    assert request.requested_as_of is None
    assert request.effective_as_of == CUTOFF


def test_request_rejects_rewritten_explicit_cutoff() -> None:
    with pytest.raises(ValidationError, match="must equal"):
        _request(effective_as_of=date(2026, 7, 18))


def test_gold_stes_arguments_validate_without_translation() -> None:
    records = [
        json.loads(line)
        for line in (ROOT / "data" / "benchmark" / "core" / "core-batch-001.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
    ]

    for record in records[:2]:
        arguments = record["tool_expectations"][0]["arguments"]
        assert StesAsOfArguments.model_validate(arguments).model_dump(mode="json") == arguments

    assert set(StesAsOfArguments.model_json_schema()["properties"]) == {
        "activity",
        "as_of",
        "freq",
        "measure",
        "normalization_rule_id",
        "period",
        "ref_area",
        "unit_measure",
    }


def test_stes_contract_cross_binds_dimensions_rule_and_frequency() -> None:
    gdp = StesAsOfArguments(
        ref_area="KOR",
        freq="Q",
        measure="B1GQ_Q",
        unit_measure="XDC",
        activity="_T",
        period="2025-Q1",
        as_of=CUTOFF,
        normalization_rule_id="oecd-stes-kor-b1gq-q-xdc-billion-krw-v1",
    )
    assert gdp.measure == "B1GQ_Q"

    for updates, message in (
        ({"ref_area": "USA"}, "scope and normalization"),
        (
            {"normalization_rule_id": "oecd-stes-kor-b1gq-q-xdc-billion-krw-v1"},
            "scope and normalization",
        ),
        ({"period": "2026-Q1"}, "period frequency"),
    ):
        payload = _stes_arguments().model_dump(mode="python")
        payload.update(updates)
        with pytest.raises(ValidationError, match=message):
            StesAsOfArguments.model_validate(payload)


@pytest.mark.parametrize(
    "period",
    (
        "xxxx-05",
        "\u0662\u0660\u0662\u0666-05",
        "2026-\u0660\u0665",
        "2026-5",
        "2026-00",
        "2026-13",
        "2026-Q0",
        "2026-Q5",
        "202605",
    ),
)
def test_stes_contract_requires_ascii_calendar_periods(period: str) -> None:
    payload = _stes_arguments().model_dump(mode="python")
    payload["period"] = period

    with pytest.raises(ValidationError):
        StesAsOfArguments.model_validate(payload)


@pytest.mark.parametrize(
    (
        "source_system",
        "table_id",
        "item_id",
        "period",
        "normalization_rule_id",
    ),
    [
        (
            "ecos",
            "200Y108",
            "10601",
            "2026Q1",
            "ecos-200y108-10601-billion-krw-v1",
        ),
        (
            "ecos",
            "301Y017",
            "SA000",
            "202605",
            "ecos-301y017-sa000-million-usd-v1",
        ),
        (
            "kosis",
            "DT_1J22003",
            "T/T10",
            "202606",
            "kosis-101-dt-1j22003-t-t10-index-v1",
        ),
    ],
)
def test_snapshot_flat_arguments_accept_only_approved_units(
    source_system: str,
    table_id: str,
    item_id: str,
    period: str,
    normalization_rule_id: str,
) -> None:
    arguments = _snapshot_arguments(
        source_system=source_system,
        table_id=table_id,
        item_id=item_id,
        period=period,
        normalization_rule_id=normalization_rule_id,
    )

    assert set(arguments.model_dump()) == {
        "source_system",
        "table_id",
        "item_id",
        "period",
        "as_of",
        "normalization_rule_id",
    }
    assert set(SnapshotAsOfArguments.model_json_schema()["properties"]) == set(
        arguments.model_dump()
    )


@pytest.mark.parametrize(
    "updates",
    [
        {"source_system": "oecd"},
        {"table_id": "200Y999"},
        {"item_id": "neighbor"},
        {"normalization_rule_id": "ecos-301y017-sa000-million-usd-v1"},
        {"period": "202601"},
        {"source_system": "kosis"},
    ],
)
def test_snapshot_arguments_reject_unknown_or_inconsistent_scope(
    updates: dict[str, str],
) -> None:
    payload = _snapshot_arguments().model_dump(mode="python")
    payload.update(updates)

    with pytest.raises(ValidationError):
        SnapshotAsOfArguments.model_validate(payload)


@pytest.mark.parametrize(
    "forbidden",
    ["source_id", "path", "manifest", "ledger", "raw_bytes", "snapshot_timestamp"],
)
def test_snapshot_arguments_reject_model_selected_artifacts(forbidden: str) -> None:
    payload = _snapshot_arguments().model_dump(mode="python")
    payload[forbidden] = "forbidden"

    with pytest.raises(ValidationError, match="Extra inputs"):
        SnapshotAsOfArguments.model_validate(payload)


def test_snapshot_arguments_reject_quarter_for_monthly_unit() -> None:
    payload = _snapshot_arguments(
        table_id="301Y017",
        item_id="SA000",
        period="202605",
        normalization_rule_id="ecos-301y017-sa000-million-usd-v1",
    ).model_dump(mode="python")
    payload["period"] = "2026Q1"

    with pytest.raises(ValidationError, match="period frequency"):
        SnapshotAsOfArguments.model_validate(payload)


def test_callable_argument_schemas_are_closed_and_language_is_bilingual() -> None:
    assert SnapshotAsOfArguments.model_json_schema()["additionalProperties"] is False
    assert StesAsOfArguments.model_json_schema()["additionalProperties"] is False
    assert TemporalDocumentArguments.model_json_schema()["additionalProperties"] is False

    for language in ("ko", "en"):
        assert _document_call(language=language).arguments.language.value == language

    with pytest.raises(ValidationError):
        _document_call(language="und")


@pytest.mark.parametrize("route", list(EvidenceRoute))
def test_route_plan_accepts_all_four_routes(route: EvidenceRoute) -> None:
    plan = _plan(route)

    assert plan.route is route


@pytest.mark.parametrize(
    ("route", "calls", "reason", "message"),
    [
        (EvidenceRoute.DOCUMENTS, (), None, "inconsistent"),
        (EvidenceRoute.DATA, (_document_call(),), None, "inconsistent"),
        (
            EvidenceRoute.DOCUMENTS_AND_DATA,
            (_document_call(),),
            None,
            "inconsistent",
        ),
        (EvidenceRoute.ABSTAIN, (_document_call(),), "no", "cannot contain"),
        (EvidenceRoute.ABSTAIN, (), None, "requires"),
        (EvidenceRoute.DOCUMENTS, (_document_call(),), "no", "cannot contain"),
    ],
)
def test_route_plan_rejects_inconsistent_shapes(
    route: EvidenceRoute,
    calls: tuple[Any, ...],
    reason: str | None,
    message: str,
) -> None:
    abstention = (
        PlanAbstention(reason_code="planned-abstention", message=reason)
        if reason is not None
        else None
    )
    with pytest.raises(ValidationError, match=message):
        RoutePlan(route=route, tool_calls=calls, abstention=abstention)


def test_route_plan_rejects_duplicate_call_ids() -> None:
    with pytest.raises(ValidationError, match="unique"):
        RoutePlan(
            route=EvidenceRoute.DOCUMENTS_AND_DATA,
            tool_calls=(_document_call(call_id="duplicate"), _snapshot_call(call_id="duplicate")),
        )


def test_route_plan_rejects_unknown_tool_name() -> None:
    payload = _plan(EvidenceRoute.DATA).model_dump(mode="json")
    payload["tool_calls"][0]["tool_name"] = "read_arbitrary_file"

    with pytest.raises(ValidationError):
        RoutePlan.model_validate(payload)


@pytest.mark.parametrize(
    ("updates", "message"),
    [
        ({"normalized_value": "999"}, "normalized_value"),
        ({"canonical_unit": "bogus_unit"}, "canonical_unit"),
        ({"display_places": 2, "display_value": "123.45"}, "display_places"),
        ({"display_value": "123.4"}, "display_value"),
    ],
)
def test_normalized_observation_freezes_rule_and_display(
    updates: dict[str, Any],
    message: str,
) -> None:
    assert _normalization().display_value == "123.5"

    payload = _normalization().model_dump(mode="python")
    payload.update(updates)
    with pytest.raises(ValidationError, match=message):
        NormalizedObservation.model_validate(payload)


def test_normalization_contract_applies_non_identity_multiplier() -> None:
    observation = _normalization(
        raw_value="1000000000",
        normalization_rule_id="oecd-stes-kor-b1gq-q-xdc-billion-krw-v1",
        normalized_value="1.000000000",
        canonical_unit="billion_krw",
        display_places=1,
        display_value="1.0",
    )

    assert observation.normalized_value == "1.000000000"


def test_snapshot_evidence_rejects_post_cutoff_publication_or_retrieval() -> None:
    with pytest.raises(ValidationError, match="published after"):
        _snapshot_evidence(source_published_on=date(2026, 7, 18))

    with pytest.raises(ValidationError, match="retrieved after"):
        _snapshot_evidence(
            source_retrieved_at=datetime(2026, 7, 17, 15, 0, tzinfo=UTC),
        )


def test_public_observation_evidence_rejects_scope_rule_mismatch() -> None:
    snapshot_payload = _snapshot_evidence().model_dump(mode="python")
    snapshot_payload["source_system"] = "kosis"
    with pytest.raises(ValidationError, match="snapshot scope"):
        SnapshotObservationEvidence.model_validate(snapshot_payload)

    vintage_payload = _vintage_evidence().model_dump(mode="python")
    vintage_payload["measure"] = "B1GQ_Q"
    with pytest.raises(ValidationError, match="STES scope"):
        VintageObservationEvidence.model_validate(vintage_payload)


def test_large_finite_decimal_does_not_escape_as_decimal_exception() -> None:
    value = "9" * 120
    observation = _normalization(
        raw_value=value,
        normalized_value=value,
        display_value=f"{value}.0",
    )

    assert observation.raw_value == value


@pytest.mark.parametrize(
    ("model", "field"),
    [
        (TemporalDocumentCall, "tool_name"),
        (StesAsOfCall, "tool_name"),
        (SnapshotAsOfCall, "tool_name"),
        (TemporalDocumentResult, "tool_name"),
        (StesAsOfResult, "tool_name"),
        (SnapshotAsOfResult, "tool_name"),
        (VintageObservationEvidence, "evidence_kind"),
        (SnapshotObservationEvidence, "evidence_kind"),
    ],
)
def test_discriminator_fields_are_required_in_json_schema(
    model: type[Any],
    field: str,
) -> None:
    assert field in model.model_json_schema()["required"]


@pytest.mark.parametrize(
    ("phase", "call_id"),
    [
        (FailurePhase.TOOL_EXECUTION, None),
        (FailurePhase.PLANNER, "call-001"),
    ],
)
def test_failure_call_id_is_bound_to_tool_execution(
    phase: FailurePhase,
    call_id: str | None,
) -> None:
    with pytest.raises(ValidationError, match="only tool_execution"):
        ExecutionFailure(
            phase=phase,
            code="failure",
            message="sanitized failure",
            call_id=call_id,
        )


def test_each_tool_result_accepts_its_typed_success_payload() -> None:
    assert _document_result().payload is not None
    assert _stes_result().payload is not None
    assert _snapshot_result().payload is not None


@pytest.mark.parametrize(
    ("model", "tool_name"),
    [
        (TemporalDocumentResult, ToolName.RETRIEVE_TEMPORAL_DOCUMENTS),
        (StesAsOfResult, ToolName.RESOLVE_STES_AS_OF),
        (SnapshotAsOfResult, ToolName.READ_SNAPSHOT_AS_OF),
    ],
)
def test_tool_result_accepts_abstention(model: type[Any], tool_name: ToolName) -> None:
    result = model(
        call_id="call-001",
        tool_name=tool_name,
        status=ToolOutcomeStatus.ABSTAINED,
        abstention=ToolAbstention(reason_code="no-evidence", message="No cutoff-safe evidence."),
    )

    assert result.status is ToolOutcomeStatus.ABSTAINED


@pytest.mark.parametrize(
    ("model", "tool_name"),
    [
        (TemporalDocumentResult, ToolName.RETRIEVE_TEMPORAL_DOCUMENTS),
        (StesAsOfResult, ToolName.RESOLVE_STES_AS_OF),
        (SnapshotAsOfResult, ToolName.READ_SNAPSHOT_AS_OF),
    ],
)
def test_tool_result_accepts_sanitized_tool_error(
    model: type[Any],
    tool_name: ToolName,
) -> None:
    failure = ExecutionFailure(
        phase=FailurePhase.TOOL_EXECUTION,
        code="invalid-source",
        message="Source content did not validate.",
        call_id="call-001",
    )
    result = model(
        call_id="call-001",
        tool_name=tool_name,
        status=ToolOutcomeStatus.ERROR,
        error=failure,
    )

    assert result.error == failure


def test_tool_result_status_must_match_exactly_one_outcome() -> None:
    with pytest.raises(ValidationError, match="exactly one"):
        SnapshotAsOfResult(
            call_id="call-001",
            tool_name=ToolName.READ_SNAPSHOT_AS_OF,
            status=ToolOutcomeStatus.SUCCESS,
            payload=_snapshot_evidence(),
            abstention=ToolAbstention(reason_code="conflict", message="Conflicting outcome."),
        )

    with pytest.raises(ValidationError, match="tool_execution phase"):
        SnapshotAsOfResult(
            call_id="call-001",
            tool_name=ToolName.READ_SNAPSHOT_AS_OF,
            status=ToolOutcomeStatus.ERROR,
            error=ExecutionFailure(
                phase=FailurePhase.PACKET_ASSEMBLY,
                code="wrong-phase",
                message="Wrong phase for a tool result.",
            ),
        )

    with pytest.raises(ValidationError, match="error call_id"):
        SnapshotAsOfResult(
            call_id="call-001",
            tool_name=ToolName.READ_SNAPSHOT_AS_OF,
            status=ToolOutcomeStatus.ERROR,
            error=ExecutionFailure(
                phase=FailurePhase.TOOL_EXECUTION,
                code="wrong-call",
                message="Failure belongs to another call.",
                call_id="call-002",
            ),
        )


@pytest.mark.parametrize(
    "route",
    [
        EvidenceRoute.DOCUMENTS,
        EvidenceRoute.DATA,
        EvidenceRoute.DOCUMENTS_AND_DATA,
    ],
)
def test_complete_evidence_packet_accepts_each_evidence_route(route: EvidenceRoute) -> None:
    packet = _packet(route)

    assert packet.status is PacketStatus.COMPLETE


def test_abstained_packet_exposes_no_partial_evidence() -> None:
    packet = _packet(EvidenceRoute.ABSTAIN)
    assert not packet.documents
    assert not packet.observations

    with pytest.raises(ValidationError, match="partial evidence"):
        ExecutionEvidencePacket(
            request=_request(),
            planned_route=EvidenceRoute.DATA,
            status=PacketStatus.ABSTAINED,
            observations=(_snapshot_evidence(),),
            abstention=PacketAbstention(
                origin=AbstentionOrigin.TOOL,
                origin_call_id="call-snapshot-001",
                reason_code="no-row",
                message="No selected row.",
            ),
        )

    with pytest.raises(ValidationError, match="requires abstention"):
        ExecutionEvidencePacket(
            request=_request(),
            planned_route=EvidenceRoute.DATA,
            status=PacketStatus.ABSTAINED,
        )


@pytest.mark.parametrize(
    ("origin", "origin_call_id"),
    [
        (AbstentionOrigin.TOOL, None),
        (AbstentionOrigin.PLAN, "call-001"),
    ],
)
def test_packet_abstention_binds_call_id_to_tool_origin(
    origin: AbstentionOrigin,
    origin_call_id: str | None,
) -> None:
    with pytest.raises(ValidationError, match="only tool-origin"):
        PacketAbstention(
            origin=origin,
            origin_call_id=origin_call_id,
            reason_code="no-evidence",
            message="No evidence.",
        )


def test_abstained_packet_origin_must_match_planned_route() -> None:
    with pytest.raises(ValidationError, match="origin differs"):
        ExecutionEvidencePacket(
            request=_request(),
            planned_route=EvidenceRoute.ABSTAIN,
            status=PacketStatus.ABSTAINED,
            abstention=PacketAbstention(
                origin=AbstentionOrigin.TOOL,
                origin_call_id="call-001",
                reason_code="wrong-origin",
                message="Wrong origin.",
            ),
        )


@pytest.mark.parametrize(
    ("route", "documents", "observations", "abstention", "message"),
    [
        (EvidenceRoute.ABSTAIN, (), (), None, "cannot produce"),
        (
            EvidenceRoute.DATA,
            (),
            (_snapshot_evidence(),),
            PacketAbstention(
                origin=AbstentionOrigin.TOOL,
                origin_call_id="call-snapshot-001",
                reason_code="conflict",
                message="Conflict.",
            ),
            "cannot contain",
        ),
        (EvidenceRoute.DOCUMENTS, (), (_snapshot_evidence(),), None, "inconsistent"),
    ],
)
def test_complete_packet_rejects_inconsistent_shape(
    route: EvidenceRoute,
    documents: tuple[DocumentMatchEvidence, ...],
    observations: tuple[Any, ...],
    abstention: PacketAbstention | None,
    message: str,
) -> None:
    with pytest.raises(ValidationError, match=message):
        ExecutionEvidencePacket(
            request=_request(),
            planned_route=route,
            status=PacketStatus.COMPLETE,
            documents=documents,
            observations=observations,
            abstention=abstention,
        )


def test_packet_rejects_post_cutoff_document_and_mismatched_observation_cutoff() -> None:
    with pytest.raises(ValidationError, match="document evidence"):
        ExecutionEvidencePacket(
            request=_request(),
            planned_route=EvidenceRoute.DOCUMENTS,
            status=PacketStatus.COMPLETE,
            documents=(_document_evidence(published_on=date(2026, 7, 18)),),
        )

    with pytest.raises(ValidationError, match="observation evidence"):
        ExecutionEvidencePacket(
            request=_request(),
            planned_route=EvidenceRoute.DATA,
            status=PacketStatus.COMPLETE,
            observations=(_vintage_evidence(as_of=date(2026, 7, 16)),),
        )


def test_planner_provenance_distinguishes_scripted_recorded_and_replay() -> None:
    scripted = PlannerProvenance(planner_id="scripted-planner", mode=PlannerMode.SCRIPTED)
    recorded = PlannerProvenance(
        planner_id="recorded-planner",
        mode=PlannerMode.RECORDED,
        recording_id="recording-001",
        output_sha256=SHA_A,
        model_id="model/checkpoint",
    )
    replay = PlannerProvenance(
        planner_id="replay-planner",
        mode=PlannerMode.REPLAY,
        recording_id="recording-001",
        output_sha256=SHA_A,
        model_id="model/checkpoint",
    )

    assert (scripted.mode, recorded.mode, replay.mode) == (
        PlannerMode.SCRIPTED,
        PlannerMode.RECORDED,
        PlannerMode.REPLAY,
    )

    digest_linked_script = PlannerProvenance(
        planner_id="scripted-planner",
        mode=PlannerMode.SCRIPTED,
        recording_id="recording-001",
        output_sha256=SHA_A,
    )
    assert digest_linked_script.recording_id == "recording-001"

    with pytest.raises(ValidationError, match="appear together"):
        PlannerProvenance(
            planner_id="scripted-planner",
            mode=PlannerMode.SCRIPTED,
            recording_id="recording-001",
        )

    with pytest.raises(ValidationError, match="cannot claim a model_id"):
        PlannerProvenance(
            planner_id="scripted-planner",
            mode=PlannerMode.SCRIPTED,
            model_id="model/checkpoint",
        )

    with pytest.raises(ValidationError, match="complete recording"):
        PlannerProvenance(planner_id="recorded-planner", mode=PlannerMode.RECORDED)


@pytest.mark.parametrize("route", list(EvidenceRoute))
def test_trace_round_trips_for_all_four_routes(route: EvidenceRoute) -> None:
    trace = _trace(route)

    assert ExecutionTrace.model_validate_json(trace.model_dump_json()) == trace


def test_trace_rejects_non_utc_recording_timestamp() -> None:
    payload = _trace().model_dump(mode="python")
    payload["recorded_at"] = datetime(
        2026,
        7,
        29,
        12,
        0,
        tzinfo=timezone(timedelta(hours=9)),
    )

    with pytest.raises(ValidationError, match="UTC"):
        ExecutionTrace.model_validate(payload)


@pytest.mark.parametrize(
    ("updates", "message"),
    [
        ({"plan": None}, "requires plan"),
        ({"evidence_packet": None}, "requires plan"),
        (
            {
                "failure": ExecutionFailure(
                    phase=FailurePhase.PACKET_ASSEMBLY,
                    code="unexpected",
                    message="Unexpected failure.",
                )
            },
            "cannot contain failure",
        ),
    ],
)
def test_terminal_trace_requires_exact_top_level_shape(
    updates: dict[str, Any],
    message: str,
) -> None:
    payload = _as_payload(_trace(), **updates)

    with pytest.raises(ValidationError, match=message):
        ExecutionTrace.model_validate(payload)


def test_trace_rejects_packet_request_or_route_drift() -> None:
    trace = _trace(EvidenceRoute.DOCUMENTS)
    changed_request = _request(question="This is a different replayable question.")
    changed_packet = _packet(EvidenceRoute.DOCUMENTS, request=changed_request)

    with pytest.raises(ValidationError, match="packet request"):
        ExecutionTrace.model_validate(_as_payload(trace, evidence_packet=changed_packet))

    with pytest.raises(ValidationError, match="packet route"):
        ExecutionTrace.model_validate(
            _as_payload(
                trace,
                evidence_packet=_packet(EvidenceRoute.DATA),
            )
        )


def test_complete_trace_requires_complete_packet_and_successful_results() -> None:
    trace = _trace(EvidenceRoute.DATA)
    abstained_packet = ExecutionEvidencePacket(
        request=_request(),
        planned_route=EvidenceRoute.DATA,
        status=PacketStatus.ABSTAINED,
        abstention=PacketAbstention(
            origin=AbstentionOrigin.TOOL,
            origin_call_id="call-snapshot-001",
            reason_code="no-row",
            message="No selected row.",
        ),
    )
    abstained_result = SnapshotAsOfResult(
        call_id="call-snapshot-001",
        tool_name=ToolName.READ_SNAPSHOT_AS_OF,
        status=ToolOutcomeStatus.ABSTAINED,
        abstention=ToolAbstention(reason_code="no-row", message="No selected row."),
    )

    with pytest.raises(ValidationError, match="complete evidence packet"):
        ExecutionTrace.model_validate(_as_payload(trace, evidence_packet=abstained_packet))

    with pytest.raises(ValidationError, match="successful tool results"):
        ExecutionTrace.model_validate(
            _as_payload(
                trace,
                tool_results=(abstained_result,),
                evidence_packet=_packet(EvidenceRoute.DATA),
            )
        )


def test_complete_trace_packet_must_equal_successful_result_payloads() -> None:
    trace = _trace(EvidenceRoute.DOCUMENTS)
    changed_packet = ExecutionEvidencePacket(
        request=_request(),
        planned_route=EvidenceRoute.DOCUMENTS,
        status=PacketStatus.COMPLETE,
        documents=(_document_evidence(text="다른 합성 근거입니다."),),
    )

    with pytest.raises(ValidationError, match="does not match"):
        ExecutionTrace.model_validate(_as_payload(trace, evidence_packet=changed_packet))


def test_trace_rejects_call_cutoff_and_document_query_drift() -> None:
    trace = _trace(EvidenceRoute.DOCUMENTS)
    earlier_call = _document_call(as_of=date(2026, 7, 16))
    cutoff_plan = RoutePlan(route=EvidenceRoute.DOCUMENTS, tool_calls=(earlier_call,))

    with pytest.raises(ValidationError, match="call as_of"):
        ExecutionTrace.model_validate(_as_payload(trace, plan=cutoff_plan))

    changed_call = _document_call(question="This is a different document question.")
    query_plan = RoutePlan(route=EvidenceRoute.DOCUMENTS, tool_calls=(changed_call,))
    with pytest.raises(ValidationError, match="question or language"):
        ExecutionTrace.model_validate(_as_payload(trace, plan=query_plan))


@pytest.mark.parametrize(
    "results",
    [
        (),
        (_document_result(), _document_result(call_id="call-doc-002")),
    ],
)
def test_complete_trace_requires_exact_result_count(results: tuple[Any, ...]) -> None:
    trace = _trace(EvidenceRoute.DOCUMENTS)

    with pytest.raises(ValidationError, match="call count"):
        ExecutionTrace.model_validate(_as_payload(trace, tool_results=results))


def test_trace_rejects_result_identity_or_tool_name_drift() -> None:
    trace = _trace(EvidenceRoute.DOCUMENTS)

    with pytest.raises(ValidationError, match="identity or name"):
        ExecutionTrace.model_validate(
            _as_payload(trace, tool_results=(_document_result(call_id="other-call"),))
        )

    with pytest.raises(ValidationError, match="identity or name"):
        ExecutionTrace.model_validate(
            _as_payload(
                trace,
                tool_results=(_snapshot_result(call_id="call-doc-001"),),
            )
        )


def test_trace_rejects_document_result_language_and_cutoff_drift() -> None:
    trace = _trace(EvidenceRoute.DOCUMENTS)

    with pytest.raises(ValidationError, match="language differs"):
        ExecutionTrace.model_validate(
            _as_payload(
                trace,
                tool_results=(_document_result(evidence=_document_evidence(language="en")),),
            )
        )

    with pytest.raises(ValidationError, match="post-cutoff"):
        ExecutionTrace.model_validate(
            _as_payload(
                trace,
                tool_results=(
                    _document_result(evidence=_document_evidence(published_on=date(2026, 7, 18))),
                ),
            )
        )


def test_trace_binds_document_results_to_limit_uniqueness_and_order() -> None:
    trace = _trace(EvidenceRoute.DOCUMENTS)
    low = _document_evidence(chunk_id="chunk-low", score=1.0)
    high = _document_evidence(chunk_id="chunk-high", score=3.0)

    too_many = TemporalDocumentResult(
        call_id="call-doc-001",
        tool_name=ToolName.RETRIEVE_TEMPORAL_DOCUMENTS,
        status=ToolOutcomeStatus.SUCCESS,
        payload=DocumentRetrievalPayload(matches=(high, low)),
    )
    limited_plan = RoutePlan(
        route=EvidenceRoute.DOCUMENTS,
        tool_calls=(_document_call(top_k=1),),
    )
    with pytest.raises(ValidationError, match="top_k"):
        ExecutionTrace.model_validate(
            _as_payload(trace, plan=limited_plan, tool_results=(too_many,))
        )

    duplicate = TemporalDocumentResult(
        call_id="call-doc-001",
        tool_name=ToolName.RETRIEVE_TEMPORAL_DOCUMENTS,
        status=ToolOutcomeStatus.SUCCESS,
        payload=DocumentRetrievalPayload(matches=(high, high)),
    )
    with pytest.raises(ValidationError, match="must be unique"):
        ExecutionTrace.model_validate(_as_payload(trace, tool_results=(duplicate,)))

    out_of_order = TemporalDocumentResult(
        call_id="call-doc-001",
        tool_name=ToolName.RETRIEVE_TEMPORAL_DOCUMENTS,
        status=ToolOutcomeStatus.SUCCESS,
        payload=DocumentRetrievalPayload(matches=(low, high)),
    )
    with pytest.raises(ValidationError, match="order is not deterministic"):
        ExecutionTrace.model_validate(_as_payload(trace, tool_results=(out_of_order,)))


def test_trace_rejects_vintage_and_snapshot_result_argument_drift() -> None:
    vintage_trace = ExecutionTrace(
        trace_id="trace-vintage",
        recorded_at=datetime(2026, 7, 29, 3, 0, tzinfo=UTC),
        request=_request(),
        environment=_environment(),
        planner=PlannerProvenance(planner_id="scripted-planner-v1", mode=PlannerMode.SCRIPTED),
        status=TraceStatus.COMPLETE,
        plan=RoutePlan(route=EvidenceRoute.DATA, tool_calls=(_stes_call(),)),
        tool_results=(_stes_result(),),
        evidence_packet=ExecutionEvidencePacket(
            request=_request(),
            planned_route=EvidenceRoute.DATA,
            status=PacketStatus.COMPLETE,
            observations=(_vintage_evidence(),),
        ),
    )
    changed_vintage = _vintage_evidence(period="2026-04")
    with pytest.raises(ValidationError, match="resolver arguments"):
        ExecutionTrace.model_validate(
            _as_payload(
                vintage_trace,
                tool_results=(_stes_result(evidence=changed_vintage),),
            )
        )

    snapshot_trace = _trace(EvidenceRoute.DATA)
    changed_snapshot = _snapshot_evidence(period="2025Q4")
    with pytest.raises(ValidationError, match="snapshot arguments"):
        ExecutionTrace.model_validate(
            _as_payload(
                snapshot_trace,
                tool_results=(_snapshot_result(evidence=changed_snapshot),),
            )
        )


def test_tool_level_abstention_terminates_a_successful_prefix() -> None:
    plan = RoutePlan(
        route=EvidenceRoute.DOCUMENTS_AND_DATA,
        tool_calls=(_document_call(), _snapshot_call()),
    )
    abstained_result = SnapshotAsOfResult(
        call_id="call-snapshot-001",
        tool_name=ToolName.READ_SNAPSHOT_AS_OF,
        status=ToolOutcomeStatus.ABSTAINED,
        abstention=ToolAbstention(
            reason_code="no-snapshot-by-cutoff",
            message="No eligible snapshot exists by the cutoff.",
        ),
    )
    packet = ExecutionEvidencePacket(
        request=_request(),
        planned_route=EvidenceRoute.DOCUMENTS_AND_DATA,
        status=PacketStatus.ABSTAINED,
        abstention=PacketAbstention(
            origin=AbstentionOrigin.TOOL,
            origin_call_id="call-snapshot-001",
            reason_code="no-snapshot-by-cutoff",
            message="No eligible snapshot exists by the cutoff.",
        ),
    )
    trace = ExecutionTrace(
        trace_id="trace-tool-abstention",
        recorded_at=datetime(2026, 7, 29, 3, 0, tzinfo=UTC),
        request=_request(),
        environment=_environment(),
        planner=PlannerProvenance(planner_id="scripted-planner-v1", mode=PlannerMode.SCRIPTED),
        status=TraceStatus.ABSTAINED,
        plan=plan,
        tool_results=(_document_result(), abstained_result),
        evidence_packet=packet,
    )

    assert trace.tool_results[0].status is ToolOutcomeStatus.SUCCESS
    assert trace.tool_results[-1].status is ToolOutcomeStatus.ABSTAINED

    mismatched_packet = ExecutionEvidencePacket(
        request=_request(),
        planned_route=EvidenceRoute.DOCUMENTS_AND_DATA,
        status=PacketStatus.ABSTAINED,
        abstention=PacketAbstention(
            origin=AbstentionOrigin.TOOL,
            origin_call_id="call-snapshot-001",
            reason_code="different-reason",
            message="A different abstention.",
        ),
    )
    with pytest.raises(ValidationError, match="terminal tool result"):
        ExecutionTrace.model_validate(_as_payload(trace, evidence_packet=mismatched_packet))

    for invalid_results in (
        (),
        (_document_result(),),
        (
            TemporalDocumentResult(
                call_id="call-doc-001",
                tool_name=ToolName.RETRIEVE_TEMPORAL_DOCUMENTS,
                status=ToolOutcomeStatus.ABSTAINED,
                abstention=ToolAbstention(reason_code="no-doc", message="No document."),
            ),
            abstained_result,
        ),
    ):
        with pytest.raises(ValidationError, match="terminate a successful result prefix"):
            ExecutionTrace.model_validate(_as_payload(trace, tool_results=invalid_results))


def test_planned_abstention_cannot_contain_tool_results() -> None:
    trace = _trace(EvidenceRoute.ABSTAIN)

    mismatched_packet = ExecutionEvidencePacket(
        request=_request(),
        planned_route=EvidenceRoute.ABSTAIN,
        status=PacketStatus.ABSTAINED,
        abstention=PacketAbstention(
            origin=AbstentionOrigin.PLAN,
            reason_code="different-reason",
            message="A different planned abstention.",
        ),
    )
    with pytest.raises(ValidationError, match="differs from the route plan"):
        ExecutionTrace.model_validate(_as_payload(trace, evidence_packet=mismatched_packet))

    with pytest.raises(ValidationError, match="cannot contain tool results"):
        ExecutionTrace.model_validate(_as_payload(trace, tool_results=(_snapshot_result(),)))


def test_abstained_trace_requires_abstained_packet() -> None:
    trace = _trace(EvidenceRoute.ABSTAIN)

    with pytest.raises(ValidationError, match="requires abstained"):
        ExecutionTrace.model_validate(
            _as_payload(
                trace,
                evidence_packet=ExecutionEvidencePacket(
                    request=_request(),
                    planned_route=EvidenceRoute.DOCUMENTS,
                    status=PacketStatus.COMPLETE,
                    documents=(_document_evidence(),),
                ),
                plan=_plan(EvidenceRoute.DOCUMENTS),
            )
        )


@pytest.mark.parametrize("phase", [FailurePhase.PLANNER, FailurePhase.PLAN_VALIDATION])
def test_planner_boundary_failures_have_no_execution_data(phase: FailurePhase) -> None:
    failure = ExecutionFailure(phase=phase, code="invalid-plan", message="Plan did not validate.")
    planner = (
        PlannerProvenance(
            planner_id="scripted-planner-v1",
            mode=PlannerMode.SCRIPTED,
            recording_id="invalid-plan-001",
            output_sha256=SHA_A,
        )
        if phase is FailurePhase.PLAN_VALIDATION
        else PlannerProvenance(planner_id="scripted-planner-v1", mode=PlannerMode.SCRIPTED)
    )
    trace = ExecutionTrace(
        trace_id=f"trace-{phase.value}-failure",
        recorded_at=datetime(2026, 7, 29, 3, 0, tzinfo=UTC),
        request=_request(),
        environment=_environment(),
        planner=planner,
        status=TraceStatus.FAILED,
        failure=failure,
    )

    assert trace.failure == failure

    with pytest.raises(ValidationError, match="cannot contain execution data"):
        ExecutionTrace.model_validate(_as_payload(trace, plan=_plan(EvidenceRoute.DATA)))


def test_plan_validation_failure_requires_digest_linked_candidate_output() -> None:
    with pytest.raises(ValidationError, match="digest-linked"):
        ExecutionTrace(
            trace_id="trace-undigested-plan-failure",
            recorded_at=datetime(2026, 7, 29, 3, 0, tzinfo=UTC),
            request=_request(),
            environment=_environment(),
            planner=PlannerProvenance(
                planner_id="scripted-planner-v1",
                mode=PlannerMode.SCRIPTED,
            ),
            status=TraceStatus.FAILED,
            failure=ExecutionFailure(
                phase=FailurePhase.PLAN_VALIDATION,
                code="invalid-plan",
                message="Candidate plan did not validate.",
            ),
        )


def test_failed_trace_requires_failure_and_forbids_packet() -> None:
    planner_failure = ExecutionTrace(
        trace_id="trace-planner-failure",
        recorded_at=datetime(2026, 7, 29, 3, 0, tzinfo=UTC),
        request=_request(),
        environment=_environment(),
        planner=PlannerProvenance(planner_id="scripted-planner-v1", mode=PlannerMode.SCRIPTED),
        status=TraceStatus.FAILED,
        failure=ExecutionFailure(
            phase=FailurePhase.PLANNER,
            code="planner-failed",
            message="Planner did not return a response.",
        ),
    )

    with pytest.raises(ValidationError, match="requires failure"):
        ExecutionTrace.model_validate(_as_payload(planner_failure, failure=None))

    with pytest.raises(ValidationError, match="forbids evidence packet"):
        ExecutionTrace.model_validate(
            _as_payload(
                planner_failure,
                evidence_packet=_packet(EvidenceRoute.DATA),
            )
        )


def test_tool_failure_terminates_a_successful_prefix() -> None:
    failure = ExecutionFailure(
        phase=FailurePhase.TOOL_EXECUTION,
        code="invalid-snapshot",
        message="Snapshot content did not validate.",
        call_id="call-snapshot-001",
    )
    error_result = SnapshotAsOfResult(
        call_id="call-snapshot-001",
        tool_name=ToolName.READ_SNAPSHOT_AS_OF,
        status=ToolOutcomeStatus.ERROR,
        error=failure,
    )
    trace = ExecutionTrace(
        trace_id="trace-tool-failure",
        recorded_at=datetime(2026, 7, 29, 3, 0, tzinfo=UTC),
        request=_request(),
        environment=_environment(),
        planner=PlannerProvenance(planner_id="scripted-planner-v1", mode=PlannerMode.SCRIPTED),
        status=TraceStatus.FAILED,
        plan=RoutePlan(
            route=EvidenceRoute.DOCUMENTS_AND_DATA,
            tool_calls=(_document_call(), _snapshot_call()),
        ),
        tool_results=(_document_result(), error_result),
        failure=failure,
    )

    assert trace.failure == failure

    with pytest.raises(ValidationError, match="requires a validated plan"):
        ExecutionTrace.model_validate(_as_payload(trace, plan=None))

    for invalid_results in (
        (),
        (_document_result(),),
        (
            TemporalDocumentResult(
                call_id="call-doc-001",
                tool_name=ToolName.RETRIEVE_TEMPORAL_DOCUMENTS,
                status=ToolOutcomeStatus.ABSTAINED,
                abstention=ToolAbstention(reason_code="no-doc", message="No document."),
            ),
            error_result,
        ),
    ):
        with pytest.raises(ValidationError, match="terminate a successful result prefix"):
            ExecutionTrace.model_validate(_as_payload(trace, tool_results=invalid_results))

    other_failure = ExecutionFailure(
        phase=FailurePhase.TOOL_EXECUTION,
        code="different-failure",
        message="A different sanitized failure.",
        call_id="call-snapshot-001",
    )
    with pytest.raises(ValidationError, match="terminate a successful result prefix"):
        ExecutionTrace.model_validate(_as_payload(trace, failure=other_failure))


def test_packet_assembly_failure_requires_all_successful_results() -> None:
    failure = ExecutionFailure(
        phase=FailurePhase.PACKET_ASSEMBLY,
        code="packet-invalid",
        message="Evidence packet did not validate.",
    )
    trace = ExecutionTrace(
        trace_id="trace-packet-failure",
        recorded_at=datetime(2026, 7, 29, 3, 0, tzinfo=UTC),
        request=_request(),
        environment=_environment(),
        planner=PlannerProvenance(planner_id="scripted-planner-v1", mode=PlannerMode.SCRIPTED),
        status=TraceStatus.FAILED,
        plan=_plan(EvidenceRoute.DATA),
        tool_results=(_snapshot_result(),),
        failure=failure,
    )

    assert trace.failure == failure

    abstained_result = SnapshotAsOfResult(
        call_id="call-snapshot-001",
        tool_name=ToolName.READ_SNAPSHOT_AS_OF,
        status=ToolOutcomeStatus.ABSTAINED,
        abstention=ToolAbstention(reason_code="no-row", message="No selected row."),
    )
    with pytest.raises(ValidationError, match="requires successful"):
        ExecutionTrace.model_validate(_as_payload(trace, tool_results=(abstained_result,)))
