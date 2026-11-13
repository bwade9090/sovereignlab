"""Deterministic latest-only ECOS/KOSIS snapshot reader."""

import json
from datetime import UTC, date, datetime, time
from enum import StrEnum
from zoneinfo import ZoneInfo

from sovereignlab.artifacts import SourceArtifact
from sovereignlab.normalization import normalization_rule, normalized_observation
from sovereignlab.schemas import (
    SnapshotAsOfCall,
    SnapshotAsOfResult,
    SnapshotObservationEvidence,
    SourceSystem,
    ToolAbstention,
    ToolName,
    ToolOutcomeStatus,
)
from sovereignlab.snapshots.registry import (
    SnapshotRegistry,
    SnapshotRegistryEntry,
    SnapshotSeriesBinding,
)

_SEOUL = ZoneInfo("Asia/Seoul")


class SnapshotAbstentionReason(StrEnum):
    """Evidence conditions under which the reader returns no observation."""

    NO_SNAPSHOT_AVAILABLE_BY_CUTOFF = "no_snapshot_available_by_cutoff"
    INVALID_SNAPSHOT_JSON = "invalid_snapshot_json"
    SOURCE_SCOPE_MISMATCH = "source_scope_mismatch"
    SOURCE_UNIT_MISMATCH = "source_unit_mismatch"
    MISSING_SELECTED_ROW = "missing_selected_row"
    DUPLICATE_SELECTED_ROW = "duplicate_selected_row"
    BLANK_SELECTED_OBSERVATION = "blank_selected_observation"
    INVALID_SOURCE_VALUE = "invalid_source_value"


_ABSTENTION_MESSAGES = {
    SnapshotAbstentionReason.NO_SNAPSHOT_AVAILABLE_BY_CUTOFF: (
        "No registered snapshot was available by the requested cutoff."
    ),
    SnapshotAbstentionReason.INVALID_SNAPSHOT_JSON: (
        "The selected snapshot is not valid bounded provider JSON."
    ),
    SnapshotAbstentionReason.SOURCE_SCOPE_MISMATCH: (
        "The selected snapshot differs from its approved exact scope."
    ),
    SnapshotAbstentionReason.SOURCE_UNIT_MISMATCH: (
        "The selected snapshot source unit differs from the trusted mapping."
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


def read_snapshot_as_of(
    *,
    call: SnapshotAsOfCall,
    registry: SnapshotRegistry,
) -> SnapshotAsOfResult:
    """Read one observation from the newest registered snapshot captured by the cutoff."""

    arguments = call.arguments
    entry = registry.entry_for(arguments.source_system, arguments.table_id, arguments.item_id)

    artifact = _select_artifact(entry, arguments.as_of)
    if artifact is None:
        return _abstain(call, SnapshotAbstentionReason.NO_SNAPSHOT_AVAILABLE_BY_CUTOFF)

    raw_value = _selected_raw_value(artifact.archive_bytes, entry.binding, arguments.period)
    if isinstance(raw_value, SnapshotAbstentionReason):
        return _abstain(call, raw_value)

    rule = normalization_rule(arguments.source_system, arguments.table_id, arguments.item_id)
    try:
        observation = normalized_observation(rule, raw_value)
    except (ArithmeticError, ValueError):
        return _abstain(call, SnapshotAbstentionReason.INVALID_SOURCE_VALUE)

    manifest = artifact.manifest
    reference = manifest.rights_decision
    assert reference is not None  # enforced when the registry admits the snapshot
    return SnapshotAsOfResult(
        call_id=call.call_id,
        tool_name=ToolName.READ_SNAPSHOT_AS_OF,
        status=ToolOutcomeStatus.SUCCESS,
        payload=SnapshotObservationEvidence(
            evidence_kind="latest_snapshot",
            source_id=manifest.source_id,
            source_sha256=manifest.content_sha256,
            source_system=arguments.source_system,
            source_published_on=manifest.published_on,
            source_retrieved_at=manifest.retrieved_at,
            rights_catalog_id=reference.catalog_id,
            rights_decision_id=reference.decision_id,
            as_of=arguments.as_of,
            table_id=arguments.table_id,
            item_id=arguments.item_id,
            period=arguments.period,
            observation=observation,
        ),
    )


def _select_artifact(entry: SnapshotRegistryEntry, as_of: date) -> SourceArtifact | None:
    """Pick the newest capture retrieved by the end of the cutoff day in Seoul."""

    cutoff = datetime.combine(as_of, time.max, _SEOUL).astimezone(UTC)
    eligible = [
        artifact
        for artifact in entry.artifacts
        if artifact.manifest.published_on <= as_of and artifact.manifest.retrieved_at <= cutoff
    ]
    if not eligible:
        return None
    return max(eligible, key=lambda artifact: artifact.manifest.retrieved_at)


def _selected_raw_value(
    payload: bytes,
    binding: SnapshotSeriesBinding,
    period: str,
) -> str | SnapshotAbstentionReason:
    try:
        document = json.loads(payload.decode("utf-8-sig"))
    except (UnicodeDecodeError, ValueError, RecursionError):
        return SnapshotAbstentionReason.INVALID_SNAPSHOT_JSON
    if binding.source_system is SourceSystem.ECOS:
        return _selected_ecos_value(document, binding, period)
    return _selected_kosis_value(document, binding, period)


def _selected_ecos_value(
    document: object,
    binding: SnapshotSeriesBinding,
    period: str,
) -> str | SnapshotAbstentionReason:
    result = document.get("StatisticSearch") if isinstance(document, dict) else None
    rows = result.get("row") if isinstance(result, dict) else None
    total = result.get("list_total_count") if isinstance(result, dict) else None
    if not isinstance(rows, list) or not rows or type(total) is not int or total != len(rows):
        return SnapshotAbstentionReason.INVALID_SNAPSHOT_JSON

    matches: list[dict[str, object]] = []
    for row in rows:
        if not isinstance(row, dict):
            return SnapshotAbstentionReason.INVALID_SNAPSHOT_JSON
        if (
            row.get("STAT_CODE") != binding.table_id
            or row.get("ITEM_CODE1") != binding.provider_item_id
            # The approved series has no sub-item: the three codes must be present and null.
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
    if not isinstance(document, list) or not document:
        return SnapshotAbstentionReason.INVALID_SNAPSHOT_JSON

    expected = {
        "ORG_ID": binding.organisation_id,
        "TBL_ID": binding.table_id,
        "ITM_ID": binding.provider_item_id,
        "C1": binding.geography_id,
        "PRD_SE": binding.frequency,
    }
    matches: list[dict[str, object]] = []
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
    if raw_value is None or (isinstance(raw_value, str) and not raw_value.strip()):
        return SnapshotAbstentionReason.BLANK_SELECTED_OBSERVATION
    if not isinstance(raw_value, str) or raw_value != raw_value.strip():
        return SnapshotAbstentionReason.INVALID_SOURCE_VALUE
    return raw_value


def _valid_provider_period(value: object, frequency: str) -> bool:
    if not isinstance(value, str) or len(value) != 6 or not value.isascii():
        return False
    if not value[:4].isdigit():
        return False
    if frequency == "Q":
        return value[4] == "Q" and value[5] in "1234"
    return value[4:].isdigit() and 1 <= int(value[4:]) <= 12


def _abstain(call: SnapshotAsOfCall, reason: SnapshotAbstentionReason) -> SnapshotAsOfResult:
    return SnapshotAsOfResult(
        call_id=call.call_id,
        tool_name=ToolName.READ_SNAPSHOT_AS_OF,
        status=ToolOutcomeStatus.ABSTAINED,
        abstention=ToolAbstention(
            reason_code=reason.value,
            message=_ABSTENTION_MESSAGES[reason],
        ),
    )
