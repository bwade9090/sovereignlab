"""Offline regression tests for the fail-closed STES as-of resolver."""

import csv
import hashlib
import io
from datetime import date

import pytest
from pydantic import ValidationError

from sovereignlab.schemas import (
    EditionAvailabilityLedger,
    SourceManifest,
    VintageSemantics,
)
from sovereignlab.vintage import (
    AsOfQuery,
    AsOfResolution,
    ResolverAbstentionReason,
    StesSeriesKey,
    resolve_stes_as_of,
)

FLOW_URL = "https://example.org/public/rest/data/EXAMPLE,DSD_EXAMPLE%40DF_EXAMPLE,1.0/all"
HEADERS = (
    "REF_AREA",
    "FREQ",
    "MEASURE",
    "Measure",
    "UNIT_MEASURE",
    "ACTIVITY",
    "EDITION",
    "TIME_PERIOD",
    "OBS_VALUE",
)
SELECTED_ROW = ("KOR", "Q", "B1GQ_Q", "Real GDP label", "", "", "202405", "2024-Q1", "100.0")
FUTURE_ROW = ("KOR", "Q", "B1GQ_Q", "Real GDP label", "", "", "202406", "2024-Q1", "future-value")


@pytest.fixture
def query() -> AsOfQuery:
    return AsOfQuery(
        as_of=date(2024, 5, 31),
        series=StesSeriesKey(ref_area="KOR", freq="Q", measure="B1GQ_Q"),
        period="2024-Q1",
    )


def _csv_bytes(
    rows: tuple[tuple[str, ...], ...],
    *,
    headers: tuple[str, ...] = HEADERS,
) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.writer(stream, lineterminator="\n")
    writer.writerow(headers)
    writer.writerows(rows)
    return stream.getvalue().encode("utf-8-sig")


def _manifest(
    archive_source: SourceManifest,
    payload: bytes,
    *,
    url: str = FLOW_URL,
    media_type: str = "text/csv",
    vintage_semantics: VintageSemantics = VintageSemantics.HISTORICAL_ARCHIVE,
) -> SourceManifest:
    data = archive_source.model_dump(mode="python")
    data.update(
        canonical_url=url,
        media_type=media_type,
        byte_size=len(payload),
        content_sha256=hashlib.sha256(payload).hexdigest(),
        vintage_semantics=vintage_semantics,
    )
    return SourceManifest.model_validate(data)


def _resolve(
    *,
    archive_source: SourceManifest,
    availability_ledger: EditionAvailabilityLedger,
    query: AsOfQuery,
    payload: bytes | None = None,
    manifest: SourceManifest | None = None,
) -> AsOfResolution:
    resolved_payload = payload or _csv_bytes((SELECTED_ROW, FUTURE_ROW))
    resolved_manifest = manifest or _manifest(archive_source, resolved_payload)
    return resolve_stes_as_of(
        archive_bytes=resolved_payload,
        manifest=resolved_manifest,
        ledger=availability_ledger,
        query=query,
    )


def test_resolver_selects_exact_code_columns_and_exposes_only_one_row(
    archive_source: SourceManifest,
    availability_ledger: EditionAvailabilityLedger,
    query: AsOfQuery,
) -> None:
    payload = _csv_bytes(((), (" ",), SELECTED_ROW, FUTURE_ROW))
    result = _resolve(
        archive_source=archive_source,
        availability_ledger=availability_ledger,
        query=query,
        payload=payload,
    )

    assert result.abstention is None
    assert result.evidence is not None
    assert result.evidence.dataflow_id == availability_ledger.dataflow_id
    assert result.evidence.observation.measure == "B1GQ_Q"
    assert result.evidence.observation.observation_value == "100.0"
    serialized = result.model_dump_json()
    assert "Real GDP label" not in serialized
    assert "202406" not in serialized
    assert "future-value" not in serialized


def test_resolver_accepts_sdmx_csv_media_type_and_unversioned_url(
    archive_source: SourceManifest,
    availability_ledger: EditionAvailabilityLedger,
    query: AsOfQuery,
) -> None:
    payload = _csv_bytes((SELECTED_ROW,))
    manifest = _manifest(
        archive_source,
        payload,
        url=("https://example.org/public/rest/data/EXAMPLE,DSD_EXAMPLE%40DF_EXAMPLE,/all"),
        media_type="application/vnd.sdmx.data+csv",
    )

    result = _resolve(
        archive_source=archive_source,
        availability_ledger=availability_ledger,
        query=query,
        payload=payload,
        manifest=manifest,
    )

    assert result.evidence is not None


@pytest.mark.parametrize(
    ("as_of", "reason"),
    [
        (date(2024, 4, 30), ResolverAbstentionReason.NO_EDITION_DEFINITELY_AVAILABLE),
        (date(2026, 7, 20), ResolverAbstentionReason.CUTOFF_BEYOND_COMPLETE_THROUGH),
    ],
)
def test_resolver_propagates_ledger_abstentions_without_parsing_rows(
    archive_source: SourceManifest,
    availability_ledger: EditionAvailabilityLedger,
    query: AsOfQuery,
    as_of: date,
    reason: ResolverAbstentionReason,
) -> None:
    payload = b"not,csv,but,the,ledger,abstains,first"
    manifest = _manifest(archive_source, payload)

    result = _resolve(
        archive_source=archive_source,
        availability_ledger=availability_ledger,
        query=query.model_copy(update={"as_of": as_of}),
        payload=payload,
        manifest=manifest,
    )

    assert result.abstention is not None
    assert result.abstention.reason is reason


def test_resolver_abstains_across_an_unresolved_newer_edition(
    archive_source: SourceManifest,
    availability_ledger: EditionAvailabilityLedger,
    query: AsOfQuery,
) -> None:
    ledger_data = availability_ledger.model_dump(mode="python")
    ledger_data["editions"][1]["status"] = "unresolved"
    ledger_data["editions"][1]["available_by"] = None
    ledger_data["editions"][1]["last_absent_at"] = None
    ledger_data["editions"][1]["evidence"] = ()
    unresolved_ledger = EditionAvailabilityLedger.model_validate(ledger_data)

    result = _resolve(
        archive_source=archive_source,
        availability_ledger=unresolved_ledger,
        query=query,
    )

    assert result.abstention is not None
    assert result.abstention.reason is ResolverAbstentionReason.UNRESOLVED_NEWER_EDITION
    serialized = result.model_dump_json()
    assert "202406" not in serialized
    assert "future-value" not in serialized


def test_resolver_rejects_latest_only_source_before_reading_content(
    archive_source: SourceManifest,
    availability_ledger: EditionAvailabilityLedger,
    query: AsOfQuery,
) -> None:
    payload = _csv_bytes((SELECTED_ROW,))
    manifest = _manifest(
        archive_source,
        payload,
        vintage_semantics=VintageSemantics.LATEST_ONLY,
    )

    result = _resolve(
        archive_source=archive_source,
        availability_ledger=availability_ledger,
        query=query,
        payload=payload,
        manifest=manifest,
    )

    assert result.abstention is not None
    assert result.abstention.reason is ResolverAbstentionReason.SOURCE_NOT_HISTORICAL_ARCHIVE


def test_resolver_rejects_unsupported_media_type(
    archive_source: SourceManifest,
    availability_ledger: EditionAvailabilityLedger,
    query: AsOfQuery,
) -> None:
    payload = _csv_bytes((SELECTED_ROW,))
    manifest = _manifest(archive_source, payload, media_type="application/json")

    result = _resolve(
        archive_source=archive_source,
        availability_ledger=availability_ledger,
        query=query,
        payload=payload,
        manifest=manifest,
    )

    assert result.abstention is not None
    assert result.abstention.reason is ResolverAbstentionReason.UNSUPPORTED_MEDIA_TYPE


@pytest.mark.parametrize("changed_payload", [b"short", b"X" + _csv_bytes((SELECTED_ROW,))[1:]])
def test_resolver_verifies_manifest_size_and_sha256(
    archive_source: SourceManifest,
    availability_ledger: EditionAvailabilityLedger,
    query: AsOfQuery,
    changed_payload: bytes,
) -> None:
    original = _csv_bytes((SELECTED_ROW,))
    manifest = _manifest(archive_source, original)

    result = _resolve(
        archive_source=archive_source,
        availability_ledger=availability_ledger,
        query=query,
        payload=changed_payload,
        manifest=manifest,
    )

    assert result.abstention is not None
    assert result.abstention.reason is ResolverAbstentionReason.SOURCE_CONTENT_MISMATCH


@pytest.mark.parametrize(
    "url",
    [
        "https://example.org/no-dataflow",
        "https://example.org/public/rest/data/",
        "https://example.org/public/rest/data/EXAMPLE,,1.0/all",
        "https://example.org/public/rest/data/EXAMPLE,ONE,TWO,THREE/all",
    ],
)
def test_resolver_requires_a_verifiable_dataflow_in_the_manifest_url(
    archive_source: SourceManifest,
    availability_ledger: EditionAvailabilityLedger,
    query: AsOfQuery,
    url: str,
) -> None:
    payload = _csv_bytes((SELECTED_ROW,))
    manifest = _manifest(archive_source, payload, url=url)

    result = _resolve(
        archive_source=archive_source,
        availability_ledger=availability_ledger,
        query=query,
        payload=payload,
        manifest=manifest,
    )

    assert result.abstention is not None
    assert result.abstention.reason is ResolverAbstentionReason.MANIFEST_DATAFLOW_UNVERIFIABLE


@pytest.mark.parametrize(
    "url",
    [
        "https://example.org/public/rest/data/OTHER,DSD_EXAMPLE%40DF_EXAMPLE,1.0/all",
        "https://example.org/public/rest/data/EXAMPLE,DSD_EXAMPLE%40DF_EXAMPLE,2.0/all",
    ],
)
def test_resolver_rejects_manifest_ledger_dataflow_mismatch(
    archive_source: SourceManifest,
    availability_ledger: EditionAvailabilityLedger,
    query: AsOfQuery,
    url: str,
) -> None:
    payload = _csv_bytes((SELECTED_ROW,))
    manifest = _manifest(archive_source, payload, url=url)

    result = _resolve(
        archive_source=archive_source,
        availability_ledger=availability_ledger,
        query=query,
        payload=payload,
        manifest=manifest,
    )

    assert result.abstention is not None
    assert result.abstention.reason is ResolverAbstentionReason.MANIFEST_DATAFLOW_MISMATCH


def test_resolver_converts_calendar_overflow_to_a_safe_abstention(
    archive_source: SourceManifest,
    availability_ledger: EditionAvailabilityLedger,
    query: AsOfQuery,
) -> None:
    result = _resolve(
        archive_source=archive_source,
        availability_ledger=availability_ledger,
        query=query.model_copy(update={"as_of": date.max}),
    )

    assert result.abstention is not None
    assert result.abstention.reason is ResolverAbstentionReason.INVALID_CUTOFF


@pytest.mark.parametrize(
    ("payload", "reason"),
    [
        (b"\xff", ResolverAbstentionReason.INVALID_SDMX_CSV),
        (b"\n", ResolverAbstentionReason.INVALID_SDMX_CSV),
        (b'"unterminated', ResolverAbstentionReason.INVALID_SDMX_CSV),
        (
            _csv_bytes((SELECTED_ROW,), headers=(*HEADERS, "MEASURE")),
            ResolverAbstentionReason.INVALID_SDMX_CSV,
        ),
        (
            _csv_bytes((SELECTED_ROW,), headers=tuple(h for h in HEADERS if h != "MEASURE")),
            ResolverAbstentionReason.MISSING_REQUIRED_COLUMNS,
        ),
        (
            _csv_bytes((SELECTED_ROW[:-1],)),
            ResolverAbstentionReason.INVALID_SDMX_CSV,
        ),
        (
            _csv_bytes((FUTURE_ROW,)),
            ResolverAbstentionReason.MISSING_SELECTED_ROW,
        ),
        (
            _csv_bytes((SELECTED_ROW, SELECTED_ROW)),
            ResolverAbstentionReason.DUPLICATE_SELECTED_ROW,
        ),
        (
            _csv_bytes(((*SELECTED_ROW[:-1], " "),)),
            ResolverAbstentionReason.BLANK_SELECTED_OBSERVATION,
        ),
        (
            _csv_bytes(((*SELECTED_ROW[:-1], "x" * 10_001),)),
            ResolverAbstentionReason.INVALID_SDMX_CSV,
        ),
    ],
)
def test_resolver_abstains_on_malformed_or_unusable_csv(
    archive_source: SourceManifest,
    availability_ledger: EditionAvailabilityLedger,
    query: AsOfQuery,
    payload: bytes,
    reason: ResolverAbstentionReason,
) -> None:
    manifest = _manifest(archive_source, payload)

    result = _resolve(
        archive_source=archive_source,
        availability_ledger=availability_ledger,
        query=query,
        payload=payload,
        manifest=manifest,
    )

    assert result.evidence is None
    assert result.abstention is not None
    assert result.abstention.reason is reason


def test_resolver_abstains_when_csv_fails_during_row_iteration(
    archive_source: SourceManifest,
    availability_ledger: EditionAvailabilityLedger,
    query: AsOfQuery,
) -> None:
    header = ",".join(HEADERS).encode()
    payload = b"\xef\xbb\xbf" + header + b'\n"unterminated'
    manifest = _manifest(archive_source, payload)

    result = _resolve(
        archive_source=archive_source,
        availability_ledger=availability_ledger,
        query=query,
        payload=payload,
        manifest=manifest,
    )

    assert result.abstention is not None
    assert result.abstention.reason is ResolverAbstentionReason.INVALID_SDMX_CSV


def test_resolution_model_requires_exactly_one_outcome(
    archive_source: SourceManifest,
    availability_ledger: EditionAvailabilityLedger,
    query: AsOfQuery,
) -> None:
    success = _resolve(
        archive_source=archive_source,
        availability_ledger=availability_ledger,
        query=query,
    )
    assert success.evidence is not None
    abstention = _resolve(
        archive_source=archive_source,
        availability_ledger=availability_ledger,
        query=query.model_copy(update={"as_of": date(2026, 7, 20)}),
    )
    assert abstention.abstention is not None

    with pytest.raises(ValidationError, match="exactly one"):
        AsOfResolution()
    with pytest.raises(ValidationError, match="exactly one"):
        AsOfResolution(evidence=success.evidence, abstention=abstention.abstention)
