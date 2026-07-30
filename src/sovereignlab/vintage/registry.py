"""Trusted, digest-linked inputs for the historical STES resolver adapter."""

import csv
import hashlib
import io
import json
import re
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from xml.etree import ElementTree

from pydantic import BaseModel, ValidationError

from sovereignlab.normalization import normalization_rule
from sovereignlab.schemas import (
    AvailabilityEvidenceBasis,
    BenchmarkBundle,
    EditionAvailabilityLedger,
    RedistributionStatus,
    RightsCatalog,
    SourceKind,
    SourceManifest,
    SourceSystem,
    VintageSemantics,
)
from sovereignlab.vintage.resolver import _manifest_dataflow_reference

STES_REGISTRY_ID = "kor-rtd-stes-resolver-registry-v1"
STES_REGISTRY_DESCRIPTOR_SHA256 = "103eb3bea7beebadeb0a7e193ff76fc95b518a8a7bed6825d9eb1f25431fb420"
STES_DATAFLOW_ID = "OECD.SDD.STES:DSD_STES_REVISIONS@DF_STES_REVISIONS"
STES_DATAFLOW_VERSION = "4.0"
MAX_STES_DATA_ARCHIVE_BYTES = 25_000_000
MAX_STES_SUPPORT_ARCHIVE_BYTES = 1_000_000
MAX_STES_METADATA_BYTES = 1_000_000
MAX_STES_ARCHIVE_ROWS = 100_000
MAX_STES_ARCHIVE_COLUMNS = 64
MAX_STES_LEDGER_EDITIONS = 500

_EDITION_PATTERN = re.compile(r"^[0-9]{4}(?:0[1-9]|1[0-2])$")
_MONTHLY_PERIOD_PATTERN = re.compile(r"^[0-9]{4}-(?:0[1-9]|1[0-2])$")
_PLAIN_DECIMAL_PATTERN = re.compile(r"^[+-]?[0-9]+(?:\.[0-9]+)?$")
_CONSTRAINT_SOURCE_PATTERN = re.compile(
    r"^oecd-stes-(availableconstraint|contentconstraint)-"
    r"([0-9]{8}t[0-9]{12}z)$"
)
_AVAILABLE_CONSTRAINT_URL = (
    "https://sdmx.oecd.org/public/rest/availableconstraint/"
    "OECD.SDD.STES,DSD_STES_REVISIONS%40DF_STES_REVISIONS,4.0/"
    "all/all/EDITION?mode=exact"
)
_CONTENT_CONSTRAINT_URL = (
    "https://sdmx.oecd.org/public/rest/contentconstraint/OECD.SDD.STES/"
    "CR_A_DSD_STES_REVISIONS%40DF_STES_REVISIONS/4.0?references=none"
)
_CONTENT_CONSTRAINT_ID = "CR_A_DSD_STES_REVISIONS@DF_STES_REVISIONS"
_REQUIRED_ARCHIVE_COLUMNS = (
    "REF_AREA",
    "FREQ",
    "MEASURE",
    "UNIT_MEASURE",
    "ACTIVITY",
    "EDITION",
    "TIME_PERIOD",
    "OBS_VALUE",
)


class StesRegistryLoadError(ValueError):
    """Sanitized harness failure while loading explicitly trusted STES inputs."""


class RawEvidenceAvailability(StrEnum):
    """Whether an exact frozen call scope has approved public raw evidence."""

    ALLOWED = "allowed"
    UNAVAILABLE = "unavailable"


class StesArtifactRole(StrEnum):
    """The two artifact roles admitted by the trusted registry."""

    DATA_ARCHIVE = "data_archive"
    AVAILABILITY_SUPPORT = "availability_support"


@dataclass(frozen=True)
class StesSeriesBinding:
    """Harness-owned authorization and normalization policy for one call scope."""

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
        """Return the exact five-dimensional model-visible scope."""

        return (
            self.ref_area,
            self.freq,
            self.measure,
            self.unit_measure,
            self.activity,
        )

    @property
    def item_id(self) -> str:
        """Return the rights/normalization item identifier."""

        return ".".join(self.scope)

    def descriptor(self) -> dict[str, str | None]:
        """Return stable policy material without paths or raw observations."""

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
_BINDINGS_BY_SCOPE = {binding.scope: binding for binding in STES_SERIES_BINDINGS}


class _RegistryPayloadError(ValueError):
    pass


class _DuplicateJsonKey(ValueError):
    pass


class _InvalidJsonConstant(ValueError):
    pass


@dataclass(frozen=True)
class StesSourceArtifact:
    """One exact manifest and the immutable archive bytes it describes."""

    role: StesArtifactRole
    manifest: SourceManifest
    manifest_bytes: bytes = field(repr=False, compare=False)
    archive_bytes: bytes = field(repr=False, compare=False)

    def validated(self) -> "_ValidatedSourceArtifact":
        """Rebuild the strict manifest and verify its exact archive bytes."""

        _require_exact_bytes(
            self.manifest_bytes,
            max_bytes=MAX_STES_METADATA_BYTES,
            label="STES manifest",
        )
        manifest = _parse_json_model(self.manifest_bytes, SourceManifest)
        if manifest != self.manifest:
            raise ValueError("STES manifest model differs from its exact JSON bytes")
        max_archive_bytes = {
            StesArtifactRole.DATA_ARCHIVE: MAX_STES_DATA_ARCHIVE_BYTES,
            StesArtifactRole.AVAILABILITY_SUPPORT: MAX_STES_SUPPORT_ARCHIVE_BYTES,
        }.get(self.role)
        if max_archive_bytes is None:
            raise ValueError("STES artifact has an unknown trusted role")
        _require_exact_bytes(
            self.archive_bytes,
            max_bytes=max_archive_bytes,
            label="STES archive",
        )
        if (
            len(self.archive_bytes) != manifest.byte_size
            or hashlib.sha256(self.archive_bytes).hexdigest() != manifest.content_sha256
        ):
            raise ValueError("STES archive bytes differ from their exact manifest")
        return _ValidatedSourceArtifact(
            role=self.role,
            manifest=manifest,
            manifest_bytes=self.manifest_bytes,
            archive_bytes=self.archive_bytes,
        )


@dataclass(frozen=True)
class StesLedgerArtifact:
    """One strict availability ledger and its exact committed JSON bytes."""

    ledger: EditionAvailabilityLedger
    ledger_bytes: bytes = field(repr=False, compare=False)

    def validated(self) -> "_ValidatedLedgerArtifact":
        """Rebuild the ledger from exact bytes and enforce its resource bound."""

        _require_exact_bytes(
            self.ledger_bytes,
            max_bytes=MAX_STES_METADATA_BYTES,
            label="STES availability ledger",
        )
        ledger = _parse_json_model(self.ledger_bytes, EditionAvailabilityLedger)
        if ledger != self.ledger:
            raise ValueError("STES ledger model differs from its exact JSON bytes")
        if len(ledger.editions) > MAX_STES_LEDGER_EDITIONS:
            raise ValueError("STES availability ledger exceeds its edition bound")
        return _ValidatedLedgerArtifact(
            ledger=ledger,
            ledger_bytes=self.ledger_bytes,
        )


@dataclass(frozen=True)
class StesCatalogArtifact:
    """One strict rights catalog and its exact committed JSON bytes."""

    catalog: RightsCatalog
    catalog_bytes: bytes = field(repr=False, compare=False)

    def validated(self) -> "_ValidatedCatalogArtifact":
        """Rebuild the catalog from exact bytes."""

        _require_exact_bytes(
            self.catalog_bytes,
            max_bytes=MAX_STES_METADATA_BYTES,
            label="STES rights catalog",
        )
        catalog = _parse_json_model(self.catalog_bytes, RightsCatalog)
        if catalog != self.catalog:
            raise ValueError("STES rights catalog model differs from its exact JSON bytes")
        return _ValidatedCatalogArtifact(
            catalog=catalog,
            catalog_bytes=self.catalog_bytes,
        )


@dataclass(frozen=True)
class StesRegistryEntry:
    """One frozen callable scope and its optional approved data artifact."""

    binding: StesSeriesBinding
    data_artifact: StesSourceArtifact | None = None


@dataclass(frozen=True)
class StesRegistry:
    """Complete immutable provenance and policy for deterministic STES resolution."""

    registry_id: str
    entries: tuple[StesRegistryEntry, ...]
    support_artifacts: tuple[StesSourceArtifact, ...]
    ledger_artifacts: tuple[StesLedgerArtifact, ...]
    catalog_artifacts: tuple[StesCatalogArtifact, ...]
    active_ledger_id: str
    complete_through_source_id: str
    captured_at_source_id: str

    def __post_init__(self) -> None:
        self.validated_state()

    def validated_state(self) -> "_ValidatedStesRegistry":
        """Rebuild every model from exact bytes and cross-validate all bindings."""

        if type(self.registry_id) is not str or not self.registry_id.strip():
            raise ValueError("STES registry ID must be a non-empty string")
        _require_exact_tuple(self.entries, "STES registry entries")
        _require_exact_tuple(self.support_artifacts, "STES support artifacts")
        _require_exact_tuple(self.ledger_artifacts, "STES ledger artifacts")
        _require_exact_tuple(self.catalog_artifacts, "STES catalog artifacts")

        entries: list[_ValidatedStesEntry] = []
        scopes: list[tuple[str, str, str, str, str]] = []
        for entry in self.entries:
            if type(entry) is not StesRegistryEntry:
                raise ValueError("STES registry entry has an invalid type")
            if type(entry.binding) is not StesSeriesBinding:
                raise ValueError("STES registry binding has an invalid type")
            approved = _BINDINGS_BY_SCOPE.get(entry.binding.scope)
            if approved != entry.binding:
                raise ValueError("STES registry contains a non-approved scope binding")
            scopes.append(entry.binding.scope)

            artifact: _ValidatedSourceArtifact | None = None
            if entry.data_artifact is not None:
                if type(entry.data_artifact) is not StesSourceArtifact:
                    raise ValueError("STES registry data artifact has an invalid type")
                artifact = StesSourceArtifact.validated(entry.data_artifact)
            if entry.binding.raw_evidence is RawEvidenceAvailability.ALLOWED:
                if artifact is None or artifact.role is not StesArtifactRole.DATA_ARCHIVE:
                    raise ValueError("allowed STES scope requires one trusted data archive")
            elif artifact is not None:
                raise ValueError("unavailable STES scope cannot carry a data archive")
            entries.append(
                _ValidatedStesEntry(
                    binding=entry.binding,
                    data_artifact=artifact,
                )
            )
        if len(scopes) != len(set(scopes)) or set(scopes) != set(_BINDINGS_BY_SCOPE):
            raise ValueError("STES registry must contain every frozen scope exactly once")

        support_artifacts: list[_ValidatedSourceArtifact] = []
        constraint_by_source_id: dict[str, _StesConstraintSnapshot] = {}
        for artifact in self.support_artifacts:
            if type(artifact) is not StesSourceArtifact:
                raise ValueError("STES support artifact has an invalid type")
            validated = StesSourceArtifact.validated(artifact)
            if validated.role is not StesArtifactRole.AVAILABILITY_SUPPORT:
                raise ValueError("STES support artifact has an invalid trusted role")
            snapshot = _validate_support_artifact(validated)
            if snapshot.source_id in constraint_by_source_id:
                raise ValueError("STES support constraint source IDs must be unique")
            constraint_by_source_id[snapshot.source_id] = snapshot
            support_artifacts.append(validated)

        ledger_artifacts: list[_ValidatedLedgerArtifact] = []
        for artifact in self.ledger_artifacts:
            if type(artifact) is not StesLedgerArtifact:
                raise ValueError("STES ledger artifact has an invalid type")
            ledger_artifacts.append(StesLedgerArtifact.validated(artifact))

        catalog_artifacts: list[_ValidatedCatalogArtifact] = []
        for artifact in self.catalog_artifacts:
            if type(artifact) is not StesCatalogArtifact:
                raise ValueError("STES catalog artifact has an invalid type")
            catalog_artifacts.append(StesCatalogArtifact.validated(artifact))

        data_sources = tuple(
            entry.data_artifact for entry in entries if entry.data_artifact is not None
        )
        source_artifacts = (*data_sources, *support_artifacts)
        source_ids = tuple(artifact.manifest.source_id for artifact in source_artifacts)
        if len(source_ids) != len(set(source_ids)):
            raise ValueError("STES registry source IDs must be unique")

        ledger_by_id = _unique_models(
            ledger_artifacts,
            attribute="ledger",
            nested_id="ledger_id",
            label="STES ledger ID",
        )
        catalog_by_id = _unique_models(
            catalog_artifacts,
            attribute="catalog",
            nested_id="catalog_id",
            label="STES catalog ID",
        )
        active_ledger = _validate_ledger_chain(
            ledger_by_id,
            active_ledger_id=self.active_ledger_id,
        )
        _validate_catalog_chain(catalog_by_id)
        _validate_constraint_ledger_join(
            constraint_by_source_id,
            support_artifacts,
            ledger_artifacts,
        )

        support_by_id = {artifact.manifest.source_id: artifact for artifact in support_artifacts}
        try:
            complete_source = support_by_id[self.complete_through_source_id]
            captured_source = support_by_id[self.captured_at_source_id]
        except KeyError:
            raise ValueError("STES registry completeness sources are missing") from None
        if complete_source.manifest.retrieved_at != active_ledger.complete_through:
            raise ValueError("STES ledger complete_through lacks its exact support capture")
        if captured_source.manifest.retrieved_at != active_ledger.captured_at:
            raise ValueError("STES ledger captured_at lacks its exact support capture")

        sources = tuple(artifact.manifest for artifact in source_artifacts)
        ledgers = tuple(artifact.ledger for artifact in ledger_artifacts)
        catalogs = tuple(artifact.catalog for artifact in catalog_artifacts)
        BenchmarkBundle(
            sources=sources,
            records=(),
            availability_ledgers=ledgers,
            rights_catalogs=catalogs,
        )

        validated_entries = tuple(entries)
        active_catalog_ids = {artifact.catalog.catalog_id for artifact in catalog_artifacts} - {
            artifact.catalog.supersedes_catalog_id
            for artifact in catalog_artifacts
            if artifact.catalog.supersedes_catalog_id is not None
        }
        for entry in validated_entries:
            rule = normalization_rule(
                SourceSystem.OECD,
                "DSD_STES_REVISIONS@DF_STES_REVISIONS",
                entry.binding.item_id,
            )
            if rule.rule_id != entry.binding.normalization_rule_id:
                raise ValueError("STES binding differs from the normalization registry")
            if entry.data_artifact is not None:
                _validate_data_manifest(
                    entry.data_artifact.manifest,
                    entry.binding,
                    active_ledger,
                    active_catalog_ids,
                )
                summary = _validate_archive_scope(
                    entry.data_artifact.archive_bytes,
                    entry.binding,
                )
                _validate_archive_ledger_join(summary, active_ledger)
                entry = _ValidatedStesEntry(
                    binding=entry.binding,
                    data_artifact=entry.data_artifact,
                    archive_summary=summary,
                )
                index = next(
                    index
                    for index, candidate in enumerate(validated_entries)
                    if candidate.binding.scope == entry.binding.scope
                )
                validated_entries = (
                    *validated_entries[:index],
                    entry,
                    *validated_entries[index + 1 :],
                )

        _validate_unavailable_rights_policy(
            validated_entries,
            catalog_artifacts,
            active_catalog_ids,
        )
        return _ValidatedStesRegistry(
            entries=validated_entries,
            support_artifacts=tuple(support_artifacts),
            ledger_artifacts=tuple(ledger_artifacts),
            catalog_artifacts=tuple(catalog_artifacts),
            active_ledger=active_ledger,
        )

    def canonical_descriptor_bytes(self) -> bytes:
        """Serialize complete order-independent registry provenance."""

        state = self.validated_state()
        descriptor = {
            "active_ledger_id": state.active_ledger.ledger_id,
            "captured_at_source_id": self.captured_at_source_id,
            "catalogs": sorted(
                (artifact.descriptor() for artifact in state.catalog_artifacts),
                key=lambda item: item["catalog_id"],
            ),
            "complete_through_source_id": self.complete_through_source_id,
            "entries": sorted(
                (entry.descriptor() for entry in state.entries),
                key=lambda item: (
                    item["binding"]["ref_area"],
                    item["binding"]["freq"],
                    item["binding"]["measure"],
                ),
            ),
            "ledgers": sorted(
                (artifact.descriptor() for artifact in state.ledger_artifacts),
                key=lambda item: item["ledger_id"],
            ),
            "registry_id": self.registry_id,
            "schema_version": "1.0.0",
            "support_artifacts": sorted(
                (artifact.descriptor() for artifact in state.support_artifacts),
                key=lambda item: item["source_id"],
            ),
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
class StesArtifactLocation:
    """Harness-only locations for one explicitly admitted manifest/archive pair."""

    role: StesArtifactRole
    manifest_path: Path
    archive_path: Path
    binding: StesSeriesBinding | None = None


COMMITTED_STES_ARTIFACT_LOCATIONS = (
    StesArtifactLocation(
        role=StesArtifactRole.DATA_ARCHIVE,
        binding=CLI_STES_BINDING,
        manifest_path=Path("data/manifests/oecd-stes-cli-kor-li-aa-20260717t115302688498z.json"),
        archive_path=Path(
            "data/archive/oecd-stes/oecd-stes-cli-kor-li-aa-20260717t115302688498z.csv"
        ),
    ),
    StesArtifactLocation(
        role=StesArtifactRole.AVAILABILITY_SUPPORT,
        manifest_path=Path(
            "data/manifests/oecd-stes-availableconstraint-20260717t101906273935z.json"
        ),
        archive_path=Path(
            "data/archive/oecd-stes/oecd-stes-availableconstraint-20260717t101906273935z.xml"
        ),
    ),
    StesArtifactLocation(
        role=StesArtifactRole.AVAILABILITY_SUPPORT,
        manifest_path=Path(
            "data/manifests/oecd-stes-contentconstraint-20260717t101906273935z.json"
        ),
        archive_path=Path(
            "data/archive/oecd-stes/oecd-stes-contentconstraint-20260717t101906273935z.xml"
        ),
    ),
    StesArtifactLocation(
        role=StesArtifactRole.AVAILABILITY_SUPPORT,
        manifest_path=Path(
            "data/manifests/oecd-stes-availableconstraint-20260717t115242998550z.json"
        ),
        archive_path=Path(
            "data/archive/oecd-stes/oecd-stes-availableconstraint-20260717t115242998550z.xml"
        ),
    ),
    StesArtifactLocation(
        role=StesArtifactRole.AVAILABILITY_SUPPORT,
        manifest_path=Path(
            "data/manifests/oecd-stes-contentconstraint-20260717t115242998550z.json"
        ),
        archive_path=Path(
            "data/archive/oecd-stes/oecd-stes-contentconstraint-20260717t115242998550z.xml"
        ),
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
    artifact_locations: tuple[StesArtifactLocation, ...],
    ledger_paths: tuple[Path, ...],
    catalog_paths: tuple[Path, ...],
    active_ledger_id: str,
    complete_through_source_id: str,
    captured_at_source_id: str,
) -> StesRegistry:
    """Load an explicitly enumerated, repository-confined trusted registry."""

    try:
        root = repository_root.resolve(strict=True)
    except (AttributeError, OSError, RuntimeError, TypeError):
        raise StesRegistryLoadError("the trusted repository root could not be resolved") from None
    if type(artifact_locations) is not tuple:
        raise ValueError("trusted STES artifact locations must be a tuple")
    if type(ledger_paths) is not tuple or type(catalog_paths) is not tuple:
        raise ValueError("trusted STES metadata locations must be tuples")
    if any(type(location) is not StesArtifactLocation for location in artifact_locations):
        raise StesRegistryLoadError("the trusted STES registry is invalid")
    if any(
        not isinstance(path, Path)
        for location in artifact_locations
        for path in (location.manifest_path, location.archive_path)
    ) or any(not isinstance(path, Path) for path in (*ledger_paths, *catalog_paths)):
        raise StesRegistryLoadError("the trusted STES registry is invalid")

    relative_paths = (
        *(
            path
            for location in artifact_locations
            for path in (location.manifest_path, location.archive_path)
        ),
        *ledger_paths,
        *catalog_paths,
    )
    if len(relative_paths) != len(set(relative_paths)):
        raise ValueError("trusted STES registry roles must use distinct files")

    data_artifacts: dict[tuple[str, str, str, str, str], StesSourceArtifact] = {}
    support_artifacts: list[StesSourceArtifact] = []
    try:
        for location in artifact_locations:
            artifact = _load_source_artifact(root, location)
            if location.role is StesArtifactRole.DATA_ARCHIVE:
                if (
                    location.binding is None
                    or _BINDINGS_BY_SCOPE.get(location.binding.scope) != location.binding
                    or location.binding.raw_evidence is not RawEvidenceAvailability.ALLOWED
                ):
                    raise ValueError("trusted STES data location has an invalid binding")
                if location.binding.scope in data_artifacts:
                    raise ValueError("trusted STES data scope is registered more than once")
                data_artifacts[location.binding.scope] = artifact
            elif location.role is StesArtifactRole.AVAILABILITY_SUPPORT:
                if location.binding is not None:
                    raise ValueError("STES support location cannot carry a series binding")
                support_artifacts.append(artifact)
            else:
                raise ValueError("trusted STES artifact location has an invalid role")

        ledger_artifacts = tuple(_load_ledger_artifact(root, path) for path in ledger_paths)
        catalog_artifacts = tuple(_load_catalog_artifact(root, path) for path in catalog_paths)
        return StesRegistry(
            registry_id=registry_id,
            entries=tuple(
                StesRegistryEntry(
                    binding=binding,
                    data_artifact=data_artifacts.get(binding.scope),
                )
                for binding in STES_SERIES_BINDINGS
            ),
            support_artifacts=tuple(support_artifacts),
            ledger_artifacts=ledger_artifacts,
            catalog_artifacts=catalog_artifacts,
            active_ledger_id=active_ledger_id,
            complete_through_source_id=complete_through_source_id,
            captured_at_source_id=captured_at_source_id,
        )
    except StesRegistryLoadError:
        raise
    except (AttributeError, OSError, RuntimeError, TypeError, ValidationError, ValueError):
        raise StesRegistryLoadError("the trusted STES registry is invalid") from None


def load_committed_stes_registry(repository_root: Path) -> StesRegistry:
    """Load the exact STES provenance set admitted for the offline baseline."""

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
        raise ValueError("committed STES registry changed; preserve v1 and create a new version")
    return registry


@dataclass(frozen=True)
class _ValidatedSourceArtifact:
    role: StesArtifactRole
    manifest: SourceManifest
    manifest_bytes: bytes = field(repr=False)
    archive_bytes: bytes = field(repr=False)

    def descriptor(self) -> dict[str, int | str]:
        return {
            "archive_byte_size": len(self.archive_bytes),
            "archive_sha256": hashlib.sha256(self.archive_bytes).hexdigest(),
            "manifest_archive_byte_size": self.manifest.byte_size,
            "manifest_archive_sha256": self.manifest.content_sha256,
            "manifest_byte_size": len(self.manifest_bytes),
            "manifest_sha256": hashlib.sha256(self.manifest_bytes).hexdigest(),
            "role": self.role.value,
            "source_id": self.manifest.source_id,
        }


@dataclass(frozen=True)
class _ValidatedLedgerArtifact:
    ledger: EditionAvailabilityLedger
    ledger_bytes: bytes = field(repr=False)

    def descriptor(self) -> dict[str, int | str | None]:
        return {
            "byte_size": len(self.ledger_bytes),
            "content_sha256": hashlib.sha256(self.ledger_bytes).hexdigest(),
            "dataflow_id": self.ledger.dataflow_id,
            "dataflow_version": self.ledger.dataflow_version,
            "edition_count": len(self.ledger.editions),
            "ledger_id": self.ledger.ledger_id,
            "supersedes_ledger_id": self.ledger.supersedes_ledger_id,
        }


@dataclass(frozen=True)
class _ValidatedCatalogArtifact:
    catalog: RightsCatalog
    catalog_bytes: bytes = field(repr=False)

    def descriptor(self) -> dict[str, int | str | None]:
        return {
            "byte_size": len(self.catalog_bytes),
            "catalog_id": self.catalog.catalog_id,
            "content_sha256": hashlib.sha256(self.catalog_bytes).hexdigest(),
            "supersedes_catalog_id": self.catalog.supersedes_catalog_id,
        }


class _ConstraintRole(StrEnum):
    AVAILABLE = "availableconstraint"
    CONTENT = "contentconstraint"


@dataclass(frozen=True)
class _StesConstraintSnapshot:
    role: _ConstraintRole
    capture_token: str
    source_id: str
    dataflow_id: str
    dataflow_version: str
    constraint_id: str
    constraint_version: str
    valid_from: datetime | None
    editions: frozenset[str]


@dataclass(frozen=True)
class _StesArchiveSummary:
    row_count: int
    column_count: int
    edition_count: int
    first_edition: str
    last_edition: str
    editions: frozenset[str] = field(repr=False)
    observation_keys: frozenset[tuple[str, str]] = field(repr=False)

    def descriptor(self) -> dict[str, int | str]:
        return {
            "column_count": self.column_count,
            "edition_count": self.edition_count,
            "first_edition": self.first_edition,
            "last_edition": self.last_edition,
            "row_count": self.row_count,
        }


@dataclass(frozen=True)
class _ValidatedStesEntry:
    binding: StesSeriesBinding
    data_artifact: _ValidatedSourceArtifact | None = None
    archive_summary: _StesArchiveSummary | None = None

    def descriptor(self) -> dict[str, object]:
        return {
            "archive_summary": (
                None if self.archive_summary is None else self.archive_summary.descriptor()
            ),
            "binding": self.binding.descriptor(),
            "data_artifact": (
                None if self.data_artifact is None else self.data_artifact.descriptor()
            ),
        }


@dataclass(frozen=True)
class _ValidatedStesRegistry:
    entries: tuple[_ValidatedStesEntry, ...]
    support_artifacts: tuple[_ValidatedSourceArtifact, ...]
    ledger_artifacts: tuple[_ValidatedLedgerArtifact, ...]
    catalog_artifacts: tuple[_ValidatedCatalogArtifact, ...]
    active_ledger: EditionAvailabilityLedger

    @property
    def rights_catalogs(self) -> tuple[RightsCatalog, ...]:
        return tuple(artifact.catalog for artifact in self.catalog_artifacts)

    def entry_for(
        self,
        scope: tuple[str, str, str, str, str],
    ) -> _ValidatedStesEntry | None:
        return next((entry for entry in self.entries if entry.binding.scope == scope), None)


def _validate_support_artifact(
    artifact: _ValidatedSourceArtifact,
) -> _StesConstraintSnapshot:
    manifest = artifact.manifest
    source_match = _CONSTRAINT_SOURCE_PATTERN.fullmatch(manifest.source_id)
    if source_match is None:
        raise ValueError("STES support source ID does not identify a constraint capture")
    role = _ConstraintRole(source_match.group(1))
    expected_url = {
        _ConstraintRole.AVAILABLE: _AVAILABLE_CONSTRAINT_URL,
        _ConstraintRole.CONTENT: _CONTENT_CONSTRAINT_URL,
    }[role]
    if (
        manifest.source_kind is not SourceKind.API
        or manifest.publisher != "OECD"
        or manifest.document_family != "oecd-stes-constraint"
        or manifest.media_type != "application/xml"
        or manifest.vintage_semantics is not VintageSemantics.LATEST_ONLY
        or manifest.redistribution.status is not RedistributionStatus.METADATA_ONLY
        or str(manifest.canonical_url) != expected_url
    ):
        raise ValueError("STES availability support manifest differs from its trusted role")
    return _parse_constraint_xml(
        artifact.archive_bytes,
        role=role,
        capture_token=source_match.group(2),
        source_id=manifest.source_id,
    )


def _parse_constraint_xml(
    payload: bytes,
    *,
    role: _ConstraintRole,
    capture_token: str,
    source_id: str,
) -> _StesConstraintSnapshot:
    if b"<!DOCTYPE" in payload.upper() or b"<!ENTITY" in payload.upper():
        raise ValueError("trusted STES constraint XML cannot contain a document type")
    try:
        root = ElementTree.fromstring(payload)
    except ElementTree.ParseError:
        raise ValueError("trusted STES constraint archive is invalid XML") from None
    if _local_name(root.tag) != "Structure":
        raise ValueError("trusted STES constraint XML has an invalid root")
    constraints = tuple(
        element for element in root.iter() if _local_name(element.tag) == "ContentConstraint"
    )
    if len(constraints) != 1:
        raise ValueError("trusted STES XML must contain one content constraint")
    constraint = constraints[0]
    references = tuple(
        element for element in constraint.iter() if _local_name(element.tag) == "Ref"
    )
    if len(references) != 1:
        raise ValueError("trusted STES XML must contain one dataflow reference")
    reference = references[0]
    agency = reference.get("agencyID")
    flow = reference.get("id")
    flow_version = reference.get("version")
    constraint_id = constraint.get("id")
    constraint_version = constraint.get("version")
    if not all((agency, flow, flow_version, constraint_id, constraint_version)):
        raise ValueError("trusted STES constraint identity is incomplete")

    edition_regions = tuple(
        element
        for element in constraint.iter()
        if _local_name(element.tag) == "KeyValue" and element.get("id") == "EDITION"
    )
    if len(edition_regions) != 1:
        raise ValueError("trusted STES XML must contain one edition inventory")
    edition_values = tuple(
        child.text or "" for child in edition_regions[0] if _local_name(child.tag) == "Value"
    )
    editions = frozenset(edition_values)
    if (
        not editions
        or len(editions) != len(edition_values)
        or any(_EDITION_PATTERN.fullmatch(edition) is None for edition in editions)
    ):
        raise ValueError("trusted STES constraint has an invalid edition inventory")

    valid_from_text = constraint.get("validFrom")
    if role is _ConstraintRole.AVAILABLE:
        expected_identity = ("CC", "1.0")
        if valid_from_text is not None:
            raise ValueError("available constraint cannot declare content validFrom")
        valid_from = None
    else:
        expected_identity = (_CONTENT_CONSTRAINT_ID, STES_DATAFLOW_VERSION)
        if valid_from_text is None:
            raise ValueError("content constraint requires validFrom")
        valid_from = _parse_aware_instant(valid_from_text)
    if (
        f"{agency}:{flow}" != STES_DATAFLOW_ID
        or flow_version != STES_DATAFLOW_VERSION
        or (constraint_id, constraint_version) != expected_identity
    ):
        raise ValueError("trusted STES constraint differs from its exact role")
    return _StesConstraintSnapshot(
        role=role,
        capture_token=capture_token,
        source_id=source_id,
        dataflow_id=f"{agency}:{flow}",
        dataflow_version=flow_version,
        constraint_id=constraint_id,
        constraint_version=constraint_version,
        valid_from=valid_from,
        editions=editions,
    )


def _validate_constraint_ledger_join(
    constraint_by_source_id: dict[str, _StesConstraintSnapshot],
    support_artifacts: list[_ValidatedSourceArtifact],
    ledger_artifacts: list[_ValidatedLedgerArtifact],
) -> None:
    manifest_by_id = {
        artifact.manifest.source_id: artifact.manifest for artifact in support_artifacts
    }
    if set(manifest_by_id) != set(constraint_by_source_id):
        raise ValueError("STES support manifests and parsed constraints differ")

    captures: dict[str, dict[_ConstraintRole, _StesConstraintSnapshot]] = {}
    for snapshot in constraint_by_source_id.values():
        roles = captures.setdefault(snapshot.capture_token, {})
        if snapshot.role in roles:
            raise ValueError("STES constraint capture repeats a role")
        roles[snapshot.role] = snapshot

    for roles in captures.values():
        if set(roles) != {_ConstraintRole.AVAILABLE, _ConstraintRole.CONTENT}:
            raise ValueError("STES constraint capture must contain both exact roles")
        available = roles[_ConstraintRole.AVAILABLE]
        content = roles[_ConstraintRole.CONTENT]
        available_manifest = manifest_by_id[available.source_id]
        if available.editions != content.editions:
            raise ValueError("STES constraint pair has inconsistent edition inventories")
        if content.valid_from is None or content.valid_from > available_manifest.retrieved_at:
            raise ValueError("STES content validFrom follows its availability capture")

    used_captures: set[str] = set()
    for artifact in ledger_artifacts:
        ledger = artifact.ledger
        candidates = tuple(
            token
            for token, roles in captures.items()
            if manifest_by_id[roles[_ConstraintRole.AVAILABLE].source_id].retrieved_at
            == ledger.complete_through
            and manifest_by_id[roles[_ConstraintRole.CONTENT].source_id].retrieved_at
            == ledger.captured_at
        )
        if len(candidates) != 1:
            raise ValueError("STES ledger lacks one exact constraint capture pair")
        capture_token = candidates[0]
        used_captures.add(capture_token)
        inventory = captures[capture_token][_ConstraintRole.AVAILABLE].editions
        if {record.edition for record in ledger.editions} != inventory:
            raise ValueError("STES ledger differs from its constraint edition inventory")
        for record in ledger.editions:
            for evidence in record.evidence:
                _validate_constraint_evidence(
                    record.edition,
                    evidence.basis,
                    evidence.asserted_instant,
                    evidence.source_manifest_ids,
                    evidence.constraint_id,
                    evidence.constraint_version,
                    constraint_by_source_id,
                    manifest_by_id,
                )
    if used_captures != set(captures):
        raise ValueError("STES registry contains an unused constraint capture")


def _validate_constraint_evidence(
    edition: str,
    basis: AvailabilityEvidenceBasis,
    asserted_instant: datetime,
    source_manifest_ids: tuple[str, ...],
    constraint_id: str | None,
    constraint_version: str | None,
    constraint_by_source_id: dict[str, _StesConstraintSnapshot],
    manifest_by_id: dict[str, SourceManifest],
) -> None:
    try:
        snapshots = tuple(constraint_by_source_id[source_id] for source_id in source_manifest_ids)
    except KeyError:
        raise ValueError("STES availability evidence has an unknown support source") from None
    if len({snapshot.capture_token for snapshot in snapshots}) != 1:
        raise ValueError("STES availability evidence crosses constraint captures")
    roles = {snapshot.role: snapshot for snapshot in snapshots}
    if basis is AvailabilityEvidenceBasis.SDMX_CONSTRAINT_VALID_FROM:
        if set(roles) != {_ConstraintRole.AVAILABLE, _ConstraintRole.CONTENT}:
            raise ValueError("STES validFrom evidence requires one exact constraint pair")
        content = roles[_ConstraintRole.CONTENT]
        if (
            asserted_instant != content.valid_from
            or constraint_id != content.constraint_id
            or constraint_version != content.constraint_version
        ):
            raise ValueError("STES validFrom evidence differs from its content constraint")
    elif basis is AvailabilityEvidenceBasis.FIRST_OBSERVED_AT:
        if set(roles) != {_ConstraintRole.AVAILABLE} or len(snapshots) != 1:
            raise ValueError("STES first-observed evidence requires one availability constraint")
        available = roles[_ConstraintRole.AVAILABLE]
        if asserted_instant != manifest_by_id[available.source_id].retrieved_at:
            raise ValueError("STES first-observed evidence differs from its capture instant")
    else:
        raise ValueError("STES availability ledger uses an unsupported evidence basis")
    if any(edition not in snapshot.editions for snapshot in snapshots):
        raise ValueError("STES availability evidence omits its asserted edition")


def _parse_aware_instant(value: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        raise ValueError("trusted STES constraint has an invalid instant") from None
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError("trusted STES constraint has an invalid instant")
    return parsed.astimezone(UTC)


def _local_name(tag: str) -> str:
    return tag.rsplit("}", maxsplit=1)[-1]


def _validate_data_manifest(
    manifest: SourceManifest,
    binding: StesSeriesBinding,
    active_ledger: EditionAvailabilityLedger,
    active_catalog_ids: set[str],
) -> None:
    reference = manifest.rights_decision
    flow = _manifest_dataflow_reference(manifest)
    if (
        manifest.source_id != binding.source_id
        or manifest.source_kind is not SourceKind.API
        or manifest.publisher != "OECD"
        or manifest.document_family != binding.document_family
        or manifest.media_type not in {"text/csv", "application/vnd.sdmx.data+csv"}
        or manifest.vintage_semantics is not VintageSemantics.HISTORICAL_ARCHIVE
        or manifest.redistribution.status is not RedistributionStatus.ALLOWED
        or reference is None
        or reference.catalog_id not in active_catalog_ids
        or reference.decision_id != binding.rights_decision_id
        or reference.source_system is not SourceSystem.OECD
        or reference.table_id != "DSD_STES_REVISIONS@DF_STES_REVISIONS"
        or reference.item_id != binding.item_id
        or flow != (active_ledger.dataflow_id, active_ledger.dataflow_version)
    ):
        raise ValueError("STES data manifest differs from its trusted exact-scope binding")


def _validate_archive_scope(
    payload: bytes,
    binding: StesSeriesBinding,
) -> _StesArchiveSummary:
    try:
        text = payload.decode("utf-8-sig")
        reader = csv.reader(io.StringIO(text, newline=""), strict=True)
        header = next(reader)
    except (UnicodeDecodeError, csv.Error, StopIteration):
        raise ValueError("trusted STES archive is not valid bounded CSV") from None
    if (
        not header
        or len(header) > MAX_STES_ARCHIVE_COLUMNS
        or len(header) != len(set(header))
        or any(column not in header for column in _REQUIRED_ARCHIVE_COLUMNS)
    ):
        raise ValueError("trusted STES archive has invalid columns")
    indexes = {column: header.index(column) for column in _REQUIRED_ARCHIVE_COLUMNS}
    expected_scope = dict(
        zip(
            _REQUIRED_ARCHIVE_COLUMNS[:5],
            binding.scope,
            strict=True,
        )
    )
    editions: set[str] = set()
    observation_keys: set[tuple[str, str]] = set()
    row_count = 0
    try:
        for row in reader:
            if not row or all(not value.strip() for value in row):
                continue
            row_count += 1
            if row_count > MAX_STES_ARCHIVE_ROWS or len(row) != len(header):
                raise ValueError("trusted STES archive exceeds its bounded row shape")
            if any(row[indexes[column]] != value for column, value in expected_scope.items()):
                raise ValueError("trusted STES archive contains a neighboring series")
            edition = row[indexes["EDITION"]]
            period = row[indexes["TIME_PERIOD"]]
            raw_value = row[indexes["OBS_VALUE"]]
            if _EDITION_PATTERN.fullmatch(edition) is None or (
                _MONTHLY_PERIOD_PATTERN.fullmatch(period) is None
            ):
                raise ValueError("trusted STES archive has invalid edition or period codes")
            observation_key = (edition, period)
            if observation_key in observation_keys:
                raise ValueError("trusted STES archive repeats an edition-period observation")
            if (
                raw_value != raw_value.strip()
                or len(raw_value) > 128
                or _PLAIN_DECIMAL_PATTERN.fullmatch(raw_value) is None
            ):
                raise ValueError("trusted STES archive contains an invalid observation value")
            observation_keys.add(observation_key)
            editions.add(edition)
    except csv.Error:
        raise ValueError("trusted STES archive is not valid bounded CSV") from None
    if not row_count or not editions:
        raise ValueError("trusted STES archive contains no observations")
    return _StesArchiveSummary(
        row_count=row_count,
        column_count=len(header),
        edition_count=len(editions),
        first_edition=min(editions),
        last_edition=max(editions),
        editions=frozenset(editions),
        observation_keys=frozenset(observation_keys),
    )


def _validate_archive_ledger_join(
    summary: _StesArchiveSummary,
    active_ledger: EditionAvailabilityLedger,
) -> None:
    ledger_editions = frozenset(record.edition for record in active_ledger.editions)
    if not summary.editions.issubset(ledger_editions) or summary.last_edition != max(
        ledger_editions
    ):
        raise ValueError("trusted STES archive differs from the active ledger edition scope")


def _validate_ledger_chain(
    ledger_by_id: dict[str, _ValidatedLedgerArtifact],
    *,
    active_ledger_id: str,
) -> EditionAvailabilityLedger:
    if not ledger_by_id:
        raise ValueError("STES registry has no availability ledger")
    for artifact in ledger_by_id.values():
        ledger = artifact.ledger
        if (
            ledger.dataflow_id != STES_DATAFLOW_ID
            or ledger.dataflow_version != STES_DATAFLOW_VERSION
            or ledger.cutoff_timezone != "Asia/Seoul"
            or ledger.cutoff_semantics != "inclusive_end_of_day"
        ):
            raise ValueError("STES ledger differs from the trusted cutoff/dataflow contract")

    visited: set[str] = set()
    current_id: str | None = active_ledger_id
    while current_id is not None:
        if current_id in visited:
            raise ValueError("STES availability ledger chain contains a cycle")
        try:
            successor = ledger_by_id[current_id].ledger
        except KeyError:
            raise ValueError("STES ledger chain has a missing predecessor") from None
        visited.add(current_id)
        predecessor_id = successor.supersedes_ledger_id
        if predecessor_id is not None:
            try:
                predecessor = ledger_by_id[predecessor_id].ledger
            except KeyError:
                raise ValueError("STES ledger chain has a missing predecessor") from None
            _validate_ledger_successor(predecessor, successor)
        current_id = predecessor_id
    if visited != set(ledger_by_id):
        raise ValueError("STES registry must contain one connected active ledger chain")
    return ledger_by_id[active_ledger_id].ledger


def _validate_ledger_successor(
    predecessor: EditionAvailabilityLedger,
    successor: EditionAvailabilityLedger,
) -> None:
    if (
        predecessor.dataflow_id != successor.dataflow_id
        or predecessor.dataflow_version != successor.dataflow_version
        or predecessor.cutoff_timezone != successor.cutoff_timezone
        or predecessor.cutoff_semantics != successor.cutoff_semantics
        or predecessor.generated_at > successor.generated_at
        or predecessor.captured_at > successor.captured_at
        or predecessor.complete_through > successor.complete_through
    ):
        raise ValueError("STES successor ledger rewrites its predecessor contract")
    successor_by_edition = {record.edition: record for record in successor.editions}
    if any(successor_by_edition.get(record.edition) != record for record in predecessor.editions):
        raise ValueError("STES successor ledger must preserve every predecessor edition")


def _validate_catalog_chain(
    catalog_by_id: dict[str, _ValidatedCatalogArtifact],
) -> None:
    if not catalog_by_id:
        raise ValueError("STES registry has no rights catalog")
    superseded_ids: set[str] = set()
    for artifact in catalog_by_id.values():
        predecessor = artifact.catalog.supersedes_catalog_id
        if predecessor is not None:
            if predecessor not in catalog_by_id:
                raise ValueError("STES rights catalog chain has a missing predecessor")
            superseded_ids.add(predecessor)
    active_ids = set(catalog_by_id) - superseded_ids
    if len(active_ids) != 1:
        raise ValueError("STES registry must have one active rights catalog")
    visited: set[str] = set()
    current_id: str | None = next(iter(active_ids))
    while current_id is not None:
        if current_id in visited:
            raise ValueError("STES rights catalog chain contains a cycle")
        successor = catalog_by_id[current_id].catalog
        visited.add(current_id)
        predecessor_id = successor.supersedes_catalog_id
        if predecessor_id is not None:
            predecessor = catalog_by_id[predecessor_id].catalog
            _validate_catalog_successor(predecessor, successor)
        current_id = predecessor_id
    if visited != set(catalog_by_id):
        raise ValueError("STES registry must contain one connected rights catalog chain")


def _validate_catalog_successor(
    predecessor: RightsCatalog,
    successor: RightsCatalog,
) -> None:
    if (
        predecessor.recorded_at > successor.recorded_at
        or predecessor.project_use_profile is not successor.project_use_profile
    ):
        raise ValueError("STES successor rights catalog rewrites its predecessor contract")
    successor_instruments = {
        instrument.instrument_id: instrument for instrument in successor.instruments
    }
    successor_decisions = {decision.decision_id: decision for decision in successor.decisions}
    if any(
        successor_instruments.get(instrument.instrument_id) != instrument
        for instrument in predecessor.instruments
    ) or any(
        successor_decisions.get(decision.decision_id) != decision
        for decision in predecessor.decisions
    ):
        raise ValueError("STES successor rights catalog must be append-only")


def _validate_unavailable_rights_policy(
    entries: tuple[_ValidatedStesEntry, ...],
    catalog_artifacts: list[_ValidatedCatalogArtifact],
    active_catalog_ids: set[str],
) -> None:
    unavailable_items = {
        entry.binding.item_id
        for entry in entries
        if entry.binding.raw_evidence is RawEvidenceAvailability.UNAVAILABLE
    }
    for artifact in catalog_artifacts:
        if artifact.catalog.catalog_id not in active_catalog_ids:
            continue
        for decision in artifact.catalog.decisions:
            if (
                decision.source_system is SourceSystem.OECD
                and decision.table_id == "DSD_STES_REVISIONS@DF_STES_REVISIONS"
                and decision.item_id in unavailable_items
                and decision.decision_state is RedistributionStatus.ALLOWED
            ):
                raise ValueError(
                    "STES unavailable policy conflicts with an active allowed decision"
                )


def _parse_json_model[ModelT: BaseModel](payload: bytes, model: type[ModelT]) -> ModelT:
    try:
        text = payload.decode("utf-8")
        document = json.loads(
            text,
            object_pairs_hook=_unique_object,
            parse_constant=_reject_json_constant,
        )
        if not isinstance(document, dict):
            raise _RegistryPayloadError("trusted STES JSON must contain one object")
        return model.model_validate(document)
    except (RecursionError, UnicodeDecodeError, ValidationError, ValueError):
        raise _RegistryPayloadError("trusted STES JSON is invalid") from None


def _unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise _DuplicateJsonKey(key)
        result[key] = value
    return result


def _reject_json_constant(value: str) -> object:
    raise _InvalidJsonConstant(value)


def _require_exact_bytes(payload: bytes, *, max_bytes: int, label: str) -> None:
    if type(payload) is not bytes:
        raise ValueError(f"{label} must be exact immutable bytes")
    if not 0 < len(payload) <= max_bytes:
        raise ValueError(f"{label} exceeds its bounded size")


def _require_exact_tuple(value: object, label: str) -> None:
    if type(value) is not tuple:
        raise ValueError(f"{label} must be an immutable tuple")


def _unique_models(
    artifacts: list[object],
    *,
    attribute: str,
    nested_id: str,
    label: str,
) -> dict[str, object]:
    indexed: dict[str, object] = {}
    for artifact in artifacts:
        model = getattr(artifact, attribute)
        item_id = getattr(model, nested_id)
        if item_id in indexed:
            raise ValueError(f"{label} must be unique")
        indexed[item_id] = artifact
    return indexed


def _load_source_artifact(
    root: Path,
    location: StesArtifactLocation,
) -> StesSourceArtifact:
    if type(location) is not StesArtifactLocation:
        raise ValueError("trusted STES artifact location has an invalid type")
    manifest_bytes, manifest_path = _read_trusted_file(
        root,
        location.manifest_path,
        required_root=root / "data" / "manifests",
        suffix=".json",
        max_bytes=MAX_STES_METADATA_BYTES,
        label="STES manifest",
    )
    archive_suffix = {
        StesArtifactRole.DATA_ARCHIVE: ".csv",
        StesArtifactRole.AVAILABILITY_SUPPORT: ".xml",
    }.get(location.role)
    if archive_suffix is None:
        raise ValueError("trusted STES artifact location has an invalid role")
    archive_bytes, archive_path = _read_trusted_file(
        root,
        location.archive_path,
        required_root=root / "data" / "archive" / "oecd-stes",
        suffix=archive_suffix,
        max_bytes=(
            MAX_STES_DATA_ARCHIVE_BYTES
            if location.role is StesArtifactRole.DATA_ARCHIVE
            else MAX_STES_SUPPORT_ARCHIVE_BYTES
        ),
        label="STES archive",
    )
    manifest = _parse_json_model(manifest_bytes, SourceManifest)
    if manifest_path.stem != manifest.source_id or archive_path.stem != manifest.source_id:
        raise ValueError("STES manifest/archive filenames must equal the source ID")
    return StesSourceArtifact(
        role=location.role,
        manifest=manifest,
        manifest_bytes=manifest_bytes,
        archive_bytes=archive_bytes,
    )


def _load_ledger_artifact(root: Path, relative_path: Path) -> StesLedgerArtifact:
    payload, path = _read_trusted_file(
        root,
        relative_path,
        required_root=root / "data" / "availability",
        suffix=".json",
        max_bytes=MAX_STES_METADATA_BYTES,
        label="STES availability ledger",
    )
    ledger = _parse_json_model(payload, EditionAvailabilityLedger)
    if path.stem != ledger.ledger_id:
        raise ValueError("STES ledger filename must equal its ledger ID")
    return StesLedgerArtifact(ledger=ledger, ledger_bytes=payload)


def _load_catalog_artifact(root: Path, relative_path: Path) -> StesCatalogArtifact:
    payload, path = _read_trusted_file(
        root,
        relative_path,
        required_root=root / "data" / "rights",
        suffix=".json",
        max_bytes=MAX_STES_METADATA_BYTES,
        label="STES rights catalog",
    )
    catalog = _parse_json_model(payload, RightsCatalog)
    if path.stem != catalog.catalog_id:
        raise ValueError("STES rights catalog filename must equal its catalog ID")
    return StesCatalogArtifact(catalog=catalog, catalog_bytes=payload)


def _read_trusted_file(
    root: Path,
    relative_path: Path,
    *,
    required_root: Path,
    suffix: str,
    max_bytes: int,
    label: str,
) -> tuple[bytes, Path]:
    path = _resolve_trusted_path(
        root,
        relative_path,
        required_root=required_root,
    )
    if path.suffix != suffix:
        raise ValueError(f"trusted {label} has an invalid suffix")
    if not path.is_file():
        raise StesRegistryLoadError(f"the trusted {label} does not exist")
    try:
        byte_size = path.stat().st_size
    except OSError:
        raise StesRegistryLoadError(f"the trusted {label} could not be inspected") from None
    if not 0 < byte_size <= max_bytes:
        raise ValueError(f"trusted {label} exceeds its bounded size")
    try:
        payload = path.read_bytes()
    except OSError:
        raise StesRegistryLoadError(f"the trusted {label} could not be read") from None
    if len(payload) != byte_size:
        raise ValueError(f"trusted {label} changed while it was read")
    return payload, path


def _resolve_trusted_path(
    root: Path,
    relative_path: Path,
    *,
    required_root: Path,
) -> Path:
    if relative_path.is_absolute():
        raise ValueError("trusted STES paths must be repository-relative")
    try:
        path = (root / relative_path).resolve(strict=False)
        confined_root = required_root.resolve(strict=True)
    except (OSError, RuntimeError):
        raise StesRegistryLoadError(
            "the trusted STES artifact root could not be resolved"
        ) from None
    if not path.is_relative_to(confined_root):
        raise ValueError("trusted STES path escapes its approved repository root")
    return path
