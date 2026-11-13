"""Typed tool adapter over the fail-closed historical STES resolver."""

from enum import StrEnum

from sovereignlab.normalization import normalization_rule, normalized_observation
from sovereignlab.schemas import (
    SourceSystem,
    StesAsOfCall,
    StesAsOfResult,
    ToolAbstention,
    ToolName,
    ToolOutcomeStatus,
    VintageObservationEvidence,
)
from sovereignlab.vintage.registry import STES_TABLE_ID, StesRegistry
from sovereignlab.vintage.resolver import (
    AsOfQuery,
    ResolverAbstentionReason,
    StesSeriesKey,
    resolve_stes_as_of,
)


class StesAdapterAbstentionReason(StrEnum):
    """Adapter-level evidence conditions that return no observation."""

    PUBLIC_RAW_EVIDENCE_UNAVAILABLE = "public_raw_evidence_unavailable"
    INVALID_SOURCE_VALUE = "invalid_source_value"


_ABSTENTION_MESSAGES = {
    ResolverAbstentionReason.SOURCE_NOT_HISTORICAL_ARCHIVE: (
        "The selected STES source is not a historical archive."
    ),
    ResolverAbstentionReason.UNSUPPORTED_MEDIA_TYPE: (
        "The selected STES archive media type is unsupported."
    ),
    ResolverAbstentionReason.SOURCE_CONTENT_MISMATCH: (
        "The selected STES archive bytes do not match their manifest."
    ),
    ResolverAbstentionReason.MANIFEST_DATAFLOW_UNVERIFIABLE: (
        "The selected STES manifest has no verifiable dataflow reference."
    ),
    ResolverAbstentionReason.MANIFEST_DATAFLOW_MISMATCH: (
        "The selected STES manifest differs from the trusted availability ledger."
    ),
    ResolverAbstentionReason.INVALID_CUTOFF: (
        "The requested cutoff cannot be resolved by the trusted availability ledger."
    ),
    ResolverAbstentionReason.LEDGER_SELECTION_FAILED: (
        "The trusted availability ledger could not select an edition."
    ),
    ResolverAbstentionReason.CUTOFF_BEYOND_COMPLETE_THROUGH: (
        "The requested cutoff is beyond the ledger's verified completeness boundary."
    ),
    ResolverAbstentionReason.NO_EDITION_DEFINITELY_AVAILABLE: (
        "No STES edition was definitely available by the requested cutoff."
    ),
    ResolverAbstentionReason.UNRESOLVED_NEWER_EDITION: (
        "A potentially newer STES edition prevents a fail-closed selection."
    ),
    ResolverAbstentionReason.INVALID_SDMX_CSV: (
        "The selected STES archive is not valid bounded SDMX-CSV."
    ),
    ResolverAbstentionReason.MISSING_REQUIRED_COLUMNS: (
        "The selected STES archive is missing required columns."
    ),
    ResolverAbstentionReason.MISSING_SELECTED_ROW: (
        "The requested STES observation is absent from the selected edition."
    ),
    ResolverAbstentionReason.DUPLICATE_SELECTED_ROW: (
        "The requested STES observation is ambiguous in the selected edition."
    ),
    ResolverAbstentionReason.BLANK_SELECTED_OBSERVATION: (
        "The selected STES observation is blank."
    ),
    StesAdapterAbstentionReason.PUBLIC_RAW_EVIDENCE_UNAVAILABLE: (
        "Public raw evidence is unavailable for the validated STES scope."
    ),
    StesAdapterAbstentionReason.INVALID_SOURCE_VALUE: (
        "The selected STES observation is not a plain finite decimal."
    ),
}


def execute_stes_as_of_call(
    *,
    call: StesAsOfCall,
    registry: StesRegistry,
) -> StesAsOfResult:
    """Resolve one observation from the edition the ledger proves available by the cutoff."""

    arguments = call.arguments
    entry = registry.entry_for(
        (
            arguments.ref_area,
            arguments.freq,
            arguments.measure,
            arguments.unit_measure,
            arguments.activity,
        )
    )
    artifact = entry.data_artifact
    if artifact is None:
        return _abstain(call, StesAdapterAbstentionReason.PUBLIC_RAW_EVIDENCE_UNAVAILABLE)

    resolution = resolve_stes_as_of(
        archive_bytes=artifact.archive_bytes,
        manifest=artifact.manifest,
        ledger=registry.active_ledger,
        query=AsOfQuery(
            as_of=arguments.as_of,
            series=StesSeriesKey(
                ref_area=arguments.ref_area,
                freq=arguments.freq,
                measure=arguments.measure,
                unit_measure=arguments.unit_measure,
                activity=arguments.activity,
            ),
            period=arguments.period,
        ),
    )
    if resolution.abstention is not None:
        return _abstain(call, resolution.abstention.reason)
    evidence = resolution.evidence
    assert evidence is not None  # a resolution carries exactly one outcome
    selected = evidence.observation

    rule = normalization_rule(SourceSystem.OECD, STES_TABLE_ID, entry.binding.item_id)
    try:
        observation = normalized_observation(rule, selected.observation_value)
    except (ArithmeticError, ValueError):
        return _abstain(call, StesAdapterAbstentionReason.INVALID_SOURCE_VALUE)

    manifest = artifact.manifest
    reference = manifest.rights_decision
    assert reference is not None  # enforced when the registry admits the archive
    return StesAsOfResult(
        call_id=call.call_id,
        tool_name=ToolName.RESOLVE_STES_AS_OF,
        status=ToolOutcomeStatus.SUCCESS,
        payload=VintageObservationEvidence(
            evidence_kind="vintage_observation",
            source_id=manifest.source_id,
            source_sha256=manifest.content_sha256,
            source_system=SourceSystem.OECD,
            source_published_on=manifest.published_on,
            source_retrieved_at=manifest.retrieved_at,
            rights_catalog_id=reference.catalog_id,
            rights_decision_id=reference.decision_id,
            ledger_id=evidence.ledger_id,
            dataflow_id=evidence.dataflow_id,
            dataflow_version=evidence.dataflow_version,
            as_of=arguments.as_of,
            ref_area=selected.ref_area,
            freq=selected.freq,
            measure=selected.measure,
            unit_measure=selected.unit_measure,
            activity=selected.activity,
            selected_edition=selected.edition,
            period=selected.time_period,
            observation=observation,
        ),
    )


def _abstain(
    call: StesAsOfCall,
    reason: ResolverAbstentionReason | StesAdapterAbstentionReason,
) -> StesAsOfResult:
    return StesAsOfResult(
        call_id=call.call_id,
        tool_name=ToolName.RESOLVE_STES_AS_OF,
        status=ToolOutcomeStatus.ABSTAINED,
        abstention=ToolAbstention(
            reason_code=reason.value,
            message=_ABSTENTION_MESSAGES[reason],
        ),
    )
