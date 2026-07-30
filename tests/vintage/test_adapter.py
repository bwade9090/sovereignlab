"""Offline regression tests for the typed historical STES adapter."""

import copy
from dataclasses import replace
from datetime import date
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

import sovereignlab.vintage.adapter as adapter_module
import sovereignlab.vintage.registry as registry_module
from sovereignlab.schemas import (
    BenchmarkRecord,
    FailurePhase,
    SourceSystem,
    StesAsOfArguments,
    StesAsOfCall,
    StesAsOfResult,
    ToolOutcomeStatus,
)
from sovereignlab.vintage.adapter import (
    StesAdapterAbstentionReason,
    execute_stes_as_of_call,
)
from sovereignlab.vintage.registry import (
    CLI_STES_BINDING,
    GDP_STES_BINDING,
    StesRegistry,
    load_committed_stes_registry,
)
from sovereignlab.vintage.resolver import (
    AsOfAbstention,
    AsOfQuery,
    AsOfResolution,
    ResolverAbstentionReason,
    StesSeriesKey,
    resolve_stes_as_of,
)

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
CORE_BATCH_PATH = REPOSITORY_ROOT / "data/benchmark/core/core-batch-001.jsonl"
GOLD_AS_OF = date(2026, 7, 9)
GOLD_PERIOD = "2026-05"
GOLD_EDITION = "202607"
GOLD_VALUE = "102.66"
CLI_SCOPE = ("KOR", "M", "LI_AA", "IX", "_T")

RESOLVER_ABSTENTION_MESSAGES = {
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
}


@pytest.fixture(scope="module")
def committed_registry() -> StesRegistry:
    """Load and validate the large immutable provenance set only once."""

    return load_committed_stes_registry(REPOSITORY_ROOT)


@pytest.fixture(scope="module")
def committed_state(committed_registry: StesRegistry) -> Any:
    return committed_registry.validated_state()


@pytest.fixture(scope="module")
def trusted_resolution(committed_state: Any) -> AsOfResolution:
    entry = committed_state.entry_for(CLI_SCOPE)
    assert entry is not None
    assert entry.data_artifact is not None
    return resolve_stes_as_of(
        archive_bytes=entry.data_artifact.archive_bytes,
        manifest=entry.data_artifact.manifest,
        ledger=committed_state.active_ledger,
        query=_query(),
    )


@pytest.fixture
def fast_registry(
    committed_registry: StesRegistry,
    committed_state: Any,
    monkeypatch: pytest.MonkeyPatch,
) -> StesRegistry:
    """Reuse one already rebuilt state for tests of post-registry adapter branches."""

    monkeypatch.setattr(
        StesRegistry,
        "validated_state",
        lambda _registry: committed_state,
    )
    return committed_registry


def _cli_call(
    *,
    as_of: date = GOLD_AS_OF,
    period: str = GOLD_PERIOD,
    call_id: str = "stes-cli-call-01",
) -> StesAsOfCall:
    return StesAsOfCall(
        call_id=call_id,
        tool_name="resolve_stes_as_of",
        arguments=StesAsOfArguments(
            ref_area="KOR",
            freq="M",
            measure="LI_AA",
            unit_measure="IX",
            activity="_T",
            period=period,
            as_of=as_of,
            normalization_rule_id=CLI_STES_BINDING.normalization_rule_id,
        ),
    )


def _gdp_call(*, call_id: str = "stes-gdp-call-01") -> StesAsOfCall:
    return StesAsOfCall(
        call_id=call_id,
        tool_name="resolve_stes_as_of",
        arguments=StesAsOfArguments(
            ref_area="KOR",
            freq="Q",
            measure="B1GQ_Q",
            unit_measure="XDC",
            activity="_T",
            period="2026-Q1",
            as_of=GOLD_AS_OF,
            normalization_rule_id=GDP_STES_BINDING.normalization_rule_id,
        ),
    )


def _query() -> AsOfQuery:
    return AsOfQuery(
        as_of=GOLD_AS_OF,
        series=StesSeriesKey(
            ref_area="KOR",
            freq="M",
            measure="LI_AA",
            unit_measure="IX",
            activity="_T",
        ),
        period=GOLD_PERIOD,
    )


def _install_resolution(
    monkeypatch: pytest.MonkeyPatch,
    resolution: object,
    *,
    reference: object | None = None,
) -> None:
    monkeypatch.setattr(
        adapter_module,
        "_resolve_stes_as_of",
        lambda **_kwargs: resolution,
    )
    monkeypatch.setattr(
        adapter_module,
        "_reference_resolve_stes_as_of",
        lambda **_kwargs: resolution if reference is None else reference,
    )


def _assert_error(
    result: StesAsOfResult,
    call: StesAsOfCall,
    code: str,
) -> None:
    assert result.call_id == call.call_id
    assert result.status is ToolOutcomeStatus.ERROR
    assert result.payload is None
    assert result.abstention is None
    assert result.error is not None
    assert result.error.phase is FailurePhase.TOOL_EXECUTION
    assert result.error.code == code
    assert result.error.call_id == call.call_id
    serialized = result.model_dump_json().lower()
    assert "private" not in serialized
    assert "local path" not in serialized


def _assert_abstention(
    result: StesAsOfResult,
    reason: ResolverAbstentionReason | StesAdapterAbstentionReason,
    message: str,
) -> None:
    assert result.status is ToolOutcomeStatus.ABSTAINED
    assert result.payload is None
    assert result.error is None
    assert result.abstention is not None
    assert result.abstention.reason_code == reason.value
    assert result.abstention.message == message


def _selected_resolution(
    trusted: AsOfResolution,
    **updates: object,
) -> AsOfResolution:
    assert trusted.evidence is not None
    selected = trusted.evidence.observation.model_copy(update=updates)
    return AsOfResolution(
        evidence=trusted.evidence.model_copy(update={"observation": selected}),
    )


def _evidence_resolution(
    trusted: AsOfResolution,
    **updates: object,
) -> AsOfResolution:
    assert trusted.evidence is not None
    return AsOfResolution(evidence=trusted.evidence.model_copy(update=updates))


def test_committed_cli_gold_maps_to_selected_typed_evidence(
    committed_registry: StesRegistry,
) -> None:
    call = _cli_call()

    result = execute_stes_as_of_call(call=call, registry=committed_registry)

    assert result.call_id == call.call_id
    assert result.tool_name.value == "resolve_stes_as_of"
    assert result.status is ToolOutcomeStatus.SUCCESS
    assert result.abstention is None
    assert result.error is None
    assert result.payload is not None
    evidence = result.payload
    assert evidence.evidence_kind == "vintage_observation"
    assert evidence.source_id == CLI_STES_BINDING.source_id
    assert evidence.source_system is SourceSystem.OECD
    assert evidence.rights_decision_id == CLI_STES_BINDING.rights_decision_id
    assert evidence.ledger_id == registry_module.COMMITTED_ACTIVE_STES_LEDGER_ID
    assert evidence.dataflow_id == registry_module.STES_DATAFLOW_ID
    assert evidence.dataflow_version == registry_module.STES_DATAFLOW_VERSION
    assert evidence.as_of == GOLD_AS_OF
    assert (
        evidence.ref_area,
        evidence.freq,
        evidence.measure,
        evidence.unit_measure,
        evidence.activity,
    ) == CLI_SCOPE
    assert evidence.selected_edition == GOLD_EDITION
    assert evidence.period == GOLD_PERIOD
    assert evidence.observation.raw_value == GOLD_VALUE
    assert evidence.observation.normalization_rule_id == CLI_STES_BINDING.normalization_rule_id
    assert evidence.observation.normalized_value == GOLD_VALUE
    assert evidence.observation.canonical_unit == "oecd_amplitude_adjusted_index"
    assert evidence.observation.display_places == 2
    assert evidence.observation.display_value == GOLD_VALUE
    serialized = result.model_dump_json()
    for forbidden in (
        "canonical_url",
        "archive_bytes",
        "data/archive",
        "available_by",
        "202608",
    ):
        assert forbidden not in serialized


def test_success_json_round_trip_and_repeated_replay_are_byte_identical(
    committed_registry: StesRegistry,
) -> None:
    call = _cli_call(call_id="stes-replay-call")

    first = execute_stes_as_of_call(call=call, registry=committed_registry)
    second = execute_stes_as_of_call(call=call, registry=committed_registry)

    assert first.model_dump_json() == second.model_dump_json()
    assert StesAsOfResult.model_validate_json(first.model_dump_json()) == first


def test_core_batch_bilingual_records_preserve_the_exact_flat_arguments() -> None:
    records = tuple(
        BenchmarkRecord.model_validate_json(line)
        for line in CORE_BATCH_PATH.read_text(encoding="utf-8").splitlines()
        if line.strip()
    )
    pair = tuple(record for record in records if record.parallel_group_id == "kv-core-data-01")
    expected = _cli_call().arguments

    assert len(pair) == 2
    for record in pair:
        assert record.as_of == GOLD_AS_OF
        assert len(record.tool_expectations) == 1
        expectation = record.tool_expectations[0]
        assert expectation.tool_name == "resolve_stes_as_of"
        arguments = StesAsOfArguments.model_validate(expectation.arguments)
        assert arguments == expected
        assert set(expectation.arguments) == {
            "ref_area",
            "freq",
            "measure",
            "unit_measure",
            "activity",
            "period",
            "as_of",
            "normalization_rule_id",
        }


@pytest.mark.parametrize(
    ("as_of", "reason"),
    (
        (date(2026, 6, 30), ResolverAbstentionReason.NO_EDITION_DEFINITELY_AVAILABLE),
        (date(2026, 7, 17), ResolverAbstentionReason.CUTOFF_BEYOND_COMPLETE_THROUGH),
    ),
    ids=("before-first-resolved-edition", "beyond-completeness"),
)
def test_committed_cutoff_abstentions_are_stable(
    committed_registry: StesRegistry,
    as_of: date,
    reason: ResolverAbstentionReason,
) -> None:
    result = execute_stes_as_of_call(
        call=_cli_call(as_of=as_of, call_id=f"stes-cutoff-{as_of.isoformat()}"),
        registry=committed_registry,
    )

    _assert_abstention(result, reason, RESOLVER_ABSTENTION_MESSAGES[reason])


def test_gdp_rights_abstention_happens_before_either_resolver(
    fast_registry: StesRegistry,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_if_called(**_kwargs: object) -> Any:
        pytest.fail("private resolver must not run for unavailable GDP raw evidence")

    monkeypatch.setattr(adapter_module, "_resolve_stes_as_of", fail_if_called)
    monkeypatch.setattr(adapter_module, "_reference_resolve_stes_as_of", fail_if_called)
    call = _gdp_call()

    result = execute_stes_as_of_call(call=call, registry=fast_registry)

    _assert_abstention(
        result,
        StesAdapterAbstentionReason.PUBLIC_RAW_EVIDENCE_UNAVAILABLE,
        "Public raw evidence is unavailable for the validated STES scope.",
    )


def test_non_registry_input_returns_a_call_bound_sanitized_error() -> None:
    call = _cli_call(call_id="stes-wrong-registry-type")

    result = execute_stes_as_of_call(
        call=call,
        registry=object(),  # type: ignore[arg-type]
    )

    _assert_error(result, call, "stes_registry_misconfigured")


@pytest.mark.parametrize(
    ("field", "replacement"),
    (
        ("registry_id", ""),
        ("entries", "private invalid entries"),
        ("active_ledger_id", "private-missing-ledger"),
    ),
)
def test_mutated_registry_is_revalidated_at_call_time(
    committed_registry: StesRegistry,
    field: str,
    replacement: object,
) -> None:
    corrupted = copy.copy(committed_registry)
    object.__setattr__(corrupted, field, replacement)
    call = _cli_call(call_id=f"stes-mutated-{field}")

    result = execute_stes_as_of_call(call=call, registry=corrupted)

    _assert_error(result, call, "stes_registry_misconfigured")


@pytest.mark.parametrize(
    "case",
    (
        "missing-entry",
        "wrong-scope",
        "wrong-normalization",
        "unknown-rights-state",
        "missing-archive",
    ),
)
def test_invalid_validated_entry_is_a_registry_error(
    fast_registry: StesRegistry,
    committed_state: Any,
    monkeypatch: pytest.MonkeyPatch,
    case: str,
) -> None:
    cli_entry = committed_state.entry_for(CLI_SCOPE)
    gdp_entry = committed_state.entry_for(GDP_STES_BINDING.scope)
    assert cli_entry is not None
    assert gdp_entry is not None
    if case == "missing-entry":
        replacement = None
    elif case == "wrong-scope":
        replacement = gdp_entry
    elif case == "wrong-normalization":
        replacement = SimpleNamespace(
            binding=replace(
                cli_entry.binding,
                normalization_rule_id=GDP_STES_BINDING.normalization_rule_id,
            ),
            data_artifact=cli_entry.data_artifact,
        )
    elif case == "unknown-rights-state":
        replacement = SimpleNamespace(
            binding=replace(
                cli_entry.binding,
                raw_evidence="private-unknown",  # type: ignore[arg-type]
            ),
            data_artifact=cli_entry.data_artifact,
        )
    else:
        replacement = SimpleNamespace(
            binding=cli_entry.binding,
            data_artifact=None,
        )
    monkeypatch.setattr(
        type(committed_state),
        "entry_for",
        lambda _state, _scope: replacement,
    )
    call = _cli_call(call_id=f"stes-invalid-entry-{case}")

    result = execute_stes_as_of_call(call=call, registry=fast_registry)

    _assert_error(result, call, "stes_registry_misconfigured")


def test_unexpected_resolver_exception_is_sanitized(
    fast_registry: StesRegistry,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_resolver(**_kwargs: object) -> Any:
        raise RuntimeError("private source row at local path")

    monkeypatch.setattr(adapter_module, "_resolve_stes_as_of", fail_resolver)
    call = _cli_call(call_id="stes-resolver-exception")

    result = execute_stes_as_of_call(call=call, registry=fast_registry)

    _assert_error(result, call, "stes_resolver_failed")


def test_candidate_query_mutation_cannot_change_the_reference_period(
    fast_registry: StesRegistry,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    seen_query: AsOfQuery | None = None

    def mutate_query_then_resolve(
        *,
        archive_bytes: bytes,
        manifest: Any,
        ledger: Any,
        query: AsOfQuery,
    ) -> AsOfResolution:
        nonlocal seen_query
        seen_query = query
        object.__setattr__(query, "period", "2026-04")
        return resolve_stes_as_of(
            archive_bytes=archive_bytes,
            manifest=manifest,
            ledger=ledger,
            query=query,
        )

    monkeypatch.setattr(adapter_module, "_resolve_stes_as_of", mutate_query_then_resolve)
    call = _cli_call(call_id="stes-candidate-query-mutation")

    result = execute_stes_as_of_call(call=call, registry=fast_registry)

    assert seen_query is not None
    assert seen_query.period == "2026-04"
    assert call.arguments.period == GOLD_PERIOD
    _assert_error(result, call, "stes_resolver_failed")


def test_candidate_manifest_rights_mutation_cannot_change_success_provenance(
    fast_registry: StesRegistry,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_catalog_id = "forged-rights-catalog"
    fake_decision_id = "forged-rights-decision"

    def mutate_manifest_then_resolve(
        *,
        archive_bytes: bytes,
        manifest: Any,
        ledger: Any,
        query: AsOfQuery,
    ) -> AsOfResolution:
        assert manifest.rights_decision is not None
        object.__setattr__(
            manifest,
            "rights_decision",
            manifest.rights_decision.model_copy(
                update={
                    "catalog_id": fake_catalog_id,
                    "decision_id": fake_decision_id,
                }
            ),
        )
        return resolve_stes_as_of(
            archive_bytes=archive_bytes,
            manifest=manifest,
            ledger=ledger,
            query=query,
        )

    monkeypatch.setattr(adapter_module, "_resolve_stes_as_of", mutate_manifest_then_resolve)
    call = _cli_call(call_id="stes-candidate-manifest-mutation")

    result = execute_stes_as_of_call(call=call, registry=fast_registry)

    assert result.status is ToolOutcomeStatus.SUCCESS
    assert result.payload is not None
    assert result.payload.rights_catalog_id != fake_catalog_id
    assert result.payload.rights_decision_id != fake_decision_id
    assert result.payload.rights_decision_id == CLI_STES_BINDING.rights_decision_id
    assert fake_catalog_id not in result.model_dump_json()
    assert fake_decision_id not in result.model_dump_json()


def test_candidate_cannot_change_the_result_call_id(
    fast_registry: StesRegistry,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    call = _cli_call(call_id="stes-original-call-id")
    original_call_id = call.call_id
    mutated_call_id = "stes-mutated-call-id"

    def mutate_outer_call_then_resolve(
        *,
        archive_bytes: bytes,
        manifest: Any,
        ledger: Any,
        query: AsOfQuery,
    ) -> AsOfResolution:
        object.__setattr__(call, "call_id", mutated_call_id)
        return resolve_stes_as_of(
            archive_bytes=archive_bytes,
            manifest=manifest,
            ledger=ledger,
            query=query,
        )

    monkeypatch.setattr(adapter_module, "_resolve_stes_as_of", mutate_outer_call_then_resolve)

    result = execute_stes_as_of_call(call=call, registry=fast_registry)

    assert call.call_id == mutated_call_id
    assert result.status is ToolOutcomeStatus.SUCCESS
    assert result.call_id == original_call_id
    assert result.error is None


def test_final_flat_call_recheck_rejects_a_drifted_validated_outcome(
    fast_registry: StesRegistry,
    trusted_resolution: AsOfResolution,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    drifted = _selected_resolution(trusted_resolution, time_period="2026-04")
    assert drifted.evidence is not None
    _install_resolution(monkeypatch, trusted_resolution)
    monkeypatch.setattr(
        adapter_module,
        "_validate_resolution",
        lambda *_args, **_kwargs: drifted.evidence,
    )
    call = _cli_call(call_id="stes-final-flat-call-recheck")

    result = execute_stes_as_of_call(call=call, registry=fast_registry)

    _assert_error(result, call, "stes_resolver_failed")


def _forged_low_level_resolution(
    trusted: AsOfResolution,
    case: str,
) -> object:
    if case == "wrong-type":
        return object()
    if case == "abstention":
        assert trusted.evidence is not None
        return AsOfResolution(
            abstention=AsOfAbstention(
                source_manifest_id=trusted.evidence.source_manifest_id,
                ledger_id=trusted.evidence.ledger_id,
                as_of=trusted.evidence.as_of,
                reason=ResolverAbstentionReason.MISSING_SELECTED_ROW,
            )
        )
    if case == "evidence-type":
        return AsOfResolution.model_construct(evidence=object(), abstention=None)
    if case == "source":
        return _evidence_resolution(trusted, source_manifest_id="private-forged-source")
    if case == "hash":
        return _evidence_resolution(trusted, source_sha256="f" * 64)
    if case == "ledger":
        return _evidence_resolution(trusted, ledger_id="private-forged-ledger")
    if case == "flow":
        return _evidence_resolution(trusted, dataflow_id="private-forged-flow")
    if case == "flow-version":
        return _evidence_resolution(trusted, dataflow_version="private-version")
    if case == "dimension":
        return _selected_resolution(trusted, ref_area="USA")
    if case == "period":
        return _selected_resolution(trusted, time_period="2026-04")
    if case == "edition":
        return _selected_resolution(trusted, edition="202606")
    return _selected_resolution(trusted, observation_value="999.99")


@pytest.mark.parametrize(
    "case",
    (
        "wrong-type",
        "abstention",
        "evidence-type",
        "source",
        "hash",
        "ledger",
        "flow",
        "flow-version",
        "dimension",
        "period",
        "edition",
        "value",
    ),
)
def test_forged_low_level_result_cannot_replace_the_fresh_reference(
    fast_registry: StesRegistry,
    trusted_resolution: AsOfResolution,
    monkeypatch: pytest.MonkeyPatch,
    case: str,
) -> None:
    forged = _forged_low_level_resolution(trusted_resolution, case)
    _install_resolution(
        monkeypatch,
        forged,
        reference=trusted_resolution,
    )
    call = _cli_call(call_id=f"stes-forged-{case}")

    result = execute_stes_as_of_call(call=call, registry=fast_registry)

    _assert_error(result, call, "stes_resolver_failed")


def _matching_invalid_resolution(
    trusted: AsOfResolution,
    case: str,
) -> object:
    assert trusted.evidence is not None
    if case == "wrong-reference-type":
        return object()
    if case == "abstention-type":
        return AsOfResolution.model_construct(evidence=None, abstention=object())
    if case == "abstention-provenance":
        return AsOfResolution(
            abstention=AsOfAbstention(
                source_manifest_id="private-forged-source",
                ledger_id=trusted.evidence.ledger_id,
                as_of=trusted.evidence.as_of,
                reason=ResolverAbstentionReason.MISSING_SELECTED_ROW,
            )
        )
    if case == "evidence-type":
        return AsOfResolution.model_construct(evidence=object(), abstention=None)
    if case == "evidence-provenance":
        return _evidence_resolution(trusted, ledger_id="private-forged-ledger")
    if case == "selected-type":
        forged_evidence = trusted.evidence.model_copy(update={"observation": object()})
        return AsOfResolution.model_construct(evidence=forged_evidence, abstention=None)
    return _selected_resolution(trusted, measure="private-forged-measure")


@pytest.mark.parametrize(
    "case",
    (
        "wrong-reference-type",
        "abstention-type",
        "abstention-provenance",
        "evidence-type",
        "evidence-provenance",
        "selected-type",
        "selected-query",
    ),
)
def test_matching_invalid_internal_result_is_still_rejected(
    fast_registry: StesRegistry,
    trusted_resolution: AsOfResolution,
    monkeypatch: pytest.MonkeyPatch,
    case: str,
) -> None:
    invalid = _matching_invalid_resolution(trusted_resolution, case)
    if case == "wrong-reference-type":
        _install_resolution(
            monkeypatch,
            trusted_resolution,
            reference=invalid,
        )
    else:
        _install_resolution(monkeypatch, invalid)
    call = _cli_call(call_id=f"stes-invalid-internal-{case}")

    result = execute_stes_as_of_call(call=call, registry=fast_registry)

    _assert_error(result, call, "stes_resolver_failed")


def test_matching_model_construct_abstention_with_private_reason_is_rejected(
    fast_registry: StesRegistry,
    trusted_resolution: AsOfResolution,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    assert trusted_resolution.evidence is not None
    abstention = AsOfAbstention.model_construct(
        source_manifest_id=trusted_resolution.evidence.source_manifest_id,
        ledger_id=trusted_resolution.evidence.ledger_id,
        as_of=trusted_resolution.evidence.as_of,
        reason="private-unvalidated-reason",
    )
    invalid = AsOfResolution.model_construct(
        evidence=None,
        abstention=abstention,
    )
    _install_resolution(monkeypatch, invalid)
    call = _cli_call(call_id="stes-invalid-abstention-reason")

    result = execute_stes_as_of_call(call=call, registry=fast_registry)

    _assert_error(result, call, "stes_resolver_failed")


def test_matching_model_construct_selected_row_with_deleted_value_is_rejected(
    fast_registry: StesRegistry,
    trusted_resolution: AsOfResolution,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    assert trusted_resolution.evidence is not None
    selected = trusted_resolution.evidence.observation.model_copy()
    object.__delattr__(selected, "observation_value")
    evidence = trusted_resolution.evidence.model_copy(update={"observation": selected})
    invalid = AsOfResolution.model_construct(
        evidence=evidence,
        abstention=None,
    )
    _install_resolution(monkeypatch, invalid)
    call = _cli_call(call_id="stes-deleted-observation-value")

    result = execute_stes_as_of_call(call=call, registry=fast_registry)

    _assert_error(result, call, "stes_resolver_failed")


@pytest.mark.parametrize(
    ("reason", "message"),
    tuple(RESOLVER_ABSTENTION_MESSAGES.items()),
)
def test_every_resolver_abstention_has_a_stable_sanitized_mapping(
    fast_registry: StesRegistry,
    trusted_resolution: AsOfResolution,
    monkeypatch: pytest.MonkeyPatch,
    reason: ResolverAbstentionReason,
    message: str,
) -> None:
    assert trusted_resolution.evidence is not None
    abstention = AsOfResolution(
        abstention=AsOfAbstention(
            source_manifest_id=trusted_resolution.evidence.source_manifest_id,
            ledger_id=trusted_resolution.evidence.ledger_id,
            as_of=trusted_resolution.evidence.as_of,
            reason=reason,
        )
    )
    _install_resolution(monkeypatch, abstention)
    call = _cli_call(call_id=f"stes-abstention-{reason.value}")

    result = execute_stes_as_of_call(call=call, registry=fast_registry)

    _assert_abstention(result, reason, message)


@pytest.mark.parametrize(
    ("exception", "code"),
    (
        (ValueError("private missing rule"), "stes_registry_misconfigured"),
        (RuntimeError("private lookup failure"), "stes_normalization_failed"),
    ),
    ids=("missing-rule", "unexpected-lookup-failure"),
)
def test_normalization_lookup_failures_are_sanitized(
    fast_registry: StesRegistry,
    trusted_resolution: AsOfResolution,
    monkeypatch: pytest.MonkeyPatch,
    exception: Exception,
    code: str,
) -> None:
    _install_resolution(monkeypatch, trusted_resolution)

    def fail_lookup(*_args: object) -> Any:
        raise exception

    monkeypatch.setattr(adapter_module, "normalization_rule", fail_lookup)
    call = _cli_call(call_id=f"stes-normalization-lookup-{code}")

    result = execute_stes_as_of_call(call=call, registry=fast_registry)

    _assert_error(result, call, code)


@pytest.mark.parametrize(
    "case",
    ("rule-id", "source-system", "table-id", "item-id", "invalid-object"),
)
def test_normalization_rule_mismatch_is_a_registry_error(
    fast_registry: StesRegistry,
    trusted_resolution: AsOfResolution,
    monkeypatch: pytest.MonkeyPatch,
    case: str,
) -> None:
    _install_resolution(monkeypatch, trusted_resolution)
    rule = adapter_module.normalization_rule(
        SourceSystem.OECD,
        adapter_module._STES_NORMALIZATION_TABLE_ID,
        CLI_STES_BINDING.item_id,
    )
    replacements = {
        "rule-id": {"rule_id": GDP_STES_BINDING.normalization_rule_id},
        "source-system": {"source_system": SourceSystem.KOSIS},
        "table-id": {"table_id": "private-neighbor-table"},
        "item-id": {"item_id": "private.neighbor.item"},
    }
    mismatched: object = (
        object() if case == "invalid-object" else replace(rule, **replacements[case])
    )
    monkeypatch.setattr(
        adapter_module,
        "normalization_rule",
        lambda *_args: mismatched,
    )
    call = _cli_call(call_id=f"stes-normalization-mismatch-{case}")

    result = execute_stes_as_of_call(call=call, registry=fast_registry)

    _assert_error(result, call, "stes_registry_misconfigured")


def test_invalid_selected_decimal_becomes_a_stable_abstention(
    fast_registry: StesRegistry,
    trusted_resolution: AsOfResolution,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    invalid = _selected_resolution(trusted_resolution, observation_value="NaN")
    _install_resolution(monkeypatch, invalid)

    result = execute_stes_as_of_call(
        call=_cli_call(call_id="stes-invalid-decimal"),
        registry=fast_registry,
    )

    _assert_abstention(
        result,
        StesAdapterAbstentionReason.INVALID_SOURCE_VALUE,
        "The selected STES observation is not a plain finite decimal.",
    )


def test_unexpected_normalizer_failure_is_sanitized(
    fast_registry: StesRegistry,
    trusted_resolution: AsOfResolution,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _install_resolution(monkeypatch, trusted_resolution)

    def fail_normalizer(*_args: object) -> Any:
        raise RuntimeError("private decimal internals at local path")

    monkeypatch.setattr(adapter_module, "normalize_source_value", fail_normalizer)
    call = _cli_call(call_id="stes-unexpected-normalizer")

    result = execute_stes_as_of_call(call=call, registry=fast_registry)

    _assert_error(result, call, "stes_normalization_failed")


def test_missing_rights_reference_is_a_registry_error(
    fast_registry: StesRegistry,
    committed_state: Any,
    trusted_resolution: AsOfResolution,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    entry = committed_state.entry_for(CLI_SCOPE)
    assert entry is not None
    assert entry.data_artifact is not None
    manifest = entry.data_artifact.manifest.model_copy(update={"rights_decision": None})

    def parse_without_rights(_model: object, _payload: bytes) -> Any:
        return manifest.model_copy()

    monkeypatch.setattr(
        adapter_module.SourceManifest,
        "model_validate_json",
        classmethod(parse_without_rights),
    )
    _install_resolution(monkeypatch, trusted_resolution)
    call = _cli_call(call_id="stes-missing-rights-reference")

    result = execute_stes_as_of_call(call=call, registry=fast_registry)

    _assert_error(result, call, "stes_registry_misconfigured")


def test_evidence_mapper_failure_is_sanitized_and_call_bound(
    fast_registry: StesRegistry,
    trusted_resolution: AsOfResolution,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _install_resolution(monkeypatch, trusted_resolution)

    def fail_evidence(**_kwargs: object) -> Any:
        raise RuntimeError("private evidence detail at local path")

    monkeypatch.setattr(adapter_module, "VintageObservationEvidence", fail_evidence)
    call = _cli_call(call_id="stes-evidence-mapper-failure")

    result = execute_stes_as_of_call(call=call, registry=fast_registry)

    _assert_error(result, call, "stes_normalization_failed")
