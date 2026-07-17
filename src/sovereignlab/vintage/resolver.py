"""Fail-closed SDMX-CSV as-of resolution for the live STES revisions flow."""

import csv
import hashlib
import io
from datetime import date
from enum import StrEnum
from typing import Annotated, cast
from urllib.parse import unquote, urlsplit

from pydantic import Field, StringConstraints, model_validator

from sovereignlab.schemas.availability import (
    EditionAbstentionReason,
    EditionAvailabilityLedger,
    EditionCode,
)
from sovereignlab.schemas.common import (
    ExternalIdentifier,
    Identifier,
    NonEmptyText,
    Sha256,
    StrictModel,
)
from sovereignlab.schemas.source import SourceManifest, VintageSemantics

_CSV_MEDIA_TYPES = frozenset({"application/vnd.sdmx.data+csv", "text/csv"})
_REQUIRED_COLUMNS = (
    "REF_AREA",
    "FREQ",
    "MEASURE",
    "UNIT_MEASURE",
    "ACTIVITY",
    "EDITION",
    "TIME_PERIOD",
    "OBS_VALUE",
)
_OptionalSdmxCode = Annotated[str, StringConstraints(max_length=256)]


class ResolverAbstentionReason(StrEnum):
    """Safe, structured reasons for returning no observation."""

    SOURCE_NOT_HISTORICAL_ARCHIVE = "source_not_historical_archive"
    UNSUPPORTED_MEDIA_TYPE = "unsupported_media_type"
    SOURCE_CONTENT_MISMATCH = "source_content_mismatch"
    MANIFEST_DATAFLOW_UNVERIFIABLE = "manifest_dataflow_unverifiable"
    MANIFEST_DATAFLOW_MISMATCH = "manifest_dataflow_mismatch"
    INVALID_CUTOFF = "invalid_cutoff"
    LEDGER_SELECTION_FAILED = "ledger_selection_failed"
    CUTOFF_BEYOND_COMPLETE_THROUGH = "cutoff_beyond_complete_through"
    NO_EDITION_DEFINITELY_AVAILABLE = "no_edition_definitely_available"
    UNRESOLVED_NEWER_EDITION = "unresolved_newer_edition"
    INVALID_SDMX_CSV = "invalid_sdmx_csv"
    MISSING_REQUIRED_COLUMNS = "missing_required_columns"
    MISSING_SELECTED_ROW = "missing_selected_row"
    DUPLICATE_SELECTED_ROW = "duplicate_selected_row"
    BLANK_SELECTED_OBSERVATION = "blank_selected_observation"


_LEDGER_ABSTENTION_REASONS = {
    EditionAbstentionReason.CUTOFF_BEYOND_COMPLETE_THROUGH: (
        ResolverAbstentionReason.CUTOFF_BEYOND_COMPLETE_THROUGH
    ),
    EditionAbstentionReason.NO_EDITION_DEFINITELY_AVAILABLE: (
        ResolverAbstentionReason.NO_EDITION_DEFINITELY_AVAILABLE
    ),
    EditionAbstentionReason.UNRESOLVED_NEWER_EDITION: (
        ResolverAbstentionReason.UNRESOLVED_NEWER_EDITION
    ),
}


class StesSeriesKey(StrictModel):
    """The five series dimensions preceding EDITION in the STES revisions DSD."""

    ref_area: ExternalIdentifier
    freq: ExternalIdentifier
    measure: ExternalIdentifier
    unit_measure: _OptionalSdmxCode = ""
    activity: _OptionalSdmxCode = ""

    def csv_dimensions(self) -> tuple[tuple[str, str], ...]:
        """Return the exact, case-sensitive SDMX code-column selection."""

        return (
            ("REF_AREA", self.ref_area),
            ("FREQ", self.freq),
            ("MEASURE", self.measure),
            ("UNIT_MEASURE", self.unit_measure),
            ("ACTIVITY", self.activity),
        )


class AsOfQuery(StrictModel):
    """One date-cutoff lookup for an exact STES series and observation period."""

    as_of: date
    series: StesSeriesKey
    period: NonEmptyText = Field(max_length=64)


class SelectedObservation(StrictModel):
    """The only SDMX row fields that a successful resolver result may expose."""

    ref_area: ExternalIdentifier
    freq: ExternalIdentifier
    measure: ExternalIdentifier
    unit_measure: _OptionalSdmxCode = ""
    activity: _OptionalSdmxCode = ""
    edition: EditionCode
    time_period: NonEmptyText = Field(max_length=64)
    observation_value: NonEmptyText


class AsOfEvidencePacket(StrictModel):
    """Manifest- and ledger-backed evidence containing exactly one selected row."""

    source_manifest_id: Identifier
    source_sha256: Sha256
    ledger_id: Identifier
    dataflow_id: NonEmptyText = Field(max_length=256)
    dataflow_version: NonEmptyText = Field(max_length=64)
    as_of: date
    observation: SelectedObservation


class AsOfAbstention(StrictModel):
    """An abstention that intentionally carries no edition code or observation value."""

    source_manifest_id: Identifier
    ledger_id: Identifier
    as_of: date
    reason: ResolverAbstentionReason


class AsOfResolution(StrictModel):
    """Exactly one successful evidence packet or safe abstention."""

    evidence: AsOfEvidencePacket | None = None
    abstention: AsOfAbstention | None = None

    @model_validator(mode="after")
    def require_exactly_one_outcome(self) -> "AsOfResolution":
        if (self.evidence is None) == (self.abstention is None):
            raise ValueError("resolution requires exactly one of evidence or abstention")
        return self


def resolve_stes_as_of(
    *,
    archive_bytes: bytes,
    manifest: SourceManifest,
    ledger: EditionAvailabilityLedger,
    query: AsOfQuery,
) -> AsOfResolution:
    """Resolve one STES observation without exposing any later edition inventory."""

    if manifest.vintage_semantics is not VintageSemantics.HISTORICAL_ARCHIVE:
        return _abstain(
            manifest,
            ledger,
            query,
            ResolverAbstentionReason.SOURCE_NOT_HISTORICAL_ARCHIVE,
        )
    if manifest.media_type not in _CSV_MEDIA_TYPES:
        return _abstain(manifest, ledger, query, ResolverAbstentionReason.UNSUPPORTED_MEDIA_TYPE)
    if not _content_matches_manifest(archive_bytes, manifest):
        return _abstain(manifest, ledger, query, ResolverAbstentionReason.SOURCE_CONTENT_MISMATCH)

    manifest_flow = _manifest_dataflow_reference(manifest)
    if manifest_flow is None:
        return _abstain(
            manifest,
            ledger,
            query,
            ResolverAbstentionReason.MANIFEST_DATAFLOW_UNVERIFIABLE,
        )
    manifest_dataflow_id, manifest_dataflow_version = manifest_flow
    if manifest_dataflow_id != ledger.dataflow_id or (
        manifest_dataflow_version is not None
        and manifest_dataflow_version != ledger.dataflow_version
    ):
        return _abstain(
            manifest,
            ledger,
            query,
            ResolverAbstentionReason.MANIFEST_DATAFLOW_MISMATCH,
        )

    try:
        cutoff_exclusive = ledger.cutoff_exclusive(query.as_of)
    except ValueError:
        return _abstain(manifest, ledger, query, ResolverAbstentionReason.INVALID_CUTOFF)
    selection = ledger.select_edition(cutoff_exclusive)
    if selection.abstention is not None:
        return _abstain(
            manifest,
            ledger,
            query,
            _LEDGER_ABSTENTION_REASONS.get(
                selection.abstention,
                ResolverAbstentionReason.LEDGER_SELECTION_FAILED,
            ),
        )

    row_lookup = _find_selected_row(
        archive_bytes,
        query,
        cast(str, selection.selected_edition),
    )
    if isinstance(row_lookup, ResolverAbstentionReason):
        return _abstain(manifest, ledger, query, row_lookup)
    row = row_lookup

    observation = SelectedObservation(
        ref_area=row["REF_AREA"],
        freq=row["FREQ"],
        measure=row["MEASURE"],
        unit_measure=row["UNIT_MEASURE"],
        activity=row["ACTIVITY"],
        edition=row["EDITION"],
        time_period=row["TIME_PERIOD"],
        observation_value=row["OBS_VALUE"],
    )
    return AsOfResolution(
        evidence=AsOfEvidencePacket(
            source_manifest_id=manifest.source_id,
            source_sha256=manifest.content_sha256,
            ledger_id=ledger.ledger_id,
            dataflow_id=ledger.dataflow_id,
            dataflow_version=ledger.dataflow_version,
            as_of=query.as_of,
            observation=observation,
        )
    )


def _abstain(
    manifest: SourceManifest,
    ledger: EditionAvailabilityLedger,
    query: AsOfQuery,
    reason: ResolverAbstentionReason,
) -> AsOfResolution:
    return AsOfResolution(
        abstention=AsOfAbstention(
            source_manifest_id=manifest.source_id,
            ledger_id=ledger.ledger_id,
            as_of=query.as_of,
            reason=reason,
        )
    )


def _content_matches_manifest(payload: bytes, manifest: SourceManifest) -> bool:
    if len(payload) != manifest.byte_size:
        return False
    return hashlib.sha256(payload).hexdigest() == manifest.content_sha256


def _manifest_dataflow_reference(manifest: SourceManifest) -> tuple[str, str | None] | None:
    path = unquote(urlsplit(str(manifest.canonical_url)).path)
    marker = "/data/"
    if marker not in path:
        return None
    flow_segment = path.split(marker, maxsplit=1)[1].split("/", maxsplit=1)[0]
    parts = flow_segment.split(",")
    if len(parts) not in {2, 3}:
        return None
    agency, flow = parts[:2]
    if not agency or not flow:
        return None
    version = parts[2] or None if len(parts) == 3 else None
    return f"{agency}:{flow}", version


def _find_selected_row(
    payload: bytes,
    query: AsOfQuery,
    selected_edition: str,
) -> dict[str, str] | ResolverAbstentionReason:
    try:
        text = payload.decode("utf-8-sig")
        reader = csv.reader(io.StringIO(text, newline=""), strict=True)
        header = next(reader)
    except (UnicodeDecodeError, csv.Error, StopIteration):
        return ResolverAbstentionReason.INVALID_SDMX_CSV

    if not header or len(header) != len(set(header)):
        return ResolverAbstentionReason.INVALID_SDMX_CSV
    if any(column not in header for column in _REQUIRED_COLUMNS):
        return ResolverAbstentionReason.MISSING_REQUIRED_COLUMNS

    indexes = {column: header.index(column) for column in _REQUIRED_COLUMNS}
    expected = (
        *query.series.csv_dimensions(),
        ("EDITION", selected_edition),
        ("TIME_PERIOD", query.period),
    )
    match: dict[str, str] | None = None
    try:
        for values in reader:
            if not values or all(not value.strip() for value in values):
                continue
            if len(values) != len(header):
                return ResolverAbstentionReason.INVALID_SDMX_CSV
            if all(values[indexes[column]] == value for column, value in expected):
                if match is not None:
                    return ResolverAbstentionReason.DUPLICATE_SELECTED_ROW
                match = {column: values[indexes[column]] for column in _REQUIRED_COLUMNS}
    except csv.Error:
        return ResolverAbstentionReason.INVALID_SDMX_CSV

    if match is None:
        return ResolverAbstentionReason.MISSING_SELECTED_ROW
    if not match["OBS_VALUE"].strip():
        return ResolverAbstentionReason.BLANK_SELECTED_OBSERVATION
    if len(match["OBS_VALUE"].strip()) > 10_000:
        return ResolverAbstentionReason.INVALID_SDMX_CSV
    return match
