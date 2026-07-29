"""Trusted, digest-linked bindings for committed latest-only snapshots."""

import hashlib
import json
from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path

from sovereignlab.normalization import normalization_rule
from sovereignlab.schemas import (
    BenchmarkBundle,
    RedistributionStatus,
    RightsCatalog,
    SourceKind,
    SourceManifest,
    SourceSystem,
    VintageSemantics,
)

SNAPSHOT_REGISTRY_ID = "kor-rtd-latest-only-snapshot-registry-v1"
SNAPSHOT_REGISTRY_DESCRIPTOR_SHA256 = (
    "67ebecf0aa15b5a2d53aff737cd28bd8779e3993abebca9e6c3d840f2006aa5b"
)
MAX_SNAPSHOT_BYTES = 10_000_000


class SnapshotRegistryLoadError(ValueError):
    """Sanitized harness failure while loading an explicitly trusted artifact."""


@dataclass(frozen=True)
class SnapshotSeriesBinding:
    """Harness-owned provider selectors for one exact callable snapshot scope."""

    source_system: SourceSystem
    table_id: str
    item_id: str
    document_family: str
    rights_decision_id: str
    normalization_rule_id: str
    frequency: str
    raw_unit: str
    provider_item_id: str
    organisation_id: str | None = None
    geography_id: str | None = None

    @property
    def scope(self) -> tuple[SourceSystem, str, str]:
        """Return the exact model-visible scope key."""

        return (self.source_system, self.table_id, self.item_id)

    def descriptor(self) -> dict[str, str | None]:
        """Return the stable public-data-free binding descriptor."""

        return {
            "document_family": self.document_family,
            "frequency": self.frequency,
            "geography_id": self.geography_id,
            "item_id": self.item_id,
            "normalization_rule_id": self.normalization_rule_id,
            "organisation_id": self.organisation_id,
            "provider_item_id": self.provider_item_id,
            "raw_unit": self.raw_unit,
            "rights_decision_id": self.rights_decision_id,
            "source_system": self.source_system.value,
            "table_id": self.table_id,
        }


ECOS_GDP_BINDING = SnapshotSeriesBinding(
    source_system=SourceSystem.ECOS,
    table_id="200Y108",
    item_id="10601",
    document_family="ecos-200y108-10601",
    rights_decision_id="ecos-200y108-10601-rights-v1",
    normalization_rule_id="ecos-200y108-10601-billion-krw-v1",
    frequency="Q",
    raw_unit="십억원",
    provider_item_id="10601",
)
ECOS_CURRENT_ACCOUNT_BINDING = SnapshotSeriesBinding(
    source_system=SourceSystem.ECOS,
    table_id="301Y017",
    item_id="SA000",
    document_family="ecos-301y017-sa000",
    rights_decision_id="ecos-301y017-sa000-rights-v1",
    normalization_rule_id="ecos-301y017-sa000-million-usd-v1",
    frequency="M",
    raw_unit="백만달러",
    provider_item_id="SA000",
)
KOSIS_CPI_BINDING = SnapshotSeriesBinding(
    source_system=SourceSystem.KOSIS,
    table_id="DT_1J22003",
    item_id="T/T10",
    document_family="kosis-101-dt-1j22003-t-t10",
    rights_decision_id="kosis-101-dt-1j22003-t-t10-rights-v1",
    normalization_rule_id="kosis-101-dt-1j22003-t-t10-index-v1",
    frequency="M",
    raw_unit="2020＝100",  # noqa: RUF001 - provider-native fullwidth unit is exact.
    provider_item_id="T",
    organisation_id="101",
    geography_id="T10",
)
SNAPSHOT_SERIES_BINDINGS = (
    ECOS_GDP_BINDING,
    ECOS_CURRENT_ACCOUNT_BINDING,
    KOSIS_CPI_BINDING,
)
_APPROVED_BINDINGS_BY_SCOPE = {binding.scope: binding for binding in SNAPSHOT_SERIES_BINDINGS}


@dataclass(frozen=True)
class SnapshotArtifact:
    """One strict manifest plus the immutable bytes injected by the harness."""

    manifest: SourceManifest
    manifest_bytes: bytes = field(repr=False, compare=False)
    archive_bytes: bytes = field(repr=False, compare=False)

    def __post_init__(self) -> None:
        if not isinstance(self.manifest_bytes, bytes):
            raise ValueError("snapshot manifest bytes must be immutable bytes")
        if not isinstance(self.archive_bytes, bytes):
            raise ValueError("snapshot archive bytes must be immutable bytes")
        if SourceManifest.model_validate_json(self.manifest_bytes) != self.manifest:
            raise ValueError("snapshot manifest model differs from its exact JSON bytes")

    @property
    def manifest_sha256(self) -> str:
        """Hash the exact manifest bytes carried by this artifact."""

        return hashlib.sha256(self.manifest_bytes).hexdigest()

    def descriptor(self) -> dict[str, int | str]:
        """Return digest material without serializing paths or raw observations."""

        return {
            "archive_byte_size": len(self.archive_bytes),
            "archive_sha256": hashlib.sha256(self.archive_bytes).hexdigest(),
            "manifest_archive_byte_size": self.manifest.byte_size,
            "manifest_archive_sha256": self.manifest.content_sha256,
            "manifest_sha256": self.manifest_sha256,
            "source_id": self.manifest.source_id,
        }


@dataclass(frozen=True)
class SnapshotCatalogArtifact:
    """One strict rights catalog and the hash of its exact committed JSON bytes."""

    catalog: RightsCatalog
    catalog_bytes: bytes = field(repr=False, compare=False)

    def __post_init__(self) -> None:
        if not isinstance(self.catalog_bytes, bytes):
            raise ValueError("rights catalog bytes must be immutable bytes")
        if RightsCatalog.model_validate_json(self.catalog_bytes) != self.catalog:
            raise ValueError("rights catalog model differs from its exact JSON bytes")

    @property
    def content_sha256(self) -> str:
        """Hash the exact catalog bytes carried by this artifact."""

        return hashlib.sha256(self.catalog_bytes).hexdigest()

    def descriptor(self) -> dict[str, str]:
        """Return stable catalog digest material."""

        return {
            "catalog_id": self.catalog.catalog_id,
            "content_sha256": self.content_sha256,
        }


@dataclass(frozen=True)
class SnapshotRegistryEntry:
    """One approved scope and the explicitly registered captures for that scope."""

    binding: SnapshotSeriesBinding
    artifacts: tuple[SnapshotArtifact, ...] = ()


@dataclass(frozen=True)
class SnapshotRegistry:
    """Immutable trusted inputs for deterministic latest-only selection."""

    registry_id: str
    entries: tuple[SnapshotRegistryEntry, ...]
    catalog_artifacts: tuple[SnapshotCatalogArtifact, ...]

    def __post_init__(self) -> None:
        scopes = tuple(entry.binding.scope for entry in self.entries)
        if len(scopes) != len(set(scopes)):
            raise ValueError("snapshot registry scope bindings must be unique")
        if any(
            _APPROVED_BINDINGS_BY_SCOPE.get(entry.binding.scope) != entry.binding
            for entry in self.entries
        ):
            raise ValueError("snapshot registry contains a non-approved scope binding")

        source_ids = tuple(
            artifact.manifest.source_id for entry in self.entries for artifact in entry.artifacts
        )
        if len(source_ids) != len(set(source_ids)):
            raise ValueError("snapshot registry source IDs must be unique")

        catalog_ids = tuple(artifact.catalog.catalog_id for artifact in self.catalog_artifacts)
        if len(catalog_ids) != len(set(catalog_ids)):
            raise ValueError("snapshot registry catalog IDs must be unique")

    @property
    def rights_catalogs(self) -> tuple[RightsCatalog, ...]:
        """Return the strict catalogs injected into the registry."""

        return tuple(artifact.catalog for artifact in self.catalog_artifacts)

    def entry_for(
        self,
        source_system: SourceSystem,
        table_id: str,
        item_id: str,
    ) -> SnapshotRegistryEntry | None:
        """Look up an exact validated callable scope without inference."""

        scope = (source_system, table_id, item_id)
        return next(
            (entry for entry in self.entries if entry.binding.scope == scope),
            None,
        )

    def canonical_descriptor_bytes(self) -> bytes:
        """Serialize order-independent registry provenance for trace hashing."""

        entries = []
        for entry in sorted(
            self.entries,
            key=lambda item: (
                item.binding.source_system.value,
                item.binding.table_id,
                item.binding.item_id,
            ),
        ):
            entries.append(
                {
                    "artifacts": sorted(
                        (artifact.descriptor() for artifact in entry.artifacts),
                        key=lambda item: item["source_id"],
                    ),
                    "binding": entry.binding.descriptor(),
                }
            )
        descriptor = {
            "catalogs": sorted(
                (artifact.descriptor() for artifact in self.catalog_artifacts),
                key=lambda item: item["catalog_id"],
            ),
            "entries": entries,
            "registry_id": self.registry_id,
            "schema_version": "1.0.0",
        }
        return json.dumps(
            descriptor,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")

    @property
    def descriptor_sha256(self) -> str:
        """Hash the exact canonical registry descriptor."""

        return hashlib.sha256(self.canonical_descriptor_bytes()).hexdigest()


@dataclass(frozen=True)
class SnapshotArtifactLocation:
    """Harness-only relative locations for one explicitly admitted capture."""

    binding: SnapshotSeriesBinding
    manifest_path: Path
    archive_path: Path


COMMITTED_SNAPSHOT_LOCATIONS = (
    SnapshotArtifactLocation(
        binding=ECOS_GDP_BINDING,
        manifest_path=Path("data/manifests/ecos-200y108-10601-20260717t115242998550z.json"),
        archive_path=Path("data/archive/ecos/ecos-200y108-10601-20260717t115242998550z.json"),
    ),
    SnapshotArtifactLocation(
        binding=ECOS_CURRENT_ACCOUNT_BINDING,
        manifest_path=Path("data/manifests/ecos-301y017-sa000-20260717t115242998550z.json"),
        archive_path=Path("data/archive/ecos/ecos-301y017-sa000-20260717t115242998550z.json"),
    ),
    SnapshotArtifactLocation(
        binding=KOSIS_CPI_BINDING,
        manifest_path=Path("data/manifests/kosis-101-dt-1j22003-t-t10-20260717t115242998550z.json"),
        archive_path=Path(
            "data/archive/kosis/kosis-101-dt-1j22003-t-t10-20260717t115242998550z.json"
        ),
    ),
)
COMMITTED_RIGHTS_CATALOG_PATHS = (
    Path("data/rights/kor-rtd-rights-2026-07-16.json"),
    Path("data/rights/kor-rtd-rights-2026-07-17.json"),
)


def load_snapshot_registry(
    repository_root: Path,
    *,
    registry_id: str,
    artifact_locations: Sequence[SnapshotArtifactLocation],
    rights_catalog_paths: Sequence[Path],
) -> SnapshotRegistry:
    """Load an explicitly enumerated, repository-confined trusted registry."""

    try:
        root = repository_root.resolve(strict=True)
    except OSError:
        raise SnapshotRegistryLoadError(
            "the trusted repository root could not be resolved"
        ) from None
    catalog_artifacts = tuple(_load_catalog_artifact(root, path) for path in rights_catalog_paths)
    artifacts_by_scope: dict[
        tuple[SourceSystem, str, str],
        list[SnapshotArtifact],
    ] = {binding.scope: [] for binding in SNAPSHOT_SERIES_BINDINGS}

    for location in artifact_locations:
        approved = _APPROVED_BINDINGS_BY_SCOPE.get(location.binding.scope)
        if approved != location.binding:
            raise ValueError("snapshot artifact location uses a non-approved binding")
        artifact = _load_snapshot_artifact(root, location)
        artifacts_by_scope[location.binding.scope].append(artifact)

    registry = SnapshotRegistry(
        registry_id=registry_id,
        entries=tuple(
            SnapshotRegistryEntry(
                binding=binding,
                artifacts=tuple(artifacts_by_scope[binding.scope]),
            )
            for binding in SNAPSHOT_SERIES_BINDINGS
        ),
        catalog_artifacts=catalog_artifacts,
    )
    BenchmarkBundle(
        sources=tuple(
            artifact.manifest for entry in registry.entries for artifact in entry.artifacts
        ),
        records=(),
        rights_catalogs=registry.rights_catalogs,
    )
    return registry


def load_committed_snapshot_registry(repository_root: Path) -> SnapshotRegistry:
    """Load the exact three currently admitted snapshots for the offline baseline."""

    registry = load_snapshot_registry(
        repository_root,
        registry_id=SNAPSHOT_REGISTRY_ID,
        artifact_locations=COMMITTED_SNAPSHOT_LOCATIONS,
        rights_catalog_paths=COMMITTED_RIGHTS_CATALOG_PATHS,
    )
    if registry.descriptor_sha256 != SNAPSHOT_REGISTRY_DESCRIPTOR_SHA256:
        raise ValueError(
            "committed snapshot registry descriptor changed; preserve v1 and create a new version"
        )
    return registry


def _load_catalog_artifact(root: Path, relative_path: Path) -> SnapshotCatalogArtifact:
    path = _resolve_trusted_path(
        root,
        relative_path,
        required_root=root / "data" / "rights",
    )
    try:
        payload = path.read_bytes()
    except OSError:
        raise SnapshotRegistryLoadError("the trusted rights catalog could not be read") from None
    catalog = RightsCatalog.model_validate_json(payload)
    if path.stem != catalog.catalog_id:
        raise ValueError("rights catalog filename must equal its catalog ID")
    return SnapshotCatalogArtifact(
        catalog=catalog,
        catalog_bytes=payload,
    )


def _load_snapshot_artifact(
    root: Path,
    location: SnapshotArtifactLocation,
) -> SnapshotArtifact:
    manifest_path = _resolve_trusted_path(
        root,
        location.manifest_path,
        required_root=root / "data" / "manifests",
    )
    archive_path = _resolve_trusted_path(
        root,
        location.archive_path,
        required_root=root / "data" / "archive" / location.binding.source_system.value,
    )
    try:
        manifest_payload = manifest_path.read_bytes()
    except OSError:
        raise SnapshotRegistryLoadError("the trusted snapshot manifest could not be read") from None
    manifest = SourceManifest.model_validate_json(manifest_payload)
    _require_manifest_binding(manifest, location.binding)
    if (
        manifest_path.stem != manifest.source_id
        or archive_path.stem != manifest.source_id
        or manifest_path.suffix != ".json"
        or archive_path.suffix != ".json"
    ):
        raise ValueError("snapshot manifest/archive filenames must equal the source ID")
    if not archive_path.is_file():
        raise SnapshotRegistryLoadError("the trusted snapshot archive does not exist")
    try:
        archive_size = archive_path.stat().st_size
    except OSError:
        raise SnapshotRegistryLoadError(
            "the trusted snapshot archive could not be inspected"
        ) from None
    if manifest.byte_size > MAX_SNAPSHOT_BYTES or archive_size > MAX_SNAPSHOT_BYTES:
        raise ValueError("registered snapshot archive exceeds the bounded reader limit")
    if archive_size != manifest.byte_size:
        raise ValueError("registered snapshot archive does not match its manifest")
    try:
        archive_bytes = archive_path.read_bytes()
    except OSError:
        raise SnapshotRegistryLoadError("the trusted snapshot archive could not be read") from None
    if (
        len(archive_bytes) != manifest.byte_size
        or hashlib.sha256(archive_bytes).hexdigest() != manifest.content_sha256
    ):
        raise ValueError("registered snapshot archive does not match its manifest")
    return SnapshotArtifact(
        manifest=manifest,
        manifest_bytes=manifest_payload,
        archive_bytes=archive_bytes,
    )


def _resolve_trusted_path(
    root: Path,
    relative_path: Path,
    *,
    required_root: Path,
) -> Path:
    if relative_path.is_absolute():
        raise ValueError("trusted artifact locations must be repository-relative")
    try:
        path = (root / relative_path).resolve(strict=False)
        confined_root = required_root.resolve(strict=True)
    except OSError:
        raise SnapshotRegistryLoadError("the trusted artifact root could not be resolved") from None
    if not path.is_relative_to(confined_root):
        raise ValueError("trusted artifact location escapes its approved repository root")
    return path


def _require_manifest_binding(
    manifest: SourceManifest,
    binding: SnapshotSeriesBinding,
) -> None:
    reference = manifest.rights_decision
    rule = normalization_rule(
        binding.source_system,
        binding.table_id,
        binding.item_id,
    )
    if (
        manifest.source_kind is not SourceKind.API
        or manifest.vintage_semantics is not VintageSemantics.LATEST_ONLY
        or manifest.media_type != "application/json"
        or manifest.redistribution.status is not RedistributionStatus.ALLOWED
        or manifest.document_family != binding.document_family
        or not manifest.source_id.startswith(f"{binding.document_family}-")
        or reference is None
        or reference.source_system is not binding.source_system
        or reference.table_id != binding.table_id
        or reference.item_id != binding.item_id
        or reference.decision_id != binding.rights_decision_id
        or rule.rule_id != binding.normalization_rule_id
    ):
        raise ValueError("snapshot manifest differs from its trusted exact-scope binding")
