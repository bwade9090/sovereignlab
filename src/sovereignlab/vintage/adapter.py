"""Typed execution adapter over the fail-closed historical STES resolver."""

from decimal import DecimalException, localcontext
from enum import StrEnum

from pydantic import ValidationError

from sovereignlab.normalization import (
    format_display,
    normalization_rule,
    normalize_source_value,
)
from sovereignlab.schemas import (
    EditionAvailabilityLedger,
    ExecutionFailure,
    FailurePhase,
    NormalizedObservation,
    SourceManifest,
    SourceSystem,
    StesAsOfCall,
    StesAsOfResult,
    ToolAbstention,
    ToolName,
    ToolOutcomeStatus,
    VintageObservationEvidence,
)
from sovereignlab.vintage.registry import (
    RawEvidenceAvailability,
    StesRegistry,
)
from sovereignlab.vintage.resolver import (
    AsOfAbstention,
    AsOfEvidencePacket,
    AsOfQuery,
    AsOfResolution,
    ResolverAbstentionReason,
    SelectedObservation,
    StesSeriesKey,
)
from sovereignlab.vintage.resolver import (
    resolve_stes_as_of as _reference_resolve_stes_as_of,
)

_resolve_stes_as_of = _reference_resolve_stes_as_of
_STES_NORMALIZATION_TABLE_ID = "DSD_STES_REVISIONS@DF_STES_REVISIONS"


class StesAdapterAbstentionReason(StrEnum):
    """Adapter-level evidence conditions that safely return no observation."""

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
    """Execute one flat typed call using only trusted registry artifacts."""

    expected_call_id = call.call_id
    if type(registry) is not StesRegistry:
        return _error(
            expected_call_id,
            code="stes_registry_misconfigured",
            message="The trusted STES registry is misconfigured.",
        )
    try:
        state = StesRegistry.validated_state(registry)
    except Exception:
        return _error(
            expected_call_id,
            code="stes_registry_misconfigured",
            message="The trusted STES registry is misconfigured.",
        )

    arguments = call.arguments
    scope = (
        arguments.ref_area,
        arguments.freq,
        arguments.measure,
        arguments.unit_measure,
        arguments.activity,
    )
    expected_period = arguments.period
    expected_as_of = arguments.as_of
    expected_rule_id = arguments.normalization_rule_id
    entry = state.entry_for(scope)
    if (
        entry is None
        or entry.binding.scope != scope
        or entry.binding.normalization_rule_id != expected_rule_id
    ):
        return _error(
            expected_call_id,
            code="stes_registry_misconfigured",
            message="The trusted STES registry has no exact binding for this validated call.",
        )

    if entry.binding.raw_evidence is RawEvidenceAvailability.UNAVAILABLE:
        return _abstain(
            expected_call_id,
            StesAdapterAbstentionReason.PUBLIC_RAW_EVIDENCE_UNAVAILABLE,
        )
    if (
        entry.binding.raw_evidence is not RawEvidenceAvailability.ALLOWED
        or entry.data_artifact is None
    ):
        return _error(
            expected_call_id,
            code="stes_registry_misconfigured",
            message="The trusted STES registry has no approved archive for this validated call.",
        )

    artifact = entry.data_artifact
    try:
        active_ledger_artifact = next(
            candidate
            for candidate in state.ledger_artifacts
            if candidate.ledger.ledger_id == state.active_ledger.ledger_id
        )
        reference_manifest = SourceManifest.model_validate_json(artifact.manifest_bytes)
        candidate_manifest = SourceManifest.model_validate_json(artifact.manifest_bytes)
        reference_ledger = EditionAvailabilityLedger.model_validate_json(
            active_ledger_artifact.ledger_bytes
        )
        candidate_ledger = EditionAvailabilityLedger.model_validate_json(
            active_ledger_artifact.ledger_bytes
        )
        reference = reference_manifest.rights_decision
        if (
            reference_manifest != artifact.manifest
            or candidate_manifest != reference_manifest
            or reference_ledger != state.active_ledger
            or candidate_ledger != reference_ledger
            or reference is None
            or reference.decision_id != entry.binding.rights_decision_id
        ):
            raise ValueError("trusted STES runtime material differs from the registry")
    except Exception:
        return _error(
            expected_call_id,
            code="stes_registry_misconfigured",
            message="The trusted STES registry runtime material is inconsistent.",
        )

    try:
        reference_query = AsOfQuery(
            as_of=expected_as_of,
            series=StesSeriesKey(
                ref_area=scope[0],
                freq=scope[1],
                measure=scope[2],
                unit_measure=scope[3],
                activity=scope[4],
            ),
            period=expected_period,
        )
        candidate_query = AsOfQuery.model_validate(reference_query.model_dump(mode="python"))
        reference_resolution = _reference_resolve_stes_as_of(
            archive_bytes=artifact.archive_bytes,
            manifest=reference_manifest,
            ledger=reference_ledger,
            query=reference_query,
        )
        resolution = _resolve_stes_as_of(
            archive_bytes=artifact.archive_bytes,
            manifest=candidate_manifest,
            ledger=candidate_ledger,
            query=candidate_query,
        )
        outcome = _validate_resolution(
            resolution,
            reference_resolution,
            query=reference_query,
            manifest_id=reference_manifest.source_id,
            manifest_sha256=reference_manifest.content_sha256,
            ledger_id=reference_ledger.ledger_id,
            dataflow_id=reference_ledger.dataflow_id,
            dataflow_version=reference_ledger.dataflow_version,
        )
    except Exception:
        return _error(
            expected_call_id,
            code="stes_resolver_failed",
            message="The deterministic STES resolver failed unexpectedly.",
        )

    if isinstance(outcome, ResolverAbstentionReason):
        return _abstain(expected_call_id, outcome)
    selected = outcome.observation
    if (
        selected.ref_area,
        selected.freq,
        selected.measure,
        selected.unit_measure,
        selected.activity,
        selected.time_period,
        outcome.as_of,
    ) != (*scope, expected_period, expected_as_of):
        return _error(
            expected_call_id,
            code="stes_resolver_failed",
            message="The deterministic STES resolver result was invalid.",
        )
    manifest = reference_manifest

    try:
        rule = normalization_rule(
            SourceSystem.OECD,
            _STES_NORMALIZATION_TABLE_ID,
            entry.binding.item_id,
        )
    except ValueError:
        return _error(
            expected_call_id,
            code="stes_registry_misconfigured",
            message="The frozen normalization registry has no exact validated STES scope.",
        )
    except Exception:
        return _error(
            expected_call_id,
            code="stes_normalization_failed",
            message="The deterministic STES normalizer failed unexpectedly.",
        )
    try:
        rule_matches = (
            rule.rule_id == expected_rule_id
            and rule.source_system is SourceSystem.OECD
            and rule.table_id == _STES_NORMALIZATION_TABLE_ID
            and rule.item_id == entry.binding.item_id
        )
    except Exception:
        rule_matches = False
    if not rule_matches:
        return _error(
            expected_call_id,
            code="stes_registry_misconfigured",
            message="The frozen normalization registry differs from the validated STES call.",
        )

    try:
        raw_value = selected.observation_value
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
            StesAdapterAbstentionReason.INVALID_SOURCE_VALUE,
        )
    except Exception:
        return _error(
            expected_call_id,
            code="stes_normalization_failed",
            message="The deterministic STES normalizer failed unexpectedly.",
        )

    try:
        evidence = VintageObservationEvidence(
            evidence_kind="vintage_observation",
            source_id=manifest.source_id,
            source_sha256=manifest.content_sha256,
            source_system=SourceSystem.OECD,
            source_published_on=manifest.published_on,
            source_retrieved_at=manifest.retrieved_at,
            rights_catalog_id=reference.catalog_id,
            rights_decision_id=reference.decision_id,
            ledger_id=outcome.ledger_id,
            dataflow_id=outcome.dataflow_id,
            dataflow_version=outcome.dataflow_version,
            as_of=expected_as_of,
            ref_area=selected.ref_area,
            freq=selected.freq,
            measure=selected.measure,
            unit_measure=selected.unit_measure,
            activity=selected.activity,
            selected_edition=selected.edition,
            period=selected.time_period,
            observation=observation,
        )
        return StesAsOfResult(
            call_id=expected_call_id,
            tool_name=ToolName.RESOLVE_STES_AS_OF,
            status=ToolOutcomeStatus.SUCCESS,
            payload=evidence,
        )
    except Exception:
        return _error(
            expected_call_id,
            code="stes_normalization_failed",
            message="The deterministic STES evidence mapper failed unexpectedly.",
        )


def _validate_resolution(
    resolution: AsOfResolution,
    reference_resolution: AsOfResolution,
    *,
    query: AsOfQuery,
    manifest_id: str,
    manifest_sha256: str,
    ledger_id: str,
    dataflow_id: str,
    dataflow_version: str,
) -> AsOfEvidencePacket | ResolverAbstentionReason:
    if type(resolution) is not AsOfResolution or type(reference_resolution) is not AsOfResolution:
        raise ValueError("STES resolution is not exactly reproducible")
    try:
        rebuilt = AsOfResolution.model_validate(
            resolution.model_dump(mode="python", warnings="error")
        )
        rebuilt_reference = AsOfResolution.model_validate(
            reference_resolution.model_dump(mode="python", warnings="error")
        )
    except Exception:
        raise ValueError("STES resolution is not exactly reproducible") from None
    if (
        rebuilt != resolution
        or rebuilt_reference != reference_resolution
        or rebuilt != rebuilt_reference
    ):
        raise ValueError("STES resolution is not exactly reproducible")
    resolution = rebuilt

    if resolution.abstention is not None:
        abstention = resolution.abstention
        if (
            type(abstention) is not AsOfAbstention
            or type(abstention.reason) is not ResolverAbstentionReason
            or (
                abstention.source_manifest_id,
                abstention.ledger_id,
                abstention.as_of,
            )
            != (
                manifest_id,
                ledger_id,
                query.as_of,
            )
        ):
            raise ValueError("STES abstention differs from its trusted inputs")
        return abstention.reason

    evidence = resolution.evidence
    if type(evidence) is not AsOfEvidencePacket or (
        evidence.source_manifest_id,
        evidence.source_sha256,
        evidence.ledger_id,
        evidence.dataflow_id,
        evidence.dataflow_version,
        evidence.as_of,
    ) != (
        manifest_id,
        manifest_sha256,
        ledger_id,
        dataflow_id,
        dataflow_version,
        query.as_of,
    ):
        raise ValueError("STES evidence provenance differs from its trusted inputs")

    selected = evidence.observation
    if type(selected) is not SelectedObservation or (
        selected.ref_area,
        selected.freq,
        selected.measure,
        selected.unit_measure,
        selected.activity,
        selected.time_period,
    ) != (
        query.series.ref_area,
        query.series.freq,
        query.series.measure,
        query.series.unit_measure,
        query.series.activity,
        query.period,
    ):
        raise ValueError("STES selected row differs from its validated query")
    return evidence


def _abstain(
    call_id: str,
    reason: ResolverAbstentionReason | StesAdapterAbstentionReason,
) -> StesAsOfResult:
    return StesAsOfResult(
        call_id=call_id,
        tool_name=ToolName.RESOLVE_STES_AS_OF,
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
) -> StesAsOfResult:
    return StesAsOfResult(
        call_id=call_id,
        tool_name=ToolName.RESOLVE_STES_AS_OF,
        status=ToolOutcomeStatus.ERROR,
        error=ExecutionFailure(
            phase=FailurePhase.TOOL_EXECUTION,
            code=code,
            message=message,
            call_id=call_id,
        ),
    )
