"""Offline tests for the owner-approved OECD Korea CLI revision archive."""

import csv
import io
from datetime import UTC, datetime
from pathlib import Path

import httpx
import pytest

from sovereignlab.harvest import oecd_cli, weekly
from sovereignlab.schemas import (
    BenchmarkBundle,
    EditionAvailabilityLedger,
    EditionAvailabilityRecord,
    EditionResolutionStatus,
    SourceManifest,
)

CAPTURED_AT = datetime(2026, 7, 17, 13, 0, tzinfo=UTC)
FIELDS = (
    "REF_AREA",
    "FREQ",
    "MEASURE",
    "UNIT_MEASURE",
    "ACTIVITY",
    "EDITION",
    "TIME_PERIOD",
    "OBS_VALUE",
)
DEFAULT_ROWS = (
    {
        "REF_AREA": "KOR",
        "FREQ": "M",
        "MEASURE": "LI_AA",
        "UNIT_MEASURE": "IX",
        "ACTIVITY": "_T",
        "EDITION": "202606",
        "TIME_PERIOD": "2026-04",
        "OBS_VALUE": "100.1",
    },
    {
        "REF_AREA": "KOR",
        "FREQ": "M",
        "MEASURE": "LI_AA",
        "UNIT_MEASURE": "IX",
        "ACTIVITY": "_T",
        "EDITION": "202607",
        "TIME_PERIOD": "2026-05",
        "OBS_VALUE": "99.9",
    },
)


def _csv_payload(
    rows: tuple[dict[str, str], ...] | None = None,
    *,
    fields: tuple[str, ...] = FIELDS,
) -> bytes:
    resolved = DEFAULT_ROWS if rows is None else rows
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    writer.writerows(resolved)
    return stream.getvalue().encode()


def _ledger(
    editions: tuple[str, ...] = ("202606", "202607"),
    *,
    flow: str = weekly.OECD_DATAFLOW_ID,
    version: str = weekly.OECD_DATAFLOW_VERSION,
) -> EditionAvailabilityLedger:
    return EditionAvailabilityLedger(
        ledger_id="test-oecd-ledger",
        dataflow_id=flow,
        dataflow_version=version,
        generated_at=CAPTURED_AT,
        captured_at=CAPTURED_AT,
        complete_through=CAPTURED_AT,
        cutoff_timezone="Asia/Seoul",
        editions=tuple(
            EditionAvailabilityRecord(
                edition=edition,
                status=EditionResolutionStatus.UNRESOLVED,
            )
            for edition in editions
        ),
    )


def _client(payload: bytes | None = None, status_code: int = 200) -> httpx.Client:
    body = _csv_payload() if payload is None else payload

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(status_code, content=body, request=request)

    return httpx.Client(transport=httpx.MockTransport(handler))


def _capture(
    root: Path,
    *,
    payload: bytes | None = None,
    ledger: EditionAvailabilityLedger | None = None,
    status_code: int = 200,
    captured_at: datetime = CAPTURED_AT,
) -> oecd_cli.CLIArchiveSummary:
    catalog = weekly.load_rights_catalog(Path.cwd())
    with _client(payload, status_code) as client:
        return oecd_cli.capture_oecd_cli_archive(
            root,
            client=client,
            rights_catalog=catalog,
            availability_ledger=ledger or _ledger(),
            now=lambda: captured_at,
        )


def test_capture_writes_rights_linked_append_only_archive(tmp_path: Path) -> None:
    summary = _capture(tmp_path)

    assert summary.row_count == 2
    assert summary.edition_count == 2
    assert (summary.first_edition, summary.last_edition) == ("202606", "202607")
    assert (summary.first_period, summary.last_period) == ("2026-04", "2026-05")
    archive = tmp_path / summary.archive_path
    manifest = SourceManifest.model_validate_json(
        (tmp_path / summary.manifest_path).read_text(encoding="utf-8")
    )
    catalog = weekly.load_rights_catalog(Path.cwd())
    BenchmarkBundle(sources=(manifest,), records=(), rights_catalogs=(catalog,))
    assert archive.read_bytes() == _csv_payload()
    assert manifest.rights_decision is not None
    assert manifest.rights_decision.decision_id == oecd_cli.OECD_CLI_RIGHTS_DECISION_ID
    assert manifest.rights_decision.item_id == "KOR.M.LI_AA.IX._T"

    with pytest.raises(FileExistsError, match="refuses existing path"):
        _capture(tmp_path)


@pytest.mark.parametrize(
    ("payload", "message"),
    [
        (b"\xff", "not valid UTF-8"),
        (_csv_payload(rows=(), fields=("REF_AREA",)), "missing required"),
        (_csv_payload(rows=()), "no observations"),
        (_csv_payload().replace(b"KOR", b"USA", 1), "outside"),
        (_csv_payload().replace(b"202606", b"202613", 1), "invalid edition"),
        (_csv_payload().replace(b"2026-04", b"2026-13", 1), "invalid monthly"),
        (_csv_payload().replace(b"100.1", b" ", 1), "blank observation"),
        (
            _csv_payload(rows=(DEFAULT_ROWS[1], DEFAULT_ROWS[1])),
            "duplicate edition-period",
        ),
        (_csv_payload().replace(b"100.1\n", b"100.1,extra\n", 1), "outside"),
    ],
)
def test_invalid_csv_fails_closed(tmp_path: Path, payload: bytes, message: str) -> None:
    with pytest.raises(ValueError, match=message):
        _capture(tmp_path, payload=payload)


def test_empty_and_http_error_responses_fail_before_writes(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="empty OECD"):
        _capture(tmp_path, payload=b"")
    with pytest.raises(httpx.HTTPStatusError):
        _capture(tmp_path, status_code=503)
    assert not any(tmp_path.rglob("*"))


@pytest.mark.parametrize(
    ("ledger", "message"),
    [
        (_ledger(flow="OTHER:FLOW"), "different dataflows"),
        (_ledger(version="3.0"), "different dataflows"),
        (_ledger(("202607",)), "outside the availability ledger"),
        (_ledger(("202606", "202607", "202608")), "latest edition"),
    ],
)
def test_ledger_join_fails_closed(
    tmp_path: Path,
    ledger: EditionAvailabilityLedger,
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        _capture(tmp_path, ledger=ledger)


def test_latest_ledger_loader_and_capture_clock_validation(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match="no committed"):
        oecd_cli.load_latest_availability_ledger(tmp_path)

    directory = tmp_path / "data" / "availability"
    directory.mkdir(parents=True)
    older_time = datetime(2026, 6, 17, tzinfo=UTC)
    older = _ledger(("202606",)).model_copy(
        update={
            "ledger_id": "older-ledger",
            "generated_at": older_time,
            "captured_at": older_time,
            "complete_through": older_time,
        }
    )
    newer = _ledger()
    for name, ledger in (
        ("oecd-stes-ledger-old.json", older),
        ("oecd-stes-ledger-new.json", newer),
    ):
        (directory / name).write_text(ledger.model_dump_json(), encoding="utf-8")
    assert oecd_cli.load_latest_availability_ledger(tmp_path).ledger_id == newer.ledger_id

    with pytest.raises(ValueError, match="timezone-aware"):
        _capture(tmp_path / "naive", captured_at=datetime(2026, 7, 17))
