"""Trusted latest-only snapshot registry and deterministic reader."""

from sovereignlab.snapshots.reader import (
    SnapshotAbstentionReason,
    read_snapshot_as_of,
)
from sovereignlab.snapshots.registry import (
    COMMITTED_RIGHTS_CATALOG_PATHS,
    COMMITTED_SNAPSHOT_LOCATIONS,
    ECOS_CURRENT_ACCOUNT_BINDING,
    ECOS_GDP_BINDING,
    KOSIS_CPI_BINDING,
    MAX_SNAPSHOT_BYTES,
    SNAPSHOT_REGISTRY_DESCRIPTOR_SHA256,
    SNAPSHOT_REGISTRY_ID,
    SNAPSHOT_SERIES_BINDINGS,
    SnapshotArtifact,
    SnapshotArtifactLocation,
    SnapshotCatalogArtifact,
    SnapshotRegistry,
    SnapshotRegistryEntry,
    SnapshotRegistryLoadError,
    SnapshotSeriesBinding,
    load_committed_snapshot_registry,
    load_snapshot_registry,
)

__all__ = [
    "COMMITTED_RIGHTS_CATALOG_PATHS",
    "COMMITTED_SNAPSHOT_LOCATIONS",
    "ECOS_CURRENT_ACCOUNT_BINDING",
    "ECOS_GDP_BINDING",
    "KOSIS_CPI_BINDING",
    "MAX_SNAPSHOT_BYTES",
    "SNAPSHOT_REGISTRY_DESCRIPTOR_SHA256",
    "SNAPSHOT_REGISTRY_ID",
    "SNAPSHOT_SERIES_BINDINGS",
    "SnapshotAbstentionReason",
    "SnapshotArtifact",
    "SnapshotArtifactLocation",
    "SnapshotCatalogArtifact",
    "SnapshotRegistry",
    "SnapshotRegistryEntry",
    "SnapshotRegistryLoadError",
    "SnapshotSeriesBinding",
    "load_committed_snapshot_registry",
    "load_snapshot_registry",
    "read_snapshot_as_of",
]
