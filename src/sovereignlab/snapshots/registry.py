"""Explicit, digest-pinned registry of the committed latest-only ECOS/KOSIS snapshots."""

from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from sovereignlab.artifacts import (
    CatalogArtifact,
    SourceArtifact,
    canonical_sha256,
    load_catalog_artifact,
    load_source_artifact,
    sha256_hex,
)
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


@dataclass(frozen=True)
class SnapshotSeriesBinding:
    """Provider selectors and policy for one approved snapshot series."""

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
        """Return the callable scope key."""

        return (self.source_system, self.table_id, self.item_id)

    def descriptor(self) -> dict[str, str | None]:
        """Return the binding's registry-digest material."""

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


@dataclass(frozen=True)
class SnapshotRegistryEntry:
    """One approved series and the captures admitted for it."""

    binding: SnapshotSeriesBinding
    artifacts: tuple[SourceArtifact, ...] = ()


@dataclass(frozen=True)
class SnapshotRegistry:
    """The admitted snapshots and rights catalogs that the reader may use."""

    registry_id: str
    entries: tuple[SnapshotRegistryEntry, ...]
    catalog_artifacts: tuple[CatalogArtifact, ...]

    @property
    def rights_catalogs(self) -> tuple[RightsCatalog, ...]:
        """Return the rights catalogs carried by the registry."""

        return tuple(artifact.catalog for artifact in self.catalog_artifacts)

    def entry_for(
        self,
        source_system: SourceSystem,
        table_id: str,
        item_id: str,
    ) -> SnapshotRegistryEntry:
        """Return the entry for one exact scope."""

        scope = (source_system, table_id, item_id)
        for entry in self.entries:
            if entry.binding.scope == scope:
                return entry
        raise KeyError(f"no snapshot binding for {scope!r}")

    @property
    def descriptor_sha256(self) -> str:
        """Hash every admitted binding, manifest, archive, and catalog."""

        entries = sorted(
            self.entries,
            key=lambda entry: (
                entry.binding.source_system.value,
                entry.binding.table_id,
                entry.binding.item_id,
            ),
        )
        return canonical_sha256(
            {
                "catalogs": sorted(
                    (
                        {
                            "catalog_id": artifact.catalog.catalog_id,
                            "content_sha256": sha256_hex(artifact.catalog_bytes),
                        }
                        for artifact in self.catalog_artifacts
                    ),
                    key=lambda item: item["catalog_id"],
                ),
                "entries": [
                    {
                        "artifacts": sorted(
                            (_artifact_descriptor(artifact) for artifact in entry.artifacts),
                            key=lambda item: item["source_id"],
                        ),
                        "binding": entry.binding.descriptor(),
                    }
                    for entry in entries
                ],
                "registry_id": self.registry_id,
                "schema_version": "1.0.0",
            }
        )


@dataclass(frozen=True)
class SnapshotArtifactLocation:
    """Repository-relative paths of one admitted capture."""

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
    """Load explicitly listed snapshots and check their checksums and rights links."""

    artifacts: dict[tuple[SourceSystem, str, str], list[SourceArtifact]] = {
        binding.scope: [] for binding in SNAPSHOT_SERIES_BINDINGS
    }
    for location in artifact_locations:
        artifact = load_source_artifact(
            repository_root,
            location.manifest_path,
            location.archive_path,
        )
        _require_manifest_binding(artifact.manifest, location.binding)
        # The reader picks the newest capture by its instant, so a tie would be ambiguous.
        if any(
            other.manifest.retrieved_at == artifact.manifest.retrieved_at
            for other in artifacts[location.binding.scope]
        ):
            raise ValueError(f"snapshot {artifact.manifest.source_id} repeats a capture instant")
        artifacts[location.binding.scope].append(artifact)

    registry = SnapshotRegistry(
        registry_id=registry_id,
        entries=tuple(
            SnapshotRegistryEntry(binding=binding, artifacts=tuple(artifacts[binding.scope]))
            for binding in SNAPSHOT_SERIES_BINDINGS
        ),
        catalog_artifacts=tuple(
            load_catalog_artifact(repository_root, path) for path in rights_catalog_paths
        ),
    )
    # The bundle validator cross-checks every manifest's rights link against the catalogs.
    BenchmarkBundle(
        sources=tuple(
            artifact.manifest for entry in registry.entries for artifact in entry.artifacts
        ),
        records=(),
        rights_catalogs=registry.rights_catalogs,
    )
    return registry


def load_committed_snapshot_registry(repository_root: Path) -> SnapshotRegistry:
    """Load snapshot registry v1: the three 2026-07-17 captures used by the benchmark."""

    registry = load_snapshot_registry(
        repository_root,
        registry_id=SNAPSHOT_REGISTRY_ID,
        artifact_locations=COMMITTED_SNAPSHOT_LOCATIONS,
        rights_catalog_paths=COMMITTED_RIGHTS_CATALOG_PATHS,
    )
    if registry.descriptor_sha256 != SNAPSHOT_REGISTRY_DESCRIPTOR_SHA256:
        raise ValueError(
            "committed snapshot registry changed; keep v1 as is and add a new registry version"
        )
    return registry


def _artifact_descriptor(artifact: SourceArtifact) -> dict[str, int | str]:
    return {
        "archive_byte_size": len(artifact.archive_bytes),
        "archive_sha256": sha256_hex(artifact.archive_bytes),
        "manifest_archive_byte_size": artifact.manifest.byte_size,
        "manifest_archive_sha256": artifact.manifest.content_sha256,
        "manifest_sha256": sha256_hex(artifact.manifest_bytes),
        "source_id": artifact.manifest.source_id,
    }


def _require_manifest_binding(manifest: SourceManifest, binding: SnapshotSeriesBinding) -> None:
    """Admit only an allowed latest-only API snapshot of the binding's exact series."""

    reference = manifest.rights_decision
    rule = normalization_rule(binding.source_system, binding.table_id, binding.item_id)
    if (
        manifest.source_kind is not SourceKind.API
        or manifest.vintage_semantics is not VintageSemantics.LATEST_ONLY
        or manifest.media_type != "application/json"
        or manifest.redistribution.status is not RedistributionStatus.ALLOWED
        or manifest.document_family != binding.document_family
        or reference is None
        or reference.source_system is not binding.source_system
        or reference.table_id != binding.table_id
        or reference.item_id != binding.item_id
        or reference.decision_id != binding.rights_decision_id
        or rule.rule_id != binding.normalization_rule_id
    ):
        raise ValueError(f"snapshot {manifest.source_id} differs from its approved series binding")
