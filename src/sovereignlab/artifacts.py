"""Loading and digest helpers shared by the committed evidence registries."""

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path

from sovereignlab.schemas import EditionAvailabilityLedger, RightsCatalog, SourceManifest


def sha256_hex(payload: bytes) -> str:
    """Return the lowercase SHA-256 hex digest of exact bytes."""

    return hashlib.sha256(payload).hexdigest()


def canonical_sha256(descriptor: object) -> str:
    """Hash a registry descriptor in its canonical sorted, compact JSON form."""

    canonical = json.dumps(descriptor, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
    return sha256_hex(canonical.encode("utf-8"))


@dataclass(frozen=True)
class SourceArtifact:
    """One source manifest with its exact manifest and archive bytes."""

    manifest: SourceManifest
    manifest_bytes: bytes = field(repr=False, compare=False)
    archive_bytes: bytes = field(repr=False, compare=False)


@dataclass(frozen=True)
class LedgerArtifact:
    """One edition-availability ledger with its exact committed bytes."""

    ledger: EditionAvailabilityLedger
    ledger_bytes: bytes = field(repr=False, compare=False)


@dataclass(frozen=True)
class CatalogArtifact:
    """One rights catalog with its exact committed bytes."""

    catalog: RightsCatalog
    catalog_bytes: bytes = field(repr=False, compare=False)


def load_source_artifact(root: Path, manifest_path: Path, archive_path: Path) -> SourceArtifact:
    """Read one manifest/archive pair and verify the archive against its manifest."""

    manifest_bytes = (root / manifest_path).read_bytes()
    manifest = SourceManifest.model_validate_json(manifest_bytes)
    archive_bytes = (root / archive_path).read_bytes()
    if manifest_path.stem != manifest.source_id or archive_path.stem != manifest.source_id:
        raise ValueError(f"{manifest_path} and {archive_path} must be named after the source ID")
    if (
        len(archive_bytes) != manifest.byte_size
        or sha256_hex(archive_bytes) != manifest.content_sha256
    ):
        raise ValueError(f"{archive_path} does not match its manifest")
    return SourceArtifact(
        manifest=manifest,
        manifest_bytes=manifest_bytes,
        archive_bytes=archive_bytes,
    )


def load_ledger_artifact(root: Path, path: Path) -> LedgerArtifact:
    """Read one committed availability ledger."""

    payload = (root / path).read_bytes()
    ledger = EditionAvailabilityLedger.model_validate_json(payload)
    if path.stem != ledger.ledger_id:
        raise ValueError(f"{path} must be named after its ledger ID")
    return LedgerArtifact(ledger=ledger, ledger_bytes=payload)


def load_catalog_artifact(root: Path, path: Path) -> CatalogArtifact:
    """Read one committed rights catalog."""

    payload = (root / path).read_bytes()
    catalog = RightsCatalog.model_validate_json(payload)
    if path.stem != catalog.catalog_id:
        raise ValueError(f"{path} must be named after its catalog ID")
    return CatalogArtifact(catalog=catalog, catalog_bytes=payload)
