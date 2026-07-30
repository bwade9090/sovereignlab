"""Deterministic latest-only ECOS/KOSIS snapshot adapter."""

import hashlib
import json
from datetime import UTC, date, datetime, time
from decimal import DecimalException, localcontext
from enum import StrEnum
from zoneinfo import ZoneInfo

from pydantic import ValidationError

from sovereignlab.normalization import (
    format_display,
    normalization_rule,
    normalize_source_value,
)
from sovereignlab.schemas import (
    BenchmarkBundle,
    ExecutionFailure,
    FailurePhase,
    NormalizedObservation,
    RedistributionStatus,
    SnapshotAsOfCall,
    SnapshotAsOfResult,
    SnapshotObservationEvidence,
    SourceKind,
    SourceSystem,
    ToolAbstention,
    ToolName,
    ToolOutcomeStatus,
    VintageSemantics,
)
from sovereignlab.snapshots.registry import (
    MAX_SNAPSHOT_BYTES,
    SnapshotArtifact,
    SnapshotRegistry,
    SnapshotRegistryEntry,
    SnapshotSeriesBinding,
)

_SEOUL = ZoneInfo("Asia/Seoul")
_MAX_ROWS = 1_000
_MAX_DECIMAL_TEXT = 128


class SnapshotAbstentionReason(StrEnum):
    """Known evidence conditions that safely produce no snapshot observation."""

    NO_SNAPSHOT_AVAILABLE_BY_CUTOFF = "no_snapshot_available_by_cutoff"
    AMBIGUOUS_SNAPSHOT_FRONTIER = "ambiguous_snapshot_frontier"
    SOURCE_NOT_API = "source_not_api"
    SOURCE_NOT_LATEST_ONLY = "source_not_latest_only"
    UNSUPPORTED_MEDIA_TYPE = "unsupported_media_type"
    SOURCE_CONTENT_MISMATCH = "source_content_mismatch"
    SOURCE_SCOPE_MISMATCH = "source_scope_mismatch"
    SOURCE_UNIT_MISMATCH = "source_unit_mismatch"
    RIGHTS_VALIDATION_FAILED = "rights_validation_failed"
    INVALID_SNAPSHOT_JSON = "invalid_snapshot_json"
    MISSING_SELECTED_ROW = "missing_selected_row"
    DUPLICATE_SELECTED_ROW = "duplicate_selected_row"
    BLANK_SELECTED_OBSERVATION = "blank_selected_observation"
    INVALID_SOURCE_VALUE = "invalid_source_value"


_ABSTENTION_MESSAGES = {
    SnapshotAbstentionReason.NO_SNAPSHOT_AVAILABLE_BY_CUTOFF: (
        "No registered snapshot was available by the requested cutoff."
    ),
    SnapshotAbstentionReason.AMBIGUOUS_SNAPSHOT_FRONTIER: (
        "The latest registered snapshot frontier is ambiguous."
    ),
    SnapshotAbstentionReason.SOURCE_NOT_API: (
        "The selected artifact is not an approved API snapshot."
    ),
    SnapshotAbstentionReason.SOURCE_NOT_LATEST_ONLY: (
        "The selected artifact does not have latest-only vintage semantics."
    ),
    SnapshotAbstentionReason.UNSUPPORTED_MEDIA_TYPE: (
        "The selected snapshot media type is unsupported."
    ),
    SnapshotAbstentionReason.SOURCE_CONTENT_MISMATCH: (
        "The selected snapshot bytes do not match their manifest."
    ),
    SnapshotAbstentionReason.SOURCE_SCOPE_MISMATCH: (
        "The selected snapshot differs from its approved exact scope."
    ),
    SnapshotAbstentionReason.SOURCE_UNIT_MISMATCH: (
        "The selected snapshot source unit differs from the trusted mapping."
    ),
    SnapshotAbstentionReason.RIGHTS_VALIDATION_FAILED: (
        "The selected snapshot does not pass the approved rights contract."
    ),
    SnapshotAbstentionReason.INVALID_SNAPSHOT_JSON: (
        "The selected snapshot is not valid bounded provider JSON."
    ),
    SnapshotAbstentionReason.MISSING_SELECTED_ROW: (
        "The requested period is absent from the selected snapshot."
    ),
    SnapshotAbstentionReason.DUPLICATE_SELECTED_ROW: (
        "The requested period is ambiguous in the selected snapshot."
    ),
    SnapshotAbstentionReason.BLANK_SELECTED_OBSERVATION: (
        "The selected snapshot observation is blank."
    ),
    SnapshotAbstentionReason.INVALID_SOURCE_VALUE: (
        "The selected snapshot observation is not a plain finite decimal."
    ),
}


class _DuplicateJsonKey(ValueError):
    pass


class _InvalidJsonConstant(ValueError):
    pass


def read_snapshot_as_of(
    *,
    call: SnapshotAsOfCall,
    registry: SnapshotRegistry,
) -> SnapshotAsOfResult:
    """Read one exact observation without accepting model-selected artifacts."""

    expected_call_id = call.call_id
    arguments = call.arguments
    source_system = arguments.source_system
    table_id = arguments.table_id
    item_id = arguments.item_id
    period = arguments.period
    as_of = arguments.as_of
    normalization_rule_id = arguments.normalization_rule_id

    if type(registry) is not SnapshotRegistry:
        return _error(
            expected_call_id,
            code="snapshot_registry_misconfigured",
            message="The trusted snapshot registry is misconfigured.",
        )
    try:
        state = SnapshotRegistry.validated_state(registry)
    except Exception:
        return _error(
            expected_call_id,
            code="snapshot_registry_misconfigured",
            message="The trusted snapshot registry is misconfigured.",
        )

    entry = state.entry_for(
        source_system,
        table_id,
        item_id,
    )
    if entry is None:
        return _error(
            expected_call_id,
            code="snapshot_registry_misconfigured",
            message="The trusted snapshot registry has no binding for this validated scope.",
        )

    selection = _select_artifact(entry, as_of)
    if isinstance(selection, SnapshotAbstentionReason):
        return _abstain(expected_call_id, selection)
    artifact = selection

    try:
        manifest_reason = _validate_manifest(
            artifact,
            entry.binding,
            state,
        )
    except Exception:
        return _error(
            expected_call_id,
            code="snapshot_manifest_validation_failed",
            message="The deterministic snapshot manifest validator failed unexpectedly.",
        )
    if manifest_reason is not None:
        return _abstain(expected_call_id, manifest_reason)

    payload = artifact.archive_bytes

    if artifact.manifest.byte_size > MAX_SNAPSHOT_BYTES:
        return _abstain(
            expected_call_id,
            SnapshotAbstentionReason.SOURCE_CONTENT_MISMATCH,
        )
    if (
        len(payload) > MAX_SNAPSHOT_BYTES
        or len(payload) != artifact.manifest.byte_size
        or hashlib.sha256(payload).hexdigest() != artifact.manifest.content_sha256
    ):
        return _abstain(
            expected_call_id,
            SnapshotAbstentionReason.SOURCE_CONTENT_MISMATCH,
        )

    try:
        raw_value = _selected_raw_value(
            payload,
            entry.binding,
            period,
        )
    except Exception:
        return _error(
            expected_call_id,
            code="snapshot_parser_failed",
            message="The deterministic snapshot parser failed unexpectedly.",
        )
    if isinstance(raw_value, SnapshotAbstentionReason):
        return _abstain(expected_call_id, raw_value)

    try:
        rule = normalization_rule(
            source_system,
            table_id,
            item_id,
        )
    except ValueError:
        return _error(
            expected_call_id,
            code="snapshot_registry_misconfigured",
            message="The frozen normalization registry has no exact validated scope.",
        )
    except Exception:
        return _error(
            expected_call_id,
            code="snapshot_normalization_failed",
            message="The deterministic snapshot normalizer failed unexpectedly.",
        )
    if rule.rule_id != normalization_rule_id:
        return _error(
            expected_call_id,
            code="snapshot_registry_misconfigured",
            message="The frozen normalization registry differs from the validated call.",
        )
    try:
        with localcontext() as context:
            context.prec = 256
            normalized = normalize_source_value(rule, raw_value)
            display_value = format_display(
                normalized.exact_value,
                places=rule.recommended_display_places,
            )
        observation = NormalizedObservation(
            raw_value=raw_value,
            normalization_rule_id=rule.rule_id,
            normalized_value=format(normalized.exact_value, "f"),
            canonical_unit=normalized.unit.value,
            display_places=rule.recommended_display_places,
            display_value=display_value,
        )
    except (ArithmeticError, DecimalException, ValidationError, ValueError):
        return _abstain(
            expected_call_id,
            SnapshotAbstentionReason.INVALID_SOURCE_VALUE,
        )
    except Exception:
        return _error(
            expected_call_id,
            code="snapshot_normalization_failed",
            message="The deterministic snapshot normalizer failed unexpectedly.",
        )

    reference = artifact.manifest.rights_decision
    assert reference is not None
    evidence = SnapshotObservationEvidence(
        evidence_kind="latest_snapshot",
        source_id=artifact.manifest.source_id,
        source_sha256=artifact.manifest.content_sha256,
        source_system=source_system,
        source_published_on=artifact.manifest.published_on,
        source_retrieved_at=artifact.manifest.retrieved_at,
        rights_catalog_id=reference.catalog_id,
        rights_decision_id=reference.decision_id,
        as_of=as_of,
        table_id=table_id,
        item_id=item_id,
        period=period,
        observation=observation,
    )
    return SnapshotAsOfResult(
        call_id=expected_call_id,
        tool_name=ToolName.READ_SNAPSHOT_AS_OF,
        status=ToolOutcomeStatus.SUCCESS,
        payload=evidence,
    )


def _select_artifact(
    entry: SnapshotRegistryEntry,
    as_of: date,
) -> SnapshotArtifact | SnapshotAbstentionReason:
    cutoff = datetime.combine(as_of, time.max, _SEOUL).astimezone(UTC)
    eligible = tuple(
        artifact
        for artifact in entry.artifacts
        if artifact.manifest.published_on <= as_of and artifact.manifest.retrieved_at <= cutoff
    )
    if not eligible:
        return SnapshotAbstentionReason.NO_SNAPSHOT_AVAILABLE_BY_CUTOFF

    latest_retrieved_at = max(artifact.manifest.retrieved_at for artifact in eligible)
    frontier = tuple(
        artifact for artifact in eligible if artifact.manifest.retrieved_at == latest_retrieved_at
    )
    if len(frontier) != 1:
        return SnapshotAbstentionReason.AMBIGUOUS_SNAPSHOT_FRONTIER
    return frontier[0]


def _validate_manifest(
    artifact: SnapshotArtifact,
    binding: SnapshotSeriesBinding,
    registry: SnapshotRegistry,
) -> SnapshotAbstentionReason | None:
    manifest = artifact.manifest
    if manifest.source_kind is not SourceKind.API:
        return SnapshotAbstentionReason.SOURCE_NOT_API
    if manifest.vintage_semantics is not VintageSemantics.LATEST_ONLY:
        return SnapshotAbstentionReason.SOURCE_NOT_LATEST_ONLY
    if manifest.media_type != "application/json":
        return SnapshotAbstentionReason.UNSUPPORTED_MEDIA_TYPE

    reference = manifest.rights_decision
    if manifest.document_family != binding.document_family or not manifest.source_id.startswith(
        f"{binding.document_family}-"
    ):
        return SnapshotAbstentionReason.SOURCE_SCOPE_MISMATCH
    if reference is None or manifest.redistribution.status is not RedistributionStatus.ALLOWED:
        return SnapshotAbstentionReason.RIGHTS_VALIDATION_FAILED
    if (
        reference.source_system is not binding.source_system
        or reference.table_id != binding.table_id
        or reference.item_id != binding.item_id
        or reference.decision_id != binding.rights_decision_id
    ):
        return SnapshotAbstentionReason.SOURCE_SCOPE_MISMATCH
    try:
        BenchmarkBundle(
            sources=(manifest,),
            records=(),
            rights_catalogs=registry.rights_catalogs,
        )
    except (ValidationError, ValueError):
        return SnapshotAbstentionReason.RIGHTS_VALIDATION_FAILED
    return None


def _selected_raw_value(
    payload: bytes,
    binding: SnapshotSeriesBinding,
    period: str,
) -> str | SnapshotAbstentionReason:
    try:
        text = payload.decode("utf-8-sig")
        document = json.loads(
            text,
            object_pairs_hook=_unique_object,
            parse_constant=_reject_json_constant,
        )
    except (UnicodeDecodeError, ValueError, RecursionError):
        return SnapshotAbstentionReason.INVALID_SNAPSHOT_JSON

    if binding.source_system is SourceSystem.ECOS:
        return _selected_ecos_value(document, binding, period)
    if binding.source_system is SourceSystem.KOSIS:
        return _selected_kosis_value(document, binding, period)
    return SnapshotAbstentionReason.SOURCE_SCOPE_MISMATCH


def _selected_ecos_value(
    document: object,
    binding: SnapshotSeriesBinding,
    period: str,
) -> str | SnapshotAbstentionReason:
    if not isinstance(document, dict) or set(document) != {"StatisticSearch"}:
        return SnapshotAbstentionReason.INVALID_SNAPSHOT_JSON
    result = document["StatisticSearch"]
    if not isinstance(result, dict):
        return SnapshotAbstentionReason.INVALID_SNAPSHOT_JSON
    total = result.get("list_total_count")
    rows = result.get("row")
    if (
        type(total) is not int
        or not isinstance(rows, list)
        or not rows
        or total != len(rows)
        or len(rows) > _MAX_ROWS
    ):
        return SnapshotAbstentionReason.INVALID_SNAPSHOT_JSON

    matches: list[dict[str, object]] = []
    for row in rows:
        if not isinstance(row, dict):
            return SnapshotAbstentionReason.INVALID_SNAPSHOT_JSON
        if (
            row.get("STAT_CODE") != binding.table_id
            or row.get("ITEM_CODE1") != binding.provider_item_id
            or any(
                f"ITEM_CODE{index}" not in row or row[f"ITEM_CODE{index}"] is not None
                for index in range(2, 5)
            )
            or not _valid_provider_period(row.get("TIME"), binding.frequency)
        ):
            return SnapshotAbstentionReason.SOURCE_SCOPE_MISMATCH
        if row.get("UNIT_NAME") != binding.raw_unit:
            return SnapshotAbstentionReason.SOURCE_UNIT_MISMATCH
        if row["TIME"] == period:
            matches.append(row)
    return _raw_value_from_matches(matches, "DATA_VALUE")


def _selected_kosis_value(
    document: object,
    binding: SnapshotSeriesBinding,
    period: str,
) -> str | SnapshotAbstentionReason:
    if not isinstance(document, list) or not document or len(document) > _MAX_ROWS:
        return SnapshotAbstentionReason.INVALID_SNAPSHOT_JSON

    matches: list[dict[str, object]] = []
    expected = {
        "ORG_ID": binding.organisation_id,
        "TBL_ID": binding.table_id,
        "ITM_ID": binding.provider_item_id,
        "C1": binding.geography_id,
        "PRD_SE": binding.frequency,
    }
    for row in document:
        if not isinstance(row, dict):
            return SnapshotAbstentionReason.INVALID_SNAPSHOT_JSON
        if any(row.get(key) != value for key, value in expected.items()) or not (
            _valid_provider_period(row.get("PRD_DE"), binding.frequency)
        ):
            return SnapshotAbstentionReason.SOURCE_SCOPE_MISMATCH
        if row.get("UNIT_NM") != binding.raw_unit:
            return SnapshotAbstentionReason.SOURCE_UNIT_MISMATCH
        if row["PRD_DE"] == period:
            matches.append(row)
    return _raw_value_from_matches(matches, "DT")


def _raw_value_from_matches(
    matches: list[dict[str, object]],
    value_field: str,
) -> str | SnapshotAbstentionReason:
    if not matches:
        return SnapshotAbstentionReason.MISSING_SELECTED_ROW
    if len(matches) > 1:
        return SnapshotAbstentionReason.DUPLICATE_SELECTED_ROW
    raw_value = matches[0].get(value_field)
    if raw_value is None or raw_value == "":
        return SnapshotAbstentionReason.BLANK_SELECTED_OBSERVATION
    if not isinstance(raw_value, str):
        return SnapshotAbstentionReason.INVALID_SOURCE_VALUE
    stripped = raw_value.strip()
    if not stripped:
        return SnapshotAbstentionReason.BLANK_SELECTED_OBSERVATION
    if raw_value != stripped or len(raw_value) > _MAX_DECIMAL_TEXT:
        return SnapshotAbstentionReason.INVALID_SOURCE_VALUE
    return raw_value


def _valid_provider_period(value: object, frequency: str) -> bool:
    if not isinstance(value, str):
        return False
    if frequency == "Q":
        return (
            len(value) == 6
            and value[:4].isascii()
            and value[:4].isdigit()
            and value[4] == "Q"
            and value[5] in "1234"
        )
    return (
        frequency == "M"
        and len(value) == 6
        and value.isascii()
        and value.isdigit()
        and 1 <= int(value[4:]) <= 12
    )


def _unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise _DuplicateJsonKey(key)
        result[key] = value
    return result


def _reject_json_constant(value: str) -> object:
    raise _InvalidJsonConstant(value)


def _abstain(
    call_id: str,
    reason: SnapshotAbstentionReason,
) -> SnapshotAsOfResult:
    return SnapshotAsOfResult(
        call_id=call_id,
        tool_name=ToolName.READ_SNAPSHOT_AS_OF,
        status=ToolOutcomeStatus.ABSTAINED,
        abstention=ToolAbstention(
            reason_code=reason.value,
            message=_ABSTENTION_MESSAGES[reason],
        ),
    )


def _error(
    call_id: str,
    *,
    code: str,
    message: str,
) -> SnapshotAsOfResult:
    return SnapshotAsOfResult(
        call_id=call_id,
        tool_name=ToolName.READ_SNAPSHOT_AS_OF,
        status=ToolOutcomeStatus.ERROR,
        error=ExecutionFailure(
            phase=FailurePhase.TOOL_EXECUTION,
            code=code,
            message=message,
            call_id=call_id,
        ),
    )
