"""Adversarial offline tests for the trusted STES artifact registry."""

import copy
import csv
import hashlib
import io
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import pytest

import sovereignlab.vintage.registry as registry_module
from sovereignlab.schemas import (
    AvailabilityEvidenceBasis,
    EditionAvailabilityLedger,
    RedistributionStatus,
    RightsCatalog,
    SourceKind,
    SourceManifest,
    SourceSystem,
    VintageSemantics,
)
from sovereignlab.vintage.registry import (
    CLI_STES_BINDING,
    COMMITTED_ACTIVE_STES_LEDGER_ID,
    COMMITTED_CAPTURED_AT_SOURCE_ID,
    COMMITTED_COMPLETE_THROUGH_SOURCE_ID,
    COMMITTED_STES_ARTIFACT_LOCATIONS,
    COMMITTED_STES_CATALOG_PATHS,
    COMMITTED_STES_LEDGER_PATHS,
    GDP_STES_BINDING,
    MAX_STES_ARCHIVE_COLUMNS,
    STES_DATAFLOW_ID,
    STES_DATAFLOW_VERSION,
    STES_REGISTRY_DESCRIPTOR_SHA256,
    STES_REGISTRY_ID,
    StesArtifactLocation,
    StesArtifactRole,
    StesCatalogArtifact,
    StesLedgerArtifact,
    StesRegistry,
    StesRegistryEntry,
    StesRegistryLoadError,
    StesSeriesBinding,
    StesSourceArtifact,
    load_committed_stes_registry,
    load_stes_registry,
)

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
EXPECTED_DESCRIPTOR_SHA256 = "103eb3bea7beebadeb0a7e193ff76fc95b518a8a7bed6825d9eb1f25431fb420"
CLI_SOURCE_ID = "oecd-stes-cli-kor-li-aa-20260717t115302688498z"

_CSV_HEADERS = (
    "REF_AREA",
    "FREQ",
    "MEASURE",
    "UNIT_MEASURE",
    "ACTIVITY",
    "EDITION",
    "TIME_PERIOD",
    "OBS_VALUE",
)
_CLI_ROW = ("KOR", "M", "LI_AA", "IX", "_T", "202607", "2026-05", "102.66")
_OLDER_CLI_ROW = ("KOR", "M", "LI_AA", "IX", "_T", "202606", "2026-04", "101.25")
_UNSET = object()


class _BytesSubclass(bytes):
    """A mutable-behavior surface that must not cross the exact-bytes boundary."""


class _TupleSubclass(tuple):
    pass


def _csv_bytes(
    rows: tuple[tuple[str, ...], ...] = (_OLDER_CLI_ROW, _CLI_ROW),
    *,
    headers: tuple[str, ...] = _CSV_HEADERS,
) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.writer(stream, lineterminator="\n")
    writer.writerow(headers)
    writer.writerows(rows)
    return stream.getvalue().encode("utf-8-sig")


def _constraint_xml(
    *,
    role: str = "available",
    root: str = "Structure",
    constraint_count: int = 1,
    reference_count: int = 1,
    edition_region_count: int = 1,
    editions: tuple[str, ...] = ("202607",),
    agency: str | None = "OECD.SDD.STES",
    flow: str | None = "DSD_STES_REVISIONS@DF_STES_REVISIONS",
    flow_version: str | None = "4.0",
    constraint_id: str | None = None,
    constraint_version: str | None = None,
    valid_from: object = _UNSET,
) -> bytes:
    if constraint_id is None:
        constraint_id = "CC" if role == "available" else "CR_A_DSD_STES_REVISIONS@DF_STES_REVISIONS"
    if constraint_version is None:
        constraint_version = "1.0" if role == "available" else "4.0"
    if valid_from is _UNSET:
        valid_from = None if role == "available" else "2026-07-08T09:33:35.737Z"

    def attribute(name: str, value: object) -> str:
        return "" if value is None else f' {name}="{value}"'

    references = "".join(
        (
            "<Ref"
            f"{attribute('agencyID', agency)}"
            f"{attribute('id', flow)}"
            f"{attribute('version', flow_version)}"
            "/>"
        )
        for _ in range(reference_count)
    )
    values = "".join(f"<Value>{edition}</Value>" for edition in editions)
    inventories = "".join(
        f'<KeyValue id="EDITION">{values}</KeyValue>' for _ in range(edition_region_count)
    )
    constraint = (
        "<ContentConstraint"
        f"{attribute('id', constraint_id)}"
        f"{attribute('version', constraint_version)}"
        f"{attribute('validFrom', valid_from)}"
        f">{references}{inventories}</ContentConstraint>"
    )
    return f"<{root}>{constraint * constraint_count}</{root}>".encode()


def _model_bytes(model: Any) -> bytes:
    return model.model_dump_json(exclude_none=True).encode("utf-8")


def _source_artifact_with(
    artifact: StesSourceArtifact,
    *,
    archive_bytes: bytes | None = None,
    **manifest_updates: object,
) -> StesSourceArtifact:
    payload = artifact.archive_bytes if archive_bytes is None else archive_bytes
    updates = {
        "byte_size": len(payload),
        "content_sha256": hashlib.sha256(payload).hexdigest(),
        **manifest_updates,
    }
    manifest = SourceManifest.model_validate(
        {
            **artifact.manifest.model_dump(mode="python"),
            **updates,
        }
    )
    return StesSourceArtifact(
        role=artifact.role,
        manifest=manifest,
        manifest_bytes=_model_bytes(manifest),
        archive_bytes=payload,
    )


def _ledger_artifact_with(
    artifact: StesLedgerArtifact,
    **updates: object,
) -> StesLedgerArtifact:
    ledger = EditionAvailabilityLedger.model_validate(
        {
            **artifact.ledger.model_dump(mode="python"),
            **updates,
        }
    )
    return StesLedgerArtifact(ledger=ledger, ledger_bytes=_model_bytes(ledger))


def _catalog_artifact_with(
    artifact: StesCatalogArtifact,
    **updates: object,
) -> StesCatalogArtifact:
    catalog = RightsCatalog.model_validate(
        {
            **artifact.catalog.model_dump(mode="python"),
            **updates,
        }
    )
    return StesCatalogArtifact(catalog=catalog, catalog_bytes=_model_bytes(catalog))


def _registry(
    base: StesRegistry,
    **updates: object,
) -> StesRegistry:
    values = {
        "registry_id": base.registry_id,
        "entries": base.entries,
        "support_artifacts": base.support_artifacts,
        "ledger_artifacts": base.ledger_artifacts,
        "catalog_artifacts": base.catalog_artifacts,
        "active_ledger_id": base.active_ledger_id,
        "complete_through_source_id": base.complete_through_source_id,
        "captured_at_source_id": base.captured_at_source_id,
    }
    values.update(updates)
    return StesRegistry(**values)  # type: ignore[arg-type]


def _tampered_registry(base: StesRegistry, **updates: object) -> StesRegistry:
    clone = copy.copy(base)
    for attribute, value in updates.items():
        object.__setattr__(clone, attribute, value)
    return clone


def _generic_committed_registry() -> StesRegistry:
    return load_stes_registry(
        REPOSITORY_ROOT,
        registry_id=STES_REGISTRY_ID,
        artifact_locations=COMMITTED_STES_ARTIFACT_LOCATIONS,
        ledger_paths=COMMITTED_STES_LEDGER_PATHS,
        catalog_paths=COMMITTED_STES_CATALOG_PATHS,
        active_ledger_id=COMMITTED_ACTIVE_STES_LEDGER_ID,
        complete_through_source_id=COMMITTED_COMPLETE_THROUGH_SOURCE_ID,
        captured_at_source_id=COMMITTED_CAPTURED_AT_SOURCE_ID,
    )


@pytest.fixture(scope="module")
def committed_registry() -> StesRegistry:
    return load_committed_stes_registry(REPOSITORY_ROOT)


@pytest.fixture(scope="module")
def small_registry(committed_registry: StesRegistry) -> StesRegistry:
    cli_entry = next(
        entry for entry in committed_registry.entries if entry.binding == CLI_STES_BINDING
    )
    assert cli_entry.data_artifact is not None
    small_data = _source_artifact_with(
        cli_entry.data_artifact,
        archive_bytes=_csv_bytes(),
    )
    return _registry(
        committed_registry,
        registry_id="test-stes-registry-v1",
        entries=(
            StesRegistryEntry(binding=CLI_STES_BINDING, data_artifact=small_data),
            StesRegistryEntry(binding=GDP_STES_BINDING),
        ),
    )


def _write_registry_tree(root: Path, registry: StesRegistry) -> None:
    artifacts = {
        artifact.manifest.source_id: artifact
        for artifact in (
            *(entry.data_artifact for entry in registry.entries if entry.data_artifact is not None),
            *registry.support_artifacts,
        )
    }
    for location in COMMITTED_STES_ARTIFACT_LOCATIONS:
        source_id = location.manifest_path.stem
        artifact = artifacts[source_id]
        manifest_path = root / location.manifest_path
        archive_path = root / location.archive_path
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        archive_path.parent.mkdir(parents=True, exist_ok=True)
        manifest_path.write_bytes(artifact.manifest_bytes)
        archive_path.write_bytes(artifact.archive_bytes)

    for relative_path, artifact in zip(
        COMMITTED_STES_LEDGER_PATHS,
        registry.ledger_artifacts,
        strict=True,
    ):
        path = root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(artifact.ledger_bytes)
    for relative_path, artifact in zip(
        COMMITTED_STES_CATALOG_PATHS,
        registry.catalog_artifacts,
        strict=True,
    ):
        path = root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(artifact.catalog_bytes)


def _load_tree(root: Path, **updates: object) -> StesRegistry:
    arguments: dict[str, object] = {
        "registry_id": "test-stes-registry-v1",
        "artifact_locations": COMMITTED_STES_ARTIFACT_LOCATIONS,
        "ledger_paths": COMMITTED_STES_LEDGER_PATHS,
        "catalog_paths": COMMITTED_STES_CATALOG_PATHS,
        "active_ledger_id": COMMITTED_ACTIVE_STES_LEDGER_ID,
        "complete_through_source_id": COMMITTED_COMPLETE_THROUGH_SOURCE_ID,
        "captured_at_source_id": COMMITTED_CAPTURED_AT_SOURCE_ID,
    }
    arguments.update(updates)
    return load_stes_registry(root, **arguments)  # type: ignore[arg-type]


def test_committed_registry_loads_exact_provenance_and_archive_summary(
    committed_registry: StesRegistry,
) -> None:
    assert committed_registry.registry_id == STES_REGISTRY_ID
    assert STES_REGISTRY_DESCRIPTOR_SHA256 == EXPECTED_DESCRIPTOR_SHA256
    assert committed_registry.descriptor_sha256 == EXPECTED_DESCRIPTOR_SHA256

    state = committed_registry.validated_state()
    assert state.active_ledger.ledger_id == COMMITTED_ACTIVE_STES_LEDGER_ID
    assert len(state.entries) == 2
    assert len(state.support_artifacts) == 4
    assert len(state.ledger_artifacts) == 2
    assert len(state.catalog_artifacts) == 2
    assert tuple(catalog.catalog.catalog_id for catalog in state.catalog_artifacts) == (
        "kor-rtd-rights-2026-07-16",
        "kor-rtd-rights-2026-07-17",
    )
    assert tuple(catalog.catalog.catalog_id for catalog in state.catalog_artifacts) == tuple(
        catalog.catalog_id for catalog in state.rights_catalogs
    )

    cli = state.entry_for(CLI_STES_BINDING.scope)
    gdp = state.entry_for(GDP_STES_BINDING.scope)
    assert cli is not None and cli.data_artifact is not None
    assert cli.archive_summary is not None
    assert cli.archive_summary.descriptor() == {
        "column_count": 28,
        "edition_count": 239,
        "first_edition": "200604",
        "last_edition": "202607",
        "row_count": 75_060,
    }
    assert len(cli.data_artifact.archive_bytes) == 21_734_727
    assert (
        hashlib.sha256(cli.data_artifact.archive_bytes).hexdigest()
        == "ac7d0f9a2517870173885f1d45e2edea90f54cd485e2f539c73afddde566f058"
    )
    assert gdp is not None and gdp.data_artifact is None
    assert gdp.archive_summary is None
    assert state.entry_for(("USA", "M", "LI_AA", "IX", "_T")) is None

    descriptor = committed_registry.canonical_descriptor_bytes().decode("utf-8")
    assert len(descriptor.encode("utf-8")) == 4_379
    assert "data/archive" not in descriptor
    assert "sdmx.oecd.org" not in descriptor
    assert "102.66" not in descriptor


def test_descriptor_is_order_independent(small_registry: StesRegistry) -> None:
    reversed_registry = _registry(
        small_registry,
        entries=tuple(reversed(small_registry.entries)),
        support_artifacts=tuple(reversed(small_registry.support_artifacts)),
        ledger_artifacts=tuple(reversed(small_registry.ledger_artifacts)),
        catalog_artifacts=tuple(reversed(small_registry.catalog_artifacts)),
    )

    assert reversed_registry.canonical_descriptor_bytes() == (
        small_registry.canonical_descriptor_bytes()
    )
    assert reversed_registry.descriptor_sha256 == small_registry.descriptor_sha256


def test_generic_loader_matches_committed_loader(
    committed_registry: StesRegistry,
) -> None:
    generic = _generic_committed_registry()

    assert generic.canonical_descriptor_bytes() == committed_registry.canonical_descriptor_bytes()
    assert generic.descriptor_sha256 == committed_registry.descriptor_sha256


def test_committed_registry_id_is_pinned_to_one_descriptor(
    committed_registry: StesRegistry,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        registry_module, "load_stes_registry", lambda *args, **kwargs: committed_registry
    )
    monkeypatch.setattr(registry_module, "STES_REGISTRY_DESCRIPTOR_SHA256", "0" * 64)

    with pytest.raises(ValueError, match="preserve v1"):
        load_committed_stes_registry(REPOSITORY_ROOT)


def test_explicit_locations_cover_all_current_stes_inputs() -> None:
    manifests = {
        path.relative_to(REPOSITORY_ROOT)
        for path in (REPOSITORY_ROOT / "data" / "manifests").glob("oecd-stes-*.json")
    }
    archives = {
        path.relative_to(REPOSITORY_ROOT)
        for path in (REPOSITORY_ROOT / "data" / "archive" / "oecd-stes").glob("*")
        if path.is_file()
    }
    ledgers = {
        path.relative_to(REPOSITORY_ROOT)
        for path in (REPOSITORY_ROOT / "data" / "availability").glob("oecd-stes-ledger-*.json")
    }
    catalogs = {
        path.relative_to(REPOSITORY_ROOT)
        for path in (REPOSITORY_ROOT / "data" / "rights").glob("*.json")
    }

    assert manifests == {location.manifest_path for location in COMMITTED_STES_ARTIFACT_LOCATIONS}
    assert archives == {location.archive_path for location in COMMITTED_STES_ARTIFACT_LOCATIONS}
    assert ledgers == set(COMMITTED_STES_LEDGER_PATHS)
    assert catalogs == set(COMMITTED_STES_CATALOG_PATHS)


@pytest.mark.parametrize(
    "field",
    ("entries", "support_artifacts", "ledger_artifacts", "catalog_artifacts"),
)
def test_registry_requires_exact_immutable_tuples(
    small_registry: StesRegistry,
    field: str,
) -> None:
    values = list(getattr(small_registry, field))
    corrupt = _tampered_registry(small_registry, **{field: values})
    with pytest.raises(ValueError, match="immutable tuple"):
        corrupt.validated_state()

    deceptive = _tampered_registry(
        small_registry,
        **{field: _TupleSubclass(getattr(small_registry, field))},
    )
    with pytest.raises(ValueError, match="immutable tuple"):
        deceptive.validated_state()


@pytest.mark.parametrize("registry_id", ("", " ", 7))
def test_registry_requires_a_nonblank_builtin_string_id(
    small_registry: StesRegistry,
    registry_id: object,
) -> None:
    corrupt = _tampered_registry(small_registry, registry_id=registry_id)
    with pytest.raises(ValueError, match="non-empty string"):
        corrupt.validated_state()


@pytest.mark.parametrize(
    ("field", "invalid"),
    (
        ("entries", (object(),)),
        ("support_artifacts", (object(),)),
        ("ledger_artifacts", (object(),)),
        ("catalog_artifacts", (object(),)),
    ),
)
def test_registry_rejects_invalid_artifact_types(
    small_registry: StesRegistry,
    field: str,
    invalid: tuple[object, ...],
) -> None:
    corrupt = _tampered_registry(small_registry, **{field: invalid})
    with pytest.raises(ValueError, match="invalid type"):
        corrupt.validated_state()


def test_registry_rejects_invalid_entry_binding_and_data_types(
    small_registry: StesRegistry,
) -> None:
    invalid_binding = _tampered_registry(
        small_registry,
        entries=(
            StesRegistryEntry(binding="not a binding"),  # type: ignore[arg-type]
            small_registry.entries[1],
        ),
    )
    with pytest.raises(ValueError, match="binding has an invalid type"):
        invalid_binding.validated_state()

    neighboring = replace(CLI_STES_BINDING, measure="NEIGHBOR")
    nonapproved = _tampered_registry(
        small_registry,
        entries=(
            StesRegistryEntry(binding=neighboring),
            small_registry.entries[1],
        ),
    )
    with pytest.raises(ValueError, match="non-approved"):
        nonapproved.validated_state()

    invalid_data = _tampered_registry(
        small_registry,
        entries=(
            StesRegistryEntry(
                binding=CLI_STES_BINDING,
                data_artifact=object(),  # type: ignore[arg-type]
            ),
            small_registry.entries[1],
        ),
    )
    with pytest.raises(ValueError, match="data artifact has an invalid type"):
        invalid_data.validated_state()


def test_registry_requires_each_frozen_scope_exactly_once(
    small_registry: StesRegistry,
) -> None:
    missing = _tampered_registry(small_registry, entries=(small_registry.entries[0],))
    duplicate = _tampered_registry(
        small_registry,
        entries=(small_registry.entries[0], small_registry.entries[0]),
    )
    for registry in (missing, duplicate):
        with pytest.raises(ValueError, match="every frozen scope exactly once"):
            registry.validated_state()


def test_allowed_and_unavailable_scopes_enforce_archive_policy(
    small_registry: StesRegistry,
) -> None:
    allowed_missing = _tampered_registry(
        small_registry,
        entries=(
            StesRegistryEntry(binding=CLI_STES_BINDING),
            small_registry.entries[1],
        ),
    )
    with pytest.raises(ValueError, match="allowed STES scope"):
        allowed_missing.validated_state()

    cli_artifact = small_registry.entries[0].data_artifact
    assert cli_artifact is not None
    wrong_role = replace(cli_artifact, role=StesArtifactRole.AVAILABILITY_SUPPORT)
    allowed_wrong_role = _tampered_registry(
        small_registry,
        entries=(
            StesRegistryEntry(binding=CLI_STES_BINDING, data_artifact=wrong_role),
            small_registry.entries[1],
        ),
    )
    with pytest.raises(ValueError, match="allowed STES scope"):
        allowed_wrong_role.validated_state()

    unavailable_with_archive = _tampered_registry(
        small_registry,
        entries=(
            small_registry.entries[0],
            StesRegistryEntry(binding=GDP_STES_BINDING, data_artifact=cli_artifact),
        ),
    )
    with pytest.raises(ValueError, match="unavailable STES scope"):
        unavailable_with_archive.validated_state()


def test_registry_rejects_support_role_and_duplicate_source_ids(
    small_registry: StesRegistry,
) -> None:
    cli_artifact = small_registry.entries[0].data_artifact
    assert cli_artifact is not None
    wrong_role = _tampered_registry(small_registry, support_artifacts=(cli_artifact,))
    with pytest.raises(ValueError, match="support artifact has an invalid trusted role"):
        wrong_role.validated_state()

    duplicate = _tampered_registry(
        small_registry,
        support_artifacts=(
            *small_registry.support_artifacts,
            small_registry.support_artifacts[0],
        ),
    )
    with pytest.raises(ValueError, match="source IDs must be unique"):
        duplicate.validated_state()

    colliding_data = _source_artifact_with(
        cli_artifact,
        source_id=small_registry.support_artifacts[0].manifest.source_id,
    )
    cross_role_duplicate = _tampered_registry(
        small_registry,
        entries=(
            StesRegistryEntry(binding=CLI_STES_BINDING, data_artifact=colliding_data),
            small_registry.entries[1],
        ),
    )
    with pytest.raises(ValueError, match="registry source IDs must be unique"):
        cross_role_duplicate.validated_state()


def test_registry_rejects_duplicate_ledger_and_catalog_ids(
    small_registry: StesRegistry,
) -> None:
    duplicate_ledger = _tampered_registry(
        small_registry,
        ledger_artifacts=(
            *small_registry.ledger_artifacts,
            small_registry.ledger_artifacts[0],
        ),
    )
    with pytest.raises(ValueError, match="ledger ID must be unique"):
        duplicate_ledger.validated_state()

    duplicate_catalog = _tampered_registry(
        small_registry,
        catalog_artifacts=(
            *small_registry.catalog_artifacts,
            small_registry.catalog_artifacts[0],
        ),
    )
    with pytest.raises(ValueError, match="catalog ID must be unique"):
        duplicate_catalog.validated_state()


def test_registry_requires_completeness_support_sources(
    small_registry: StesRegistry,
) -> None:
    for field in ("complete_through_source_id", "captured_at_source_id"):
        corrupt = _tampered_registry(small_registry, **{field: "missing-support-source"})
        with pytest.raises(ValueError, match="completeness sources are missing"):
            corrupt.validated_state()


def test_registry_cross_binds_active_ledger_capture_instants(
    small_registry: StesRegistry,
) -> None:
    wrong_complete = _tampered_registry(
        small_registry,
        complete_through_source_id=COMMITTED_CAPTURED_AT_SOURCE_ID,
    )
    with pytest.raises(ValueError, match="complete_through"):
        wrong_complete.validated_state()

    wrong_capture = _tampered_registry(
        small_registry,
        captured_at_source_id=COMMITTED_COMPLETE_THROUGH_SOURCE_ID,
    )
    with pytest.raises(ValueError, match="captured_at"):
        wrong_capture.validated_state()


def test_bundle_validation_requires_every_ledger_evidence_source(
    small_registry: StesRegistry,
) -> None:
    referenced = {
        source_id
        for ledger_artifact in small_registry.ledger_artifacts
        for edition in ledger_artifact.ledger.editions
        for evidence in edition.evidence
        for source_id in evidence.source_manifest_ids
    }
    supports = tuple(
        artifact
        for artifact in small_registry.support_artifacts
        if artifact.manifest.source_id not in referenced
        or artifact.manifest.source_id == COMMITTED_COMPLETE_THROUGH_SOURCE_ID
        or artifact.manifest.source_id == COMMITTED_CAPTURED_AT_SOURCE_ID
    )
    corrupt = _tampered_registry(small_registry, support_artifacts=supports)

    with pytest.raises(ValueError, match="lacks one exact constraint capture pair"):
        corrupt.validated_state()


def test_binding_must_match_normalization_registry(
    small_registry: StesRegistry,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class WrongRule:
        rule_id = "wrong-rule"

    monkeypatch.setattr(registry_module, "normalization_rule", lambda *args: WrongRule())
    with pytest.raises(ValueError, match="normalization registry"):
        small_registry.validated_state()


@pytest.mark.parametrize(
    ("field", "replacement", "message"),
    (
        ("source_kind", SourceKind.DATASET, "availability support manifest"),
        ("publisher", "Other Publisher", "availability support manifest"),
        ("document_family", "other-family", "availability support manifest"),
        ("media_type", "text/csv", "availability support manifest"),
        (
            "vintage_semantics",
            VintageSemantics.HISTORICAL_ARCHIVE,
            "availability support manifest",
        ),
        (
            "redistribution",
            RedistributionStatus.UNKNOWN,
            "availability support manifest",
        ),
        (
            "canonical_url",
            "https://example.invalid/wrong-constraint",
            "availability support manifest",
        ),
        ("source_id", "other-support-source", "does not identify"),
    ),
)
def test_support_manifest_must_match_its_exact_role(
    small_registry: StesRegistry,
    field: str,
    replacement: object,
    message: str,
) -> None:
    artifact = small_registry.support_artifacts[0].validated()
    if field == "redistribution":
        replacement = artifact.manifest.redistribution.model_copy(update={"status": replacement})
    manifest = artifact.manifest.model_copy(update={field: replacement})
    changed = replace(artifact, manifest=manifest)
    with pytest.raises(ValueError, match=message):
        registry_module._validate_support_artifact(changed)


def test_constraint_xml_parses_exact_role_identity_and_inventory() -> None:
    available = registry_module._parse_constraint_xml(
        _constraint_xml(),
        role=registry_module._ConstraintRole.AVAILABLE,
        capture_token="20260717t000000000000z",
        source_id="available-source",
    )
    content = registry_module._parse_constraint_xml(
        _constraint_xml(role="content"),
        role=registry_module._ConstraintRole.CONTENT,
        capture_token="20260717t000000000000z",
        source_id="content-source",
    )

    assert available.dataflow_id == STES_DATAFLOW_ID
    assert available.dataflow_version == STES_DATAFLOW_VERSION
    assert available.constraint_id == "CC"
    assert available.constraint_version == "1.0"
    assert available.valid_from is None
    assert available.editions == frozenset({"202607"})
    assert content.constraint_id == "CR_A_DSD_STES_REVISIONS@DF_STES_REVISIONS"
    assert content.constraint_version == STES_DATAFLOW_VERSION
    assert content.valid_from == datetime(2026, 7, 8, 9, 33, 35, 737000, tzinfo=UTC)


@pytest.mark.parametrize(
    ("payload", "role", "message"),
    (
        (
            b"<!DOCTYPE Structure>" + _constraint_xml(),
            registry_module._ConstraintRole.AVAILABLE,
            "document type",
        ),
        (
            b"<!ENTITY injected 'x'>" + _constraint_xml(),
            registry_module._ConstraintRole.AVAILABLE,
            "document type",
        ),
        (b"<", registry_module._ConstraintRole.AVAILABLE, "invalid XML"),
        (
            _constraint_xml(root="WrongRoot"),
            registry_module._ConstraintRole.AVAILABLE,
            "invalid root",
        ),
        (
            _constraint_xml(constraint_count=0),
            registry_module._ConstraintRole.AVAILABLE,
            "one content constraint",
        ),
        (
            _constraint_xml(constraint_count=2),
            registry_module._ConstraintRole.AVAILABLE,
            "one content constraint",
        ),
        (
            _constraint_xml(reference_count=0),
            registry_module._ConstraintRole.AVAILABLE,
            "one dataflow reference",
        ),
        (
            _constraint_xml(reference_count=2),
            registry_module._ConstraintRole.AVAILABLE,
            "one dataflow reference",
        ),
        (
            _constraint_xml(agency=None),
            registry_module._ConstraintRole.AVAILABLE,
            "identity is incomplete",
        ),
        (
            _constraint_xml(flow=None),
            registry_module._ConstraintRole.AVAILABLE,
            "identity is incomplete",
        ),
        (
            _constraint_xml(flow_version=None),
            registry_module._ConstraintRole.AVAILABLE,
            "identity is incomplete",
        ),
        (
            _constraint_xml(constraint_id=""),
            registry_module._ConstraintRole.AVAILABLE,
            "identity is incomplete",
        ),
        (
            _constraint_xml(constraint_version=""),
            registry_module._ConstraintRole.AVAILABLE,
            "identity is incomplete",
        ),
        (
            _constraint_xml(edition_region_count=0),
            registry_module._ConstraintRole.AVAILABLE,
            "one edition inventory",
        ),
        (
            _constraint_xml(edition_region_count=2),
            registry_module._ConstraintRole.AVAILABLE,
            "one edition inventory",
        ),
        (
            _constraint_xml(editions=()),
            registry_module._ConstraintRole.AVAILABLE,
            "invalid edition inventory",
        ),
        (
            _constraint_xml(editions=("202607", "202607")),
            registry_module._ConstraintRole.AVAILABLE,
            "invalid edition inventory",
        ),
        (
            _constraint_xml(editions=("2026-07",)),
            registry_module._ConstraintRole.AVAILABLE,
            "invalid edition inventory",
        ),
        (
            _constraint_xml(valid_from="2026-07-08T09:33:35Z"),
            registry_module._ConstraintRole.AVAILABLE,
            "cannot declare",
        ),
        (
            _constraint_xml(role="content", valid_from=None),
            registry_module._ConstraintRole.CONTENT,
            "requires validFrom",
        ),
        (
            _constraint_xml(role="content", valid_from="not-an-instant"),
            registry_module._ConstraintRole.CONTENT,
            "invalid instant",
        ),
        (
            _constraint_xml(role="content", valid_from="2026-07-08T09:33:35"),
            registry_module._ConstraintRole.CONTENT,
            "invalid instant",
        ),
        (
            _constraint_xml(agency="OTHER"),
            registry_module._ConstraintRole.AVAILABLE,
            "differs from its exact role",
        ),
        (
            _constraint_xml(flow="OTHER_FLOW"),
            registry_module._ConstraintRole.AVAILABLE,
            "differs from its exact role",
        ),
        (
            _constraint_xml(flow_version="5.0"),
            registry_module._ConstraintRole.AVAILABLE,
            "differs from its exact role",
        ),
        (
            _constraint_xml(constraint_id="OTHER"),
            registry_module._ConstraintRole.AVAILABLE,
            "differs from its exact role",
        ),
        (
            _constraint_xml(constraint_version="5.0"),
            registry_module._ConstraintRole.AVAILABLE,
            "differs from its exact role",
        ),
    ),
)
def test_constraint_xml_rejects_structural_identity_and_inventory_tampering(
    payload: bytes,
    role: object,
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        registry_module._parse_constraint_xml(
            payload,
            role=role,
            capture_token="20260717t000000000000z",
            source_id="synthetic-source",
        )


def _constraint_context(
    registry: StesRegistry,
) -> tuple[
    registry_module._ValidatedStesRegistry,
    list[registry_module._ValidatedSourceArtifact],
    dict[str, registry_module._StesConstraintSnapshot],
    dict[str, SourceManifest],
]:
    state = registry.validated_state()
    supports = list(state.support_artifacts)
    snapshots = {
        artifact.manifest.source_id: registry_module._validate_support_artifact(artifact)
        for artifact in supports
    }
    manifests = {artifact.manifest.source_id: artifact.manifest for artifact in supports}
    return state, supports, snapshots, manifests


def test_committed_constraint_pairs_join_every_ledger_exactly(
    small_registry: StesRegistry,
) -> None:
    state, supports, snapshots, _ = _constraint_context(small_registry)
    captures: dict[str, dict[object, registry_module._StesConstraintSnapshot]] = {}
    for snapshot in snapshots.values():
        captures.setdefault(snapshot.capture_token, {})[snapshot.role] = snapshot

    assert set(captures) == {
        "20260717t101906273935z",
        "20260717t115242998550z",
    }
    assert all(
        set(roles)
        == {
            registry_module._ConstraintRole.AVAILABLE,
            registry_module._ConstraintRole.CONTENT,
        }
        for roles in captures.values()
    )
    for roles in captures.values():
        available = roles[registry_module._ConstraintRole.AVAILABLE]
        content = roles[registry_module._ConstraintRole.CONTENT]
        assert available.editions == content.editions
        assert len(available.editions) == 330
        assert content.valid_from is not None

    registry_module._validate_constraint_ledger_join(
        snapshots,
        supports,
        list(state.ledger_artifacts),
    )
    for ledger_artifact in state.ledger_artifacts:
        ledger = ledger_artifact.ledger
        capture = next(
            roles
            for roles in captures.values()
            if next(
                artifact.manifest.retrieved_at
                for artifact in supports
                if artifact.manifest.source_id
                == roles[registry_module._ConstraintRole.AVAILABLE].source_id
            )
            == ledger.complete_through
        )
        assert {record.edition for record in ledger.editions} == capture[
            registry_module._ConstraintRole.AVAILABLE
        ].editions


@pytest.mark.parametrize(
    ("mutation", "message"),
    (
        ("manifest-set", "manifests and parsed constraints differ"),
        ("duplicate-role", "repeats a role"),
        ("missing-role", "both exact roles"),
        ("inventory", "inconsistent edition inventories"),
        ("future-valid-from", "validFrom follows"),
        ("ledger-capture", "lacks one exact constraint capture pair"),
        ("ledger-inventory", "constraint edition inventory"),
        ("unused-capture", "unused constraint capture"),
    ),
)
def test_constraint_ledger_join_rejects_cross_artifact_tampering(
    small_registry: StesRegistry,
    mutation: str,
    message: str,
) -> None:
    state, supports, snapshots, _ = _constraint_context(small_registry)
    ledgers = list(state.ledger_artifacts)
    available = next(
        snapshot
        for snapshot in snapshots.values()
        if snapshot.role is registry_module._ConstraintRole.AVAILABLE
    )
    content = next(
        snapshot
        for snapshot in snapshots.values()
        if snapshot.capture_token == available.capture_token
        and snapshot.role is registry_module._ConstraintRole.CONTENT
    )

    if mutation == "manifest-set":
        snapshots.pop(available.source_id)
    elif mutation == "duplicate-role":
        source_id = "synthetic-duplicate-available"
        original = next(
            artifact for artifact in supports if artifact.manifest.source_id == available.source_id
        )
        supports.append(
            replace(
                original,
                manifest=original.manifest.model_copy(update={"source_id": source_id}),
            )
        )
        snapshots[source_id] = replace(available, source_id=source_id)
    elif mutation == "missing-role":
        snapshots.pop(content.source_id)
        supports = [
            artifact for artifact in supports if artifact.manifest.source_id != content.source_id
        ]
    elif mutation == "inventory":
        snapshots[content.source_id] = replace(
            content,
            editions=frozenset((*tuple(content.editions)[:-1], "190001")),
        )
    elif mutation == "future-valid-from":
        available_manifest = next(
            artifact.manifest
            for artifact in supports
            if artifact.manifest.source_id == available.source_id
        )
        snapshots[content.source_id] = replace(
            content,
            valid_from=available_manifest.retrieved_at + timedelta(seconds=1),
        )
    elif mutation == "ledger-capture":
        ledger = ledgers[0].ledger.model_copy(
            update={"complete_through": datetime(2030, 1, 1, tzinfo=UTC)}
        )
        ledgers[0] = replace(ledgers[0], ledger=ledger)
    elif mutation == "ledger-inventory":
        reduced = frozenset(tuple(available.editions)[:-1])
        snapshots[available.source_id] = replace(available, editions=reduced)
        snapshots[content.source_id] = replace(content, editions=reduced)
    else:
        token = "20270101t000001000000z"
        retrieved_at = datetime(2027, 1, 1, tzinfo=UTC)
        for original_snapshot, suffix, offset in (
            (available, "available", timedelta(0)),
            (content, "content", timedelta(seconds=1)),
        ):
            source_id = f"synthetic-{suffix}-constraint"
            original = next(
                artifact
                for artifact in supports
                if artifact.manifest.source_id == original_snapshot.source_id
            )
            supports.append(
                replace(
                    original,
                    manifest=original.manifest.model_copy(
                        update={
                            "source_id": source_id,
                            "retrieved_at": retrieved_at + offset,
                        }
                    ),
                )
            )
            snapshots[source_id] = replace(
                original_snapshot,
                capture_token=token,
                source_id=source_id,
            )

    with pytest.raises(ValueError, match=message):
        registry_module._validate_constraint_ledger_join(
            snapshots,
            supports,
            ledgers,
        )


def test_constraint_evidence_must_join_one_exact_capture(
    small_registry: StesRegistry,
) -> None:
    state, _, snapshots, manifests = _constraint_context(small_registry)
    resolved = next(
        record for record in state.ledger_artifacts[0].ledger.editions if record.edition == "202607"
    )
    valid_from, first_observed = resolved.evidence
    assert valid_from.basis is AvailabilityEvidenceBasis.SDMX_CONSTRAINT_VALID_FROM
    assert first_observed.basis is AvailabilityEvidenceBasis.FIRST_OBSERVED_AT

    def validate(
        evidence: object,
        *,
        edition: str = resolved.edition,
        source_manifest_ids: tuple[str, ...] | None = None,
        basis: object | None = None,
        asserted_instant: datetime | None = None,
        constraint_id: str | None | object = _UNSET,
        constraint_version: str | None | object = _UNSET,
    ) -> None:
        registry_module._validate_constraint_evidence(
            edition,
            evidence.basis if basis is None else basis,
            evidence.asserted_instant if asserted_instant is None else asserted_instant,
            (evidence.source_manifest_ids if source_manifest_ids is None else source_manifest_ids),
            evidence.constraint_id if constraint_id is _UNSET else constraint_id,
            evidence.constraint_version if constraint_version is _UNSET else constraint_version,
            snapshots,
            manifests,
        )

    validate(valid_from)
    validate(first_observed)

    with pytest.raises(ValueError, match="unknown support source"):
        validate(first_observed, source_manifest_ids=("missing-support",))

    first_capture = snapshots[first_observed.source_manifest_ids[0]].capture_token
    other_content = next(
        snapshot
        for snapshot in snapshots.values()
        if snapshot.role is registry_module._ConstraintRole.CONTENT
        and snapshot.capture_token != first_capture
    )
    with pytest.raises(ValueError, match="crosses constraint captures"):
        validate(
            valid_from,
            source_manifest_ids=(
                first_observed.source_manifest_ids[0],
                other_content.source_id,
            ),
        )

    with pytest.raises(ValueError, match="requires one exact constraint pair"):
        validate(valid_from, source_manifest_ids=first_observed.source_manifest_ids)
    for field, value in (
        ("asserted_instant", valid_from.asserted_instant + timedelta(microseconds=1)),
        ("constraint_id", "wrong-constraint"),
        ("constraint_version", "5.0"),
    ):
        arguments = {field: value}
        with pytest.raises(ValueError, match="differs from its content constraint"):
            validate(valid_from, **arguments)

    with pytest.raises(ValueError, match="requires one availability constraint"):
        validate(first_observed, source_manifest_ids=valid_from.source_manifest_ids)
    with pytest.raises(ValueError, match="differs from its capture instant"):
        validate(
            first_observed,
            asserted_instant=first_observed.asserted_instant + timedelta(microseconds=1),
        )
    with pytest.raises(ValueError, match="unsupported evidence basis"):
        validate(first_observed, basis=object())
    with pytest.raises(ValueError, match="omits its asserted edition"):
        validate(first_observed, edition="190001")


@pytest.mark.parametrize(
    "mutation",
    (
        "source-id",
        "source-kind",
        "publisher",
        "family",
        "media",
        "vintage",
        "redistribution",
        "missing-reference",
        "inactive-catalog",
        "decision",
        "source-system",
        "table",
        "item",
        "flow",
    ),
)
def test_data_manifest_must_match_scope_rights_and_active_ledger(
    small_registry: StesRegistry,
    mutation: str,
) -> None:
    artifact = small_registry.entries[0].data_artifact
    assert artifact is not None
    manifest = artifact.manifest
    reference = manifest.rights_decision
    assert reference is not None
    active_ledger = small_registry.validated_state().active_ledger
    active_catalogs = {"kor-rtd-rights-2026-07-17"}

    if mutation == "source-id":
        manifest = manifest.model_copy(update={"source_id": "other-cli-source"})
    elif mutation == "source-kind":
        manifest = manifest.model_copy(update={"source_kind": SourceKind.DATASET})
    elif mutation == "publisher":
        manifest = manifest.model_copy(update={"publisher": "Other Publisher"})
    elif mutation == "family":
        manifest = manifest.model_copy(update={"document_family": "other-family"})
    elif mutation == "media":
        manifest = manifest.model_copy(update={"media_type": "application/json"})
    elif mutation == "vintage":
        manifest = manifest.model_copy(update={"vintage_semantics": VintageSemantics.LATEST_ONLY})
    elif mutation == "redistribution":
        manifest = manifest.model_copy(
            update={
                "redistribution": manifest.redistribution.model_copy(
                    update={"status": RedistributionStatus.METADATA_ONLY}
                )
            }
        )
    elif mutation == "missing-reference":
        manifest = manifest.model_copy(update={"rights_decision": None})
    elif mutation == "inactive-catalog":
        active_catalogs = set()
    elif mutation == "decision":
        manifest = manifest.model_copy(
            update={
                "rights_decision": reference.model_copy(update={"decision_id": "wrong-decision"})
            }
        )
    elif mutation == "source-system":
        manifest = manifest.model_copy(
            update={
                "rights_decision": reference.model_copy(
                    update={"source_system": SourceSystem.KOSIS}
                )
            }
        )
    elif mutation == "table":
        manifest = manifest.model_copy(
            update={"rights_decision": reference.model_copy(update={"table_id": "OTHER_TABLE"})}
        )
    elif mutation == "item":
        manifest = manifest.model_copy(
            update={
                "rights_decision": reference.model_copy(update={"item_id": "KOR.M.OTHER.IX._T"})
            }
        )
    else:
        manifest = manifest.model_copy(
            update={
                "canonical_url": (
                    "https://sdmx.oecd.org/public/rest/data/"
                    "OECD.SDD.STES,DSD_STES_REVISIONS%40DF_STES_REVISIONS,5.0/"
                    "KOR.M.LI_AA...?format=csvfilewithlabels"
                )
            }
        )

    with pytest.raises(ValueError, match="data manifest"):
        registry_module._validate_data_manifest(
            manifest,
            CLI_STES_BINDING,
            active_ledger,
            active_catalogs,
        )


def test_unavailable_gdp_scope_cannot_gain_active_allowed_rights(
    small_registry: StesRegistry,
) -> None:
    state = small_registry.validated_state()
    active = next(
        artifact
        for artifact in state.catalog_artifacts
        if artifact.catalog.catalog_id == "kor-rtd-rights-2026-07-17"
    )
    cli_decision = next(
        decision
        for decision in active.catalog.decisions
        if decision.decision_id == CLI_STES_BINDING.rights_decision_id
    )
    gdp_decision = cli_decision.model_copy(
        update={
            "decision_id": "oecd-stes-revisions-kor-q-b1gq-q-rights-test",
            "item_id": GDP_STES_BINDING.item_id,
            "item_title": "Synthetic GDP test decision",
            "frequency": "Q",
            "unit": "XDC",
        }
    )
    changed_catalog = active.catalog.model_copy(
        update={"decisions": (*active.catalog.decisions, gdp_decision)}
    )
    changed = registry_module._ValidatedCatalogArtifact(
        catalog=changed_catalog,
        catalog_bytes=b"synthetic",
    )

    with pytest.raises(ValueError, match="unavailable policy"):
        registry_module._validate_unavailable_rights_policy(
            state.entries,
            [changed],
            {changed_catalog.catalog_id},
        )


@pytest.mark.parametrize(
    ("payload", "message"),
    (
        (b"\xff", "valid bounded CSV"),
        (b"", "valid bounded CSV"),
        (b"\xef\xbb\xbf\n", "invalid columns"),
        (_csv_bytes(headers=(*_CSV_HEADERS, "MEASURE")), "invalid columns"),
        (
            _csv_bytes(headers=tuple(header for header in _CSV_HEADERS if header != "OBS_VALUE")),
            "invalid columns",
        ),
        (
            _csv_bytes(rows=(("KOR", "M"),)),
            "bounded row shape",
        ),
        (
            _csv_bytes(rows=(("USA", "M", "LI_AA", "IX", "_T", "202607", "2026-05", "1"),)),
            "neighboring series",
        ),
        (
            _csv_bytes(rows=(("KOR", "M", "LI_AA", "IX", "_T", "202613", "2026-05", "1"),)),
            "edition or period",
        ),
        (
            _csv_bytes(rows=(("KOR", "M", "LI_AA", "IX", "_T", "202607", "2026-Q1", "1"),)),
            "edition or period",
        ),
        (_csv_bytes(rows=((), (" ",))), "no observations"),
    ),
)
def test_archive_scope_parser_rejects_malformed_or_neighboring_content(
    payload: bytes,
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        registry_module._validate_archive_scope(payload, CLI_STES_BINDING)


def test_archive_scope_parser_bounds_columns_and_rows(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(registry_module, "MAX_STES_ARCHIVE_COLUMNS", len(_CSV_HEADERS) - 1)
    with pytest.raises(ValueError, match="invalid columns"):
        registry_module._validate_archive_scope(_csv_bytes(), CLI_STES_BINDING)

    monkeypatch.setattr(registry_module, "MAX_STES_ARCHIVE_COLUMNS", MAX_STES_ARCHIVE_COLUMNS)
    monkeypatch.setattr(registry_module, "MAX_STES_ARCHIVE_ROWS", 1)
    with pytest.raises(ValueError, match="bounded row shape"):
        registry_module._validate_archive_scope(_csv_bytes(), CLI_STES_BINDING)


def test_archive_scope_parser_handles_blank_rows_and_iteration_errors() -> None:
    payload = _csv_bytes(rows=((), (" ",), _CLI_ROW))
    summary = registry_module._validate_archive_scope(payload, CLI_STES_BINDING)
    assert summary.row_count == 1
    assert summary.edition_count == 1
    assert summary.first_edition == summary.last_edition == "202607"

    header = ",".join(_CSV_HEADERS).encode("utf-8")
    with pytest.raises(ValueError, match="valid bounded CSV"):
        registry_module._validate_archive_scope(
            b"\xef\xbb\xbf" + header + b'\n"unterminated',
            CLI_STES_BINDING,
        )


def test_archive_scope_rejects_duplicate_observation_keys() -> None:
    with pytest.raises(ValueError, match="repeats an edition-period observation"):
        registry_module._validate_archive_scope(
            _csv_bytes(rows=(_CLI_ROW, _CLI_ROW)),
            CLI_STES_BINDING,
        )


@pytest.mark.parametrize(
    "raw_value",
    (
        "",
        " ",
        " 1",
        "1 ",
        "1e3",
        "1,000",
        ".5",
        "1.",
        "NaN",
        "Infinity",
        "1" * 129,
    ),
)
def test_archive_scope_rejects_blank_or_nonplain_observation_values(
    raw_value: str,
) -> None:
    row = (*_CLI_ROW[:-1], raw_value)
    with pytest.raises(ValueError, match="invalid observation value"):
        registry_module._validate_archive_scope(
            _csv_bytes(rows=(row,)),
            CLI_STES_BINDING,
        )


@pytest.mark.parametrize("raw_value", ("0", "+1", "-1.25", "102.6600"))
def test_archive_scope_accepts_exact_plain_decimal_lexemes(raw_value: str) -> None:
    row = (*_CLI_ROW[:-1], raw_value)
    summary = registry_module._validate_archive_scope(
        _csv_bytes(rows=(row,)),
        CLI_STES_BINDING,
    )
    assert summary.observation_keys == frozenset({("202607", "2026-05")})


def test_archive_editions_must_join_active_ledger(
    small_registry: StesRegistry,
) -> None:
    state = small_registry.validated_state()
    summary = registry_module._validate_archive_scope(
        _csv_bytes(),
        CLI_STES_BINDING,
    )
    registry_module._validate_archive_ledger_join(summary, state.active_ledger)

    for changed in (
        replace(
            summary,
            editions=summary.editions | {"190001"},
        ),
        replace(
            summary,
            last_edition="202606",
        ),
    ):
        with pytest.raises(ValueError, match="active ledger edition scope"):
            registry_module._validate_archive_ledger_join(changed, state.active_ledger)


@pytest.mark.parametrize(
    "payload",
    (
        b"\xff",
        b"[]",
        b"{}",
        b'{"schema_version":"2.0.0","schema_version":"2.0.0"}',
        b'{"value":NaN}',
        b"{",
        b"[" * 1_100 + b"]" * 1_100,
    ),
    ids=(
        "invalid-utf8",
        "nonobject",
        "invalid-model",
        "duplicate-key",
        "nonfinite-constant",
        "invalid-json",
        "recursive-json",
    ),
)
def test_json_parser_rejects_untrusted_documents(payload: bytes) -> None:
    with pytest.raises(ValueError, match="trusted STES JSON is invalid"):
        registry_module._parse_json_model(payload, SourceManifest)


@pytest.mark.parametrize("role", ("manifest", "ledger", "catalog"))
def test_exact_json_artifacts_reject_bytes_subclasses_and_model_drift(
    small_registry: StesRegistry,
    role: str,
) -> None:
    if role == "manifest":
        artifact = small_registry.entries[0].data_artifact
        assert artifact is not None
        deceptive = replace(
            artifact,
            manifest_bytes=_BytesSubclass(artifact.manifest_bytes),
        )
        with pytest.raises(ValueError, match="exact immutable bytes"):
            deceptive.validated()
        changed = replace(
            artifact,
            manifest=artifact.manifest.model_copy(update={"title": "Changed title"}),
        )
        with pytest.raises(ValueError, match="model differs"):
            changed.validated()
    elif role == "ledger":
        artifact = small_registry.ledger_artifacts[0]
        deceptive = replace(
            artifact,
            ledger_bytes=_BytesSubclass(artifact.ledger_bytes),
        )
        with pytest.raises(ValueError, match="exact immutable bytes"):
            deceptive.validated()
        changed = replace(
            artifact,
            ledger=artifact.ledger.model_copy(
                update={"generated_at": artifact.ledger.generated_at}
            ),
        )
        object.__setattr__(changed, "ledger", changed.ledger.model_copy(update={"ledger_id": "x"}))
        with pytest.raises(ValueError, match="model differs"):
            changed.validated()
    else:
        artifact = small_registry.catalog_artifacts[0]
        deceptive = replace(
            artifact,
            catalog_bytes=_BytesSubclass(artifact.catalog_bytes),
        )
        with pytest.raises(ValueError, match="exact immutable bytes"):
            deceptive.validated()
        changed = replace(
            artifact,
            catalog=artifact.catalog.model_copy(update={"catalog_id": "changed-catalog"}),
        )
        with pytest.raises(ValueError, match="model differs"):
            changed.validated()


def test_source_artifact_rejects_unknown_role_and_archive_drift(
    small_registry: StesRegistry,
) -> None:
    artifact = small_registry.entries[0].data_artifact
    assert artifact is not None
    unknown = replace(artifact)
    object.__setattr__(unknown, "role", object())
    with pytest.raises(ValueError, match="unknown trusted role"):
        unknown.validated()

    for payload in (artifact.archive_bytes[:-1], b"X" + artifact.archive_bytes[1:]):
        changed = replace(artifact, archive_bytes=payload)
        with pytest.raises(ValueError, match="archive bytes differ"):
            changed.validated()

    deceptive = replace(
        artifact,
        archive_bytes=_BytesSubclass(artifact.archive_bytes),
    )
    with pytest.raises(ValueError, match="exact immutable bytes"):
        deceptive.validated()


@pytest.mark.parametrize(
    ("artifact_kind", "bound_name"),
    (
        ("data", "MAX_STES_DATA_ARCHIVE_BYTES"),
        ("support", "MAX_STES_SUPPORT_ARCHIVE_BYTES"),
        ("manifest", "MAX_STES_METADATA_BYTES"),
        ("ledger", "MAX_STES_METADATA_BYTES"),
        ("catalog", "MAX_STES_METADATA_BYTES"),
    ),
)
def test_artifact_resource_bounds_are_enforced_without_large_allocations(
    small_registry: StesRegistry,
    monkeypatch: pytest.MonkeyPatch,
    artifact_kind: str,
    bound_name: str,
) -> None:
    monkeypatch.setattr(registry_module, bound_name, 1)
    if artifact_kind == "data":
        artifact = small_registry.entries[0].data_artifact
        assert artifact is not None
        with pytest.raises(ValueError, match="bounded size"):
            artifact.validated()
    elif artifact_kind == "support":
        with pytest.raises(ValueError, match="bounded size"):
            small_registry.support_artifacts[0].validated()
    elif artifact_kind == "manifest":
        artifact = small_registry.entries[0].data_artifact
        assert artifact is not None
        with pytest.raises(ValueError, match="bounded size"):
            artifact.validated()
    elif artifact_kind == "ledger":
        with pytest.raises(ValueError, match="bounded size"):
            small_registry.ledger_artifacts[0].validated()
    else:
        with pytest.raises(ValueError, match="bounded size"):
            small_registry.catalog_artifacts[0].validated()


def test_ledger_edition_bound_is_enforced(
    small_registry: StesRegistry,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(registry_module, "MAX_STES_LEDGER_EDITIONS", 1)
    with pytest.raises(ValueError, match="edition bound"):
        small_registry.ledger_artifacts[0].validated()


def test_ledger_chain_requires_exact_dataflow_timezone_and_one_active_ledger(
    small_registry: StesRegistry,
) -> None:
    state = small_registry.validated_state()
    artifacts = {artifact.ledger.ledger_id: artifact for artifact in state.ledger_artifacts}
    assert (
        registry_module._validate_ledger_chain(
            artifacts,
            active_ledger_id=COMMITTED_ACTIVE_STES_LEDGER_ID,
        ).ledger_id
        == COMMITTED_ACTIVE_STES_LEDGER_ID
    )
    with pytest.raises(ValueError, match="no availability ledger"):
        registry_module._validate_ledger_chain({}, active_ledger_id="missing")

    active = artifacts[COMMITTED_ACTIVE_STES_LEDGER_ID]
    for field, value in (
        ("dataflow_id", "OTHER:FLOW"),
        ("dataflow_version", "5.0"),
        ("cutoff_timezone", "UTC"),
        ("cutoff_semantics", "other"),
    ):
        ledger = active.ledger.model_copy(update={field: value})
        changed = registry_module._ValidatedLedgerArtifact(ledger=ledger, ledger_bytes=b"{}")
        changed_artifacts = {**artifacts, ledger.ledger_id: changed}
        with pytest.raises(ValueError, match="cutoff/dataflow"):
            registry_module._validate_ledger_chain(
                changed_artifacts,
                active_ledger_id=COMMITTED_ACTIVE_STES_LEDGER_ID,
            )

    missing_predecessor_ledger = active.ledger.model_copy(
        update={"supersedes_ledger_id": "missing-ledger"}
    )
    missing_predecessor = registry_module._ValidatedLedgerArtifact(
        ledger=missing_predecessor_ledger,
        ledger_bytes=b"{}",
    )
    with pytest.raises(ValueError, match="missing predecessor"):
        registry_module._validate_ledger_chain(
            {missing_predecessor_ledger.ledger_id: missing_predecessor},
            active_ledger_id=missing_predecessor_ledger.ledger_id,
        )

    with pytest.raises(ValueError, match="missing predecessor"):
        registry_module._validate_ledger_chain(
            artifacts,
            active_ledger_id="wrong-active-ledger",
        )

    detached_active = registry_module._ValidatedLedgerArtifact(
        ledger=active.ledger.model_copy(update={"supersedes_ledger_id": None}),
        ledger_bytes=b"{}",
    )
    with pytest.raises(ValueError, match="connected active ledger chain"):
        registry_module._validate_ledger_chain(
            {
                **artifacts,
                detached_active.ledger.ledger_id: detached_active,
            },
            active_ledger_id=detached_active.ledger.ledger_id,
        )


def test_ledger_chain_rejects_cycles(
    small_registry: StesRegistry,
) -> None:
    state = small_registry.validated_state()
    predecessor = state.ledger_artifacts[0].ledger
    active = state.ledger_artifacts[1].ledger
    cyclic_predecessor = predecessor.model_copy(
        update={
            "supersedes_ledger_id": active.ledger_id,
            "generated_at": active.generated_at,
            "captured_at": active.captured_at,
            "complete_through": active.complete_through,
            "editions": active.editions,
        }
    )
    artifacts = {
        active.ledger_id: registry_module._ValidatedLedgerArtifact(
            ledger=active,
            ledger_bytes=b"{}",
        ),
        cyclic_predecessor.ledger_id: registry_module._ValidatedLedgerArtifact(
            ledger=cyclic_predecessor,
            ledger_bytes=b"{}",
        ),
    }

    with pytest.raises(ValueError, match="contains a cycle"):
        registry_module._validate_ledger_chain(
            artifacts,
            active_ledger_id=active.ledger_id,
        )


@pytest.mark.parametrize(
    "field",
    (
        "dataflow_id",
        "dataflow_version",
        "cutoff_timezone",
        "cutoff_semantics",
        "generated_at",
        "captured_at",
        "complete_through",
    ),
)
def test_ledger_successor_preserves_contract_and_monotonic_time(
    small_registry: StesRegistry,
    field: str,
) -> None:
    state = small_registry.validated_state()
    predecessor = state.ledger_artifacts[0].ledger
    successor = state.ledger_artifacts[1].ledger
    if field in {"generated_at", "captured_at", "complete_through"}:
        replacement = getattr(successor, field) + timedelta(microseconds=1)
    else:
        replacement = f"wrong-{field}"
    changed_predecessor = predecessor.model_copy(update={field: replacement})

    with pytest.raises(ValueError, match="rewrites its predecessor contract"):
        registry_module._validate_ledger_successor(changed_predecessor, successor)


def test_ledger_successor_preserves_every_predecessor_record(
    small_registry: StesRegistry,
) -> None:
    state = small_registry.validated_state()
    predecessor = state.ledger_artifacts[0].ledger
    successor = state.ledger_artifacts[1].ledger
    missing = successor.model_copy(update={"editions": successor.editions[1:]})
    changed_record = successor.editions[0].model_copy(update={"edition": "190001"})
    changed = successor.model_copy(update={"editions": (changed_record, *successor.editions[1:])})

    for corrupt in (missing, changed):
        with pytest.raises(ValueError, match="preserve every predecessor edition"):
            registry_module._validate_ledger_successor(predecessor, corrupt)


def test_catalog_chain_requires_predecessors_and_one_active_catalog(
    small_registry: StesRegistry,
) -> None:
    state = small_registry.validated_state()
    artifacts = {artifact.catalog.catalog_id: artifact for artifact in state.catalog_artifacts}
    registry_module._validate_catalog_chain(artifacts)
    with pytest.raises(ValueError, match="no rights catalog"):
        registry_module._validate_catalog_chain({})

    active = next(
        artifact
        for artifact in state.catalog_artifacts
        if artifact.catalog.supersedes_catalog_id is not None
    )
    missing_model = active.catalog.model_copy(update={"supersedes_catalog_id": "missing-catalog"})
    missing = registry_module._ValidatedCatalogArtifact(
        catalog=missing_model,
        catalog_bytes=b"{}",
    )
    with pytest.raises(ValueError, match="missing predecessor"):
        registry_module._validate_catalog_chain({missing_model.catalog_id: missing})

    first = state.catalog_artifacts[0]
    with pytest.raises(ValueError, match="one active rights catalog"):
        registry_module._validate_catalog_chain(
            {
                first.catalog.catalog_id: first,
                active.catalog.catalog_id: registry_module._ValidatedCatalogArtifact(
                    catalog=active.catalog.model_copy(update={"supersedes_catalog_id": None}),
                    catalog_bytes=b"{}",
                ),
            }
        )


def test_catalog_chain_rejects_cycles_and_disconnected_components(
    small_registry: StesRegistry,
) -> None:
    state = small_registry.validated_state()
    predecessor = state.catalog_artifacts[0].catalog
    active = state.catalog_artifacts[1].catalog
    cycle_tail_id = "synthetic-catalog-cycle-tail"
    cyclic_predecessor = predecessor.model_copy(
        update={
            "supersedes_catalog_id": cycle_tail_id,
            "recorded_at": active.recorded_at,
            "project_use_profile": active.project_use_profile,
            "instruments": active.instruments,
            "decisions": active.decisions,
        }
    )
    cycle_tail = predecessor.model_copy(
        update={
            "catalog_id": cycle_tail_id,
            "supersedes_catalog_id": cyclic_predecessor.catalog_id,
            "recorded_at": active.recorded_at,
            "project_use_profile": active.project_use_profile,
            "instruments": active.instruments,
            "decisions": active.decisions,
        }
    )
    cyclic = {
        active.catalog_id: registry_module._ValidatedCatalogArtifact(
            catalog=active,
            catalog_bytes=b"{}",
        ),
        cyclic_predecessor.catalog_id: registry_module._ValidatedCatalogArtifact(
            catalog=cyclic_predecessor,
            catalog_bytes=b"{}",
        ),
        cycle_tail.catalog_id: registry_module._ValidatedCatalogArtifact(
            catalog=cycle_tail,
            catalog_bytes=b"{}",
        ),
    }
    with pytest.raises(ValueError, match="contains a cycle"):
        registry_module._validate_catalog_chain(cyclic)

    extra = predecessor.model_copy(
        update={
            "catalog_id": "synthetic-disconnected-catalog",
            "supersedes_catalog_id": "synthetic-disconnected-catalog",
        }
    )
    disconnected = {artifact.catalog.catalog_id: artifact for artifact in state.catalog_artifacts}
    disconnected[extra.catalog_id] = registry_module._ValidatedCatalogArtifact(
        catalog=extra,
        catalog_bytes=b"{}",
    )
    with pytest.raises(ValueError, match="connected rights catalog chain"):
        registry_module._validate_catalog_chain(disconnected)


def test_catalog_successor_is_monotonic_and_append_only(
    small_registry: StesRegistry,
) -> None:
    state = small_registry.validated_state()
    predecessor = state.catalog_artifacts[0].catalog
    successor = state.catalog_artifacts[1].catalog
    for changed_predecessor in (
        predecessor.model_copy(
            update={"recorded_at": successor.recorded_at + timedelta(microseconds=1)}
        ),
        predecessor.model_copy(update={"project_use_profile": object()}),
    ):
        with pytest.raises(ValueError, match="rewrites its predecessor contract"):
            registry_module._validate_catalog_successor(changed_predecessor, successor)

    missing_instrument = successor.model_copy(update={"instruments": successor.instruments[1:]})
    changed_decision = successor.decisions[0].model_copy(
        update={"decision_id": "synthetic-changed-decision"}
    )
    missing_decision = successor.model_copy(
        update={"decisions": (changed_decision, *successor.decisions[1:])}
    )
    for corrupt in (missing_instrument, missing_decision):
        with pytest.raises(ValueError, match="must be append-only"):
            registry_module._validate_catalog_successor(predecessor, corrupt)


def test_loader_reads_small_exact_tree_deterministically(
    tmp_path: Path,
    small_registry: StesRegistry,
) -> None:
    _write_registry_tree(tmp_path, small_registry)

    first = _load_tree(tmp_path)
    second = _load_tree(tmp_path)

    assert first.canonical_descriptor_bytes() == second.canonical_descriptor_bytes()
    assert first.descriptor_sha256 == second.descriptor_sha256


def test_loader_sanitizes_missing_repository_and_artifact_roots(tmp_path: Path) -> None:
    missing_root = tmp_path / "private-missing-root"
    with pytest.raises(
        StesRegistryLoadError,
        match="repository root could not be resolved",
    ) as root_error:
        _load_tree(missing_root)
    assert str(missing_root) not in str(root_error.value)

    with pytest.raises(
        StesRegistryLoadError,
        match="artifact root could not be resolved",
    ) as artifact_error:
        _load_tree(tmp_path)
    assert str(tmp_path) not in str(artifact_error.value)


def test_loader_requires_tuple_locations() -> None:
    with pytest.raises(ValueError, match="artifact locations must be a tuple"):
        load_stes_registry(
            REPOSITORY_ROOT,
            registry_id="invalid-locations",
            artifact_locations=list(COMMITTED_STES_ARTIFACT_LOCATIONS),  # type: ignore[arg-type]
            ledger_paths=COMMITTED_STES_LEDGER_PATHS,
            catalog_paths=COMMITTED_STES_CATALOG_PATHS,
            active_ledger_id=COMMITTED_ACTIVE_STES_LEDGER_ID,
            complete_through_source_id=COMMITTED_COMPLETE_THROUGH_SOURCE_ID,
            captured_at_source_id=COMMITTED_CAPTURED_AT_SOURCE_ID,
        )
    for field in ("ledger_paths", "catalog_paths"):
        arguments = {
            "registry_id": "invalid-metadata-locations",
            "artifact_locations": COMMITTED_STES_ARTIFACT_LOCATIONS,
            "ledger_paths": COMMITTED_STES_LEDGER_PATHS,
            "catalog_paths": COMMITTED_STES_CATALOG_PATHS,
            "active_ledger_id": COMMITTED_ACTIVE_STES_LEDGER_ID,
            "complete_through_source_id": COMMITTED_COMPLETE_THROUGH_SOURCE_ID,
            "captured_at_source_id": COMMITTED_CAPTURED_AT_SOURCE_ID,
        }
        arguments[field] = list(arguments[field])
        with pytest.raises(ValueError, match="metadata locations must be tuples"):
            load_stes_registry(REPOSITORY_ROOT, **arguments)  # type: ignore[arg-type]


def test_loader_rejects_duplicate_role_files() -> None:
    location = COMMITTED_STES_ARTIFACT_LOCATIONS[0]
    duplicate = replace(location, archive_path=location.manifest_path)
    with pytest.raises(ValueError, match="distinct files"):
        load_stes_registry(
            REPOSITORY_ROOT,
            registry_id="duplicate-files",
            artifact_locations=(duplicate,),
            ledger_paths=(),
            catalog_paths=(),
            active_ledger_id="missing",
            complete_through_source_id="missing",
            captured_at_source_id="missing",
        )


@pytest.mark.parametrize(
    "case",
    ("invalid-location", "invalid-path", "invalid-role", "support-binding"),
)
def test_loader_sanitizes_invalid_location_roles(
    tmp_path: Path,
    small_registry: StesRegistry,
    case: str,
) -> None:
    _write_registry_tree(tmp_path, small_registry)
    locations: tuple[Any, ...] = COMMITTED_STES_ARTIFACT_LOCATIONS
    if case == "invalid-location":
        locations = (object(), *locations[1:])
    elif case == "invalid-path":
        locations = (
            replace(locations[0], manifest_path="not-a-path"),  # type: ignore[arg-type]
            *locations[1:],
        )
    elif case == "invalid-role":
        locations = (
            replace(locations[0], role="invalid"),  # type: ignore[arg-type]
            *locations[1:],
        )
    else:
        locations = (
            locations[0],
            replace(locations[1], binding=CLI_STES_BINDING),
            *locations[2:],
        )

    with pytest.raises(StesRegistryLoadError, match="registry is invalid"):
        _load_tree(tmp_path, artifact_locations=locations)


def test_source_loader_and_registry_loop_reject_unknown_location_types_and_roles(
    tmp_path: Path,
    small_registry: StesRegistry,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _write_registry_tree(tmp_path, small_registry)
    with pytest.raises(ValueError, match="location has an invalid type"):
        registry_module._load_source_artifact(tmp_path.resolve(), object())

    invalid = replace(COMMITTED_STES_ARTIFACT_LOCATIONS[0])
    object.__setattr__(invalid, "role", object())
    data_artifact = small_registry.entries[0].data_artifact
    assert data_artifact is not None
    monkeypatch.setattr(
        registry_module,
        "_load_source_artifact",
        lambda root, location: data_artifact,
    )
    with pytest.raises(StesRegistryLoadError, match="registry is invalid"):
        _load_tree(tmp_path, artifact_locations=(invalid,))


@pytest.mark.parametrize("binding", (None, GDP_STES_BINDING))
def test_loader_rejects_invalid_data_location_bindings(
    tmp_path: Path,
    small_registry: StesRegistry,
    binding: StesSeriesBinding | None,
) -> None:
    _write_registry_tree(tmp_path, small_registry)
    locations = (
        replace(COMMITTED_STES_ARTIFACT_LOCATIONS[0], binding=binding),
        *COMMITTED_STES_ARTIFACT_LOCATIONS[1:],
    )
    with pytest.raises(StesRegistryLoadError, match="registry is invalid"):
        _load_tree(tmp_path, artifact_locations=locations)


def test_loader_rejects_duplicate_data_scope(
    tmp_path: Path,
    small_registry: StesRegistry,
) -> None:
    _write_registry_tree(tmp_path, small_registry)
    original = small_registry.entries[0].data_artifact
    assert original is not None
    duplicate_id = "oecd-stes-cli-kor-li-aa-duplicate"
    duplicate = _source_artifact_with(original, source_id=duplicate_id)
    manifest_path = Path(f"data/manifests/{duplicate_id}.json")
    archive_path = Path(f"data/archive/oecd-stes/{duplicate_id}.csv")
    (tmp_path / manifest_path).write_bytes(duplicate.manifest_bytes)
    (tmp_path / archive_path).write_bytes(duplicate.archive_bytes)
    locations = (
        *COMMITTED_STES_ARTIFACT_LOCATIONS,
        StesArtifactLocation(
            role=StesArtifactRole.DATA_ARCHIVE,
            binding=CLI_STES_BINDING,
            manifest_path=manifest_path,
            archive_path=archive_path,
        ),
    )

    with pytest.raises(StesRegistryLoadError, match="registry is invalid"):
        _load_tree(tmp_path, artifact_locations=locations)


@pytest.mark.parametrize("kind", ("manifest", "archive", "ledger", "catalog"))
def test_loader_rejects_absolute_escape_wrong_suffix_and_missing_files(
    tmp_path: Path,
    small_registry: StesRegistry,
    kind: str,
) -> None:
    _write_registry_tree(tmp_path, small_registry)
    if kind in {"manifest", "archive"}:
        location = COMMITTED_STES_ARTIFACT_LOCATIONS[0]
        field = "manifest_path" if kind == "manifest" else "archive_path"
        absolute = replace(location, **{field: (tmp_path / getattr(location, field)).resolve()})
        escaped = replace(location, **{field: Path("../../outside.json")})
        wrong_suffix = replace(location, **{field: Path(f"data/manifests/wrong.{kind}")})
        missing = replace(location, **{field: Path(f"data/manifests/missing-{kind}.json")})
        for changed in (absolute, escaped, wrong_suffix, missing):
            locations = (changed, *COMMITTED_STES_ARTIFACT_LOCATIONS[1:])
            with pytest.raises(StesRegistryLoadError):
                _load_tree(tmp_path, artifact_locations=locations)
    else:
        paths = COMMITTED_STES_LEDGER_PATHS if kind == "ledger" else COMMITTED_STES_CATALOG_PATHS
        absolute_path = (tmp_path / paths[0]).resolve()
        escaped_path = Path("../../outside.json")
        wrong_suffix_path = Path(
            "data/availability/wrong.txt" if kind == "ledger" else "data/rights/wrong.txt"
        )
        missing_path = Path(
            "data/availability/missing.json" if kind == "ledger" else "data/rights/missing.json"
        )
        field = "ledger_paths" if kind == "ledger" else "catalog_paths"
        for changed in (absolute_path, escaped_path, wrong_suffix_path, missing_path):
            with pytest.raises(StesRegistryLoadError):
                _load_tree(tmp_path, **{field: (changed, *paths[1:])})


def test_loader_requires_filenames_to_equal_embedded_ids(
    tmp_path: Path,
    small_registry: StesRegistry,
) -> None:
    _write_registry_tree(tmp_path, small_registry)
    data_location = COMMITTED_STES_ARTIFACT_LOCATIONS[0]
    wrong_manifest = Path("data/manifests/wrong-source-id.json")
    (tmp_path / wrong_manifest).write_bytes((tmp_path / data_location.manifest_path).read_bytes())
    wrong_archive = Path("data/archive/oecd-stes/wrong-source-id.csv")
    (tmp_path / wrong_archive).write_bytes((tmp_path / data_location.archive_path).read_bytes())

    for location in (
        replace(data_location, manifest_path=wrong_manifest),
        replace(data_location, archive_path=wrong_archive),
    ):
        with pytest.raises(StesRegistryLoadError, match="registry is invalid"):
            _load_tree(
                tmp_path,
                artifact_locations=(location, *COMMITTED_STES_ARTIFACT_LOCATIONS[1:]),
            )

    wrong_ledger = Path("data/availability/wrong-ledger-id.json")
    (tmp_path / wrong_ledger).write_bytes((tmp_path / COMMITTED_STES_LEDGER_PATHS[0]).read_bytes())
    with pytest.raises(StesRegistryLoadError, match="registry is invalid"):
        _load_tree(
            tmp_path,
            ledger_paths=(wrong_ledger, COMMITTED_STES_LEDGER_PATHS[1]),
        )

    wrong_catalog = Path("data/rights/wrong-catalog-id.json")
    (tmp_path / wrong_catalog).write_bytes(
        (tmp_path / COMMITTED_STES_CATALOG_PATHS[0]).read_bytes()
    )
    with pytest.raises(StesRegistryLoadError, match="registry is invalid"):
        _load_tree(
            tmp_path,
            catalog_paths=(wrong_catalog, COMMITTED_STES_CATALOG_PATHS[1]),
        )


@pytest.mark.parametrize(
    "payload",
    (
        b"\xff",
        b"[]",
        b'{"schema_version":"2.0.0","schema_version":"2.0.0"}',
        b'{"value":NaN}',
        b"{",
    ),
)
def test_loader_sanitizes_invalid_manifest_json(
    tmp_path: Path,
    small_registry: StesRegistry,
    payload: bytes,
) -> None:
    _write_registry_tree(tmp_path, small_registry)
    path = tmp_path / COMMITTED_STES_ARTIFACT_LOCATIONS[0].manifest_path
    path.write_bytes(payload)

    with pytest.raises(StesRegistryLoadError, match="registry is invalid") as error:
        _load_tree(tmp_path)
    assert str(tmp_path) not in str(error.value)


def test_trusted_file_reader_sanitizes_stat_read_and_read_races(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = tmp_path.resolve()
    target = root / "data" / "manifests" / "test.json"
    target.parent.mkdir(parents=True)
    target.write_bytes(b"{}")
    original_is_file = Path.is_file
    original_stat = Path.stat
    original_read_bytes = Path.read_bytes

    def controlled_is_file(path: Path) -> bool:
        if path == target:
            return True
        return original_is_file(path)

    def fail_stat(path: Path, *args: object, **kwargs: object) -> Any:
        if path == target:
            raise OSError("private path")
        return original_stat(path, *args, **kwargs)

    monkeypatch.setattr(Path, "is_file", controlled_is_file)
    monkeypatch.setattr(Path, "stat", fail_stat)
    with pytest.raises(StesRegistryLoadError, match="could not be inspected"):
        registry_module._read_trusted_file(
            root,
            Path("data/manifests/test.json"),
            required_root=root / "data" / "manifests",
            suffix=".json",
            max_bytes=10,
            label="test",
        )

    monkeypatch.undo()

    def fail_read(path: Path) -> bytes:
        if path == target:
            raise OSError("private path")
        return original_read_bytes(path)

    monkeypatch.setattr(Path, "read_bytes", fail_read)
    with pytest.raises(StesRegistryLoadError, match="could not be read"):
        registry_module._read_trusted_file(
            root,
            Path("data/manifests/test.json"),
            required_root=root / "data" / "manifests",
            suffix=".json",
            max_bytes=10,
            label="test",
        )

    monkeypatch.undo()

    def changed_read(path: Path) -> bytes:
        payload = original_read_bytes(path)
        return payload + b"X" if path == target else payload

    monkeypatch.setattr(Path, "read_bytes", changed_read)
    with pytest.raises(ValueError, match="changed while"):
        registry_module._read_trusted_file(
            root,
            Path("data/manifests/test.json"),
            required_root=root / "data" / "manifests",
            suffix=".json",
            max_bytes=10,
            label="test",
        )


@pytest.mark.parametrize("size", (0, 3))
def test_trusted_file_reader_rejects_empty_and_oversized_files(
    tmp_path: Path,
    size: int,
) -> None:
    target = tmp_path / "data" / "manifests" / "test.json"
    target.parent.mkdir(parents=True)
    target.write_bytes(b"X" * size)
    with pytest.raises(ValueError, match="bounded size"):
        registry_module._read_trusted_file(
            tmp_path,
            Path("data/manifests/test.json"),
            required_root=tmp_path / "data" / "manifests",
            suffix=".json",
            max_bytes=2,
            label="test",
        )
