"""Immutable edition-availability ledger and fail-closed selection semantics (ADR 0005)."""

from collections.abc import Callable
from datetime import UTC, date, datetime, time, timedelta
from enum import StrEnum
from typing import Annotated, Literal
from zoneinfo import ZoneInfo

from pydantic import AfterValidator, AwareDatetime, Field, StringConstraints, model_validator

from sovereignlab.schemas.common import (
    AVAILABILITY_SCHEMA_VERSION,
    ExternalIdentifier,
    Identifier,
    NonEmptyText,
    StrictModel,
)

EditionCode = Annotated[str, StringConstraints(pattern=r"^[0-9]{4}(0[1-9]|1[0-2])$")]
SdmxFlowReference = Annotated[
    str,
    StringConstraints(
        min_length=3,
        max_length=256,
        pattern=r"^[A-Za-z0-9][A-Za-z0-9._@:-]*$",
    ),
]
SdmxArtefactVersion = Annotated[str, StringConstraints(pattern=r"^[0-9]+(\.[0-9]+)*$")]


def _require_utc(value: datetime) -> datetime:
    if value.utcoffset() != timedelta(0):
        raise ValueError("ledger timestamps must be canonical UTC instants")
    return value


UtcDatetime = Annotated[AwareDatetime, AfterValidator(_require_utc)]


def _require_iana_timezone(value: str) -> str:
    try:
        ZoneInfo(value)
    except (KeyError, ValueError) as error:
        raise ValueError(f"unknown IANA timezone: {value}") from error
    return value


TimezoneName = Annotated[
    str,
    StringConstraints(min_length=1, max_length=64),
    AfterValidator(_require_iana_timezone),
]


class AvailabilityAssertion(StrEnum):
    """Which ledger-record field one evidence entry supports."""

    AVAILABLE_BY = "available_by"
    NOT_BEFORE = "not_before"
    LAST_ABSENT_AT = "last_absent_at"


class AvailabilityEvidenceBasis(StrEnum):
    """The only availability-evidence bases ADR 0005 permits."""

    PUBLISHER_TIMESTAMP = "publisher_timestamp"
    PUBLISHER_DATE_CONSERVATIVE = "publisher_date_conservative"
    SDMX_CONSTRAINT_VALID_FROM = "sdmx_constraint_valid_from"
    FIRST_OBSERVED_AT = "first_observed_at"


class EditionResolutionStatus(StrEnum):
    """Whether an edition's first-availability instant is demonstrated."""

    RESOLVED = "resolved"
    UNRESOLVED = "unresolved"


class EditionCutoffState(StrEnum):
    """An edition's derived state at one exclusive cutoff instant."""

    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"
    UNKNOWN = "unknown"


class EditionAbstentionReason(StrEnum):
    """Structured fail-closed reasons for refusing to select an edition."""

    CUTOFF_BEYOND_COMPLETE_THROUGH = "cutoff_beyond_complete_through"
    NO_EDITION_DEFINITELY_AVAILABLE = "no_edition_definitely_available"
    UNRESOLVED_NEWER_EDITION = "unresolved_newer_edition"


class AvailabilityEvidence(StrictModel):
    """One manifest-backed availability assertion with an approved evidence basis."""

    basis: AvailabilityEvidenceBasis
    supports: AvailabilityAssertion
    asserted_instant: UtcDatetime
    source_manifest_ids: tuple[Identifier, ...] = Field(min_length=1)
    publisher_date: date | None = None
    publisher_timezone: TimezoneName | None = None
    constraint_id: ExternalIdentifier | None = None
    constraint_version: SdmxArtefactVersion | None = None
    notes: NonEmptyText | None = None

    @model_validator(mode="after")
    def enforce_basis_contract(self) -> "AvailabilityEvidence":
        if len(set(self.source_manifest_ids)) != len(self.source_manifest_ids):
            raise ValueError("evidence source_manifest_ids must be unique")

        is_conservative = self.basis is AvailabilityEvidenceBasis.PUBLISHER_DATE_CONSERVATIVE
        if (self.publisher_date is not None or self.publisher_timezone is not None) and (
            not is_conservative
        ):
            raise ValueError("publisher date fields require the publisher-date-conservative basis")
        if is_conservative:
            if self.publisher_date is None or self.publisher_timezone is None:
                raise ValueError(
                    "publisher-date-conservative basis requires publisher_date and "
                    "publisher_timezone"
                )
            if self.supports is not AvailabilityAssertion.AVAILABLE_BY:
                raise ValueError("publisher-date-conservative basis can only support available_by")
            safe_instant = datetime.combine(
                _following_day(self.publisher_date, "publisher_date"),
                time.min,
                tzinfo=ZoneInfo(self.publisher_timezone),
            ).astimezone(UTC)
            if self.asserted_instant != safe_instant:
                raise ValueError(
                    "conservative assertion must equal the start of the following "
                    "publisher-local day"
                )

        is_constraint = self.basis is AvailabilityEvidenceBasis.SDMX_CONSTRAINT_VALID_FROM
        if (self.constraint_id is not None or self.constraint_version is not None) and (
            not is_constraint
        ):
            raise ValueError("constraint fields require the sdmx-constraint-valid-from basis")
        if is_constraint and (self.constraint_id is None or self.constraint_version is None):
            raise ValueError(
                "sdmx-constraint-valid-from basis requires constraint_id and constraint_version"
            )
        return self


class EditionAvailabilityRecord(StrictModel):
    """The evidence-backed availability window of one opaque edition code."""

    edition: EditionCode
    status: EditionResolutionStatus
    available_by: UtcDatetime | None = None
    not_before: UtcDatetime | None = None
    last_absent_at: UtcDatetime | None = None
    evidence: tuple[AvailabilityEvidence, ...] = ()

    @model_validator(mode="after")
    def enforce_window_and_evidence(self) -> "EditionAvailabilityRecord":
        if self.status is EditionResolutionStatus.RESOLVED and self.available_by is None:
            raise ValueError("resolved edition requires available_by")
        if self.status is EditionResolutionStatus.UNRESOLVED and self.available_by is not None:
            raise ValueError("unresolved edition cannot invent available_by")
        if (
            self.available_by is not None
            and self.not_before is not None
            and self.not_before > self.available_by
        ):
            raise ValueError("not_before cannot follow available_by")
        if (
            self.available_by is not None
            and self.last_absent_at is not None
            and self.last_absent_at >= self.available_by
        ):
            raise ValueError("last_absent_at must precede available_by")

        self._match_assertion(AvailabilityAssertion.AVAILABLE_BY, self.available_by, min)
        self._match_assertion(AvailabilityAssertion.NOT_BEFORE, self.not_before, max)
        self._match_assertion(AvailabilityAssertion.LAST_ABSENT_AT, self.last_absent_at, max)
        return self

    def _match_assertion(
        self,
        assertion: AvailabilityAssertion,
        value: datetime | None,
        strongest: Callable[[tuple[datetime, ...]], datetime],
    ) -> None:
        instants = tuple(
            item.asserted_instant for item in self.evidence if item.supports is assertion
        )
        if value is None:
            if instants:
                raise ValueError(f"evidence supports an absent {assertion.value} assertion")
            return
        if not instants:
            raise ValueError(f"{assertion.value} assertion requires supporting evidence")
        if value != strongest(instants):
            raise ValueError(
                f"{assertion.value} must equal the strongest supported evidence instant"
            )

    def state_at(self, cutoff_exclusive: datetime) -> EditionCutoffState:
        """Derive this edition's ADR 0005 state strictly before the exclusive cutoff."""

        _require_aware_cutoff(cutoff_exclusive)
        if self.available_by is not None and self.available_by < cutoff_exclusive:
            return EditionCutoffState.AVAILABLE
        if self.not_before is not None and self.not_before >= cutoff_exclusive:
            return EditionCutoffState.UNAVAILABLE
        if self.last_absent_at is not None and self.last_absent_at >= cutoff_exclusive:
            return EditionCutoffState.UNAVAILABLE
        return EditionCutoffState.UNKNOWN


class EditionSelection(StrictModel):
    """The fail-closed outcome of selecting an edition at one cutoff."""

    selected_edition: EditionCode | None = None
    abstention: EditionAbstentionReason | None = None

    @model_validator(mode="after")
    def require_exactly_one_outcome(self) -> "EditionSelection":
        if (self.selected_edition is None) == (self.abstention is None):
            raise ValueError("selection requires exactly one of selected_edition or abstention")
        return self


class EditionAvailabilityLedger(StrictModel):
    """One immutable, append-only availability snapshot for a single dataflow."""

    schema_version: Literal["1.0.0"] = AVAILABILITY_SCHEMA_VERSION
    ledger_id: Identifier
    dataflow_id: SdmxFlowReference
    dataflow_version: SdmxArtefactVersion
    generated_at: UtcDatetime
    captured_at: UtcDatetime
    complete_through: UtcDatetime
    cutoff_timezone: TimezoneName
    cutoff_semantics: Literal["inclusive_end_of_day"] = "inclusive_end_of_day"
    supersedes_ledger_id: Identifier | None = None
    editions: tuple[EditionAvailabilityRecord, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def enforce_ledger_integrity(self) -> "EditionAvailabilityLedger":
        if self.supersedes_ledger_id == self.ledger_id:
            raise ValueError("ledger cannot supersede itself")
        if self.complete_through > self.captured_at:
            raise ValueError("complete_through cannot follow captured_at")
        if self.captured_at > self.generated_at:
            raise ValueError("captured_at cannot follow generated_at")

        seen: set[str] = set()
        for record in self.editions:
            if record.edition in seen:
                raise ValueError(f"duplicate edition: {record.edition}")
            seen.add(record.edition)
            if record.available_by is not None and record.available_by > self.generated_at:
                raise ValueError(
                    f"edition {record.edition} available_by cannot follow generated_at"
                )
            if record.last_absent_at is not None and record.last_absent_at > self.generated_at:
                raise ValueError(
                    f"edition {record.edition} last_absent_at cannot follow generated_at"
                )
        return self

    def cutoff_exclusive(self, as_of: date) -> datetime:
        """Return the exclusive UTC instant ending the inclusive `as_of` day in the ledger zone."""

        zone = ZoneInfo(self.cutoff_timezone)
        return datetime.combine(_following_day(as_of, "as_of"), time.min, tzinfo=zone).astimezone(
            UTC
        )

    def select_edition(self, cutoff_exclusive: datetime) -> EditionSelection:
        """Select the newest definitely available edition, abstaining across any unknown."""

        _require_aware_cutoff(cutoff_exclusive)
        if cutoff_exclusive > self.complete_through:
            return EditionSelection(
                abstention=EditionAbstentionReason.CUTOFF_BEYOND_COMPLETE_THROUGH
            )

        states = {record.edition: record.state_at(cutoff_exclusive) for record in self.editions}
        available = [
            edition for edition, state in states.items() if state is EditionCutoffState.AVAILABLE
        ]
        if not available:
            return EditionSelection(
                abstention=EditionAbstentionReason.NO_EDITION_DEFINITELY_AVAILABLE
            )
        candidate = max(available)
        if any(
            edition > candidate and state is EditionCutoffState.UNKNOWN
            for edition, state in states.items()
        ):
            return EditionSelection(abstention=EditionAbstentionReason.UNRESOLVED_NEWER_EDITION)
        return EditionSelection(selected_edition=candidate)


def _following_day(value: date, field_name: str) -> date:
    try:
        return value + timedelta(days=1)
    except OverflowError as error:
        raise ValueError(f"{field_name} is out of the supported range") from error


def _require_aware_cutoff(cutoff_exclusive: datetime) -> None:
    if (
        cutoff_exclusive.tzinfo is None
        or cutoff_exclusive.tzinfo.utcoffset(cutoff_exclusive) is None
    ):
        raise ValueError("cutoff instants must be timezone-aware")
