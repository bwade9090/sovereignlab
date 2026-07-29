"""Strict contracts for the offline typed function-calling execution boundary."""

from datetime import UTC, date, datetime, time, timedelta
from decimal import ROUND_HALF_UP, Decimal, localcontext
from enum import StrEnum
from typing import Annotated, Literal
from zoneinfo import ZoneInfo

from pydantic import (
    AwareDatetime,
    Field,
    FiniteFloat,
    PositiveInt,
    StringConstraints,
    field_validator,
    model_validator,
)

from sovereignlab.schemas.availability import EditionCode
from sovereignlab.schemas.benchmark import EvidenceLocator, EvidenceRoute, QuestionText
from sovereignlab.schemas.common import (
    ExternalIdentifier,
    Identifier,
    NonEmptyText,
    Sha256,
    SourceSystem,
    StrictModel,
)
from sovereignlab.schemas.source import LanguageCode

EXECUTION_SCHEMA_VERSION = "1.0.0"

_OptionalSdmxCode = Annotated[
    str,
    StringConstraints(
        max_length=256,
        pattern=r"^(?:[A-Za-z0-9_][A-Za-z0-9._@:/-]*)?$",
    ),
]
_Period = Annotated[str, StringConstraints(min_length=1, max_length=64)]
_SnapshotPeriod = Annotated[
    str,
    StringConstraints(pattern=r"^[0-9]{4}(?:Q[1-4]|(?:0[1-9]|1[0-2]))$"),
]
_DecimalText = Annotated[
    str,
    StringConstraints(max_length=128, pattern=r"^[+-]?[0-9]+(?:\.[0-9]+)?$"),
]
_SnapshotTableId = Literal["200Y108", "301Y017", "DT_1J22003"]
_SnapshotItemId = Literal["10601", "SA000", "T/T10"]
_SnapshotNormalizationRuleId = Literal[
    "ecos-200y108-10601-billion-krw-v1",
    "ecos-301y017-sa000-million-usd-v1",
    "kosis-101-dt-1j22003-t-t10-index-v1",
]
_StesNormalizationRuleId = Literal[
    "oecd-stes-kor-li-aa-index-v1",
    "oecd-stes-kor-b1gq-q-xdc-billion-krw-v1",
]
_NormalizationRuleId = Literal[
    "ecos-200y108-10601-billion-krw-v1",
    "ecos-301y017-sa000-million-usd-v1",
    "kosis-101-dt-1j22003-t-t10-index-v1",
    "oecd-stes-kor-li-aa-index-v1",
    "oecd-stes-kor-b1gq-q-xdc-billion-krw-v1",
]

_APPROVED_SNAPSHOT_SCOPES = {
    (
        SourceSystem.ECOS,
        "200Y108",
        "10601",
    ): "ecos-200y108-10601-billion-krw-v1",
    (
        SourceSystem.ECOS,
        "301Y017",
        "SA000",
    ): "ecos-301y017-sa000-million-usd-v1",
    (
        SourceSystem.KOSIS,
        "DT_1J22003",
        "T/T10",
    ): "kosis-101-dt-1j22003-t-t10-index-v1",
}
_APPROVED_STES_SCOPES = {
    (
        "KOR",
        "M",
        "LI_AA",
        "IX",
        "_T",
    ): ("oecd-stes-kor-li-aa-index-v1", "monthly"),
    (
        "KOR",
        "Q",
        "B1GQ_Q",
        "XDC",
        "_T",
    ): ("oecd-stes-kor-b1gq-q-xdc-billion-krw-v1", "quarterly"),
}
_NORMALIZATION_CONTRACTS = {
    "ecos-200y108-10601-billion-krw-v1": (
        Decimal("1"),
        "billion_krw",
        1,
    ),
    "ecos-301y017-sa000-million-usd-v1": (
        Decimal("1"),
        "million_usd",
        1,
    ),
    "kosis-101-dt-1j22003-t-t10-index-v1": (
        Decimal("1"),
        "index_2020_100",
        2,
    ),
    "oecd-stes-kor-li-aa-index-v1": (
        Decimal("1"),
        "oecd_amplitude_adjusted_index",
        2,
    ),
    "oecd-stes-kor-b1gq-q-xdc-billion-krw-v1": (
        Decimal("0.000000001"),
        "billion_krw",
        1,
    ),
}
_SEOUL = ZoneInfo("Asia/Seoul")


def _validate_stes_scope(
    *,
    ref_area: str,
    freq: str,
    measure: str,
    unit_measure: str,
    activity: str,
    period: str,
    normalization_rule_id: str,
) -> None:
    scope = (ref_area, freq, measure, unit_measure, activity)
    expected = _APPROVED_STES_SCOPES.get(scope)
    if expected is None or expected[0] != normalization_rule_id:
        raise ValueError("STES scope and normalization rule must match a frozen Korea unit")
    is_quarterly = len(period) == 7 and period[4:6] == "-Q" and period[-1] in "1234"
    is_monthly = (
        len(period) == 7
        and period[4] == "-"
        and period[5:].isdigit()
        and 1 <= int(period[5:]) <= 12
    )
    if (expected[1] == "quarterly" and not is_quarterly) or (
        expected[1] == "monthly" and not is_monthly
    ):
        raise ValueError("STES period frequency differs from the frozen Korea unit")


def _validate_snapshot_scope(
    *,
    source_system: SourceSystem,
    table_id: str,
    item_id: str,
    period: str,
    normalization_rule_id: str,
) -> None:
    scope = (source_system, table_id, item_id)
    expected_rule = _APPROVED_SNAPSHOT_SCOPES.get(scope)
    if expected_rule != normalization_rule_id:
        raise ValueError("snapshot scope and normalization rule must match an approved unit")
    if (table_id == "200Y108") != ("Q" in period):
        raise ValueError("snapshot period frequency differs from the approved unit")


class ToolName(StrEnum):
    """The exact deterministic offline tool surface approved by ADR 0008."""

    RETRIEVE_TEMPORAL_DOCUMENTS = "retrieve_temporal_documents"
    RESOLVE_STES_AS_OF = "resolve_stes_as_of"
    READ_SNAPSHOT_AS_OF = "read_snapshot_as_of"


class ToolOutcomeStatus(StrEnum):
    """Normalized outcome states for one deterministic tool invocation."""

    SUCCESS = "success"
    ABSTAINED = "abstained"
    ERROR = "error"


class PacketStatus(StrEnum):
    """Whether an evidence packet is complete or safely abstained."""

    COMPLETE = "complete"
    ABSTAINED = "abstained"


class TraceStatus(StrEnum):
    """Terminal state of one single-shot execution trace."""

    COMPLETE = "complete"
    ABSTAINED = "abstained"
    FAILED = "failed"


class PlannerMode(StrEnum):
    """Offline planner modes plus immutable recordings of external responses."""

    SCRIPTED = "scripted"
    RECORDED = "recorded"
    REPLAY = "replay"


class FailurePhase(StrEnum):
    """The bounded execution phases in which a trace may fail."""

    PLANNER = "planner"
    PLAN_VALIDATION = "plan_validation"
    TOOL_EXECUTION = "tool_execution"
    PACKET_ASSEMBLY = "packet_assembly"


class AbstentionOrigin(StrEnum):
    """The plan or terminal tool outcome that caused a packet abstention."""

    PLAN = "plan"
    TOOL = "tool"


class ExecutionRequest(StrictModel):
    """A bilingual question with an explicit replay cutoff."""

    request_id: Identifier
    question: QuestionText
    language: Literal[LanguageCode.KOREAN, LanguageCode.ENGLISH]
    requested_as_of: date | None = None
    effective_as_of: date

    @model_validator(mode="after")
    def preserve_explicit_cutoff(self) -> "ExecutionRequest":
        if self.requested_as_of is not None and self.requested_as_of != self.effective_as_of:
            raise ValueError("effective_as_of must equal an explicit requested_as_of")
        return self


class TemporalDocumentArguments(StrictModel):
    """Callable arguments for publication-date-safe bilingual retrieval."""

    question: QuestionText
    language: Literal[LanguageCode.KOREAN, LanguageCode.ENGLISH]
    as_of: date
    top_k: PositiveInt = Field(default=5, le=20)


class StesAsOfArguments(StrictModel):
    """The frozen flat gold convention for the historical STES resolver."""

    ref_area: ExternalIdentifier
    freq: ExternalIdentifier
    measure: ExternalIdentifier
    unit_measure: _OptionalSdmxCode
    activity: _OptionalSdmxCode
    period: _Period
    as_of: date
    normalization_rule_id: _StesNormalizationRuleId

    @model_validator(mode="after")
    def enforce_frozen_scope(self) -> "StesAsOfArguments":
        _validate_stes_scope(
            ref_area=self.ref_area,
            freq=self.freq,
            measure=self.measure,
            unit_measure=self.unit_measure,
            activity=self.activity,
            period=self.period,
            normalization_rule_id=self.normalization_rule_id,
        )
        return self


class SnapshotAsOfArguments(StrictModel):
    """The frozen flat gold convention for latest-only ECOS/KOSIS snapshots."""

    source_system: Literal[SourceSystem.ECOS, SourceSystem.KOSIS]
    table_id: _SnapshotTableId
    item_id: _SnapshotItemId
    period: _SnapshotPeriod
    as_of: date
    normalization_rule_id: _SnapshotNormalizationRuleId

    @model_validator(mode="after")
    def enforce_approved_scope(self) -> "SnapshotAsOfArguments":
        _validate_snapshot_scope(
            source_system=self.source_system,
            table_id=self.table_id,
            item_id=self.item_id,
            period=self.period,
            normalization_rule_id=self.normalization_rule_id,
        )
        return self


class TemporalDocumentCall(StrictModel):
    """One native call to the temporal document retrieval adapter."""

    call_id: Identifier
    tool_name: Literal[ToolName.RETRIEVE_TEMPORAL_DOCUMENTS]
    arguments: TemporalDocumentArguments


class StesAsOfCall(StrictModel):
    """One native call to the flat historical resolver adapter."""

    call_id: Identifier
    tool_name: Literal[ToolName.RESOLVE_STES_AS_OF]
    arguments: StesAsOfArguments


class SnapshotAsOfCall(StrictModel):
    """One native call to the trusted-registry latest-only snapshot adapter."""

    call_id: Identifier
    tool_name: Literal[ToolName.READ_SNAPSHOT_AS_OF]
    arguments: SnapshotAsOfArguments


ToolCall = Annotated[
    TemporalDocumentCall | StesAsOfCall | SnapshotAsOfCall,
    Field(discriminator="tool_name"),
]


class PlanAbstention(StrictModel):
    """Structured reason for a route selected as abstain."""

    reason_code: Identifier
    message: NonEmptyText


class RoutePlan(StrictModel):
    """One complete single-shot route and its model-emitted typed calls."""

    schema_version: Literal["1.0.0"] = EXECUTION_SCHEMA_VERSION
    route: EvidenceRoute
    tool_calls: tuple[ToolCall, ...] = ()
    abstention: PlanAbstention | None = None

    @model_validator(mode="after")
    def enforce_route_shape(self) -> "RoutePlan":
        call_ids = tuple(call.call_id for call in self.tool_calls)
        if len(call_ids) != len(set(call_ids)):
            raise ValueError("route plan tool call IDs must be unique")

        if self.route is EvidenceRoute.ABSTAIN:
            if self.tool_calls:
                raise ValueError("abstain route cannot contain tool calls")
            if self.abstention is None:
                raise ValueError("abstain route requires abstention")
            return self

        if self.abstention is not None:
            raise ValueError("non-abstain route cannot contain abstention")

        has_documents = any(
            call.tool_name is ToolName.RETRIEVE_TEMPORAL_DOCUMENTS for call in self.tool_calls
        )
        has_data = any(
            call.tool_name in {ToolName.RESOLVE_STES_AS_OF, ToolName.READ_SNAPSHOT_AS_OF}
            for call in self.tool_calls
        )
        expected = {
            EvidenceRoute.DOCUMENTS: (True, False),
            EvidenceRoute.DATA: (False, True),
            EvidenceRoute.DOCUMENTS_AND_DATA: (True, True),
        }
        if (has_documents, has_data) != expected[self.route]:
            raise ValueError(f"{self.route.value} route has inconsistent typed tool calls")
        return self


class NormalizedObservation(StrictModel):
    """Exact-decimal normalization facts preserved with a selected source value."""

    raw_value: _DecimalText
    normalization_rule_id: _NormalizationRuleId
    normalized_value: _DecimalText
    canonical_unit: Identifier
    display_places: int = Field(ge=0, le=12)
    display_value: _DecimalText

    @model_validator(mode="after")
    def enforce_normalization_contract(self) -> "NormalizedObservation":
        multiplier, canonical_unit, display_places = _NORMALIZATION_CONTRACTS[
            self.normalization_rule_id
        ]
        with localcontext() as context:
            context.prec = 256
            expected_normalized = Decimal(self.raw_value) * multiplier
            if Decimal(self.normalized_value) != expected_normalized:
                raise ValueError("normalized_value must follow the frozen normalization rule")
            if self.canonical_unit != canonical_unit:
                raise ValueError("canonical_unit must follow the frozen normalization rule")
            if self.display_places != display_places:
                raise ValueError("display_places must follow the frozen normalization rule")
            quantum = Decimal(1).scaleb(-self.display_places)
            rounded = Decimal(self.normalized_value).quantize(quantum, rounding=ROUND_HALF_UP)
            expected = f"{rounded:.{self.display_places}f}"
        if self.display_value != expected:
            raise ValueError("display_value must be rounded from normalized_value")
        return self


class DocumentMatchEvidence(StrictModel):
    """One retrieved passage bound to immutable document provenance."""

    chunk_id: Identifier
    source_id: Identifier
    source_sha256: Sha256
    language: Literal[LanguageCode.KOREAN, LanguageCode.ENGLISH]
    published_on: date
    locator: EvidenceLocator
    text: NonEmptyText
    score: FiniteFloat = Field(gt=0)


class VintageObservationEvidence(StrictModel):
    """One normalized row selected through the fail-closed vintage ledger."""

    evidence_kind: Literal["vintage_observation"]
    source_id: Identifier
    source_sha256: Sha256
    source_system: Literal[SourceSystem.OECD] = SourceSystem.OECD
    source_published_on: date
    source_retrieved_at: AwareDatetime
    rights_catalog_id: Identifier
    rights_decision_id: Identifier
    ledger_id: Identifier
    dataflow_id: NonEmptyText = Field(max_length=256)
    dataflow_version: NonEmptyText = Field(max_length=64)
    as_of: date
    ref_area: ExternalIdentifier
    freq: ExternalIdentifier
    measure: ExternalIdentifier
    unit_measure: _OptionalSdmxCode
    activity: _OptionalSdmxCode
    selected_edition: EditionCode
    period: _Period
    observation: NormalizedObservation

    @model_validator(mode="after")
    def enforce_frozen_scope(self) -> "VintageObservationEvidence":
        _validate_stes_scope(
            ref_area=self.ref_area,
            freq=self.freq,
            measure=self.measure,
            unit_measure=self.unit_measure,
            activity=self.activity,
            period=self.period,
            normalization_rule_id=self.observation.normalization_rule_id,
        )
        return self


class SnapshotObservationEvidence(StrictModel):
    """One normalized row from the latest committed eligible snapshot."""

    evidence_kind: Literal["latest_snapshot"]
    source_id: Identifier
    source_sha256: Sha256
    source_system: Literal[SourceSystem.ECOS, SourceSystem.KOSIS]
    source_published_on: date
    source_retrieved_at: AwareDatetime
    rights_catalog_id: Identifier
    rights_decision_id: Identifier
    vintage_semantics: Literal["latest_only"] = "latest_only"
    as_of: date
    table_id: _SnapshotTableId
    item_id: _SnapshotItemId
    period: _SnapshotPeriod
    observation: NormalizedObservation

    @model_validator(mode="after")
    def enforce_latest_only_cutoff(self) -> "SnapshotObservationEvidence":
        _validate_snapshot_scope(
            source_system=self.source_system,
            table_id=self.table_id,
            item_id=self.item_id,
            period=self.period,
            normalization_rule_id=self.observation.normalization_rule_id,
        )
        if self.source_published_on > self.as_of:
            raise ValueError("latest-only snapshot was published after as_of")
        cutoff = datetime.combine(self.as_of, time.max, _SEOUL).astimezone(UTC)
        if self.source_retrieved_at > cutoff:
            raise ValueError("latest-only snapshot was retrieved after the as_of cutoff")
        return self


ObservationEvidence = Annotated[
    VintageObservationEvidence | SnapshotObservationEvidence,
    Field(discriminator="evidence_kind"),
]


class DocumentRetrievalPayload(StrictModel):
    """Non-empty evidence returned by the temporal retrieval adapter."""

    matches: tuple[DocumentMatchEvidence, ...] = Field(min_length=1)


class ToolAbstention(StrictModel):
    """Safe structured reason why one deterministic tool returned no evidence."""

    reason_code: Identifier
    message: NonEmptyText


class ExecutionFailure(StrictModel):
    """Sanitized failure metadata that cannot carry raw provider or artifact bytes."""

    phase: FailurePhase
    code: Identifier
    message: NonEmptyText
    call_id: Identifier | None = None

    @model_validator(mode="after")
    def bind_tool_failure_to_call(self) -> "ExecutionFailure":
        if (self.phase is FailurePhase.TOOL_EXECUTION) != (self.call_id is not None):
            raise ValueError("only tool_execution failures require call_id")
        return self


def _validate_outcome(
    *,
    call_id: str,
    status: ToolOutcomeStatus,
    payload: object | None,
    abstention: ToolAbstention | None,
    error: ExecutionFailure | None,
) -> None:
    actual = (payload is not None, abstention is not None, error is not None)
    expected = {
        ToolOutcomeStatus.SUCCESS: (True, False, False),
        ToolOutcomeStatus.ABSTAINED: (False, True, False),
        ToolOutcomeStatus.ERROR: (False, False, True),
    }
    if actual != expected[status]:
        raise ValueError("tool result status must match exactly one payload, abstention, or error")
    if error is not None and error.phase is not FailurePhase.TOOL_EXECUTION:
        raise ValueError("tool result error must use tool_execution phase")
    if error is not None and error.call_id != call_id:
        raise ValueError("tool result error call_id must match the result call_id")


class TemporalDocumentResult(StrictModel):
    """Typed result of one temporal document retrieval call."""

    call_id: Identifier
    tool_name: Literal[ToolName.RETRIEVE_TEMPORAL_DOCUMENTS]
    status: ToolOutcomeStatus
    payload: DocumentRetrievalPayload | None = None
    abstention: ToolAbstention | None = None
    error: ExecutionFailure | None = None

    @model_validator(mode="after")
    def enforce_outcome(self) -> "TemporalDocumentResult":
        _validate_outcome(
            call_id=self.call_id,
            status=self.status,
            payload=self.payload,
            abstention=self.abstention,
            error=self.error,
        )
        return self


class StesAsOfResult(StrictModel):
    """Typed result of one historical STES resolver call."""

    call_id: Identifier
    tool_name: Literal[ToolName.RESOLVE_STES_AS_OF]
    status: ToolOutcomeStatus
    payload: VintageObservationEvidence | None = None
    abstention: ToolAbstention | None = None
    error: ExecutionFailure | None = None

    @model_validator(mode="after")
    def enforce_outcome(self) -> "StesAsOfResult":
        _validate_outcome(
            call_id=self.call_id,
            status=self.status,
            payload=self.payload,
            abstention=self.abstention,
            error=self.error,
        )
        return self


class SnapshotAsOfResult(StrictModel):
    """Typed result of one latest-only snapshot read call."""

    call_id: Identifier
    tool_name: Literal[ToolName.READ_SNAPSHOT_AS_OF]
    status: ToolOutcomeStatus
    payload: SnapshotObservationEvidence | None = None
    abstention: ToolAbstention | None = None
    error: ExecutionFailure | None = None

    @model_validator(mode="after")
    def enforce_outcome(self) -> "SnapshotAsOfResult":
        _validate_outcome(
            call_id=self.call_id,
            status=self.status,
            payload=self.payload,
            abstention=self.abstention,
            error=self.error,
        )
        return self


ToolResult = Annotated[
    TemporalDocumentResult | StesAsOfResult | SnapshotAsOfResult,
    Field(discriminator="tool_name"),
]


class PacketAbstention(StrictModel):
    """Why a planned route produced no externally usable evidence packet."""

    origin: AbstentionOrigin
    origin_call_id: Identifier | None = None
    reason_code: Identifier
    message: NonEmptyText

    @model_validator(mode="after")
    def bind_origin_call(self) -> "PacketAbstention":
        if (self.origin is AbstentionOrigin.TOOL) != (self.origin_call_id is not None):
            raise ValueError("only tool-origin packet abstention requires origin_call_id")
        return self


class ExecutionEvidencePacket(StrictModel):
    """Fail-closed evidence assembled from a single route plan."""

    schema_version: Literal["1.0.0"] = EXECUTION_SCHEMA_VERSION
    request: ExecutionRequest
    planned_route: EvidenceRoute
    status: PacketStatus
    documents: tuple[DocumentMatchEvidence, ...] = ()
    observations: tuple[ObservationEvidence, ...] = ()
    abstention: PacketAbstention | None = None

    @model_validator(mode="after")
    def enforce_packet_shape(self) -> "ExecutionEvidencePacket":
        if self.status is PacketStatus.ABSTAINED:
            if self.documents or self.observations:
                raise ValueError("abstained evidence packet cannot expose partial evidence")
            if self.abstention is None:
                raise ValueError("abstained evidence packet requires abstention")
            expected_origin = (
                AbstentionOrigin.PLAN
                if self.planned_route is EvidenceRoute.ABSTAIN
                else AbstentionOrigin.TOOL
            )
            if self.abstention.origin is not expected_origin:
                raise ValueError("packet abstention origin differs from the planned route")
            return self

        if self.planned_route is EvidenceRoute.ABSTAIN:
            raise ValueError("planned abstain route cannot produce a complete evidence packet")
        if self.abstention is not None:
            raise ValueError("complete evidence packet cannot contain abstention")

        has_documents = bool(self.documents)
        has_observations = bool(self.observations)
        expected = {
            EvidenceRoute.DOCUMENTS: (True, False),
            EvidenceRoute.DATA: (False, True),
            EvidenceRoute.DOCUMENTS_AND_DATA: (True, True),
        }
        if (has_documents, has_observations) != expected[self.planned_route]:
            raise ValueError(
                f"{self.planned_route.value} packet has inconsistent assembled evidence"
            )
        if any(document.published_on > self.request.effective_as_of for document in self.documents):
            raise ValueError("document evidence was published after effective_as_of")
        if any(
            observation.as_of != self.request.effective_as_of for observation in self.observations
        ):
            raise ValueError("observation evidence cutoff differs from effective_as_of")
        return self


class ExecutionEnvironmentProvenance(StrictModel):
    """Digests required to replay deterministic tools against the same trusted inputs."""

    executor_id: Identifier
    executor_sha256: Sha256
    tool_registry_id: Identifier
    tool_registry_sha256: Sha256
    artifact_registry_id: Identifier
    artifact_registry_sha256: Sha256
    retrieval_corpus_id: Identifier
    retrieval_corpus_sha256: Sha256


class PlannerProvenance(StrictModel):
    """The offline or immutable-recording source of one canonical route plan."""

    planner_id: Identifier
    mode: PlannerMode
    recording_id: Identifier | None = None
    output_sha256: Sha256 | None = None
    model_id: NonEmptyText | None = None

    @model_validator(mode="after")
    def enforce_recording_fields(self) -> "PlannerProvenance":
        has_recording_id = self.recording_id is not None
        has_output_hash = self.output_sha256 is not None
        if has_recording_id != has_output_hash:
            raise ValueError("planner recording_id and output_sha256 must appear together")
        if self.mode is PlannerMode.SCRIPTED:
            if self.model_id is not None:
                raise ValueError("scripted planner cannot claim a model_id")
            return self
        if self.mode is not PlannerMode.SCRIPTED and (
            self.recording_id is None or self.output_sha256 is None or self.model_id is None
        ):
            raise ValueError("recorded and replay planners require complete recording metadata")
        return self


def _validate_result_against_call(call: ToolCall, result: ToolResult) -> None:
    if call.call_id != result.call_id or call.tool_name is not result.tool_name:
        raise ValueError("tool result identity or name differs from the planned call")
    if result.status is not ToolOutcomeStatus.SUCCESS:
        return

    if isinstance(call, TemporalDocumentCall):
        assert isinstance(result, TemporalDocumentResult)
        assert result.payload is not None
        matches = result.payload.matches
        if len(matches) > call.arguments.top_k:
            raise ValueError("document result exceeds the planned top_k")
        chunk_ids = tuple(match.chunk_id for match in matches)
        if len(chunk_ids) != len(set(chunk_ids)):
            raise ValueError("document result chunk IDs must be unique")
        expected_order = tuple(
            sorted(matches, key=lambda match: (-match.score, match.source_id, match.chunk_id))
        )
        if matches != expected_order:
            raise ValueError("document result order is not deterministic")
        if any(match.language != call.arguments.language for match in matches):
            raise ValueError("document result language differs from the planned call")
        if any(match.published_on > call.arguments.as_of for match in matches):
            raise ValueError("document result contains post-cutoff evidence")
        return

    if isinstance(call, StesAsOfCall):
        assert isinstance(result, StesAsOfResult)
        assert result.payload is not None
        evidence = result.payload
        arguments = call.arguments
        actual = (
            evidence.as_of,
            evidence.ref_area,
            evidence.freq,
            evidence.measure,
            evidence.unit_measure,
            evidence.activity,
            evidence.period,
            evidence.observation.normalization_rule_id,
        )
        expected = (
            arguments.as_of,
            arguments.ref_area,
            arguments.freq,
            arguments.measure,
            arguments.unit_measure,
            arguments.activity,
            arguments.period,
            arguments.normalization_rule_id,
        )
        if actual != expected:
            raise ValueError("vintage result facts differ from the planned resolver arguments")
        return

    assert isinstance(call, SnapshotAsOfCall)
    assert isinstance(result, SnapshotAsOfResult)
    assert result.payload is not None
    evidence = result.payload
    arguments = call.arguments
    actual = (
        evidence.source_system,
        evidence.table_id,
        evidence.item_id,
        evidence.period,
        evidence.as_of,
        evidence.observation.normalization_rule_id,
    )
    expected = (
        arguments.source_system,
        arguments.table_id,
        arguments.item_id,
        arguments.period,
        arguments.as_of,
        arguments.normalization_rule_id,
    )
    if actual != expected:
        raise ValueError("snapshot result facts differ from the planned snapshot arguments")


class ExecutionTrace(StrictModel):
    """Replayable single-shot plan, ordered results, and final evidence outcome."""

    schema_version: Literal["1.0.0"] = EXECUTION_SCHEMA_VERSION
    trace_id: Identifier
    recorded_at: AwareDatetime
    request: ExecutionRequest
    environment: ExecutionEnvironmentProvenance
    planner: PlannerProvenance
    status: TraceStatus
    plan: RoutePlan | None = None
    tool_results: tuple[ToolResult, ...] = ()
    evidence_packet: ExecutionEvidencePacket | None = None
    failure: ExecutionFailure | None = None

    @field_validator("recorded_at")
    @classmethod
    def require_utc_recording_time(cls, value: AwareDatetime) -> AwareDatetime:
        if value.utcoffset() != timedelta(0):
            raise ValueError("recorded_at must be a UTC instant")
        return value

    @model_validator(mode="after")
    def enforce_trace_integrity(self) -> "ExecutionTrace":
        if self.status is TraceStatus.FAILED:
            self._validate_failed_trace()
            return self

        if self.plan is None or self.evidence_packet is None:
            raise ValueError("complete or abstained trace requires plan and evidence packet")
        if self.failure is not None:
            raise ValueError("complete or abstained trace cannot contain failure")
        if self.evidence_packet.request != self.request:
            raise ValueError("evidence packet request differs from trace request")
        if self.evidence_packet.planned_route is not self.plan.route:
            raise ValueError("evidence packet route differs from planned route")

        if self.status is TraceStatus.COMPLETE:
            self._validate_request_and_result_prefix(require_full=True)
            if self.evidence_packet.status is not PacketStatus.COMPLETE:
                raise ValueError("complete trace requires complete evidence packet")
            if any(result.status is not ToolOutcomeStatus.SUCCESS for result in self.tool_results):
                raise ValueError("complete trace requires successful tool results")
            self._validate_packet_matches_results()
            return self

        if self.evidence_packet.status is not PacketStatus.ABSTAINED:
            raise ValueError("abstained trace requires abstained evidence packet")
        assert self.evidence_packet.abstention is not None
        if self.plan.route is EvidenceRoute.ABSTAIN:
            if self.tool_results:
                raise ValueError("planned abstain trace cannot contain tool results")
            assert self.plan.abstention is not None
            abstention = self.evidence_packet.abstention
            if (
                abstention.origin is not AbstentionOrigin.PLAN
                or abstention.reason_code != self.plan.abstention.reason_code
                or abstention.message != self.plan.abstention.message
            ):
                raise ValueError("planned abstention packet differs from the route plan")
            return self

        self._validate_request_and_result_prefix(require_full=False)
        if (
            not self.tool_results
            or self.tool_results[-1].status is not ToolOutcomeStatus.ABSTAINED
            or any(
                result.status is not ToolOutcomeStatus.SUCCESS for result in self.tool_results[:-1]
            )
        ):
            raise ValueError("tool-level abstention must terminate a successful result prefix")
        result = self.tool_results[-1]
        assert result.abstention is not None
        abstention = self.evidence_packet.abstention
        if (
            abstention.origin is not AbstentionOrigin.TOOL
            or abstention.origin_call_id != result.call_id
            or abstention.reason_code != result.abstention.reason_code
            or abstention.message != result.abstention.message
        ):
            raise ValueError("tool abstention packet differs from the terminal tool result")
        return self

    def _validate_request_and_result_prefix(self, *, require_full: bool) -> None:
        assert self.plan is not None
        for call in self.plan.tool_calls:
            if call.arguments.as_of != self.request.effective_as_of:
                raise ValueError("tool call as_of differs from request effective_as_of")
            if isinstance(call, TemporalDocumentCall) and (
                call.arguments.question != self.request.question
                or call.arguments.language != self.request.language
            ):
                raise ValueError("document call question or language differs from request")

        if len(self.tool_results) > len(self.plan.tool_calls) or (
            require_full and len(self.tool_results) != len(self.plan.tool_calls)
        ):
            raise ValueError("tool results must match the planned call count")
        for call, result in zip(self.plan.tool_calls, self.tool_results, strict=False):
            _validate_result_against_call(call, result)

    def _validate_packet_matches_results(self) -> None:
        assert self.evidence_packet is not None
        documents = tuple(
            match
            for result in self.tool_results
            if isinstance(result, TemporalDocumentResult)
            for match in result.payload.matches
        )
        observations = tuple(
            result.payload
            for result in self.tool_results
            if isinstance(result, (StesAsOfResult, SnapshotAsOfResult))
        )
        if (
            self.evidence_packet.documents != documents
            or self.evidence_packet.observations != observations
        ):
            raise ValueError("evidence packet does not match successful tool result payloads")

    def _validate_failed_trace(self) -> None:
        if self.failure is None or self.evidence_packet is not None:
            raise ValueError("failed trace requires failure and forbids evidence packet")
        if self.failure.phase in {FailurePhase.PLANNER, FailurePhase.PLAN_VALIDATION}:
            if self.plan is not None or self.tool_results:
                raise ValueError("planner or plan-validation failure cannot contain execution data")
            if self.failure.phase is FailurePhase.PLAN_VALIDATION and (
                self.planner.recording_id is None or self.planner.output_sha256 is None
            ):
                raise ValueError("plan-validation failure requires a digest-linked planner output")
            return
        if self.plan is None:
            raise ValueError("tool or packet failure requires a validated plan")

        self._validate_request_and_result_prefix(
            require_full=self.failure.phase is FailurePhase.PACKET_ASSEMBLY
        )
        if self.failure.phase is FailurePhase.TOOL_EXECUTION:
            if (
                not self.tool_results
                or self.tool_results[-1].status is not ToolOutcomeStatus.ERROR
                or self.tool_results[-1].error != self.failure
                or any(
                    result.status is not ToolOutcomeStatus.SUCCESS
                    for result in self.tool_results[:-1]
                )
            ):
                raise ValueError("tool failure must terminate a successful result prefix")
        elif any(result.status is not ToolOutcomeStatus.SUCCESS for result in self.tool_results):
            raise ValueError("packet-assembly failure requires successful tool results")


TOOL_ARGUMENT_MODELS: dict[ToolName, type[StrictModel]] = {
    ToolName.RETRIEVE_TEMPORAL_DOCUMENTS: TemporalDocumentArguments,
    ToolName.RESOLVE_STES_AS_OF: StesAsOfArguments,
    ToolName.READ_SNAPSHOT_AS_OF: SnapshotAsOfArguments,
}
