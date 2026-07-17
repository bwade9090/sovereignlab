"""One-time, append-only capture of the approved OECD Korea CLI revision archive."""

import csv
import hashlib
import io
import re
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

import httpx

from sovereignlab.harvest.weekly import (
    OECD_DATAFLOW_ID,
    OECD_DATAFLOW_VERSION,
    _json_artifact,
    _PendingArtifact,
    _timestamp_token,
    _write_append_only,
)
from sovereignlab.schemas import (
    BenchmarkBundle,
    EditionAvailabilityLedger,
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

OECD_CLI_ARCHIVE_URL = (
    "https://sdmx.oecd.org/public/rest/data/"
    "OECD.SDD.STES,DSD_STES_REVISIONS%40DF_STES_REVISIONS,4.0/"
    "KOR.M.LI_AA...?format=csvfilewithlabels"
)
OECD_CLI_RIGHTS_DECISION_ID = "oecd-stes-revisions-kor-m-li-aa-rights-v1"
OECD_CLI_RIGHTS_TABLE_ID = "DSD_STES_REVISIONS@DF_STES_REVISIONS"
OECD_CLI_RIGHTS_ITEM_ID = "KOR.M.LI_AA.IX._T"
_MONTH_PATTERN = re.compile(r"^[0-9]{4}-(0[1-9]|1[0-2])$")
_EDITION_PATTERN = re.compile(r"^[0-9]{4}(0[1-9]|1[0-2])$")


@dataclass(frozen=True)
class CLIArchiveSummary:
    """Paths and validated coverage of one consolidated CLI archive capture."""

    capture_token: str
    archive_path: str
    manifest_path: str
    row_count: int
    edition_count: int
    first_edition: str
    last_edition: str
    first_period: str
    last_period: str


@dataclass(frozen=True)
class _CLIInventory:
    row_count: int
    editions: frozenset[str]
    periods: frozenset[str]


def capture_oecd_cli_archive(
    repository_root: Path,
    *,
    client: httpx.Client,
    rights_catalog: RightsCatalog,
    availability_ledger: EditionAvailabilityLedger,
    now: Callable[[], datetime] = lambda: datetime.now(UTC),
) -> CLIArchiveSummary:
    """Capture the approved consolidated Korea CLI history exactly once per invocation."""

    response = client.get(OECD_CLI_ARCHIVE_URL, headers={"Accept": "text/csv"})
    response.raise_for_status()
    if not response.content:
        raise ValueError("empty OECD CLI archive response")
    retrieved_at = _canonical_now(now)
    inventory = _validate_cli_csv(response.content)
    _validate_ledger_join(inventory, availability_ledger)

    token = _timestamp_token(retrieved_at)
    source_id = f"oecd-stes-cli-kor-li-aa-{token}"
    manifest = SourceManifest(
        source_id=source_id,
        source_kind=SourceKind.API,
        publisher="OECD",
        title="Korea composite leading indicator (CLI), amplitude adjusted, revision archive",
        document_family="oecd-stes-cli-kor-li-aa",
        language=LanguageCode.UNDETERMINED,
        published_on=retrieved_at.date(),
        publication_date_basis=PublicationDateBasis.RETRIEVAL_DATE_FALLBACK,
        publication_date_notes=(
            "Dynamic consolidated edition response; retrieval date identifies these exact bytes."
        ),
        retrieved_at=retrieved_at,
        canonical_url=OECD_CLI_ARCHIVE_URL,
        media_type="text/csv",
        content_sha256=hashlib.sha256(response.content).hexdigest(),
        byte_size=len(response.content),
        redistribution=RedistributionPolicy(
            status=RedistributionStatus.ALLOWED,
            license_name="OECD Terms & Conditions — Data",
            license_url="https://www.oecd.org/en/about/terms-conditions.html",
            notes=(
                "Exact OECD-produced Korea CLI scope approved in ADR 0007; attribution required "
                "and no OECD endorsement is implied."
            ),
        ),
        vintage_semantics=VintageSemantics.HISTORICAL_ARCHIVE,
        rights_decision=SourceRightsReference(
            catalog_id=rights_catalog.catalog_id,
            decision_id=OECD_CLI_RIGHTS_DECISION_ID,
            source_system=SourceSystem.OECD,
            table_id=OECD_CLI_RIGHTS_TABLE_ID,
            item_id=OECD_CLI_RIGHTS_ITEM_ID,
        ),
        release_label=f"Consolidated revision archive capture {token}",
    )
    BenchmarkBundle(sources=(manifest,), records=(), rights_catalogs=(rights_catalog,))

    archive_path = repository_root / "data" / "archive" / "oecd-stes" / f"{source_id}.csv"
    manifest_path = repository_root / "data" / "manifests" / f"{source_id}.json"
    artifacts = [
        _PendingArtifact(archive_path, response.content),
        _json_artifact(
            manifest_path,
            manifest.model_dump(mode="json", exclude_none=True),
        ),
    ]
    _write_append_only(artifacts)
    return CLIArchiveSummary(
        capture_token=token,
        archive_path=str(archive_path.relative_to(repository_root)),
        manifest_path=str(manifest_path.relative_to(repository_root)),
        row_count=inventory.row_count,
        edition_count=len(inventory.editions),
        first_edition=min(inventory.editions),
        last_edition=max(inventory.editions),
        first_period=min(inventory.periods),
        last_period=max(inventory.periods),
    )


def load_latest_availability_ledger(repository_root: Path) -> EditionAvailabilityLedger:
    """Load the newest committed STES ledger for CLI archive validation."""

    paths = tuple((repository_root / "data" / "availability").glob("oecd-stes-ledger-*.json"))
    if not paths:
        raise FileNotFoundError("no committed STES availability ledger")
    ledgers = tuple(
        EditionAvailabilityLedger.model_validate_json(path.read_text(encoding="utf-8"))
        for path in paths
    )
    return max(ledgers, key=lambda ledger: ledger.generated_at)


def _validate_cli_csv(payload: bytes) -> _CLIInventory:
    try:
        text = payload.decode("utf-8-sig")
    except UnicodeDecodeError as error:
        raise ValueError("OECD CLI archive is not valid UTF-8 CSV") from error
    reader = csv.DictReader(io.StringIO(text, newline=""))
    required = {
        "REF_AREA",
        "FREQ",
        "MEASURE",
        "UNIT_MEASURE",
        "ACTIVITY",
        "EDITION",
        "TIME_PERIOD",
        "OBS_VALUE",
    }
    if reader.fieldnames is None or not required.issubset(reader.fieldnames):
        raise ValueError("OECD CLI archive is missing required code columns")

    editions: set[str] = set()
    periods: set[str] = set()
    observations: set[tuple[str, str]] = set()
    row_count = 0
    for row in reader:
        if None in row or any(
            row[field] != expected
            for field, expected in {
                "REF_AREA": "KOR",
                "FREQ": "M",
                "MEASURE": "LI_AA",
                "UNIT_MEASURE": "IX",
                "ACTIVITY": "_T",
            }.items()
        ):
            raise ValueError("OECD CLI archive contains rows outside the approved series")
        edition = row["EDITION"]
        period = row["TIME_PERIOD"]
        if _EDITION_PATTERN.fullmatch(edition) is None:
            raise ValueError("OECD CLI archive contains an invalid edition")
        if _MONTH_PATTERN.fullmatch(period) is None:
            raise ValueError("OECD CLI archive contains an invalid monthly period")
        if not row["OBS_VALUE"].strip():
            raise ValueError("OECD CLI archive contains a blank observation")
        key = (edition, period)
        if key in observations:
            raise ValueError("OECD CLI archive contains a duplicate edition-period row")
        observations.add(key)
        editions.add(edition)
        periods.add(period)
        row_count += 1
    if row_count == 0:
        raise ValueError("OECD CLI archive contains no observations")
    return _CLIInventory(
        row_count=row_count,
        editions=frozenset(editions),
        periods=frozenset(periods),
    )


def _validate_ledger_join(
    inventory: _CLIInventory,
    ledger: EditionAvailabilityLedger,
) -> None:
    if ledger.dataflow_id != OECD_DATAFLOW_ID or ledger.dataflow_version != OECD_DATAFLOW_VERSION:
        raise ValueError("OECD CLI archive and availability ledger describe different dataflows")
    ledger_editions = {record.edition for record in ledger.editions}
    if not inventory.editions.issubset(ledger_editions):
        raise ValueError("OECD CLI archive contains editions outside the availability ledger")
    if max(inventory.editions) != max(ledger_editions):
        raise ValueError("OECD CLI archive does not include the ledger's latest edition")


def _canonical_now(now: Callable[[], datetime]) -> datetime:
    value = now()
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("capture clock must return a timezone-aware instant")
    return value.astimezone(UTC)
