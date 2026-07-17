"""Weekly append-only OECD metadata and approved ECOS series capture."""

import hashlib
import json
import re
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, date, datetime
from pathlib import Path
from urllib.parse import quote
from xml.etree import ElementTree

import httpx
from pydantic import SecretStr

from sovereignlab.schemas import (
    AvailabilityAssertion,
    AvailabilityEvidence,
    AvailabilityEvidenceBasis,
    BenchmarkBundle,
    EditionAvailabilityLedger,
    EditionAvailabilityRecord,
    EditionResolutionStatus,
    LanguageCode,
    PublicationDateBasis,
    RedistributionPolicy,
    RedistributionStatus,
    RightsCatalog,
    SourceKind,
    SourceManifest,
    SourceRightsReference,
    SourceSystem,
    VintageSemantics,
)

OECD_DATAFLOW_ID = "OECD.SDD.STES:DSD_STES_REVISIONS@DF_STES_REVISIONS"
OECD_DATAFLOW_VERSION = "4.0"
OECD_CONSTRAINT_ID = "CR_A_DSD_STES_REVISIONS@DF_STES_REVISIONS"
OECD_AVAILABLE_CONSTRAINT_URL = (
    "https://sdmx.oecd.org/public/rest/availableconstraint/"
    "OECD.SDD.STES,DSD_STES_REVISIONS%40DF_STES_REVISIONS,4.0/"
    "all/all/EDITION?mode=exact"
)
OECD_CONTENT_CONSTRAINT_URL = (
    "https://sdmx.oecd.org/public/rest/contentconstraint/OECD.SDD.STES/"
    "CR_A_DSD_STES_REVISIONS%40DF_STES_REVISIONS/4.0?references=none"
)
RIGHTS_CATALOG_PATH = Path("data/rights/kor-rtd-rights-2026-07-16.json")
_LEDGER_PREFIX = "oecd-stes-ledger-"
_AVAILABLE_PREFIX = "oecd-stes-availableconstraint-"
_CONTENT_PREFIX = "oecd-stes-contentconstraint-"
_EDITION_PATTERN = re.compile(r"^[0-9]{4}(0[1-9]|1[0-2])$")


@dataclass(frozen=True)
class _RetrievedResource:
    public_url: str
    body: bytes
    retrieved_at: datetime
    media_type: str


@dataclass(frozen=True)
class _ConstraintSnapshot:
    dataflow_id: str
    dataflow_version: str
    constraint_id: str
    constraint_version: str
    valid_from: datetime | None
    editions: tuple[str, ...]


@dataclass(frozen=True)
class _EcosSeriesSpec:
    table_id: str
    item_id: str
    cycle: str
    start_period: str
    title: str
    decision_id: str


@dataclass(frozen=True)
class _PendingArtifact:
    path: Path
    body: bytes


@dataclass(frozen=True)
class HarvestSummary:
    """Non-secret paths and scope emitted by one capture run."""

    capture_token: str
    ledger_path: str
    manifest_paths: tuple[str, ...]
    archive_paths: tuple[str, ...]
    ecos_series_captured: tuple[str, ...]
    ecos_skipped_missing_key: bool


_ECOS_SERIES = (
    _EcosSeriesSpec(
        table_id="200Y108",
        item_id="10601",
        cycle="Q",
        start_period="1960Q1",
        title="국내총생산에 대한 지출(계절조정, 실질, 분기)",
        decision_id="ecos-200y108-10601-rights-v1",
    ),
    _EcosSeriesSpec(
        table_id="301Y017",
        item_id="SA000",
        cycle="M",
        start_period="198001",
        title="경상수지(계절조정)",
        decision_id="ecos-301y017-sa000-rights-v1",
    ),
)


def run_weekly_capture(
    repository_root: Path,
    *,
    client: httpx.Client,
    ecos_api_key: SecretStr | None = None,
    rights_catalog: RightsCatalog | None = None,
    now: Callable[[], datetime] = lambda: datetime.now(UTC),
) -> HarvestSummary:
    """Fetch, validate, and append one preflighted KOR-RTD capture set."""

    available = _fetch(
        client,
        OECD_AVAILABLE_CONSTRAINT_URL,
        public_url=OECD_AVAILABLE_CONSTRAINT_URL,
        media_type="application/xml",
        now=now,
    )
    content = _fetch(
        client,
        OECD_CONTENT_CONSTRAINT_URL,
        public_url=OECD_CONTENT_CONSTRAINT_URL,
        media_type="application/xml",
        now=now,
    )
    available_snapshot = _parse_constraint(available.body, require_valid_from=False)
    content_snapshot = _parse_constraint(content.body, require_valid_from=True)
    _validate_constraint_join(available_snapshot, content_snapshot)

    ecos_resources: list[tuple[_EcosSeriesSpec, _RetrievedResource]] = []
    key = ecos_api_key.get_secret_value().strip() if ecos_api_key is not None else ""
    capture_reference = max(available.retrieved_at, content.retrieved_at)
    if key:
        if rights_catalog is None:
            raise ValueError("ECOS capture requires the committed rights catalog")
        for spec in _ECOS_SERIES:
            request_url, public_url = _ecos_urls(spec, key, capture_reference.date())
            resource = _fetch(
                client,
                request_url,
                public_url=public_url,
                media_type="application/json",
                now=now,
            )
            _validate_ecos_response(resource.body, spec)
            ecos_resources.append((spec, resource))

    generated_at = _canonical_now(now)
    constraint_captured_at = max(available.retrieved_at, content.retrieved_at)
    token = _timestamp_token(constraint_captured_at)
    available_manifest = _oecd_manifest(
        resource=available,
        source_id=f"{_AVAILABLE_PREFIX}{token}",
        title="OECD STES exact edition availability constraint",
        token=token,
    )
    content_manifest = _oecd_manifest(
        resource=content,
        source_id=f"{_CONTENT_PREFIX}{token}",
        title="OECD STES content constraint with validFrom",
        token=token,
    )
    ledger_path = repository_root / "data" / "availability" / f"{_LEDGER_PREFIX}{token}.json"
    if ledger_path.exists():
        raise FileExistsError(f"append-only capture refuses existing path: {ledger_path}")
    previous = _latest_ledger(repository_root)
    if previous is not None:
        _validate_previous_capture(repository_root, previous)
    ledger = _build_ledger(
        snapshot=content_snapshot,
        inventory=available_snapshot.editions,
        available_manifest=available_manifest,
        content_manifest=content_manifest,
        captured_at=constraint_captured_at,
        generated_at=generated_at,
        previous=previous,
    )

    manifests = [available_manifest, content_manifest]
    artifacts = [
        _raw_artifact(repository_root, available_manifest, available.body, suffix=".xml"),
        _raw_artifact(repository_root, content_manifest, content.body, suffix=".xml"),
    ]
    for spec, resource in ecos_resources:
        assert rights_catalog is not None
        manifest = _ecos_manifest(spec, resource, rights_catalog.catalog_id, token)
        BenchmarkBundle(
            sources=(manifest,),
            records=(),
            rights_catalogs=(rights_catalog,),
        )
        manifests.append(manifest)
        artifacts.append(_raw_artifact(repository_root, manifest, resource.body, suffix=".json"))

    current_by_id = {manifest.source_id: manifest for manifest in manifests}
    evidence_manifests = _load_evidence_manifests(repository_root, ledger, current_by_id)
    BenchmarkBundle(
        sources=tuple(evidence_manifests.values()),
        records=(),
        availability_ledgers=(ledger,),
    )
    for manifest in manifests:
        artifacts.append(_manifest_artifact(repository_root, manifest))
    ledger_path = repository_root / "data" / "availability" / f"{ledger.ledger_id}.json"
    artifacts.append(_json_artifact(ledger_path, ledger.model_dump(mode="json", exclude_none=True)))
    _write_append_only(artifacts)

    return HarvestSummary(
        capture_token=token,
        ledger_path=str(ledger_path.relative_to(repository_root)),
        manifest_paths=tuple(
            str(_manifest_path(repository_root, manifest.source_id).relative_to(repository_root))
            for manifest in manifests
        ),
        archive_paths=tuple(
            str(item.path.relative_to(repository_root)) for item in artifacts[: len(manifests)]
        ),
        ecos_series_captured=tuple(f"{spec.table_id}/{spec.item_id}" for spec, _ in ecos_resources),
        ecos_skipped_missing_key=not bool(key),
    )


def load_rights_catalog(repository_root: Path) -> RightsCatalog:
    """Load the committed owner-approved catalog used by ECOS manifests."""

    path = repository_root / RIGHTS_CATALOG_PATH
    return RightsCatalog.model_validate_json(path.read_text(encoding="utf-8"))


def _fetch(
    client: httpx.Client,
    request_url: str,
    *,
    public_url: str,
    media_type: str,
    now: Callable[[], datetime],
) -> _RetrievedResource:
    response = client.get(request_url, headers={"Accept": media_type})
    response.raise_for_status()
    if not response.content:
        raise ValueError(f"empty response from {public_url}")
    return _RetrievedResource(
        public_url=public_url,
        body=response.content,
        retrieved_at=_canonical_now(now),
        media_type=media_type,
    )


def _parse_constraint(payload: bytes, *, require_valid_from: bool) -> _ConstraintSnapshot:
    try:
        root = ElementTree.fromstring(payload)
    except ElementTree.ParseError as error:
        raise ValueError("invalid SDMX constraint XML") from error
    constraints = [
        element for element in root.iter() if _local_name(element.tag) == "ContentConstraint"
    ]
    if len(constraints) != 1:
        raise ValueError("constraint response must contain exactly one ContentConstraint")
    constraint = constraints[0]
    references = [element for element in constraint.iter() if _local_name(element.tag) == "Ref"]
    if len(references) != 1:
        raise ValueError("constraint response must contain exactly one dataflow Ref")
    reference = references[0]
    agency = reference.get("agencyID")
    flow = reference.get("id")
    flow_version = reference.get("version")
    constraint_id = constraint.get("id")
    constraint_version = constraint.get("version")
    if not all((agency, flow, flow_version, constraint_id, constraint_version)):
        raise ValueError("constraint identity is incomplete")

    edition_regions = [
        element
        for element in constraint.iter()
        if _local_name(element.tag) == "KeyValue" and element.get("id") == "EDITION"
    ]
    if len(edition_regions) != 1:
        raise ValueError("constraint response must contain exactly one EDITION region")
    editions = tuple(
        child.text or "" for child in edition_regions[0] if _local_name(child.tag) == "Value"
    )
    if not editions or len(editions) != len(set(editions)):
        raise ValueError("constraint edition inventory must be non-empty and unique")
    if any(_EDITION_PATTERN.fullmatch(edition) is None for edition in editions):
        raise ValueError("constraint contains an invalid edition code")

    valid_from_text = constraint.get("validFrom")
    if require_valid_from and valid_from_text is None:
        raise ValueError("content constraint requires validFrom")
    valid_from = _parse_instant(valid_from_text) if valid_from_text is not None else None
    return _ConstraintSnapshot(
        dataflow_id=f"{agency}:{flow}",
        dataflow_version=flow_version,
        constraint_id=constraint_id,
        constraint_version=constraint_version,
        valid_from=valid_from,
        editions=tuple(sorted(editions)),
    )


def _validate_constraint_join(
    available: _ConstraintSnapshot,
    content: _ConstraintSnapshot,
) -> None:
    if available.dataflow_id != OECD_DATAFLOW_ID or content.dataflow_id != OECD_DATAFLOW_ID:
        raise ValueError("constraint dataflow does not match the approved STES flow")
    if (
        available.dataflow_version != OECD_DATAFLOW_VERSION
        or content.dataflow_version != OECD_DATAFLOW_VERSION
    ):
        raise ValueError("constraint dataflow version does not match the approved STES version")
    if (
        content.constraint_id != OECD_CONSTRAINT_ID
        or content.constraint_version != OECD_DATAFLOW_VERSION
    ):
        raise ValueError("content constraint identity does not match the approved STES constraint")
    if available.editions != content.editions:
        raise ValueError("availability and content constraint edition inventories differ")


def _build_ledger(
    *,
    snapshot: _ConstraintSnapshot,
    inventory: tuple[str, ...],
    available_manifest: SourceManifest,
    content_manifest: SourceManifest,
    captured_at: datetime,
    generated_at: datetime,
    previous: EditionAvailabilityLedger | None,
) -> EditionAvailabilityLedger:
    valid_from = snapshot.valid_from
    if valid_from is None or valid_from > available_manifest.retrieved_at:
        raise ValueError("content constraint validFrom cannot follow the availability capture")
    records: dict[str, EditionAvailabilityRecord]
    if previous is None:
        records = {
            edition: EditionAvailabilityRecord(
                edition=edition,
                status=EditionResolutionStatus.UNRESOLVED,
            )
            for edition in inventory
        }
        latest = max(inventory)
        records[latest] = _first_resolved_record(
            latest,
            valid_from,
            available_manifest,
            content_manifest,
        )
    else:
        if (
            previous.dataflow_id != snapshot.dataflow_id
            or previous.dataflow_version != snapshot.dataflow_version
        ):
            raise ValueError("previous ledger describes a different dataflow")
        previous_editions = {record.edition for record in previous.editions}
        current_editions = set(inventory)
        if not previous_editions.issubset(current_editions):
            raise ValueError("edition inventory deletion invalidates monotonic capture history")
        records = {record.edition: record for record in previous.editions}
        previous_manifest_id = _previous_available_manifest_id(previous)
        for edition in sorted(current_editions - previous_editions):
            records[edition] = _newly_observed_record(
                edition=edition,
                valid_from=valid_from,
                available_manifest=available_manifest,
                content_manifest=content_manifest,
                previous=previous,
                previous_manifest_id=previous_manifest_id,
            )

    return EditionAvailabilityLedger(
        ledger_id=f"{_LEDGER_PREFIX}{_timestamp_token(captured_at)}",
        dataflow_id=snapshot.dataflow_id,
        dataflow_version=snapshot.dataflow_version,
        generated_at=generated_at,
        captured_at=captured_at,
        complete_through=available_manifest.retrieved_at,
        cutoff_timezone="Asia/Seoul",
        supersedes_ledger_id=previous.ledger_id if previous is not None else None,
        editions=tuple(records[edition] for edition in sorted(records)),
    )


def _first_resolved_record(
    edition: str,
    valid_from: datetime,
    available_manifest: SourceManifest,
    content_manifest: SourceManifest,
) -> EditionAvailabilityRecord:
    return EditionAvailabilityRecord(
        edition=edition,
        status=EditionResolutionStatus.RESOLVED,
        available_by=valid_from,
        evidence=(
            AvailabilityEvidence(
                basis=AvailabilityEvidenceBasis.SDMX_CONSTRAINT_VALID_FROM,
                supports=AvailabilityAssertion.AVAILABLE_BY,
                asserted_instant=valid_from,
                source_manifest_ids=(available_manifest.source_id, content_manifest.source_id),
                constraint_id=OECD_CONSTRAINT_ID,
                constraint_version=OECD_DATAFLOW_VERSION,
            ),
            AvailabilityEvidence(
                basis=AvailabilityEvidenceBasis.FIRST_OBSERVED_AT,
                supports=AvailabilityAssertion.AVAILABLE_BY,
                asserted_instant=available_manifest.retrieved_at,
                source_manifest_ids=(available_manifest.source_id,),
            ),
        ),
    )


def _newly_observed_record(
    *,
    edition: str,
    valid_from: datetime,
    available_manifest: SourceManifest,
    content_manifest: SourceManifest,
    previous: EditionAvailabilityLedger,
    previous_manifest_id: str,
) -> EditionAvailabilityRecord:
    available_evidence = [
        AvailabilityEvidence(
            basis=AvailabilityEvidenceBasis.FIRST_OBSERVED_AT,
            supports=AvailabilityAssertion.AVAILABLE_BY,
            asserted_instant=available_manifest.retrieved_at,
            source_manifest_ids=(available_manifest.source_id,),
        )
    ]
    available_by = available_manifest.retrieved_at
    if previous.complete_through < valid_from <= available_manifest.retrieved_at:
        available_by = valid_from
        available_evidence.append(
            AvailabilityEvidence(
                basis=AvailabilityEvidenceBasis.SDMX_CONSTRAINT_VALID_FROM,
                supports=AvailabilityAssertion.AVAILABLE_BY,
                asserted_instant=valid_from,
                source_manifest_ids=(available_manifest.source_id, content_manifest.source_id),
                constraint_id=OECD_CONSTRAINT_ID,
                constraint_version=OECD_DATAFLOW_VERSION,
            )
        )
    return EditionAvailabilityRecord(
        edition=edition,
        status=EditionResolutionStatus.RESOLVED,
        available_by=available_by,
        last_absent_at=previous.complete_through,
        evidence=(
            *available_evidence,
            AvailabilityEvidence(
                basis=AvailabilityEvidenceBasis.FIRST_OBSERVED_AT,
                supports=AvailabilityAssertion.LAST_ABSENT_AT,
                asserted_instant=previous.complete_through,
                source_manifest_ids=(previous_manifest_id,),
            ),
        ),
    )


def _oecd_manifest(
    *,
    resource: _RetrievedResource,
    source_id: str,
    title: str,
    token: str,
) -> SourceManifest:
    return SourceManifest(
        source_id=source_id,
        source_kind=SourceKind.API,
        publisher="OECD",
        title=title,
        document_family="oecd-stes-constraint",
        language=LanguageCode.UNDETERMINED,
        published_on=resource.retrieved_at.date(),
        publication_date_basis=PublicationDateBasis.RETRIEVAL_DATE_FALLBACK,
        publication_date_notes=(
            "Dynamic constraint bytes; retrieval date is the earliest defensible publication date "
            "for this exact capture."
        ),
        retrieved_at=resource.retrieved_at,
        canonical_url=resource.public_url,
        media_type=resource.media_type,
        content_sha256=hashlib.sha256(resource.body).hexdigest(),
        byte_size=len(resource.body),
        redistribution=RedistributionPolicy(
            status=RedistributionStatus.METADATA_ONLY,
            notes=(
                "Owner-approved OECD interim ruling permits metadata publication only; this "
                "artifact is constraint metadata and contains no observations."
            ),
        ),
        release_label=f"Append-only constraint capture {token}",
    )


def _ecos_manifest(
    spec: _EcosSeriesSpec,
    resource: _RetrievedResource,
    catalog_id: str,
    token: str,
) -> SourceManifest:
    return SourceManifest(
        source_id=f"ecos-{spec.table_id.lower()}-{spec.item_id.lower()}-{token}",
        source_kind=SourceKind.API,
        publisher="한국은행",
        title=spec.title,
        document_family=f"ecos-{spec.table_id.lower()}-{spec.item_id.lower()}",
        language=LanguageCode.KOREAN,
        published_on=resource.retrieved_at.date(),
        publication_date_basis=PublicationDateBasis.RETRIEVAL_DATE_FALLBACK,
        publication_date_notes=(
            "ECOS is latest-only; retrieval date is the earliest defensible date for these exact "
            "response bytes."
        ),
        retrieved_at=resource.retrieved_at,
        canonical_url=resource.public_url,
        media_type=resource.media_type,
        content_sha256=hashlib.sha256(resource.body).hexdigest(),
        byte_size=len(resource.body),
        redistribution=RedistributionPolicy(
            status=RedistributionStatus.ALLOWED,
            license_name="ECOS Statistics Information Use Guide",
            license_url="https://ecos.bok.or.kr/",
            notes="Attributed Bank of Korea-produced series approved in ADR 0004.",
        ),
        rights_decision=SourceRightsReference(
            catalog_id=catalog_id,
            decision_id=spec.decision_id,
            source_system=SourceSystem.ECOS,
            table_id=spec.table_id,
            item_id=spec.item_id,
        ),
        vintage_semantics=VintageSemantics.LATEST_ONLY,
        release_label=f"Weekly forward capture {token}",
    )


def _ecos_urls(spec: _EcosSeriesSpec, api_key: str, captured_on: date) -> tuple[str, str]:
    end_period = _ecos_end_period(spec.cycle, captured_on)
    tail = (
        f"json/kr/1/1000/{spec.table_id}/{spec.cycle}/"
        f"{spec.start_period}/{end_period}/{spec.item_id}"
    )
    request_url = f"https://ecos.bok.or.kr/api/StatisticSearch/{quote(api_key, safe='')}/{tail}"
    public_url = f"https://ecos.bok.or.kr/api/StatisticSearch/%7Bapi-key%7D/{tail}"
    return request_url, public_url


def _ecos_end_period(cycle: str, captured_on: date) -> str:
    if cycle == "Q":
        quarter = (captured_on.month - 1) // 3 + 1
        return f"{captured_on.year}Q{quarter}"
    if cycle == "M":
        return f"{captured_on.year}{captured_on.month:02d}"
    raise ValueError(f"unsupported ECOS cycle: {cycle}")


def _validate_ecos_response(payload: bytes, spec: _EcosSeriesSpec) -> None:
    try:
        document = json.loads(payload)
        result = document["StatisticSearch"]
        total = result["list_total_count"]
        rows = result["row"]
    except (KeyError, TypeError, json.JSONDecodeError) as error:
        raise ValueError("invalid ECOS StatisticSearch response") from error
    if not isinstance(total, int) or not isinstance(rows, list) or total != len(rows) or not rows:
        raise ValueError("ECOS response is empty, truncated, or has an invalid row count")
    if total > 1000:
        raise ValueError("ECOS response exceeds the single-page capture contract")
    if any(
        not isinstance(row, dict)
        or row.get("STAT_CODE") != spec.table_id
        or row.get("ITEM_CODE1") != spec.item_id
        for row in rows
    ):
        raise ValueError("ECOS response contains rows outside the approved series scope")


def _latest_ledger(repository_root: Path) -> EditionAvailabilityLedger | None:
    directory = repository_root / "data" / "availability"
    ledgers = [
        EditionAvailabilityLedger.model_validate_json(path.read_text(encoding="utf-8"))
        for path in sorted(directory.glob(f"{_LEDGER_PREFIX}*.json"))
    ]
    if not ledgers:
        return None
    return max(ledgers, key=lambda ledger: ledger.generated_at)


def _previous_available_manifest_id(previous: EditionAvailabilityLedger) -> str:
    return f"{_AVAILABLE_PREFIX}{_ledger_token(previous)}"


def _validate_previous_capture(
    repository_root: Path,
    previous: EditionAvailabilityLedger,
) -> None:
    manifest_id = _previous_available_manifest_id(previous)
    path = _manifest_path(repository_root, manifest_id)
    manifest = SourceManifest.model_validate_json(path.read_text(encoding="utf-8"))
    if manifest.source_id != manifest_id:
        raise ValueError("previous availability manifest identity does not match its path")
    if manifest.retrieved_at != previous.complete_through:
        raise ValueError("previous ledger complete_through does not match its capture manifest")
    _verify_archived_bytes(repository_root, manifest)


def _ledger_token(ledger: EditionAvailabilityLedger) -> str:
    if not ledger.ledger_id.startswith(_LEDGER_PREFIX):
        raise ValueError("previous ledger ID does not follow the capture naming contract")
    return ledger.ledger_id.removeprefix(_LEDGER_PREFIX)


def _load_evidence_manifests(
    repository_root: Path,
    ledger: EditionAvailabilityLedger,
    current_by_id: dict[str, SourceManifest],
) -> dict[str, SourceManifest]:
    manifest_ids = {
        manifest_id
        for record in ledger.editions
        for evidence in record.evidence
        for manifest_id in evidence.source_manifest_ids
    }
    manifests: dict[str, SourceManifest] = {}
    for manifest_id in manifest_ids:
        manifest = current_by_id.get(manifest_id)
        if manifest is None:
            path = _manifest_path(repository_root, manifest_id)
            manifest = SourceManifest.model_validate_json(path.read_text(encoding="utf-8"))
            _verify_archived_bytes(repository_root, manifest)
        manifests[manifest_id] = manifest
    return manifests


def _verify_archived_bytes(repository_root: Path, manifest: SourceManifest) -> None:
    suffix = ".xml" if manifest.source_id.startswith("oecd-stes-") else ".json"
    path = _archive_path(repository_root, manifest.source_id, suffix)
    body = path.read_bytes()
    if (
        len(body) != manifest.byte_size
        or hashlib.sha256(body).hexdigest() != manifest.content_sha256
    ):
        raise ValueError(f"archived bytes do not match manifest {manifest.source_id}")


def _raw_artifact(
    repository_root: Path,
    manifest: SourceManifest,
    body: bytes,
    *,
    suffix: str,
) -> _PendingArtifact:
    return _PendingArtifact(_archive_path(repository_root, manifest.source_id, suffix), body)


def _manifest_artifact(repository_root: Path, manifest: SourceManifest) -> _PendingArtifact:
    return _json_artifact(
        _manifest_path(repository_root, manifest.source_id),
        manifest.model_dump(mode="json", exclude_none=True),
    )


def _json_artifact(path: Path, payload: object) -> _PendingArtifact:
    body = (json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode()
    return _PendingArtifact(path, body)


def _archive_path(repository_root: Path, source_id: str, suffix: str) -> Path:
    family = "ecos" if source_id.startswith("ecos-") else "oecd-stes"
    return repository_root / "data" / "archive" / family / f"{source_id}{suffix}"


def _manifest_path(repository_root: Path, source_id: str) -> Path:
    return repository_root / "data" / "manifests" / f"{source_id}.json"


def _write_append_only(artifacts: list[_PendingArtifact]) -> None:
    paths = [artifact.path for artifact in artifacts]
    if len(paths) != len(set(paths)):
        raise ValueError("capture attempted to write a duplicate artifact path")
    existing = [path for path in paths if path.exists()]
    if existing:
        raise FileExistsError(f"append-only capture refuses existing path: {existing[0]}")
    for artifact in artifacts:
        artifact.path.parent.mkdir(parents=True, exist_ok=True)
        with artifact.path.open("xb") as stream:
            stream.write(artifact.body)


def _parse_instant(value: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise ValueError(f"invalid aware timestamp: {value}") from error
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError(f"invalid aware timestamp: {value}")
    return parsed.astimezone(UTC)


def _canonical_now(now: Callable[[], datetime]) -> datetime:
    value = now()
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("capture clock must return a timezone-aware instant")
    return value.astimezone(UTC)


def _timestamp_token(value: datetime) -> str:
    return value.astimezone(UTC).strftime("%Y%m%dt%H%M%S%fZ").lower()


def _local_name(tag: str) -> str:
    return tag.rsplit("}", maxsplit=1)[-1]
