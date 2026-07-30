"""Offline regression tests for the trusted latest-only snapshot adapter."""

import hashlib
import json
import shutil
from dataclasses import replace
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

import pytest
from pydantic import ValidationError

import sovereignlab.snapshots.reader as reader_module
import sovereignlab.snapshots.registry as registry_module
from sovereignlab.schemas import (
    RedistributionStatus,
    RightsCatalog,
    SnapshotAsOfArguments,
    SnapshotAsOfCall,
    SourceKind,
    SourceManifest,
    SourceSystem,
    ToolOutcomeStatus,
    VintageSemantics,
)
from sovereignlab.snapshots import (
    COMMITTED_RIGHTS_CATALOG_PATHS,
    COMMITTED_SNAPSHOT_LOCATIONS,
    ECOS_CURRENT_ACCOUNT_BINDING,
    ECOS_GDP_BINDING,
    KOSIS_CPI_BINDING,
    MAX_SNAPSHOT_BYTES,
    SNAPSHOT_REGISTRY_DESCRIPTOR_SHA256,
    SNAPSHOT_REGISTRY_ID,
    SNAPSHOT_SERIES_BINDINGS,
    SnapshotAbstentionReason,
    SnapshotArtifact,
    SnapshotArtifactLocation,
    SnapshotCatalogArtifact,
    SnapshotRegistry,
    SnapshotRegistryEntry,
    SnapshotRegistryLoadError,
    SnapshotSeriesBinding,
    load_committed_snapshot_registry,
    load_snapshot_registry,
    read_snapshot_as_of,
)

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
AS_OF = date(2026, 7, 17)


@pytest.fixture(scope="module")
def committed_registry() -> SnapshotRegistry:
    return load_committed_snapshot_registry(REPOSITORY_ROOT)


def _call(
    binding: SnapshotSeriesBinding,
    period: str,
    *,
    as_of: date = AS_OF,
    call_id: str = "snapshot-call-01",
) -> SnapshotAsOfCall:
    return SnapshotAsOfCall(
        call_id=call_id,
        tool_name="read_snapshot_as_of",
        arguments=SnapshotAsOfArguments(
            source_system=binding.source_system,
            table_id=binding.table_id,
            item_id=binding.item_id,
            period=period,
            as_of=as_of,
            normalization_rule_id=binding.normalization_rule_id,
        ),
    )


def _artifact_for(
    registry: SnapshotRegistry,
    binding: SnapshotSeriesBinding,
) -> SnapshotArtifact:
    entry = registry.entry_for(*binding.scope)
    assert entry is not None
    assert len(entry.artifacts) == 1
    return entry.artifacts[0]


def _clone_manifest(
    source: SourceManifest,
    payload: bytes,
    **updates: Any,
) -> SourceManifest:
    data = source.model_dump(mode="python")
    data.update(
        byte_size=len(payload),
        content_sha256=hashlib.sha256(payload).hexdigest(),
        **updates,
    )
    return SourceManifest.model_validate(data)


def _artifact(
    source: SnapshotArtifact,
    payload: bytes,
    **manifest_updates: Any,
) -> SnapshotArtifact:
    manifest = _clone_manifest(source.manifest, payload, **manifest_updates)
    manifest_json = manifest.model_dump_json(exclude_none=True).encode("utf-8")
    return SnapshotArtifact(
        manifest=manifest,
        manifest_bytes=manifest_json,
        archive_bytes=payload,
    )


def _registry(
    base: SnapshotRegistry,
    binding: SnapshotSeriesBinding,
    artifacts: tuple[SnapshotArtifact, ...],
    *,
    catalogs: tuple[SnapshotCatalogArtifact, ...] | None = None,
) -> SnapshotRegistry:
    return SnapshotRegistry(
        registry_id="test-snapshot-registry-v1",
        entries=(SnapshotRegistryEntry(binding=binding, artifacts=artifacts),),
        catalog_artifacts=base.catalog_artifacts if catalogs is None else catalogs,
    )


def _ecos_payload(
    binding: SnapshotSeriesBinding = ECOS_GDP_BINDING,
    *,
    period: str = "2026Q1",
    value: object = "596692.8",
    unit: str | None = None,
    rows: list[object] | None = None,
    total: object = 1,
) -> bytes:
    if rows is None:
        rows = [
            {
                "STAT_CODE": binding.table_id,
                "ITEM_CODE1": binding.provider_item_id,
                "ITEM_CODE2": None,
                "ITEM_CODE3": None,
                "ITEM_CODE4": None,
                "TIME": period,
                "DATA_VALUE": value,
                "UNIT_NAME": binding.raw_unit if unit is None else unit,
            }
        ]
    return json.dumps(
        {"StatisticSearch": {"list_total_count": total, "row": rows}},
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")


def _kosis_payload(
    *,
    period: str = "202606",
    value: object = "119.99",
    unit: str | None = None,
    rows: list[object] | None = None,
) -> bytes:
    if rows is None:
        rows = [
            {
                "ORG_ID": "101",
                "TBL_ID": "DT_1J22003",
                "ITM_ID": "T",
                "C1": "T10",
                "PRD_SE": "M",
                "PRD_DE": period,
                "DT": value,
                "UNIT_NM": KOSIS_CPI_BINDING.raw_unit if unit is None else unit,
            }
        ]
    return json.dumps(rows, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


def _assert_abstention(
    result: Any,
    reason: SnapshotAbstentionReason,
) -> None:
    assert result.status is ToolOutcomeStatus.ABSTAINED
    assert result.payload is None
    assert result.error is None
    assert result.abstention is not None
    assert result.abstention.reason_code == reason.value


def _assert_registry_error(result: Any, call_id: str) -> None:
    assert result.status is ToolOutcomeStatus.ERROR
    assert result.payload is None
    assert result.abstention is None
    assert result.error is not None
    assert result.error.code == "snapshot_registry_misconfigured"
    assert result.error.call_id == call_id


def test_committed_registry_loads_only_the_three_explicit_approved_scopes(
    committed_registry: SnapshotRegistry,
) -> None:
    assert committed_registry.registry_id == SNAPSHOT_REGISTRY_ID
    assert tuple(entry.binding for entry in committed_registry.entries) == (
        SNAPSHOT_SERIES_BINDINGS
    )
    assert tuple(len(entry.artifacts) for entry in committed_registry.entries) == (1, 1, 1)
    assert tuple(
        catalog.catalog.catalog_id for catalog in committed_registry.catalog_artifacts
    ) == (
        "kor-rtd-rights-2026-07-16",
        "kor-rtd-rights-2026-07-17",
    )
    assert committed_registry.descriptor_sha256 == SNAPSHOT_REGISTRY_DESCRIPTOR_SHA256


def test_explicit_locations_cover_every_current_approved_snapshot_manifest() -> None:
    approved_scopes = {binding.scope for binding in SNAPSHOT_SERIES_BINDINGS}
    discovered: set[Path] = set()
    for path in (REPOSITORY_ROOT / "data" / "manifests").glob("*.json"):
        manifest = SourceManifest.model_validate_json(path.read_bytes())
        reference = manifest.rights_decision
        if (
            reference is not None
            and (
                reference.source_system,
                reference.table_id,
                reference.item_id,
            )
            in approved_scopes
            and manifest.source_kind is SourceKind.API
            and manifest.vintage_semantics is VintageSemantics.LATEST_ONLY
            and manifest.redistribution.status is RedistributionStatus.ALLOWED
        ):
            discovered.add(path.relative_to(REPOSITORY_ROOT))

    registered = {location.manifest_path for location in COMMITTED_SNAPSHOT_LOCATIONS}
    assert registered == discovered
    registered_catalogs = set(COMMITTED_RIGHTS_CATALOG_PATHS)
    discovered_catalogs = {
        path.relative_to(REPOSITORY_ROOT)
        for path in (REPOSITORY_ROOT / "data" / "rights").glob("*.json")
    }
    assert registered_catalogs == discovered_catalogs


@pytest.mark.parametrize(
    (
        "binding",
        "period",
        "raw_value",
        "canonical_unit",
        "display_places",
        "display_value",
    ),
    [
        (
            ECOS_GDP_BINDING,
            "2026Q1",
            "596692.8",
            "billion_krw",
            1,
            "596692.8",
        ),
        (
            ECOS_CURRENT_ACCOUNT_BINDING,
            "202605",
            "38121.1",
            "million_usd",
            1,
            "38121.1",
        ),
        (
            KOSIS_CPI_BINDING,
            "202606",
            "119.99",
            "index_2020_100",
            2,
            "119.99",
        ),
    ],
    ids=("ecos-gdp", "ecos-current-account", "kosis-cpi"),
)
def test_reader_returns_selected_row_only_with_complete_provenance(
    committed_registry: SnapshotRegistry,
    binding: SnapshotSeriesBinding,
    period: str,
    raw_value: str,
    canonical_unit: str,
    display_places: int,
    display_value: str,
) -> None:
    call = _call(binding, period)
    result = read_snapshot_as_of(call=call, registry=committed_registry)

    assert result.status is ToolOutcomeStatus.SUCCESS
    assert result.abstention is None
    assert result.error is None
    assert result.payload is not None
    assert result.payload.source_system is binding.source_system
    assert result.payload.table_id == binding.table_id
    assert result.payload.item_id == binding.item_id
    assert result.payload.period == period
    assert result.payload.as_of == AS_OF
    assert result.payload.vintage_semantics == "latest_only"
    assert result.payload.rights_catalog_id == "kor-rtd-rights-2026-07-17"
    assert result.payload.rights_decision_id == binding.rights_decision_id
    assert result.payload.observation.raw_value == raw_value
    assert result.payload.observation.normalized_value == raw_value
    assert result.payload.observation.canonical_unit == canonical_unit
    assert result.payload.observation.display_places == display_places
    assert result.payload.observation.display_value == display_value
    serialized = result.model_dump_json()
    assert "archive_path" not in serialized
    assert "manifest_path" not in serialized
    assert "canonical_url" not in serialized


def test_reader_preserves_a_negative_exact_decimal(
    committed_registry: SnapshotRegistry,
) -> None:
    result = read_snapshot_as_of(
        call=_call(ECOS_CURRENT_ACCOUNT_BINDING, "198001"),
        registry=committed_registry,
    )

    assert result.payload is not None
    assert result.payload.observation.raw_value == "-633.9"
    assert result.payload.observation.normalized_value == "-633.9"
    assert result.payload.observation.display_value == "-633.9"


def test_cutoff_before_first_capture_ignores_future_bytes(
    committed_registry: SnapshotRegistry,
) -> None:
    base = _artifact_for(committed_registry, ECOS_GDP_BINDING)
    future = SnapshotArtifact(
        manifest=base.manifest,
        manifest_bytes=base.manifest_bytes,
        archive_bytes=b"future-corrupt-payload",
    )
    registry = _registry(committed_registry, ECOS_GDP_BINDING, (future,))

    result = read_snapshot_as_of(
        call=_call(ECOS_GDP_BINDING, "2026Q1", as_of=date(2026, 7, 16)),
        registry=registry,
    )

    _assert_abstention(
        result,
        SnapshotAbstentionReason.NO_SNAPSHOT_AVAILABLE_BY_CUTOFF,
    )
    serialized = result.model_dump_json()
    assert base.manifest.source_id not in serialized
    assert "596692.8" not in serialized


def test_reader_uses_the_latest_eligible_capture_independent_of_registry_order(
    committed_registry: SnapshotRegistry,
) -> None:
    base = _artifact_for(committed_registry, ECOS_GDP_BINDING)
    old_payload = _ecos_payload(value="1.0")
    new_payload = _ecos_payload(value="2.0")
    old = _artifact(
        base,
        old_payload,
        source_id=f"{ECOS_GDP_BINDING.document_family}-old",
        published_on=date(2026, 7, 16),
        retrieved_at=datetime(2026, 7, 16, 1, tzinfo=UTC),
    )
    new = _artifact(
        base,
        new_payload,
        source_id=f"{ECOS_GDP_BINDING.document_family}-new",
        published_on=date(2026, 7, 17),
        retrieved_at=datetime(2026, 7, 17, 2, tzinfo=UTC),
    )

    first = read_snapshot_as_of(
        call=_call(ECOS_GDP_BINDING, "2026Q1"),
        registry=_registry(committed_registry, ECOS_GDP_BINDING, (old, new)),
    )
    second = read_snapshot_as_of(
        call=_call(ECOS_GDP_BINDING, "2026Q1"),
        registry=_registry(committed_registry, ECOS_GDP_BINDING, (new, old)),
    )

    assert first == second
    assert first.payload is not None
    assert first.payload.source_id.endswith("-new")
    assert first.payload.observation.raw_value == "2.0"


def test_reader_does_not_fall_back_when_latest_eligible_capture_is_corrupt(
    committed_registry: SnapshotRegistry,
) -> None:
    base = _artifact_for(committed_registry, ECOS_GDP_BINDING)
    old_payload = _ecos_payload(value="1.0")
    old = _artifact(
        base,
        old_payload,
        source_id=f"{ECOS_GDP_BINDING.document_family}-old",
        published_on=date(2026, 7, 16),
        retrieved_at=datetime(2026, 7, 16, 1, tzinfo=UTC),
    )
    valid_new_payload = _ecos_payload(value="2.0")
    valid_new = _artifact(
        base,
        valid_new_payload,
        source_id=f"{ECOS_GDP_BINDING.document_family}-new",
        published_on=date(2026, 7, 17),
        retrieved_at=datetime(2026, 7, 17, 2, tzinfo=UTC),
    )
    new = SnapshotArtifact(
        manifest=valid_new.manifest,
        manifest_bytes=valid_new.manifest_bytes,
        archive_bytes=b"corrupt",
    )

    result = read_snapshot_as_of(
        call=_call(ECOS_GDP_BINDING, "2026Q1"),
        registry=_registry(committed_registry, ECOS_GDP_BINDING, (old, new)),
    )

    _assert_abstention(result, SnapshotAbstentionReason.SOURCE_CONTENT_MISMATCH)


def test_registry_descriptor_binds_actual_archive_bytes(
    committed_registry: SnapshotRegistry,
) -> None:
    entry = committed_registry.entries[0]
    valid = SnapshotRegistry(
        registry_id="actual-bytes-test",
        entries=(entry,),
        catalog_artifacts=committed_registry.catalog_artifacts,
    )
    source = entry.artifacts[0]
    corrupt_artifact = SnapshotArtifact(
        manifest=source.manifest,
        manifest_bytes=source.manifest_bytes,
        archive_bytes=b"X" + source.archive_bytes[1:],
    )
    corrupt = _registry(
        committed_registry,
        entry.binding,
        (corrupt_artifact,),
    )

    assert valid.descriptor_sha256 != corrupt.descriptor_sha256


def test_registry_descriptor_binds_exact_manifest_and_catalog_bytes(
    committed_registry: SnapshotRegistry,
) -> None:
    entry = committed_registry.entries[0]
    source = entry.artifacts[0]
    changed_source = _artifact(
        source,
        source.archive_bytes,
        published_on=date(2026, 7, 16),
    )
    changed_manifest_registry = _registry(
        committed_registry,
        entry.binding,
        (changed_source,),
    )
    original_scope_registry = _registry(
        committed_registry,
        entry.binding,
        entry.artifacts,
    )
    assert changed_manifest_registry.descriptor_sha256 != original_scope_registry.descriptor_sha256

    changed_catalog_registry = SnapshotRegistry(
        registry_id=original_scope_registry.registry_id,
        entries=original_scope_registry.entries,
        catalog_artifacts=committed_registry.catalog_artifacts[:1],
    )
    assert changed_catalog_registry.descriptor_sha256 != original_scope_registry.descriptor_sha256


def test_korean_end_of_day_cutoff_is_inclusive_and_excludes_the_next_instant(
    committed_registry: SnapshotRegistry,
) -> None:
    base = _artifact_for(committed_registry, ECOS_GDP_BINDING)
    payload = _ecos_payload()
    included = _artifact(
        base,
        payload,
        source_id=f"{ECOS_GDP_BINDING.document_family}-included",
        retrieved_at=datetime(2026, 7, 17, 14, 59, 59, 999999, tzinfo=UTC),
    )
    excluded = _artifact(
        base,
        payload,
        source_id=f"{ECOS_GDP_BINDING.document_family}-excluded",
        retrieved_at=datetime(2026, 7, 17, 15, 0, 0, tzinfo=UTC),
    )

    included_result = read_snapshot_as_of(
        call=_call(ECOS_GDP_BINDING, "2026Q1"),
        registry=_registry(committed_registry, ECOS_GDP_BINDING, (included,)),
    )
    excluded_result = read_snapshot_as_of(
        call=_call(ECOS_GDP_BINDING, "2026Q1"),
        registry=_registry(committed_registry, ECOS_GDP_BINDING, (excluded,)),
    )

    assert included_result.payload is not None
    _assert_abstention(
        excluded_result,
        SnapshotAbstentionReason.NO_SNAPSHOT_AVAILABLE_BY_CUTOFF,
    )


def test_same_timestamp_frontier_abstains_without_exposing_either_artifact(
    committed_registry: SnapshotRegistry,
) -> None:
    base = _artifact_for(committed_registry, ECOS_GDP_BINDING)
    payload = _ecos_payload()
    first = _artifact(
        base,
        payload,
        source_id=f"{ECOS_GDP_BINDING.document_family}-first",
    )
    second = _artifact(
        base,
        payload,
        source_id=f"{ECOS_GDP_BINDING.document_family}-second",
    )

    result = read_snapshot_as_of(
        call=_call(ECOS_GDP_BINDING, "2026Q1"),
        registry=_registry(committed_registry, ECOS_GDP_BINDING, (first, second)),
    )

    _assert_abstention(
        result,
        SnapshotAbstentionReason.AMBIGUOUS_SNAPSHOT_FRONTIER,
    )
    serialized = result.model_dump_json()
    assert first.manifest.source_id not in serialized
    assert second.manifest.source_id not in serialized


@pytest.mark.parametrize(
    ("updates", "reason"),
    [
        ({"source_kind": SourceKind.DATASET}, SnapshotAbstentionReason.SOURCE_NOT_API),
        (
            {"vintage_semantics": VintageSemantics.HISTORICAL_ARCHIVE},
            SnapshotAbstentionReason.SOURCE_NOT_LATEST_ONLY,
        ),
        (
            {"media_type": "text/csv"},
            SnapshotAbstentionReason.UNSUPPORTED_MEDIA_TYPE,
        ),
        (
            {"document_family": "ecos-neighbor-family"},
            SnapshotAbstentionReason.SOURCE_SCOPE_MISMATCH,
        ),
    ],
    ids=("wrong-kind", "wrong-vintage", "wrong-media", "wrong-family"),
)
def test_manifest_contract_failures_abstain_without_exposing_payload(
    committed_registry: SnapshotRegistry,
    updates: dict[str, Any],
    reason: SnapshotAbstentionReason,
) -> None:
    base = _artifact_for(committed_registry, ECOS_GDP_BINDING)
    payload = _ecos_payload()
    artifact = _artifact(base, payload, **updates)
    result = read_snapshot_as_of(
        call=_call(ECOS_GDP_BINDING, "2026Q1"),
        registry=_registry(committed_registry, ECOS_GDP_BINDING, (artifact,)),
    )

    _assert_abstention(result, reason)


def test_missing_or_nonallowed_rights_link_abstains(
    committed_registry: SnapshotRegistry,
) -> None:
    base = _artifact_for(committed_registry, ECOS_GDP_BINDING)
    payload = _ecos_payload()
    redistribution = base.manifest.redistribution.model_copy(
        update={"status": RedistributionStatus.METADATA_ONLY}
    )
    missing = _artifact(
        base,
        payload,
        redistribution=redistribution,
        rights_decision=None,
    )
    nonallowed = _artifact(
        base,
        payload,
        redistribution=redistribution,
    )

    for artifact in (missing, nonallowed):
        result = read_snapshot_as_of(
            call=_call(ECOS_GDP_BINDING, "2026Q1"),
            registry=_registry(committed_registry, ECOS_GDP_BINDING, (artifact,)),
        )
        _assert_abstention(
            result,
            SnapshotAbstentionReason.RIGHTS_VALIDATION_FAILED,
        )


def test_rights_scope_or_catalog_mismatch_never_produces_evidence(
    committed_registry: SnapshotRegistry,
) -> None:
    base = _artifact_for(committed_registry, ECOS_GDP_BINDING)
    payload = _ecos_payload()
    reference = base.manifest.rights_decision
    assert reference is not None
    wrong_scope = _artifact(
        base,
        payload,
        rights_decision=reference.model_copy(update={"item_id": "SA000"}),
    )
    superseded = _artifact(
        base,
        payload,
        rights_decision=reference.model_copy(update={"catalog_id": "kor-rtd-rights-2026-07-16"}),
    )

    wrong_scope_result = read_snapshot_as_of(
        call=_call(ECOS_GDP_BINDING, "2026Q1"),
        registry=_registry(committed_registry, ECOS_GDP_BINDING, (wrong_scope,)),
    )
    superseded_result = read_snapshot_as_of(
        call=_call(ECOS_GDP_BINDING, "2026Q1"),
        registry=_registry(committed_registry, ECOS_GDP_BINDING, (superseded,)),
    )

    _assert_abstention(
        wrong_scope_result,
        SnapshotAbstentionReason.SOURCE_SCOPE_MISMATCH,
    )
    _assert_abstention(
        superseded_result,
        SnapshotAbstentionReason.RIGHTS_VALIDATION_FAILED,
    )


def test_missing_injected_catalog_abstains_without_exposing_payload(
    committed_registry: SnapshotRegistry,
) -> None:
    base = _artifact_for(committed_registry, ECOS_GDP_BINDING)
    artifact = SnapshotArtifact(
        manifest=base.manifest,
        manifest_bytes=base.manifest_bytes,
        archive_bytes=base.archive_bytes,
    )
    result = read_snapshot_as_of(
        call=_call(ECOS_GDP_BINDING, "2026Q1"),
        registry=_registry(
            committed_registry,
            ECOS_GDP_BINDING,
            (artifact,),
            catalogs=(),
        ),
    )

    _assert_abstention(
        result,
        SnapshotAbstentionReason.RIGHTS_VALIDATION_FAILED,
    )


def test_nonbytes_registry_payload_is_a_sanitized_call_bound_error(
    committed_registry: SnapshotRegistry,
) -> None:
    base = _artifact_for(committed_registry, ECOS_GDP_BINDING)
    artifact = SnapshotArtifact(
        manifest=base.manifest,
        manifest_bytes=base.manifest_bytes,
        archive_bytes=base.archive_bytes,
    )
    object.__setattr__(artifact, "archive_bytes", "not bytes")
    call = _call(ECOS_GDP_BINDING, "2026Q1", call_id="snapshot-failure-call")

    result = read_snapshot_as_of(
        call=call,
        registry=_registry(committed_registry, ECOS_GDP_BINDING, (artifact,)),
    )

    assert result.status is ToolOutcomeStatus.ERROR
    assert result.payload is None
    assert result.abstention is None
    assert result.error is not None
    assert result.error.call_id == call.call_id
    assert result.error.code == "snapshot_registry_misconfigured"


def test_call_time_revalidation_rejects_manifest_model_timestamp_mutation(
    committed_registry: SnapshotRegistry,
) -> None:
    base = _artifact_for(committed_registry, ECOS_GDP_BINDING)
    manifest = SourceManifest.model_validate_json(base.manifest_bytes)
    artifact = SnapshotArtifact(
        manifest=manifest,
        manifest_bytes=base.manifest_bytes,
        archive_bytes=base.archive_bytes,
    )
    registry = _registry(committed_registry, ECOS_GDP_BINDING, (artifact,))
    object.__setattr__(manifest, "published_on", date(2026, 7, 16))
    object.__setattr__(manifest, "retrieved_at", datetime(2026, 7, 16, tzinfo=UTC))
    call = _call(
        ECOS_GDP_BINDING,
        "2026Q1",
        as_of=date(2026, 7, 16),
        call_id="mutated-manifest-call",
    )

    result = read_snapshot_as_of(call=call, registry=registry)

    _assert_registry_error(result, call.call_id)
    assert "596692.8" not in result.model_dump_json()
    with pytest.raises(ValueError, match="manifest model differs"):
        _ = registry.descriptor_sha256


def test_call_time_revalidation_rejects_catalog_chain_model_mutation(
    committed_registry: SnapshotRegistry,
) -> None:
    catalogs = tuple(
        SnapshotCatalogArtifact(
            catalog=type(artifact.catalog).model_validate_json(artifact.catalog_bytes),
            catalog_bytes=artifact.catalog_bytes,
        )
        for artifact in committed_registry.catalog_artifacts
    )
    registry = _registry(
        committed_registry,
        ECOS_GDP_BINDING,
        (_artifact_for(committed_registry, ECOS_GDP_BINDING),),
        catalogs=catalogs,
    )
    object.__setattr__(catalogs[-1].catalog, "supersedes_catalog_id", None)
    call = _call(
        ECOS_GDP_BINDING,
        "2026Q1",
        call_id="mutated-catalog-chain-call",
    )

    result = read_snapshot_as_of(call=call, registry=registry)

    _assert_registry_error(result, call.call_id)
    with pytest.raises(ValueError, match="catalog model differs"):
        _ = registry.descriptor_sha256


def test_call_time_revalidation_rejects_binding_mutation(
    committed_registry: SnapshotRegistry,
) -> None:
    binding = replace(ECOS_GDP_BINDING)
    registry = SnapshotRegistry(
        registry_id="mutable-binding-registry",
        entries=(
            SnapshotRegistryEntry(
                binding=binding,
                artifacts=(_artifact_for(committed_registry, ECOS_GDP_BINDING),),
            ),
        ),
        catalog_artifacts=committed_registry.catalog_artifacts,
    )
    object.__setattr__(binding, "raw_unit", "forged-unit")
    call = _call(
        ECOS_GDP_BINDING,
        "2026Q1",
        call_id="mutated-binding-call",
    )

    result = read_snapshot_as_of(call=call, registry=registry)

    _assert_registry_error(result, call.call_id)


@pytest.mark.parametrize(
    "case",
    (
        "registry-id",
        "entries-container",
        "catalog-container",
        "entry-type",
        "binding-type",
        "artifact-container",
        "artifact-type",
        "catalog-type",
    ),
)
def test_call_time_revalidation_rejects_mutated_registry_structure(
    committed_registry: SnapshotRegistry,
    case: str,
) -> None:
    entry = SnapshotRegistryEntry(
        binding=replace(ECOS_GDP_BINDING),
        artifacts=(_artifact_for(committed_registry, ECOS_GDP_BINDING),),
    )
    registry = SnapshotRegistry(
        registry_id="mutable-structure-registry",
        entries=(entry,),
        catalog_artifacts=committed_registry.catalog_artifacts,
    )
    if case == "registry-id":
        object.__setattr__(registry, "registry_id", "")
    elif case == "entries-container":
        object.__setattr__(registry, "entries", [entry])
    elif case == "catalog-container":
        object.__setattr__(
            registry,
            "catalog_artifacts",
            list(registry.catalog_artifacts),
        )
    elif case == "entry-type":
        object.__setattr__(registry, "entries", (object(),))
    elif case == "binding-type":
        object.__setattr__(entry, "binding", object())
    elif case == "artifact-container":
        object.__setattr__(entry, "artifacts", list(entry.artifacts))
    elif case == "artifact-type":
        object.__setattr__(entry, "artifacts", (object(),))
    else:
        object.__setattr__(registry, "catalog_artifacts", (object(),))
    call = _call(
        ECOS_GDP_BINDING,
        "2026Q1",
        call_id=f"mutated-structure-{case}",
    )

    result = read_snapshot_as_of(call=call, registry=registry)

    _assert_registry_error(result, call.call_id)


def test_call_time_revalidation_rejects_decode_overriding_archive_bytes(
    committed_registry: SnapshotRegistry,
) -> None:
    class DeceptiveBytes(bytes):
        def decode(self, *args: Any, **kwargs: Any) -> str:
            return (
                super()
                .decode(*args, **kwargs)
                .replace(
                    '"DATA_VALUE":"596692.8"',
                    '"DATA_VALUE":"999999999.9"',
                )
            )

    base = _artifact_for(committed_registry, ECOS_GDP_BINDING)
    artifact = SnapshotArtifact(
        manifest=SourceManifest.model_validate_json(base.manifest_bytes),
        manifest_bytes=base.manifest_bytes,
        archive_bytes=base.archive_bytes,
    )
    registry = _registry(committed_registry, ECOS_GDP_BINDING, (artifact,))
    object.__setattr__(artifact, "archive_bytes", DeceptiveBytes(base.archive_bytes))
    call = _call(
        ECOS_GDP_BINDING,
        "2026Q1",
        call_id="deceptive-bytes-call",
    )

    result = read_snapshot_as_of(call=call, registry=registry)

    _assert_registry_error(result, call.call_id)
    assert "999999999.9" not in result.model_dump_json()
    with pytest.raises(ValueError, match="archive bytes"):
        _ = registry.descriptor_sha256


def test_call_id_is_copied_before_downstream_execution(
    committed_registry: SnapshotRegistry,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    call = _call(
        ECOS_GDP_BINDING,
        "2026Q1",
        call_id="original-snapshot-call-id",
    )
    original_parser = reader_module._selected_raw_value

    def mutate_call_then_parse(
        payload: bytes,
        binding: SnapshotSeriesBinding,
        period: str,
    ) -> str | SnapshotAbstentionReason:
        object.__setattr__(call, "call_id", "mutated-snapshot-call-id")
        return original_parser(payload, binding, period)

    monkeypatch.setattr(reader_module, "_selected_raw_value", mutate_call_then_parse)

    result = read_snapshot_as_of(call=call, registry=committed_registry)

    assert call.call_id == "mutated-snapshot-call-id"
    assert result.status is ToolOutcomeStatus.SUCCESS
    assert result.call_id == "original-snapshot-call-id"
    assert result.error is None


def test_missing_scope_binding_is_a_sanitized_registry_error(
    committed_registry: SnapshotRegistry,
) -> None:
    registry = SnapshotRegistry(
        registry_id="empty-test-registry",
        entries=(),
        catalog_artifacts=committed_registry.catalog_artifacts,
    )

    result = read_snapshot_as_of(
        call=_call(ECOS_GDP_BINDING, "2026Q1", call_id="missing-binding-call"),
        registry=registry,
    )

    assert result.status is ToolOutcomeStatus.ERROR
    assert result.error is not None
    assert result.error.code == "snapshot_registry_misconfigured"
    assert result.error.call_id == "missing-binding-call"


def test_corrupt_registry_normalization_binding_is_a_sanitized_error(
    committed_registry: SnapshotRegistry,
) -> None:
    entry = committed_registry.entries[0]
    corrupt_entry = SnapshotRegistryEntry(
        binding=replace(
            entry.binding,
            normalization_rule_id=ECOS_CURRENT_ACCOUNT_BINDING.normalization_rule_id,
        ),
        artifacts=entry.artifacts,
    )

    class CorruptRegistry:
        def entry_for(self, *scope: object) -> SnapshotRegistryEntry:
            return corrupt_entry

    result = read_snapshot_as_of(
        call=_call(ECOS_GDP_BINDING, "2026Q1"),
        registry=CorruptRegistry(),  # type: ignore[arg-type]
    )

    assert result.error is not None
    assert result.error.code == "snapshot_registry_misconfigured"


@pytest.mark.parametrize(
    "payload",
    [
        b"\xff",
        b"{",
        b'{"StatisticSearch":{},"StatisticSearch":{}}',
        b"[" * 1_100 + b"]" * 1_100,
        _ecos_payload().replace(
            b'"DATA_VALUE":"596692.8"',
            b'"BROKEN":NaN,"DATA_VALUE":"596692.8"',
        ),
        _ecos_payload().replace(
            b'"DATA_VALUE":"596692.8"',
            b'"BROKEN":' + b"1" * 4_301 + b',"DATA_VALUE":"596692.8"',
        ),
        b"[]",
        b'{"other":{}}',
        b'{"StatisticSearch":[]}',
        _ecos_payload(total=True),
        _ecos_payload(rows=[]),
        _ecos_payload(total=2),
        _ecos_payload(rows=["not-an-object"]),
    ],
    ids=(
        "invalid-utf8",
        "malformed-json",
        "duplicate-key",
        "too-deep",
        "nonstandard-nan",
        "oversized-integer-token",
        "wrong-root-type",
        "wrong-root-key",
        "wrong-result-type",
        "boolean-count",
        "empty-rows",
        "count-mismatch",
        "non-object-row",
    ),
)
def test_invalid_or_unbounded_ecos_json_abstains(
    committed_registry: SnapshotRegistry,
    payload: bytes,
) -> None:
    base = _artifact_for(committed_registry, ECOS_GDP_BINDING)
    artifact = _artifact(base, payload)

    result = read_snapshot_as_of(
        call=_call(ECOS_GDP_BINDING, "2026Q1"),
        registry=_registry(committed_registry, ECOS_GDP_BINDING, (artifact,)),
    )

    _assert_abstention(result, SnapshotAbstentionReason.INVALID_SNAPSHOT_JSON)


def test_ecos_row_limit_is_fail_closed(
    committed_registry: SnapshotRegistry,
) -> None:
    base = _artifact_for(committed_registry, ECOS_GDP_BINDING)
    row = json.loads(_ecos_payload())["StatisticSearch"]["row"][0]
    rows = [dict(row, TIME=f"{1960 + index // 4}Q{index % 4 + 1}") for index in range(1_001)]
    payload = _ecos_payload(rows=rows, total=1_001)
    result = read_snapshot_as_of(
        call=_call(ECOS_GDP_BINDING, "2026Q1"),
        registry=_registry(
            committed_registry,
            ECOS_GDP_BINDING,
            (_artifact(base, payload),),
        ),
    )

    _assert_abstention(result, SnapshotAbstentionReason.INVALID_SNAPSHOT_JSON)


@pytest.mark.parametrize(
    "row_update",
    [
        {"STAT_CODE": "200Y109"},
        {"ITEM_CODE1": "10602"},
        {"ITEM_CODE2": "neighbor"},
        {"ITEM_CODE3": "neighbor"},
        {"ITEM_CODE4": "neighbor"},
        {"TIME": "2026-01"},
        {"TIME": "\uff12\uff10\uff12\uff16Q1"},
        {"TIME": 202601},
    ],
    ids=(
        "table",
        "item-one",
        "item-two",
        "item-three",
        "item-four",
        "period-format",
        "unicode-period",
        "period-type",
    ),
)
def test_ecos_neighbor_scope_or_frequency_abstains(
    committed_registry: SnapshotRegistry,
    row_update: dict[str, object],
) -> None:
    base = _artifact_for(committed_registry, ECOS_GDP_BINDING)
    row = json.loads(_ecos_payload())["StatisticSearch"]["row"][0]
    row.update(row_update)
    payload = _ecos_payload(rows=[row])

    result = read_snapshot_as_of(
        call=_call(ECOS_GDP_BINDING, "2026Q1"),
        registry=_registry(
            committed_registry,
            ECOS_GDP_BINDING,
            (_artifact(base, payload),),
        ),
    )

    _assert_abstention(result, SnapshotAbstentionReason.SOURCE_SCOPE_MISMATCH)


def test_ecos_unit_mismatch_abstains_without_normalizing(
    committed_registry: SnapshotRegistry,
) -> None:
    base = _artifact_for(committed_registry, ECOS_GDP_BINDING)
    payload = _ecos_payload(unit="원")
    result = read_snapshot_as_of(
        call=_call(ECOS_GDP_BINDING, "2026Q1"),
        registry=_registry(
            committed_registry,
            ECOS_GDP_BINDING,
            (_artifact(base, payload),),
        ),
    )

    _assert_abstention(result, SnapshotAbstentionReason.SOURCE_UNIT_MISMATCH)


def test_ecos_missing_neighbor_dimension_key_abstains(
    committed_registry: SnapshotRegistry,
) -> None:
    base = _artifact_for(committed_registry, ECOS_GDP_BINDING)
    row = json.loads(_ecos_payload())["StatisticSearch"]["row"][0]
    del row["ITEM_CODE2"]
    payload = _ecos_payload(rows=[row])

    result = read_snapshot_as_of(
        call=_call(ECOS_GDP_BINDING, "2026Q1"),
        registry=_registry(
            committed_registry,
            ECOS_GDP_BINDING,
            (_artifact(base, payload),),
        ),
    )

    _assert_abstention(result, SnapshotAbstentionReason.SOURCE_SCOPE_MISMATCH)


@pytest.mark.parametrize(
    ("rows", "reason"),
    [
        (
            json.loads(_ecos_payload(period="2025Q4"))["StatisticSearch"]["row"],
            SnapshotAbstentionReason.MISSING_SELECTED_ROW,
        ),
        (
            json.loads(_ecos_payload())["StatisticSearch"]["row"] * 2,
            SnapshotAbstentionReason.DUPLICATE_SELECTED_ROW,
        ),
        (
            json.loads(_ecos_payload(value=None))["StatisticSearch"]["row"],
            SnapshotAbstentionReason.BLANK_SELECTED_OBSERVATION,
        ),
        (
            json.loads(_ecos_payload(value="  "))["StatisticSearch"]["row"],
            SnapshotAbstentionReason.BLANK_SELECTED_OBSERVATION,
        ),
        (
            json.loads(_ecos_payload(value=1.25))["StatisticSearch"]["row"],
            SnapshotAbstentionReason.INVALID_SOURCE_VALUE,
        ),
        (
            json.loads(_ecos_payload(value="1" * 129))["StatisticSearch"]["row"],
            SnapshotAbstentionReason.INVALID_SOURCE_VALUE,
        ),
        (
            json.loads(_ecos_payload(value=" 1.0 "))["StatisticSearch"]["row"],
            SnapshotAbstentionReason.INVALID_SOURCE_VALUE,
        ),
        (
            json.loads(_ecos_payload(value="1,000"))["StatisticSearch"]["row"],
            SnapshotAbstentionReason.INVALID_SOURCE_VALUE,
        ),
        (
            json.loads(_ecos_payload(value="1e3"))["StatisticSearch"]["row"],
            SnapshotAbstentionReason.INVALID_SOURCE_VALUE,
        ),
        (
            json.loads(_ecos_payload(value="NaN"))["StatisticSearch"]["row"],
            SnapshotAbstentionReason.INVALID_SOURCE_VALUE,
        ),
    ],
    ids=(
        "missing",
        "duplicate",
        "null",
        "whitespace",
        "non-string",
        "too-long",
        "surrounding-whitespace",
        "comma",
        "exponent",
        "nan",
    ),
)
def test_ecos_selected_value_failures_have_stable_reasons(
    committed_registry: SnapshotRegistry,
    rows: list[object],
    reason: SnapshotAbstentionReason,
) -> None:
    base = _artifact_for(committed_registry, ECOS_GDP_BINDING)
    payload = _ecos_payload(rows=rows, total=len(rows))
    result = read_snapshot_as_of(
        call=_call(ECOS_GDP_BINDING, "2026Q1"),
        registry=_registry(
            committed_registry,
            ECOS_GDP_BINDING,
            (_artifact(base, payload),),
        ),
    )

    _assert_abstention(result, reason)


def test_manifest_declared_oversize_abstains_before_parsing(
    committed_registry: SnapshotRegistry,
) -> None:
    base = _artifact_for(committed_registry, ECOS_GDP_BINDING)
    data = base.manifest.model_dump(mode="python")
    data["byte_size"] = MAX_SNAPSHOT_BYTES + 1
    artifact = SnapshotArtifact(
        manifest=SourceManifest.model_validate(data),
        manifest_bytes=SourceManifest.model_validate(data)
        .model_dump_json(exclude_none=True)
        .encode("utf-8"),
        archive_bytes=base.archive_bytes,
    )

    result = read_snapshot_as_of(
        call=_call(ECOS_GDP_BINDING, "2026Q1"),
        registry=_registry(committed_registry, ECOS_GDP_BINDING, (artifact,)),
    )

    _assert_abstention(result, SnapshotAbstentionReason.SOURCE_CONTENT_MISMATCH)


@pytest.mark.parametrize(
    "payload",
    [
        b"{}",
        b"[]",
        json.dumps(["not-an-object"]).encode(),
    ],
    ids=("object-root", "empty-list", "non-object-row"),
)
def test_invalid_kosis_json_shape_abstains(
    committed_registry: SnapshotRegistry,
    payload: bytes,
) -> None:
    base = _artifact_for(committed_registry, KOSIS_CPI_BINDING)
    result = read_snapshot_as_of(
        call=_call(KOSIS_CPI_BINDING, "202606"),
        registry=_registry(
            committed_registry,
            KOSIS_CPI_BINDING,
            (_artifact(base, payload),),
        ),
    )

    _assert_abstention(result, SnapshotAbstentionReason.INVALID_SNAPSHOT_JSON)


def test_kosis_row_limit_is_fail_closed(
    committed_registry: SnapshotRegistry,
) -> None:
    base = _artifact_for(committed_registry, KOSIS_CPI_BINDING)
    row = json.loads(_kosis_payload())[0]
    rows = [dict(row, PRD_DE=f"{1965 + index // 12}{index % 12 + 1:02d}") for index in range(1_001)]
    payload = _kosis_payload(rows=rows)
    result = read_snapshot_as_of(
        call=_call(KOSIS_CPI_BINDING, "202606"),
        registry=_registry(
            committed_registry,
            KOSIS_CPI_BINDING,
            (_artifact(base, payload),),
        ),
    )

    _assert_abstention(result, SnapshotAbstentionReason.INVALID_SNAPSHOT_JSON)


@pytest.mark.parametrize(
    "row_update",
    [
        {"ORG_ID": "102"},
        {"TBL_ID": "DT_1J22004"},
        {"ITM_ID": "T1"},
        {"C1": "T11"},
        {"PRD_SE": "Q"},
        {"PRD_DE": "2026-06"},
        {"PRD_DE": "\uff12\uff10\uff12\uff16\uff10\uff16"},
        {"PRD_DE": 202606},
    ],
    ids=(
        "org",
        "table",
        "item",
        "geography",
        "frequency",
        "period-format",
        "unicode-period",
        "period-type",
    ),
)
def test_kosis_hidden_selector_or_frequency_drift_abstains(
    committed_registry: SnapshotRegistry,
    row_update: dict[str, object],
) -> None:
    base = _artifact_for(committed_registry, KOSIS_CPI_BINDING)
    row = json.loads(_kosis_payload())[0]
    row.update(row_update)
    payload = _kosis_payload(rows=[row])
    result = read_snapshot_as_of(
        call=_call(KOSIS_CPI_BINDING, "202606"),
        registry=_registry(
            committed_registry,
            KOSIS_CPI_BINDING,
            (_artifact(base, payload),),
        ),
    )

    _assert_abstention(result, SnapshotAbstentionReason.SOURCE_SCOPE_MISMATCH)


def test_kosis_fullwidth_raw_unit_mapping_is_exact(
    committed_registry: SnapshotRegistry,
) -> None:
    base = _artifact_for(committed_registry, KOSIS_CPI_BINDING)
    payload = _kosis_payload(unit="2020=100")
    result = read_snapshot_as_of(
        call=_call(KOSIS_CPI_BINDING, "202606"),
        registry=_registry(
            committed_registry,
            KOSIS_CPI_BINDING,
            (_artifact(base, payload),),
        ),
    )

    _assert_abstention(result, SnapshotAbstentionReason.SOURCE_UNIT_MISMATCH)


@pytest.mark.parametrize(
    ("rows", "reason"),
    [
        (
            json.loads(_kosis_payload(period="202605")),
            SnapshotAbstentionReason.MISSING_SELECTED_ROW,
        ),
        (
            json.loads(_kosis_payload()) * 2,
            SnapshotAbstentionReason.DUPLICATE_SELECTED_ROW,
        ),
        (
            json.loads(_kosis_payload(value="")),
            SnapshotAbstentionReason.BLANK_SELECTED_OBSERVATION,
        ),
        (
            json.loads(_kosis_payload(value="Infinity")),
            SnapshotAbstentionReason.INVALID_SOURCE_VALUE,
        ),
    ],
    ids=("missing", "duplicate", "blank", "invalid-number"),
)
def test_kosis_selected_value_failures_have_stable_reasons(
    committed_registry: SnapshotRegistry,
    rows: list[object],
    reason: SnapshotAbstentionReason,
) -> None:
    base = _artifact_for(committed_registry, KOSIS_CPI_BINDING)
    payload = _kosis_payload(rows=rows)
    result = read_snapshot_as_of(
        call=_call(KOSIS_CPI_BINDING, "202606"),
        registry=_registry(
            committed_registry,
            KOSIS_CPI_BINDING,
            (_artifact(base, payload),),
        ),
    )

    _assert_abstention(result, reason)


def test_registry_descriptor_is_independent_of_entry_artifact_and_catalog_order(
    committed_registry: SnapshotRegistry,
) -> None:
    forward = committed_registry
    reverse = SnapshotRegistry(
        registry_id=forward.registry_id,
        entries=tuple(
            SnapshotRegistryEntry(
                binding=entry.binding,
                artifacts=tuple(reversed(entry.artifacts)),
            )
            for entry in reversed(forward.entries)
        ),
        catalog_artifacts=tuple(reversed(forward.catalog_artifacts)),
    )

    assert reverse.canonical_descriptor_bytes() == forward.canonical_descriptor_bytes()
    assert reverse.descriptor_sha256 == forward.descriptor_sha256


def test_registry_rejects_duplicate_or_unapproved_bindings_and_artifacts(
    committed_registry: SnapshotRegistry,
) -> None:
    entry = committed_registry.entries[0]
    with pytest.raises(ValueError, match="scope bindings"):
        SnapshotRegistry(
            registry_id="duplicate-scope",
            entries=(entry, entry),
            catalog_artifacts=committed_registry.catalog_artifacts,
        )

    unapproved = SnapshotSeriesBinding(
        source_system=SourceSystem.ECOS,
        table_id="999Y999",
        item_id="X",
        document_family="unapproved",
        rights_decision_id="unapproved-rights-v1",
        normalization_rule_id=ECOS_GDP_BINDING.normalization_rule_id,
        frequency="Q",
        raw_unit="원",
        provider_item_id="X",
    )
    with pytest.raises(ValueError, match="non-approved"):
        SnapshotRegistry(
            registry_id="unapproved-scope",
            entries=(SnapshotRegistryEntry(binding=unapproved),),
            catalog_artifacts=committed_registry.catalog_artifacts,
        )

    with pytest.raises(ValueError, match="source IDs"):
        SnapshotRegistry(
            registry_id="duplicate-source",
            entries=(
                SnapshotRegistryEntry(
                    binding=entry.binding,
                    artifacts=entry.artifacts * 2,
                ),
            ),
            catalog_artifacts=committed_registry.catalog_artifacts,
        )

    with pytest.raises(ValueError, match="catalog IDs"):
        SnapshotRegistry(
            registry_id="duplicate-catalog",
            entries=(entry,),
            catalog_artifacts=committed_registry.catalog_artifacts[:1] * 2,
        )


def test_registry_artifacts_reject_model_byte_mismatches(
    committed_registry: SnapshotRegistry,
) -> None:
    source = committed_registry.entries[0].artifacts[0]
    other_source = committed_registry.entries[1].artifacts[0]
    with pytest.raises(ValueError, match="manifest bytes"):
        SnapshotArtifact(
            manifest=source.manifest,
            manifest_bytes="not bytes",  # type: ignore[arg-type]
            archive_bytes=source.archive_bytes,
        )
    with pytest.raises(ValueError, match="archive bytes"):
        SnapshotArtifact(
            manifest=source.manifest,
            manifest_bytes=source.manifest_bytes,
            archive_bytes="not bytes",  # type: ignore[arg-type]
        )
    with pytest.raises(ValueError, match="model differs"):
        SnapshotArtifact(
            manifest=source.manifest,
            manifest_bytes=other_source.manifest_bytes,
            archive_bytes=source.archive_bytes,
        )

    catalog = committed_registry.catalog_artifacts[0]
    other_catalog = committed_registry.catalog_artifacts[1]
    with pytest.raises(ValueError, match="catalog bytes"):
        SnapshotCatalogArtifact(
            catalog=catalog.catalog,
            catalog_bytes="not bytes",  # type: ignore[arg-type]
        )
    with pytest.raises(ValueError, match="model differs"):
        SnapshotCatalogArtifact(
            catalog=catalog.catalog,
            catalog_bytes=other_catalog.catalog_bytes,
        )


def test_registry_artifacts_require_exact_model_and_builtin_byte_types(
    committed_registry: SnapshotRegistry,
) -> None:
    class DerivedSourceManifest(SourceManifest):
        pass

    class DerivedRightsCatalog(RightsCatalog):
        pass

    class DerivedBytes(bytes):
        pass

    source = committed_registry.entries[0].artifacts[0]
    catalog = committed_registry.catalog_artifacts[0]
    with pytest.raises(ValueError, match="exact strict model"):
        SnapshotArtifact(
            manifest=DerivedSourceManifest.model_validate_json(source.manifest_bytes),
            manifest_bytes=source.manifest_bytes,
            archive_bytes=source.archive_bytes,
        )
    with pytest.raises(ValueError, match="exact strict model"):
        SnapshotCatalogArtifact(
            catalog=DerivedRightsCatalog.model_validate_json(catalog.catalog_bytes),
            catalog_bytes=catalog.catalog_bytes,
        )
    with pytest.raises(ValueError, match="manifest bytes"):
        SnapshotArtifact(
            manifest=source.manifest,
            manifest_bytes=DerivedBytes(source.manifest_bytes),
            archive_bytes=source.archive_bytes,
        )
    with pytest.raises(ValueError, match="archive bytes"):
        SnapshotArtifact(
            manifest=source.manifest,
            manifest_bytes=source.manifest_bytes,
            archive_bytes=DerivedBytes(source.archive_bytes),
        )
    with pytest.raises(ValueError, match="catalog bytes"):
        SnapshotCatalogArtifact(
            catalog=catalog.catalog,
            catalog_bytes=DerivedBytes(catalog.catalog_bytes),
        )


def test_runtime_artifact_validation_rechecks_every_exact_type(
    committed_registry: SnapshotRegistry,
) -> None:
    class DerivedBytes(bytes):
        pass

    source = committed_registry.entries[0].artifacts[0]
    catalog = committed_registry.catalog_artifacts[0]

    wrong_manifest = SnapshotArtifact(
        manifest=source.manifest,
        manifest_bytes=source.manifest_bytes,
        archive_bytes=source.archive_bytes,
    )
    object.__setattr__(wrong_manifest, "manifest", object())
    with pytest.raises(ValueError, match="exact strict model"):
        wrong_manifest.validated()

    wrong_manifest_bytes = SnapshotArtifact(
        manifest=source.manifest,
        manifest_bytes=source.manifest_bytes,
        archive_bytes=source.archive_bytes,
    )
    object.__setattr__(
        wrong_manifest_bytes,
        "manifest_bytes",
        DerivedBytes(source.manifest_bytes),
    )
    with pytest.raises(ValueError, match="manifest bytes"):
        wrong_manifest_bytes.validated()

    wrong_catalog = SnapshotCatalogArtifact(
        catalog=catalog.catalog,
        catalog_bytes=catalog.catalog_bytes,
    )
    object.__setattr__(wrong_catalog, "catalog", object())
    with pytest.raises(ValueError, match="exact strict model"):
        wrong_catalog.validated()

    wrong_catalog_bytes = SnapshotCatalogArtifact(
        catalog=catalog.catalog,
        catalog_bytes=catalog.catalog_bytes,
    )
    object.__setattr__(
        wrong_catalog_bytes,
        "catalog_bytes",
        DerivedBytes(catalog.catalog_bytes),
    )
    with pytest.raises(ValueError, match="catalog bytes"):
        wrong_catalog_bytes.validated()


def test_generic_loader_matches_the_committed_convenience_loader(
    committed_registry: SnapshotRegistry,
) -> None:
    generic = load_snapshot_registry(
        REPOSITORY_ROOT,
        registry_id=SNAPSHOT_REGISTRY_ID,
        artifact_locations=COMMITTED_SNAPSHOT_LOCATIONS,
        rights_catalog_paths=COMMITTED_RIGHTS_CATALOG_PATHS,
    )

    assert generic.canonical_descriptor_bytes() == (committed_registry.canonical_descriptor_bytes())


def test_committed_registry_id_is_frozen_to_one_descriptor(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        registry_module,
        "SNAPSHOT_REGISTRY_DESCRIPTOR_SHA256",
        "0" * 64,
    )

    with pytest.raises(ValueError, match="preserve v1"):
        registry_module.load_committed_snapshot_registry(REPOSITORY_ROOT)


def test_loader_rejects_nonapproved_location_and_untrusted_paths(
    committed_registry: SnapshotRegistry,
) -> None:
    unapproved = SnapshotSeriesBinding(
        source_system=SourceSystem.ECOS,
        table_id="999Y999",
        item_id="X",
        document_family="unapproved",
        rights_decision_id="unapproved-rights-v1",
        normalization_rule_id=ECOS_GDP_BINDING.normalization_rule_id,
        frequency="Q",
        raw_unit="원",
        provider_item_id="X",
    )
    location = COMMITTED_SNAPSHOT_LOCATIONS[0]
    with pytest.raises(ValueError, match="non-approved binding"):
        load_snapshot_registry(
            REPOSITORY_ROOT,
            registry_id="unapproved-location",
            artifact_locations=(
                SnapshotArtifactLocation(
                    binding=unapproved,
                    manifest_path=location.manifest_path,
                    archive_path=location.archive_path,
                ),
            ),
            rights_catalog_paths=COMMITTED_RIGHTS_CATALOG_PATHS,
        )

    with pytest.raises(ValueError, match="repository-relative"):
        load_snapshot_registry(
            REPOSITORY_ROOT,
            registry_id="absolute-path",
            artifact_locations=(),
            rights_catalog_paths=(REPOSITORY_ROOT / COMMITTED_RIGHTS_CATALOG_PATHS[0],),
        )

    with pytest.raises(ValueError, match="escapes"):
        load_snapshot_registry(
            REPOSITORY_ROOT,
            registry_id="escaped-path",
            artifact_locations=(),
            rights_catalog_paths=(Path("data/rights/../../requirements.txt"),),
        )


def test_loader_rejects_manifest_binding_and_missing_catalog(
    committed_registry: SnapshotRegistry,
) -> None:
    gdp_location = COMMITTED_SNAPSHOT_LOCATIONS[0]
    current_account_location = COMMITTED_SNAPSHOT_LOCATIONS[1]
    with pytest.raises(ValueError, match="trusted exact-scope"):
        load_snapshot_registry(
            REPOSITORY_ROOT,
            registry_id="mismatched-binding",
            artifact_locations=(
                SnapshotArtifactLocation(
                    binding=ECOS_GDP_BINDING,
                    manifest_path=current_account_location.manifest_path,
                    archive_path=current_account_location.archive_path,
                ),
            ),
            rights_catalog_paths=COMMITTED_RIGHTS_CATALOG_PATHS,
        )

    with pytest.raises(ValidationError, match="unknown rights catalog"):
        load_snapshot_registry(
            REPOSITORY_ROOT,
            registry_id="missing-active-catalog",
            artifact_locations=(gdp_location,),
            rights_catalog_paths=(COMMITTED_RIGHTS_CATALOG_PATHS[0],),
        )


def test_loader_rejects_duplicate_locations_and_catalogs() -> None:
    location = COMMITTED_SNAPSHOT_LOCATIONS[0]
    with pytest.raises(ValueError, match="source IDs"):
        load_snapshot_registry(
            REPOSITORY_ROOT,
            registry_id="duplicate-locations",
            artifact_locations=(location, location),
            rights_catalog_paths=COMMITTED_RIGHTS_CATALOG_PATHS,
        )

    with pytest.raises(ValueError, match="catalog IDs"):
        load_snapshot_registry(
            REPOSITORY_ROOT,
            registry_id="duplicate-catalogs",
            artifact_locations=(),
            rights_catalog_paths=(
                COMMITTED_RIGHTS_CATALOG_PATHS[0],
                COMMITTED_RIGHTS_CATALOG_PATHS[0],
            ),
        )


def test_loader_rejects_wrong_catalog_filename(tmp_path: Path) -> None:
    rights_root = tmp_path / "data" / "rights"
    rights_root.mkdir(parents=True)
    source = REPOSITORY_ROOT / COMMITTED_RIGHTS_CATALOG_PATHS[0]
    shutil.copyfile(source, rights_root / "wrong-name.json")

    with pytest.raises(ValueError, match="filename"):
        load_snapshot_registry(
            tmp_path,
            registry_id="wrong-catalog-name",
            artifact_locations=(),
            rights_catalog_paths=(Path("data/rights/wrong-name.json"),),
        )


@pytest.mark.parametrize(
    "manifest_case",
    ("dataset", "historical", "media", "nonallowed"),
)
def test_loader_rejects_untrusted_manifest_semantics(
    tmp_path: Path,
    manifest_case: str,
) -> None:
    manifest_root = tmp_path / "data" / "manifests"
    archive_root = tmp_path / "data" / "archive" / "ecos"
    rights_root = tmp_path / "data" / "rights"
    manifest_root.mkdir(parents=True)
    archive_root.mkdir(parents=True)
    rights_root.mkdir(parents=True)
    location = COMMITTED_SNAPSHOT_LOCATIONS[0]
    source_manifest_path = REPOSITORY_ROOT / location.manifest_path
    source_archive_path = REPOSITORY_ROOT / location.archive_path
    source = SourceManifest.model_validate_json(source_manifest_path.read_bytes())
    data = source.model_dump(mode="python")
    if manifest_case == "dataset":
        data["source_kind"] = SourceKind.DATASET
    elif manifest_case == "historical":
        data["vintage_semantics"] = VintageSemantics.HISTORICAL_ARCHIVE
    elif manifest_case == "media":
        data["media_type"] = "text/csv"
    else:
        data["redistribution"]["status"] = RedistributionStatus.METADATA_ONLY
    changed = SourceManifest.model_validate(data)
    (tmp_path / location.manifest_path).write_text(
        changed.model_dump_json(exclude_none=True),
        encoding="utf-8",
    )
    shutil.copyfile(source_archive_path, tmp_path / location.archive_path)
    for catalog_path in COMMITTED_RIGHTS_CATALOG_PATHS:
        shutil.copyfile(
            REPOSITORY_ROOT / catalog_path,
            rights_root / catalog_path.name,
        )

    with pytest.raises(ValueError, match="trusted exact-scope"):
        load_snapshot_registry(
            tmp_path,
            registry_id=f"untrusted-{manifest_case}",
            artifact_locations=(location,),
            rights_catalog_paths=COMMITTED_RIGHTS_CATALOG_PATHS,
        )


def test_loader_rejects_archive_bytes_that_differ_from_manifest(
    tmp_path: Path,
) -> None:
    manifest_root = tmp_path / "data" / "manifests"
    archive_root = tmp_path / "data" / "archive" / "ecos"
    rights_root = tmp_path / "data" / "rights"
    manifest_root.mkdir(parents=True)
    archive_root.mkdir(parents=True)
    rights_root.mkdir(parents=True)
    location = COMMITTED_SNAPSHOT_LOCATIONS[0]
    shutil.copyfile(
        REPOSITORY_ROOT / location.manifest_path,
        tmp_path / location.manifest_path,
    )
    original = (REPOSITORY_ROOT / location.archive_path).read_bytes()
    (tmp_path / location.archive_path).write_bytes(b"X" + original[1:])
    for catalog_path in COMMITTED_RIGHTS_CATALOG_PATHS:
        shutil.copyfile(
            REPOSITORY_ROOT / catalog_path,
            rights_root / catalog_path.name,
        )

    with pytest.raises(ValueError, match="does not match"):
        load_snapshot_registry(
            tmp_path,
            registry_id="corrupt-archive",
            artifact_locations=(location,),
            rights_catalog_paths=COMMITTED_RIGHTS_CATALOG_PATHS,
        )


def test_loader_rejects_manifest_declared_oversize_before_archive_read(
    tmp_path: Path,
) -> None:
    manifest_root = tmp_path / "data" / "manifests"
    archive_root = tmp_path / "data" / "archive" / "ecos"
    rights_root = tmp_path / "data" / "rights"
    manifest_root.mkdir(parents=True)
    archive_root.mkdir(parents=True)
    rights_root.mkdir(parents=True)
    location = COMMITTED_SNAPSHOT_LOCATIONS[0]
    source = SourceManifest.model_validate_json(
        (REPOSITORY_ROOT / location.manifest_path).read_bytes()
    )
    data = source.model_dump(mode="python")
    data["byte_size"] = MAX_SNAPSHOT_BYTES + 1
    changed = SourceManifest.model_validate(data)
    (tmp_path / location.manifest_path).write_text(
        changed.model_dump_json(exclude_none=True),
        encoding="utf-8",
    )
    shutil.copyfile(
        REPOSITORY_ROOT / location.archive_path,
        tmp_path / location.archive_path,
    )
    for catalog_path in COMMITTED_RIGHTS_CATALOG_PATHS:
        shutil.copyfile(
            REPOSITORY_ROOT / catalog_path,
            rights_root / catalog_path.name,
        )

    with pytest.raises(ValueError, match="bounded reader limit"):
        load_snapshot_registry(
            tmp_path,
            registry_id="oversize-archive",
            artifact_locations=(location,),
            rights_catalog_paths=COMMITTED_RIGHTS_CATALOG_PATHS,
        )


def test_loader_rejects_oversize_archive_before_reading_it(
    tmp_path: Path,
) -> None:
    manifest_root = tmp_path / "data" / "manifests"
    archive_root = tmp_path / "data" / "archive" / "ecos"
    rights_root = tmp_path / "data" / "rights"
    manifest_root.mkdir(parents=True)
    archive_root.mkdir(parents=True)
    rights_root.mkdir(parents=True)
    location = COMMITTED_SNAPSHOT_LOCATIONS[0]
    shutil.copyfile(
        REPOSITORY_ROOT / location.manifest_path,
        tmp_path / location.manifest_path,
    )
    archive_path = tmp_path / location.archive_path
    with archive_path.open("wb") as stream:
        stream.seek(MAX_SNAPSHOT_BYTES)
        stream.write(b"X")
    for catalog_path in COMMITTED_RIGHTS_CATALOG_PATHS:
        shutil.copyfile(
            REPOSITORY_ROOT / catalog_path,
            rights_root / catalog_path.name,
        )

    with pytest.raises(ValueError, match="bounded reader limit"):
        load_snapshot_registry(
            tmp_path,
            registry_id="oversize-archive-file",
            artifact_locations=(location,),
            rights_catalog_paths=COMMITTED_RIGHTS_CATALOG_PATHS,
        )


def test_loader_sanitizes_missing_catalog_io_failure() -> None:
    with pytest.raises(
        SnapshotRegistryLoadError,
        match="trusted rights catalog could not be read",
    ):
        load_snapshot_registry(
            REPOSITORY_ROOT,
            registry_id="missing-catalog-file",
            artifact_locations=(),
            rights_catalog_paths=(Path("data/rights/not-present.json"),),
        )


def test_loader_sanitizes_missing_repository_and_artifact_roots(
    tmp_path: Path,
) -> None:
    missing_repository = tmp_path / "private-missing-repository"
    with pytest.raises(
        SnapshotRegistryLoadError,
        match="trusted repository root could not be resolved",
    ) as repository_error:
        load_snapshot_registry(
            missing_repository,
            registry_id="missing-repository",
            artifact_locations=(),
            rights_catalog_paths=(),
        )
    assert str(missing_repository) not in str(repository_error.value)

    empty_repository = tmp_path / "empty-repository"
    empty_repository.mkdir()
    with pytest.raises(
        SnapshotRegistryLoadError,
        match="trusted artifact root could not be resolved",
    ) as artifact_root_error:
        load_snapshot_registry(
            empty_repository,
            registry_id="missing-artifact-root",
            artifact_locations=(),
            rights_catalog_paths=(Path("data/rights/not-present.json"),),
        )
    assert str(empty_repository) not in str(artifact_root_error.value)


def test_loader_sanitizes_manifest_and_archive_io_failures(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    location = COMMITTED_SNAPSHOT_LOCATIONS[0]
    manifest_path = (REPOSITORY_ROOT / location.manifest_path).resolve()
    archive_path = (REPOSITORY_ROOT / location.archive_path).resolve()
    original_read_bytes = Path.read_bytes

    def fail_manifest_read(path: Path) -> bytes:
        if path == manifest_path:
            raise OSError("private manifest path")
        return original_read_bytes(path)

    monkeypatch.setattr(Path, "read_bytes", fail_manifest_read)
    with pytest.raises(
        SnapshotRegistryLoadError,
        match="trusted snapshot manifest could not be read",
    ):
        load_snapshot_registry(
            REPOSITORY_ROOT,
            registry_id="manifest-io-failure",
            artifact_locations=(location,),
            rights_catalog_paths=COMMITTED_RIGHTS_CATALOG_PATHS,
        )

    monkeypatch.undo()
    original_read_bytes = Path.read_bytes

    def fail_archive_read(path: Path) -> bytes:
        if path == archive_path:
            raise OSError("private archive path")
        return original_read_bytes(path)

    monkeypatch.setattr(Path, "read_bytes", fail_archive_read)
    with pytest.raises(
        SnapshotRegistryLoadError,
        match="trusted snapshot archive could not be read",
    ):
        load_snapshot_registry(
            REPOSITORY_ROOT,
            registry_id="archive-io-failure",
            artifact_locations=(location,),
            rights_catalog_paths=COMMITTED_RIGHTS_CATALOG_PATHS,
        )


def test_loader_sanitizes_archive_stat_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    location = COMMITTED_SNAPSHOT_LOCATIONS[0]
    archive_path = (REPOSITORY_ROOT / location.archive_path).resolve()
    original_is_file = Path.is_file
    original_stat = Path.stat

    def controlled_is_file(path: Path) -> bool:
        if path == archive_path:
            return True
        return original_is_file(path)

    def fail_archive_stat(path: Path, *args: object, **kwargs: object) -> Any:
        if path == archive_path:
            raise OSError("private archive path")
        return original_stat(path, *args, **kwargs)

    monkeypatch.setattr(Path, "is_file", controlled_is_file)
    monkeypatch.setattr(Path, "stat", fail_archive_stat)
    with pytest.raises(
        SnapshotRegistryLoadError,
        match="trusted snapshot archive could not be inspected",
    ):
        load_snapshot_registry(
            REPOSITORY_ROOT,
            registry_id="archive-stat-failure",
            artifact_locations=(location,),
            rights_catalog_paths=COMMITTED_RIGHTS_CATALOG_PATHS,
        )


def test_loader_rejects_wrong_artifact_filename_or_missing_archive(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    manifest_root = tmp_path / "data" / "manifests"
    archive_root = tmp_path / "data" / "archive" / "ecos"
    rights_root = tmp_path / "data" / "rights"
    manifest_root.mkdir(parents=True)
    archive_root.mkdir(parents=True)
    rights_root.mkdir(parents=True)
    location = COMMITTED_SNAPSHOT_LOCATIONS[0]
    source_manifest = REPOSITORY_ROOT / location.manifest_path
    source_archive = REPOSITORY_ROOT / location.archive_path
    temporary_archive = archive_root / source_archive.name
    for catalog_path in COMMITTED_RIGHTS_CATALOG_PATHS:
        shutil.copyfile(
            REPOSITORY_ROOT / catalog_path,
            rights_root / catalog_path.name,
        )

    shutil.copyfile(source_manifest, manifest_root / "wrong-name.json")
    shutil.copyfile(source_archive, temporary_archive)
    with pytest.raises(ValueError, match="filenames"):
        load_snapshot_registry(
            tmp_path,
            registry_id="wrong-artifact-name",
            artifact_locations=(
                SnapshotArtifactLocation(
                    binding=ECOS_GDP_BINDING,
                    manifest_path=Path("data/manifests/wrong-name.json"),
                    archive_path=location.archive_path,
                ),
            ),
            rights_catalog_paths=COMMITTED_RIGHTS_CATALOG_PATHS,
        )

    shutil.copyfile(source_manifest, manifest_root / source_manifest.name)
    temporary_archive.unlink()
    with pytest.raises(SnapshotRegistryLoadError, match="does not exist"):
        load_snapshot_registry(
            tmp_path,
            registry_id="missing-archive",
            artifact_locations=(location,),
            rights_catalog_paths=COMMITTED_RIGHTS_CATALOG_PATHS,
        )

    temporary_archive.write_bytes(b"short")
    with pytest.raises(ValueError, match="does not match"):
        load_snapshot_registry(
            tmp_path,
            registry_id="wrong-archive-size",
            artifact_locations=(location,),
            rights_catalog_paths=COMMITTED_RIGHTS_CATALOG_PATHS,
        )

    original_archive = source_archive.read_bytes()
    temporary_archive.write_bytes(original_archive)
    original_read_bytes = Path.read_bytes

    def change_archive_after_stat(path: Path) -> bytes:
        if path == temporary_archive.resolve():
            return original_archive[:-1]
        return original_read_bytes(path)

    monkeypatch.setattr(Path, "read_bytes", change_archive_after_stat)
    with pytest.raises(ValueError, match="does not match"):
        load_snapshot_registry(
            tmp_path,
            registry_id="archive-race",
            artifact_locations=(location,),
            rights_catalog_paths=COMMITTED_RIGHTS_CATALOG_PATHS,
        )


def test_unexpected_manifest_parser_and_normalizer_failures_become_sanitized_errors(
    committed_registry: SnapshotRegistry,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    call = _call(ECOS_GDP_BINDING, "2026Q1", call_id="unexpected-failure-call")

    def fail_manifest_validation(*args: Any, **kwargs: Any) -> Any:
        raise RuntimeError("private manifest detail")

    monkeypatch.setattr(reader_module, "_validate_manifest", fail_manifest_validation)
    manifest_result = read_snapshot_as_of(call=call, registry=committed_registry)
    assert manifest_result.error is not None
    assert manifest_result.error.code == "snapshot_manifest_validation_failed"
    assert "private manifest detail" not in manifest_result.error.message

    monkeypatch.undo()

    def fail_parser(*args: Any, **kwargs: Any) -> str:
        raise RuntimeError("raw row must not leak")

    monkeypatch.setattr(reader_module, "_selected_raw_value", fail_parser)
    parser_result = read_snapshot_as_of(call=call, registry=committed_registry)
    assert parser_result.error is not None
    assert parser_result.error.code == "snapshot_parser_failed"
    assert "raw row" not in parser_result.error.message

    monkeypatch.undo()

    def fail_normalizer(*args: Any, **kwargs: Any) -> Any:
        raise RuntimeError("normalizer internals")

    monkeypatch.setattr(reader_module, "normalize_source_value", fail_normalizer)
    normalization_result = read_snapshot_as_of(call=call, registry=committed_registry)
    assert normalization_result.error is not None
    assert normalization_result.error.code == "snapshot_normalization_failed"
    assert "normalizer internals" not in normalization_result.error.message


def test_normalization_registry_mismatch_is_a_tool_error(
    committed_registry: SnapshotRegistry,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    wrong_rule = reader_module.normalization_rule(
        SourceSystem.ECOS,
        ECOS_CURRENT_ACCOUNT_BINDING.table_id,
        ECOS_CURRENT_ACCOUNT_BINDING.item_id,
    )
    monkeypatch.setattr(reader_module, "normalization_rule", lambda *args: wrong_rule)

    result = read_snapshot_as_of(
        call=_call(ECOS_GDP_BINDING, "2026Q1"),
        registry=committed_registry,
    )

    assert result.error is not None
    assert result.error.code == "snapshot_registry_misconfigured"


@pytest.mark.parametrize(
    ("exception", "error_code"),
    [
        (ValueError("internal registry detail"), "snapshot_registry_misconfigured"),
        (RuntimeError("unexpected implementation detail"), "snapshot_normalization_failed"),
    ],
    ids=("missing-rule", "unexpected-lookup-failure"),
)
def test_normalization_lookup_failures_are_sanitized(
    committed_registry: SnapshotRegistry,
    monkeypatch: pytest.MonkeyPatch,
    exception: Exception,
    error_code: str,
) -> None:
    def fail_lookup(*args: object) -> Any:
        raise exception

    monkeypatch.setattr(reader_module, "normalization_rule", fail_lookup)
    result = read_snapshot_as_of(
        call=_call(ECOS_GDP_BINDING, "2026Q1"),
        registry=committed_registry,
    )

    assert result.error is not None
    assert result.error.code == error_code
    assert "detail" not in result.error.message


@pytest.mark.parametrize(
    ("value", "frequency", "valid"),
    [
        ("2026Q1", "Q", True),
        ("2026Q0", "Q", False),
        ("26Q1", "Q", False),
        ("\uff12\uff10\uff12\uff16Q1", "Q", False),
        (202601, "Q", False),
        ("202601", "M", True),
        ("202600", "M", False),
        ("202613", "M", False),
        ("2026Q1", "M", False),
        ("\uff12\uff10\uff12\uff16\uff10\uff11", "M", False),
        ("202601", "A", False),
    ],
)
def test_provider_period_validation_is_exact(
    value: object,
    frequency: str,
    valid: bool,
) -> None:
    assert reader_module._valid_provider_period(value, frequency) is valid


def test_unsupported_internal_provider_binding_fails_closed() -> None:
    binding = SnapshotSeriesBinding(
        source_system=SourceSystem.OECD,
        table_id="TABLE",
        item_id="ITEM",
        document_family="unsupported-provider",
        rights_decision_id="unsupported-provider-rights",
        normalization_rule_id=ECOS_GDP_BINDING.normalization_rule_id,
        frequency="M",
        raw_unit="unit",
        provider_item_id="ITEM",
    )

    assert (
        reader_module._selected_raw_value(b"{}", binding, "202601")
        is SnapshotAbstentionReason.SOURCE_SCOPE_MISMATCH
    )
