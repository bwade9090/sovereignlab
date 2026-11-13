"""Explicit, digest-pinned registry of the committed historical OECD STES evidence."""

import csv
import io
from collections.abc import Sequence
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

from sovereignlab.artifacts import (
    CatalogArtifact,
    LedgerArtifact,
    SourceArtifact,
    canonical_sha256,
    load_catalog_artifact,
    load_ledger_artifact,
    load_source_artifact,
    sha256_hex,
)
from sovereignlab.schemas import (
    BenchmarkBundle,
    EditionAvailabilityLedger,
    RedistributionStatus,
    SourceManifest,
    SourceSystem,
    VintageSemantics,
)

STES_REGISTRY_ID = "kor-rtd-stes-resolver-registry-v1"
STES_REGISTRY_DESCRIPTOR_SHA256 = "103eb3bea7beebadeb0a7e193ff76fc95b518a8a7bed6825d9eb1f25431fb420"
STES_TABLE_ID = "DSD_STES_REVISIONS@DF_STES_REVISIONS"

_SCOPE_COLUMNS = ("REF_AREA", "FREQ", "MEASURE", "UNIT_MEASURE", "ACTIVITY")


class RawEvidenceAvailability(StrEnum):
    """Whether a callable series has owner-approved public raw evidence."""

    ALLOWED = "allowed"
    UNAVAILABLE = "unavailable"


@dataclass(frozen=True)
class StesSeriesBinding:
    """Rights and normalization policy for one callable STES series."""

    ref_area: str
    freq: str
    measure: str
    unit_measure: str
    activity: str
    normalization_rule_id: str
    raw_evidence: RawEvidenceAvailability
    source_id: str | None = None
    document_family: str | None = None
    rights_decision_id: str | None = None

    @property
    def scope(self) -> tuple[str, str, str, str, str]:
        """Return the five series dimensions that identify the series."""

        return (self.ref_area, self.freq, self.measure, self.unit_measure, self.activity)

    @property
    def item_id(self) -> str:
        """Return the rights and normalization item identifier."""

        return ".".join(self.scope)

    def descriptor(self) -> dict[str, str | None]:
        """Return the binding's registry-digest material."""

        return {
            "activity": self.activity,
            "document_family": self.document_family,
            "freq": self.freq,
            "measure": self.measure,
            "normalization_rule_id": self.normalization_rule_id,
            "raw_evidence": self.raw_evidence.value,
            "ref_area": self.ref_area,
            "rights_decision_id": self.rights_decision_id,
            "source_id": self.source_id,
            "unit_measure": self.unit_measure,
        }


CLI_STES_BINDING = StesSeriesBinding(
    ref_area="KOR",
    freq="M",
    measure="LI_AA",
    unit_measure="IX",
    activity="_T",
    normalization_rule_id="oecd-stes-kor-li-aa-index-v1",
    raw_evidence=RawEvidenceAvailability.ALLOWED,
    source_id="oecd-stes-cli-kor-li-aa-20260717t115302688498z",
    document_family="oecd-stes-cli-kor-li-aa",
    rights_decision_id="oecd-stes-revisions-kor-m-li-aa-rights-v1",
)
GDP_STES_BINDING = StesSeriesBinding(
    ref_area="KOR",
    freq="Q",
    measure="B1GQ_Q",
    unit_measure="XDC",
    activity="_T",
    normalization_rule_id="oecd-stes-kor-b1gq-q-xdc-billion-krw-v1",
    raw_evidence=RawEvidenceAvailability.UNAVAILABLE,
)
STES_SERIES_BINDINGS = (CLI_STES_BINDING, GDP_STES_BINDING)


@dataclass(frozen=True)
class StesArchiveSummary:
    """Shape of one admitted data archive, recorded in the registry digest."""

    row_count: int
    column_count: int
    edition_count: int
    first_edition: str
    last_edition: str

    def descriptor(self) -> dict[str, int | str]:
        """Return the summary's registry-digest material."""

        return {
            "column_count": self.column_count,
            "edition_count": self.edition_count,
            "first_edition": self.first_edition,
            "last_edition": self.last_edition,
            "row_count": self.row_count,
        }


@dataclass(frozen=True)
class StesRegistryEntry:
    """One callable series and, when rights allow, its admitted data archive."""

    binding: StesSeriesBinding
    data_artifact: SourceArtifact | None = None
    archive_summary: StesArchiveSummary | None = None


@dataclass(frozen=True)
class StesRegistry:
    """The admitted archive, availability evidence, ledgers, and rights catalogs."""

    registry_id: str
    entries: tuple[StesRegistryEntry, ...]
    support_artifacts: tuple[SourceArtifact, ...]
    ledger_artifacts: tuple[LedgerArtifact, ...]
    catalog_artifacts: tuple[CatalogArtifact, ...]
    active_ledger_id: str
    complete_through_source_id: str
    captured_at_source_id: str

    @property
    def active_ledger(self) -> EditionAvailabilityLedger:
        """Return the ledger that decides which edition a cutoff may see."""

        for artifact in self.ledger_artifacts:
            if artifact.ledger.ledger_id == self.active_ledger_id:
                return artifact.ledger
        raise KeyError(f"active ledger {self.active_ledger_id} is not registered")

    def entry_for(self, scope: tuple[str, str, str, str, str]) -> StesRegistryEntry:
        """Return the entry for one exact five-dimensional series scope."""

        for entry in self.entries:
            if entry.binding.scope == scope:
                return entry
        raise KeyError(f"no STES binding for {scope!r}")

    @property
    def descriptor_sha256(self) -> str:
        """Hash every admitted binding, manifest, archive, ledger, and catalog."""

        return canonical_sha256(
            {
                "active_ledger_id": self.active_ledger_id,
                "captured_at_source_id": self.captured_at_source_id,
                "catalogs": sorted(
                    (
                        {
                            "byte_size": len(artifact.catalog_bytes),
                            "catalog_id": artifact.catalog.catalog_id,
                            "content_sha256": sha256_hex(artifact.catalog_bytes),
                            "supersedes_catalog_id": artifact.catalog.supersedes_catalog_id,
                        }
                        for artifact in self.catalog_artifacts
                    ),
                    key=lambda item: item["catalog_id"],
                ),
                "complete_through_source_id": self.complete_through_source_id,
                "entries": sorted(
                    (
                        {
                            "archive_summary": (
                                None
                                if entry.archive_summary is None
                                else entry.archive_summary.descriptor()
                            ),
                            "binding": entry.binding.descriptor(),
                            "data_artifact": (
                                None
                                if entry.data_artifact is None
                                else _artifact_descriptor(entry.data_artifact, "data_archive")
                            ),
                        }
                        for entry in self.entries
                    ),
                    key=lambda item: (
                        item["binding"]["ref_area"],
                        item["binding"]["freq"],
                        item["binding"]["measure"],
                    ),
                ),
                "ledgers": sorted(
                    (
                        {
                            "byte_size": len(artifact.ledger_bytes),
                            "content_sha256": sha256_hex(artifact.ledger_bytes),
                            "dataflow_id": artifact.ledger.dataflow_id,
                            "dataflow_version": artifact.ledger.dataflow_version,
                            "edition_count": len(artifact.ledger.editions),
                            "ledger_id": artifact.ledger.ledger_id,
                            "supersedes_ledger_id": artifact.ledger.supersedes_ledger_id,
                        }
                        for artifact in self.ledger_artifacts
                    ),
                    key=lambda item: item["ledger_id"],
                ),
                "registry_id": self.registry_id,
                "schema_version": "1.0.0",
                "support_artifacts": sorted(
                    (
                        _artifact_descriptor(artifact, "availability_support")
                        for artifact in self.support_artifacts
                    ),
                    key=lambda item: item["source_id"],
                ),
            }
        )


@dataclass(frozen=True)
class StesArtifactLocation:
    """Repository-relative paths of one admitted manifest/archive pair.

    A location with a binding is that series' data archive; one without is availability
    support (an OECD constraint capture that a ledger cites as evidence).
    """

    manifest_path: Path
    archive_path: Path
    binding: StesSeriesBinding | None = None


COMMITTED_STES_ARTIFACT_LOCATIONS = (
    StesArtifactLocation(
        binding=CLI_STES_BINDING,
        manifest_path=Path("data/manifests/oecd-stes-cli-kor-li-aa-20260717t115302688498z.json"),
        archive_path=Path(
            "data/archive/oecd-stes/oecd-stes-cli-kor-li-aa-20260717t115302688498z.csv"
        ),
    ),
    *(
        StesArtifactLocation(
            manifest_path=Path(f"data/manifests/oecd-stes-{role}-{token}.json"),
            archive_path=Path(f"data/archive/oecd-stes/oecd-stes-{role}-{token}.xml"),
        )
        for token in ("20260717t101906273935z", "20260717t115242998550z")
        for role in ("availableconstraint", "contentconstraint")
    ),
)
COMMITTED_STES_LEDGER_PATHS = (
    Path("data/availability/oecd-stes-ledger-20260717t101906273935z.json"),
    Path("data/availability/oecd-stes-ledger-20260717t115242998550z.json"),
)
COMMITTED_STES_CATALOG_PATHS = (
    Path("data/rights/kor-rtd-rights-2026-07-16.json"),
    Path("data/rights/kor-rtd-rights-2026-07-17.json"),
)
COMMITTED_ACTIVE_STES_LEDGER_ID = "oecd-stes-ledger-20260717t115242998550z"
COMMITTED_COMPLETE_THROUGH_SOURCE_ID = "oecd-stes-availableconstraint-20260717t115242998550z"
COMMITTED_CAPTURED_AT_SOURCE_ID = "oecd-stes-contentconstraint-20260717t115242998550z"


def load_stes_registry(
    repository_root: Path,
    *,
    registry_id: str,
    artifact_locations: Sequence[StesArtifactLocation],
    ledger_paths: Sequence[Path],
    catalog_paths: Sequence[Path],
    active_ledger_id: str,
    complete_through_source_id: str,
    captured_at_source_id: str,
) -> StesRegistry:
    """Load explicitly listed STES evidence and check checksums, rights, and ledger links."""

    data_artifacts: dict[tuple[str, str, str, str, str], SourceArtifact] = {}
    support_artifacts: list[SourceArtifact] = []
    for location in artifact_locations:
        artifact = load_source_artifact(
            repository_root,
            location.manifest_path,
            location.archive_path,
        )
        if location.binding is None:
            support_artifacts.append(artifact)
        else:
            _require_manifest_binding(artifact.manifest, location.binding)
            data_artifacts[location.binding.scope] = artifact

    entries = []
    for binding in STES_SERIES_BINDINGS:
        artifact = data_artifacts.get(binding.scope)
        if (artifact is not None) != (binding.raw_evidence is RawEvidenceAvailability.ALLOWED):
            raise ValueError("a STES series has a data archive exactly when its rights allow one")
        entries.append(
            StesRegistryEntry(
                binding=binding,
                data_artifact=artifact,
                archive_summary=(
                    None if artifact is None else _summarize_archive(artifact, binding)
                ),
            )
        )

    registry = StesRegistry(
        registry_id=registry_id,
        entries=tuple(entries),
        support_artifacts=tuple(support_artifacts),
        ledger_artifacts=tuple(
            load_ledger_artifact(repository_root, path) for path in ledger_paths
        ),
        catalog_artifacts=tuple(
            load_catalog_artifact(repository_root, path) for path in catalog_paths
        ),
        active_ledger_id=active_ledger_id,
        complete_through_source_id=complete_through_source_id,
        captured_at_source_id=captured_at_source_id,
    )

    # The bundle validator cross-checks rights links and the ledgers' evidence references.
    BenchmarkBundle(
        sources=tuple(
            artifact.manifest for artifact in (*data_artifacts.values(), *support_artifacts)
        ),
        records=(),
        availability_ledgers=tuple(artifact.ledger for artifact in registry.ledger_artifacts),
        rights_catalogs=tuple(artifact.catalog for artifact in registry.catalog_artifacts),
    )
    retrieved_at = {
        artifact.manifest.source_id: artifact.manifest.retrieved_at
        for artifact in support_artifacts
    }
    ledger = registry.active_ledger
    if (
        retrieved_at.get(complete_through_source_id) != ledger.complete_through
        or retrieved_at.get(captured_at_source_id) != ledger.captured_at
    ):
        raise ValueError("the active ledger does not match its constraint captures")
    return registry


def load_committed_stes_registry(repository_root: Path) -> StesRegistry:
    """Load STES registry v1: the 2026-07-17 CLI archive, ledgers, and constraint captures."""

    registry = load_stes_registry(
        repository_root,
        registry_id=STES_REGISTRY_ID,
        artifact_locations=COMMITTED_STES_ARTIFACT_LOCATIONS,
        ledger_paths=COMMITTED_STES_LEDGER_PATHS,
        catalog_paths=COMMITTED_STES_CATALOG_PATHS,
        active_ledger_id=COMMITTED_ACTIVE_STES_LEDGER_ID,
        complete_through_source_id=COMMITTED_COMPLETE_THROUGH_SOURCE_ID,
        captured_at_source_id=COMMITTED_CAPTURED_AT_SOURCE_ID,
    )
    if registry.descriptor_sha256 != STES_REGISTRY_DESCRIPTOR_SHA256:
        raise ValueError(
            "committed STES registry changed; keep v1 as is and add a new registry version"
        )
    return registry


def _artifact_descriptor(artifact: SourceArtifact, role: str) -> dict[str, int | str]:
    return {
        "archive_byte_size": len(artifact.archive_bytes),
        "archive_sha256": sha256_hex(artifact.archive_bytes),
        "manifest_archive_byte_size": artifact.manifest.byte_size,
        "manifest_archive_sha256": artifact.manifest.content_sha256,
        "manifest_byte_size": len(artifact.manifest_bytes),
        "manifest_sha256": sha256_hex(artifact.manifest_bytes),
        "role": role,
        "source_id": artifact.manifest.source_id,
    }


def _require_manifest_binding(manifest: SourceManifest, binding: StesSeriesBinding) -> None:
    """Admit only the allowed historical archive of the binding's exact series."""

    reference = manifest.rights_decision
    if (
        manifest.source_id != binding.source_id
        or manifest.document_family != binding.document_family
        or manifest.vintage_semantics is not VintageSemantics.HISTORICAL_ARCHIVE
        or manifest.redistribution.status is not RedistributionStatus.ALLOWED
        or reference is None
        or reference.source_system is not SourceSystem.OECD
        or reference.table_id != STES_TABLE_ID
        or reference.item_id != binding.item_id
        or reference.decision_id != binding.rights_decision_id
    ):
        raise ValueError(f"archive {manifest.source_id} differs from its approved series binding")


def _summarize_archive(artifact: SourceArtifact, binding: StesSeriesBinding) -> StesArchiveSummary:
    """Count the archive and reject any row outside the approved series."""

    text = artifact.archive_bytes.decode("utf-8-sig")
    reader = csv.reader(io.StringIO(text, newline=""), strict=True)
    header = next(reader)
    scope_indexes = [header.index(column) for column in _SCOPE_COLUMNS]
    edition_index = header.index("EDITION")
    editions: set[str] = set()
    row_count = 0
    for row in reader:
        if not row or all(not value.strip() for value in row):
            continue
        row_count += 1
        if tuple(row[index] for index in scope_indexes) != binding.scope:
            raise ValueError(f"archive {artifact.manifest.source_id} contains a neighboring series")
        editions.add(row[edition_index])
    return StesArchiveSummary(
        row_count=row_count,
        column_count=len(header),
        edition_count=len(editions),
        first_edition=min(editions),
        last_edition=max(editions),
    )
