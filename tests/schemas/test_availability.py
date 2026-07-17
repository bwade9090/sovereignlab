"""Validation and fail-closed selection tests for the edition-availability ledger."""

from datetime import UTC, date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import pytest
from pydantic import ValidationError

from sovereignlab.schemas import (
    AvailabilityAssertion,
    AvailabilityEvidence,
    AvailabilityEvidenceBasis,
    EditionAbstentionReason,
    EditionAvailabilityLedger,
    EditionAvailabilityRecord,
    EditionCutoffState,
    EditionResolutionStatus,
    EditionSelection,
)

FIRST_OBSERVED = AvailabilityEvidenceBasis.FIRST_OBSERVED_AT


def _evidence(
    *,
    basis: AvailabilityEvidenceBasis = FIRST_OBSERVED,
    supports: AvailabilityAssertion = AvailabilityAssertion.AVAILABLE_BY,
    asserted_instant: datetime = datetime(2024, 5, 10, 9, 0, tzinfo=UTC),
    **overrides: object,
) -> AvailabilityEvidence:
    return AvailabilityEvidence(
        basis=basis,
        supports=supports,
        asserted_instant=asserted_instant,
        source_manifest_ids=("example-capture-manifest",),
        **overrides,
    )


def _resolved_record(
    edition: str = "202405",
    available_by: datetime = datetime(2024, 5, 10, 9, 0, tzinfo=UTC),
) -> EditionAvailabilityRecord:
    return EditionAvailabilityRecord(
        edition=edition,
        status=EditionResolutionStatus.RESOLVED,
        available_by=available_by,
        evidence=(_evidence(asserted_instant=available_by),),
    )


def _ledger(
    editions: tuple[EditionAvailabilityRecord, ...],
    **overrides: object,
) -> EditionAvailabilityLedger:
    values: dict[str, object] = {
        "ledger_id": "test-ledger-001",
        "dataflow_id": "EXAMPLE:DSD_EXAMPLE@DF_EXAMPLE",
        "dataflow_version": "1.0",
        "generated_at": datetime(2026, 7, 14, 9, 0, tzinfo=UTC),
        "captured_at": datetime(2026, 7, 14, 8, 0, tzinfo=UTC),
        "complete_through": datetime(2026, 7, 14, 8, 0, tzinfo=UTC),
        "cutoff_timezone": "Asia/Seoul",
        "editions": editions,
    }
    values.update(overrides)
    return EditionAvailabilityLedger.model_validate(values)


def test_ledger_fixture_is_valid(availability_ledger: EditionAvailabilityLedger) -> None:
    assert availability_ledger.schema_version == "1.0.0"
    assert availability_ledger.cutoff_semantics == "inclusive_end_of_day"
    assert [record.edition for record in availability_ledger.editions] == ["202405", "202406"]


@pytest.mark.parametrize("edition", ["202400", "202413", "20241", "2024-1", "abcdef"])
def test_edition_codes_must_be_valid_month_labels(edition: str) -> None:
    with pytest.raises(ValidationError, match="edition"):
        _resolved_record(edition=edition)


def test_ledger_timestamps_must_be_utc() -> None:
    with pytest.raises(ValidationError, match="canonical UTC"):
        _ledger(
            (_resolved_record(),),
            generated_at=datetime(2026, 7, 14, 18, 0, tzinfo=ZoneInfo("Asia/Seoul")),
        )


def test_ledger_rejects_unknown_cutoff_timezone() -> None:
    with pytest.raises(ValidationError, match="unknown IANA timezone"):
        _ledger((_resolved_record(),), cutoff_timezone="Asia/Nowhere")


def test_ledger_cannot_supersede_itself() -> None:
    with pytest.raises(ValidationError, match="cannot supersede itself"):
        _ledger((_resolved_record(),), supersedes_ledger_id="test-ledger-001")


def test_ledger_accepts_a_distinct_predecessor() -> None:
    ledger = _ledger((_resolved_record(),), supersedes_ledger_id="test-ledger-000")

    assert ledger.supersedes_ledger_id == "test-ledger-000"


def test_complete_through_cannot_follow_captured_at() -> None:
    with pytest.raises(ValidationError, match="complete_through cannot follow"):
        _ledger(
            (_resolved_record(),),
            complete_through=datetime(2026, 7, 14, 8, 30, tzinfo=UTC),
        )


def test_captured_at_cannot_follow_generated_at() -> None:
    with pytest.raises(ValidationError, match="captured_at cannot follow"):
        _ledger(
            (_resolved_record(),),
            captured_at=datetime(2026, 7, 14, 9, 30, tzinfo=UTC),
            complete_through=datetime(2026, 7, 14, 8, 0, tzinfo=UTC),
        )


def test_ledger_rejects_duplicate_editions() -> None:
    with pytest.raises(ValidationError, match="duplicate edition"):
        _ledger((_resolved_record(), _resolved_record()))


def test_available_by_cannot_follow_ledger_generation() -> None:
    with pytest.raises(ValidationError, match="available_by cannot follow"):
        _ledger((_resolved_record(available_by=datetime(2026, 7, 14, 9, 30, tzinfo=UTC)),))


def test_last_absent_at_cannot_follow_ledger_generation() -> None:
    record = EditionAvailabilityRecord(
        edition="202406",
        status=EditionResolutionStatus.UNRESOLVED,
        last_absent_at=datetime(2026, 7, 14, 9, 30, tzinfo=UTC),
        evidence=(
            _evidence(
                supports=AvailabilityAssertion.LAST_ABSENT_AT,
                asserted_instant=datetime(2026, 7, 14, 9, 30, tzinfo=UTC),
            ),
        ),
    )

    with pytest.raises(ValidationError, match="last_absent_at cannot follow"):
        _ledger((record,))


def test_resolved_edition_requires_available_by() -> None:
    with pytest.raises(ValidationError, match="resolved edition requires available_by"):
        EditionAvailabilityRecord(edition="202405", status=EditionResolutionStatus.RESOLVED)


def test_unresolved_edition_cannot_invent_available_by() -> None:
    with pytest.raises(ValidationError, match="cannot invent available_by"):
        EditionAvailabilityRecord(
            edition="202405",
            status=EditionResolutionStatus.UNRESOLVED,
            available_by=datetime(2024, 5, 10, 9, 0, tzinfo=UTC),
            evidence=(_evidence(),),
        )


def test_not_before_cannot_follow_available_by() -> None:
    with pytest.raises(ValidationError, match="not_before cannot follow available_by"):
        EditionAvailabilityRecord(
            edition="202405",
            status=EditionResolutionStatus.RESOLVED,
            available_by=datetime(2024, 5, 10, 9, 0, tzinfo=UTC),
            not_before=datetime(2024, 5, 11, 9, 0, tzinfo=UTC),
            evidence=(
                _evidence(),
                _evidence(
                    supports=AvailabilityAssertion.NOT_BEFORE,
                    asserted_instant=datetime(2024, 5, 11, 9, 0, tzinfo=UTC),
                ),
            ),
        )


def test_last_absent_at_must_precede_available_by() -> None:
    with pytest.raises(ValidationError, match="last_absent_at must precede"):
        EditionAvailabilityRecord(
            edition="202405",
            status=EditionResolutionStatus.RESOLVED,
            available_by=datetime(2024, 5, 10, 9, 0, tzinfo=UTC),
            last_absent_at=datetime(2024, 5, 10, 9, 0, tzinfo=UTC),
            evidence=(
                _evidence(),
                _evidence(
                    supports=AvailabilityAssertion.LAST_ABSENT_AT,
                    asserted_instant=datetime(2024, 5, 10, 9, 0, tzinfo=UTC),
                ),
            ),
        )


def test_bounded_window_with_not_before_is_valid() -> None:
    record = EditionAvailabilityRecord(
        edition="202405",
        status=EditionResolutionStatus.RESOLVED,
        available_by=datetime(2024, 5, 10, 9, 0, tzinfo=UTC),
        not_before=datetime(2024, 5, 9, 9, 0, tzinfo=UTC),
        evidence=(
            _evidence(),
            _evidence(
                basis=AvailabilityEvidenceBasis.PUBLISHER_TIMESTAMP,
                supports=AvailabilityAssertion.NOT_BEFORE,
                asserted_instant=datetime(2024, 5, 9, 9, 0, tzinfo=UTC),
            ),
        ),
    )

    assert record.not_before is not None


def test_assertion_without_record_value_is_rejected() -> None:
    with pytest.raises(ValidationError, match="absent not_before assertion"):
        EditionAvailabilityRecord(
            edition="202405",
            status=EditionResolutionStatus.RESOLVED,
            available_by=datetime(2024, 5, 10, 9, 0, tzinfo=UTC),
            evidence=(
                _evidence(),
                _evidence(
                    supports=AvailabilityAssertion.NOT_BEFORE,
                    asserted_instant=datetime(2024, 5, 9, 9, 0, tzinfo=UTC),
                ),
            ),
        )


def test_record_value_without_evidence_is_rejected() -> None:
    with pytest.raises(ValidationError, match="available_by assertion requires supporting"):
        EditionAvailabilityRecord(
            edition="202405",
            status=EditionResolutionStatus.RESOLVED,
            available_by=datetime(2024, 5, 10, 9, 0, tzinfo=UTC),
        )


def test_record_value_must_match_strongest_evidence_instant() -> None:
    with pytest.raises(ValidationError, match="strongest supported evidence instant"):
        EditionAvailabilityRecord(
            edition="202405",
            status=EditionResolutionStatus.RESOLVED,
            available_by=datetime(2024, 5, 10, 9, 0, tzinfo=UTC),
            evidence=(_evidence(asserted_instant=datetime(2024, 5, 9, 9, 0, tzinfo=UTC)),),
        )


def test_available_by_uses_the_earliest_supported_instant() -> None:
    early = datetime(2024, 5, 9, 9, 0, tzinfo=UTC)
    record = EditionAvailabilityRecord(
        edition="202405",
        status=EditionResolutionStatus.RESOLVED,
        available_by=early,
        evidence=(
            _evidence(asserted_instant=early),
            _evidence(
                basis=AvailabilityEvidenceBasis.PUBLISHER_TIMESTAMP,
                asserted_instant=datetime(2024, 5, 10, 9, 0, tzinfo=UTC),
            ),
        ),
    )

    assert record.available_by == early


def test_evidence_manifest_ids_must_be_unique() -> None:
    with pytest.raises(ValidationError, match="source_manifest_ids must be unique"):
        AvailabilityEvidence(
            basis=FIRST_OBSERVED,
            supports=AvailabilityAssertion.AVAILABLE_BY,
            asserted_instant=datetime(2024, 5, 10, 9, 0, tzinfo=UTC),
            source_manifest_ids=("example-capture-manifest", "example-capture-manifest"),
        )


def test_evidence_instants_must_be_utc() -> None:
    with pytest.raises(ValidationError, match="canonical UTC"):
        _evidence(asserted_instant=datetime(2024, 5, 10, 9, 0, tzinfo=timezone(timedelta(hours=9))))


def test_publisher_fields_require_the_conservative_basis() -> None:
    with pytest.raises(ValidationError, match="publisher date fields require"):
        _evidence(publisher_date=date(2024, 5, 9))


def test_conservative_basis_requires_publisher_date_and_timezone() -> None:
    with pytest.raises(ValidationError, match="requires publisher_date and"):
        _evidence(
            basis=AvailabilityEvidenceBasis.PUBLISHER_DATE_CONSERVATIVE,
            publisher_date=date(2024, 5, 9),
        )


def test_conservative_basis_supports_only_available_by() -> None:
    with pytest.raises(ValidationError, match="only support available_by"):
        _evidence(
            basis=AvailabilityEvidenceBasis.PUBLISHER_DATE_CONSERVATIVE,
            supports=AvailabilityAssertion.NOT_BEFORE,
            asserted_instant=datetime(2024, 5, 9, 15, 0, tzinfo=UTC),
            publisher_date=date(2024, 5, 9),
            publisher_timezone="Asia/Seoul",
        )


def test_conservative_assertion_must_start_the_following_publisher_day() -> None:
    with pytest.raises(ValidationError, match="following publisher-local day"):
        _evidence(
            basis=AvailabilityEvidenceBasis.PUBLISHER_DATE_CONSERVATIVE,
            asserted_instant=datetime(2024, 5, 9, 0, 0, tzinfo=UTC),
            publisher_date=date(2024, 5, 9),
            publisher_timezone="Asia/Seoul",
        )


def test_conservative_assertion_accepts_the_safe_instant() -> None:
    evidence = _evidence(
        basis=AvailabilityEvidenceBasis.PUBLISHER_DATE_CONSERVATIVE,
        asserted_instant=datetime(2024, 5, 9, 15, 0, tzinfo=UTC),
        publisher_date=date(2024, 5, 9),
        publisher_timezone="Asia/Seoul",
    )

    assert evidence.publisher_timezone == "Asia/Seoul"


def test_constraint_fields_require_the_constraint_basis() -> None:
    with pytest.raises(ValidationError, match="constraint fields require"):
        _evidence(constraint_id="CR_A_DSD_EXAMPLE@DF_EXAMPLE")


def test_constraint_basis_requires_constraint_identity() -> None:
    with pytest.raises(ValidationError, match="requires constraint_id and"):
        _evidence(basis=AvailabilityEvidenceBasis.SDMX_CONSTRAINT_VALID_FROM)


def test_constraint_id_accepts_the_official_at_separator() -> None:
    evidence = _evidence(
        basis=AvailabilityEvidenceBasis.SDMX_CONSTRAINT_VALID_FROM,
        constraint_id="CR_A_DSD_STES_REVISIONS@DF_STES_REVISIONS",
        constraint_version="4.0",
    )

    assert evidence.constraint_id == "CR_A_DSD_STES_REVISIONS@DF_STES_REVISIONS"


def test_selection_outcome_must_be_exclusive() -> None:
    with pytest.raises(ValidationError, match="exactly one"):
        EditionSelection()
    with pytest.raises(ValidationError, match="exactly one"):
        EditionSelection(
            selected_edition="202405",
            abstention=EditionAbstentionReason.NO_EDITION_DEFINITELY_AVAILABLE,
        )


def test_cutoff_exclusive_ends_the_seoul_day(
    availability_ledger: EditionAvailabilityLedger,
) -> None:
    cutoff = availability_ledger.cutoff_exclusive(date(2024, 5, 31))

    assert cutoff == datetime(2024, 6, 1, 0, 0, tzinfo=ZoneInfo("Asia/Seoul"))
    assert cutoff == datetime(2024, 5, 31, 15, 0, tzinfo=UTC)


def test_state_derivation_matches_adr_0005(
    availability_ledger: EditionAvailabilityLedger,
) -> None:
    may, june = availability_ledger.editions
    cutoff = availability_ledger.cutoff_exclusive(date(2024, 5, 31))

    assert may.state_at(cutoff) is EditionCutoffState.AVAILABLE
    assert june.state_at(cutoff) is EditionCutoffState.UNAVAILABLE
    assert may.state_at(datetime(2024, 5, 1, 0, 0, tzinfo=UTC)) is EditionCutoffState.UNKNOWN


def test_not_before_proves_unavailability() -> None:
    record = EditionAvailabilityRecord(
        edition="202406",
        status=EditionResolutionStatus.UNRESOLVED,
        not_before=datetime(2024, 6, 10, 9, 0, tzinfo=UTC),
        evidence=(
            _evidence(
                basis=AvailabilityEvidenceBasis.PUBLISHER_TIMESTAMP,
                supports=AvailabilityAssertion.NOT_BEFORE,
                asserted_instant=datetime(2024, 6, 10, 9, 0, tzinfo=UTC),
            ),
        ),
    )

    assert record.state_at(datetime(2024, 6, 1, 0, 0, tzinfo=UTC)) is (
        EditionCutoffState.UNAVAILABLE
    )


def test_states_and_selection_require_aware_cutoffs(
    availability_ledger: EditionAvailabilityLedger,
) -> None:
    naive_cutoff = datetime(2024, 6, 1, 0, 0)

    with pytest.raises(ValueError, match="timezone-aware"):
        availability_ledger.editions[0].state_at(naive_cutoff)
    with pytest.raises(ValueError, match="timezone-aware"):
        availability_ledger.select_edition(naive_cutoff)


def test_selection_picks_the_newest_definitely_available_edition(
    availability_ledger: EditionAvailabilityLedger,
) -> None:
    at_may = availability_ledger.select_edition(
        availability_ledger.cutoff_exclusive(date(2024, 5, 31))
    )
    at_july = availability_ledger.select_edition(
        availability_ledger.cutoff_exclusive(date(2024, 7, 31))
    )

    assert at_may.selected_edition == "202405"
    assert at_july.selected_edition == "202406"


def test_selection_abstains_beyond_complete_through(
    availability_ledger: EditionAvailabilityLedger,
) -> None:
    selection = availability_ledger.select_edition(
        availability_ledger.cutoff_exclusive(date(2026, 7, 20))
    )

    assert selection.abstention is EditionAbstentionReason.CUTOFF_BEYOND_COMPLETE_THROUGH


def test_mid_day_capture_cannot_answer_that_same_seoul_day(
    availability_ledger: EditionAvailabilityLedger,
) -> None:
    same_day = availability_ledger.select_edition(
        availability_ledger.cutoff_exclusive(date(2026, 7, 14))
    )
    previous_day = availability_ledger.select_edition(
        availability_ledger.cutoff_exclusive(date(2026, 7, 13))
    )

    assert same_day.abstention is EditionAbstentionReason.CUTOFF_BEYOND_COMPLETE_THROUGH
    assert previous_day.selected_edition == "202406"


def test_cutoff_exactly_at_complete_through_is_answerable() -> None:
    boundary = datetime(2024, 5, 31, 15, 0, tzinfo=UTC)
    ledger = _ledger(
        (_resolved_record(),),
        captured_at=boundary,
        complete_through=boundary,
    )

    selection = ledger.select_edition(ledger.cutoff_exclusive(date(2024, 5, 31)))

    assert ledger.cutoff_exclusive(date(2024, 5, 31)) == boundary
    assert selection.selected_edition == "202405"


def test_conservative_assertion_survives_a_dst_gap() -> None:
    evidence = _evidence(
        basis=AvailabilityEvidenceBasis.PUBLISHER_DATE_CONSERVATIVE,
        asserted_instant=datetime(2018, 11, 4, 3, 0, tzinfo=UTC),
        publisher_date=date(2018, 11, 3),
        publisher_timezone="America/Sao_Paulo",
    )

    assert evidence.asserted_instant == datetime(2018, 11, 4, 3, 0, tzinfo=UTC)


def test_conservative_publisher_date_must_stay_in_range() -> None:
    with pytest.raises(ValidationError, match="out of the supported range"):
        _evidence(
            basis=AvailabilityEvidenceBasis.PUBLISHER_DATE_CONSERVATIVE,
            asserted_instant=datetime(2024, 5, 9, 15, 0, tzinfo=UTC),
            publisher_date=date(9999, 12, 31),
            publisher_timezone="Asia/Seoul",
        )


def test_cutoff_exclusive_rejects_out_of_range_as_of(
    availability_ledger: EditionAvailabilityLedger,
) -> None:
    with pytest.raises(ValueError, match="out of the supported range"):
        availability_ledger.cutoff_exclusive(date(9999, 12, 31))


def test_selection_abstains_when_nothing_is_definitely_available(
    availability_ledger: EditionAvailabilityLedger,
) -> None:
    selection = availability_ledger.select_edition(
        availability_ledger.cutoff_exclusive(date(2024, 1, 31))
    )

    assert selection.abstention is EditionAbstentionReason.NO_EDITION_DEFINITELY_AVAILABLE


def test_selection_abstains_across_an_unresolved_newer_frontier() -> None:
    unresolved_newer = EditionAvailabilityRecord(
        edition="202406",
        status=EditionResolutionStatus.UNRESOLVED,
    )
    ledger = _ledger((_resolved_record(), unresolved_newer))

    selection = ledger.select_edition(ledger.cutoff_exclusive(date(2024, 5, 31)))

    assert selection.abstention is EditionAbstentionReason.UNRESOLVED_NEWER_EDITION


def test_unresolved_older_edition_does_not_block_selection() -> None:
    unresolved_older = EditionAvailabilityRecord(
        edition="202404",
        status=EditionResolutionStatus.UNRESOLVED,
    )
    ledger = _ledger((unresolved_older, _resolved_record()))

    selection = ledger.select_edition(ledger.cutoff_exclusive(date(2024, 5, 31)))

    assert selection.selected_edition == "202405"
