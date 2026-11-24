"""Behaviour of the historical STES registry and its typed tool adapter."""

import hashlib
import json
import shutil
from datetime import date
from pathlib import Path

import pytest

from sovereignlab.artifacts import SourceArtifact
from sovereignlab.harvest.weekly import HarvestSummary
from sovereignlab.schemas import (
    SourceManifest,
    StesAsOfArguments,
    StesAsOfCall,
    StesAsOfResult,
    ToolOutcomeStatus,
)
from sovereignlab.snapshots import (
    COMMITTED_SNAPSHOT_REGISTRIES,
    load_committed_snapshot_registry,
)
from sovereignlab.vintage import (
    CLI_STES_BINDING,
    COMMITTED_STES_REGISTRIES,
    GDP_STES_BINDING,
    StesRegistry,
    StesRegistryEntry,
    StesSeriesBinding,
    execute_stes_as_of_call,
    load_committed_stes_registry,
)

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
CLI_SOURCE_ID = "oecd-stes-cli-kor-li-aa-20260717t115302688498z"
LEDGER_ID = "oecd-stes-ledger-20260717t115242998550z"
V2_CLI_SOURCE_ID = "oecd-stes-cli-kor-li-aa-20261124t010648941132z"
V2_LEDGER_ID = "oecd-stes-ledger-20261123t104316607555z"
_CSV_HEADER = "REF_AREA,FREQ,MEASURE,UNIT_MEASURE,ACTIVITY,EDITION,TIME_PERIOD,OBS_VALUE"


@pytest.fixture(scope="module")
def registry() -> StesRegistry:
    return load_committed_stes_registry(REPOSITORY_ROOT, version=1)


@pytest.fixture(scope="module")
def registry_v2() -> StesRegistry:
    return load_committed_stes_registry(REPOSITORY_ROOT, version=2)


def _resolve(
    registry: StesRegistry,
    as_of: date,
    *,
    binding: StesSeriesBinding = CLI_STES_BINDING,
    period: str = "2026-05",
) -> StesAsOfResult:
    return execute_stes_as_of_call(
        call=StesAsOfCall(
            call_id="stes-call-01",
            tool_name="resolve_stes_as_of",
            arguments=StesAsOfArguments(
                ref_area=binding.ref_area,
                freq=binding.freq,
                measure=binding.measure,
                unit_measure=binding.unit_measure,
                activity=binding.activity,
                period=period,
                as_of=as_of,
                normalization_rule_id=binding.normalization_rule_id,
            ),
        ),
        registry=registry,
    )


def _reason(result: StesAsOfResult) -> str:
    assert result.status is ToolOutcomeStatus.ABSTAINED
    assert result.payload is None
    assert result.abstention is not None
    return result.abstention.reason_code


def test_resolves_the_cli_value_from_the_edition_available_at_the_cutoff(
    registry: StesRegistry,
) -> None:
    result = _resolve(registry, date(2026, 7, 9))

    assert result.status is ToolOutcomeStatus.SUCCESS
    evidence = result.payload
    assert evidence is not None
    assert evidence.selected_edition == "202607"
    assert evidence.period == "2026-05"
    assert evidence.observation.raw_value == "102.66"
    assert evidence.observation.display_value == "102.66"
    assert evidence.observation.canonical_unit == "oecd_amplitude_adjusted_index"
    assert evidence.source_id == CLI_SOURCE_ID
    assert evidence.ledger_id == LEDGER_ID
    assert evidence.rights_decision_id == CLI_STES_BINDING.rights_decision_id


@pytest.mark.parametrize(
    ("as_of", "reason"),
    [
        # Edition 202607 is first provably available on 2026-07-08; earlier editions have no
        # availability evidence, so nothing may be answered before that day.
        (date(2026, 6, 30), "no_edition_definitely_available"),
        (date(2026, 7, 7), "no_edition_definitely_available"),
        # The ledger was captured mid-day on 2026-07-17, so it cannot vouch for the end of
        # that Seoul day or anything later.
        (date(2026, 7, 17), "cutoff_beyond_complete_through"),
        (date(2026, 8, 15), "cutoff_beyond_complete_through"),
    ],
)
def test_cutoffs_the_ledger_cannot_vouch_for_abstain(
    registry: StesRegistry,
    as_of: date,
    reason: str,
) -> None:
    result = _resolve(registry, as_of)

    assert _reason(result) == reason
    assert "102.66" not in result.model_dump_json()


@pytest.mark.parametrize("as_of", [date(2026, 7, 8), date(2026, 7, 16)])
def test_the_answerable_window_is_inclusive_at_both_ends(
    registry: StesRegistry,
    as_of: date,
) -> None:
    assert _resolve(registry, as_of).status is ToolOutcomeStatus.SUCCESS


def test_series_without_owner_approved_raw_evidence_abstains(registry: StesRegistry) -> None:
    result = _resolve(registry, date(2026, 7, 9), binding=GDP_STES_BINDING, period="2026-Q1")

    assert _reason(result) == "public_raw_evidence_unavailable"


def test_period_absent_from_the_selected_edition_abstains(registry: StesRegistry) -> None:
    assert _reason(_resolve(registry, date(2026, 7, 9), period="2030-01")) == "missing_selected_row"


def _cli_artifact(registry: StesRegistry, csv_text: str) -> SourceArtifact:
    """Clone the committed CLI artifact around a small synthetic archive."""

    base = registry.entry_for(CLI_STES_BINDING.scope).data_artifact
    assert base is not None
    payload = csv_text.encode("utf-8")
    data = base.manifest.model_dump(mode="python")
    data.update(byte_size=len(payload), content_sha256=hashlib.sha256(payload).hexdigest())
    manifest = SourceManifest.model_validate(data)
    return SourceArtifact(
        manifest=manifest,
        manifest_bytes=manifest.model_dump_json().encode("utf-8"),
        archive_bytes=payload,
    )


def test_non_decimal_observation_abstains(registry: StesRegistry) -> None:
    artifact = _cli_artifact(registry, f"{_CSV_HEADER}\nKOR,M,LI_AA,IX,_T,202607,2026-05,NaN\n")
    edited = StesRegistry(
        registry_id="test-stes-registry",
        entries=(StesRegistryEntry(binding=CLI_STES_BINDING, data_artifact=artifact),),
        support_artifacts=registry.support_artifacts,
        ledger_artifacts=registry.ledger_artifacts,
        catalog_artifacts=registry.catalog_artifacts,
        active_ledger_id=registry.active_ledger_id,
        complete_through_source_id=registry.complete_through_source_id,
        captured_at_source_id=registry.captured_at_source_id,
    )

    assert _reason(_resolve(edited, date(2026, 7, 9))) == "invalid_source_value"


def test_committed_registry_digest_is_pinned(registry: StesRegistry) -> None:
    assert registry.descriptor_sha256 == COMMITTED_STES_REGISTRIES[1].descriptor_sha256
    assert registry.active_ledger.ledger_id == LEDGER_ID
    summary = registry.entry_for(CLI_STES_BINDING.scope).archive_summary
    assert summary is not None
    assert (summary.first_edition, summary.last_edition) == ("200604", "202607")


def test_loader_rejects_an_archive_holding_a_neighboring_series(
    registry: StesRegistry,
    tmp_path: Path,
) -> None:
    for relative in ("data/manifests", "data/availability", "data/rights"):
        shutil.copytree(REPOSITORY_ROOT / relative, tmp_path / relative)
    archive_directory = tmp_path / "data/archive/oecd-stes"
    archive_directory.mkdir(parents=True)
    for path in (REPOSITORY_ROOT / "data/archive/oecd-stes").glob("*.xml"):
        shutil.copy(path, archive_directory)
    # The normalised CLI (LI_NM) is a neighboring measure outside the approved LI_AA scope.
    artifact = _cli_artifact(
        registry,
        f"{_CSV_HEADER}\n"
        "KOR,M,LI_AA,IX,_T,202607,2026-05,102.66\n"
        "KOR,M,LI_NM,IX,_T,202607,2026-05,101.10\n",
    )
    (archive_directory / f"{CLI_SOURCE_ID}.csv").write_bytes(artifact.archive_bytes)
    manifest = json.loads(artifact.manifest_bytes)
    (tmp_path / "data/manifests" / f"{CLI_SOURCE_ID}.json").write_text(
        json.dumps({key: value for key, value in manifest.items() if value is not None}),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="neighboring series"):
        load_committed_stes_registry(tmp_path, version=1)


def test_a_later_weekly_capture_stays_archive_only(
    fresh_weekly_capture: tuple[Path, HarvestSummary],
) -> None:
    # ADR 0010: every admitted registry version lists its files explicitly, so a new capture
    # changes nothing the tools or the benchmark can see until a later version admits it.
    root, _ = fresh_weekly_capture

    for version, committed in COMMITTED_STES_REGISTRIES.items():
        loaded = load_committed_stes_registry(root, version=version)
        assert loaded.descriptor_sha256 == committed.descriptor_sha256
    for version in COMMITTED_SNAPSHOT_REGISTRIES:
        load_committed_snapshot_registry(root, version=version)


# --- evidence v2: the 2026-11-24 archive and the ledgers through 2026-11-23 (ADR 0013) -------


def test_v2_admits_the_november_archive_and_ledgers(registry_v2: StesRegistry) -> None:
    assert registry_v2.descriptor_sha256 == COMMITTED_STES_REGISTRIES[2].descriptor_sha256
    assert registry_v2.active_ledger.ledger_id == V2_LEDGER_ID
    summary = registry_v2.entry_for(CLI_STES_BINDING.scope).archive_summary
    assert summary is not None
    assert (summary.first_edition, summary.last_edition) == ("200604", "202611")


def test_v2_keeps_the_v1_answer_for_july_cutoffs(
    registry: StesRegistry,
    registry_v2: StesRegistry,
) -> None:
    # Admitting newer evidence never changes what an older cutoff could see.
    old = _resolve(registry, date(2026, 7, 9)).payload
    new = _resolve(registry_v2, date(2026, 7, 9)).payload

    assert old is not None and new is not None
    assert (new.selected_edition, new.observation) == (old.selected_edition, old.observation)
    assert (new.source_id, new.ledger_id) == (V2_CLI_SOURCE_ID, V2_LEDGER_ID)


@pytest.mark.parametrize(
    ("as_of", "edition", "value"),
    [
        (date(2026, 7, 9), "202607", "102.66"),
        (date(2026, 10, 8), "202610", "102.33"),
        (date(2026, 11, 8), "202610", "102.33"),
        (date(2026, 11, 10), "202611", "102.29"),
        (date(2026, 11, 22), "202611", "102.29"),
    ],
)
def test_v2_answers_may_2026_from_the_edition_available_at_each_cutoff(
    registry_v2: StesRegistry,
    as_of: date,
    edition: str,
    value: str,
) -> None:
    # The same month, revised twice: answering 102.29 at the July cutoff leaks the future.
    evidence = _resolve(registry_v2, as_of).payload

    assert evidence is not None
    assert (evidence.selected_edition, evidence.observation.raw_value) == (edition, value)


@pytest.mark.parametrize(
    ("as_of", "reason"),
    [
        # Editions 202608-202610 were absent at the 2026-07-17 capture and are provably
        # available only from 2026-10-08, so the weekly capture gap leaves this span unresolved.
        (date(2026, 7, 17), "unresolved_newer_edition"),
        (date(2026, 9, 15), "unresolved_newer_edition"),
        (date(2026, 10, 7), "unresolved_newer_edition"),
        # Edition 202611 was absent at 09:45 UTC on 2026-11-09 and available by 12:57 UTC on
        # 2026-11-10, so the end of 2026-11-09 in Seoul falls inside that window.
        (date(2026, 11, 9), "unresolved_newer_edition"),
        # The newest ledger was captured mid-day on 2026-11-23.
        (date(2026, 11, 23), "cutoff_beyond_complete_through"),
    ],
)
def test_v2_abstains_where_availability_is_unproven(
    registry_v2: StesRegistry,
    as_of: date,
    reason: str,
) -> None:
    assert _reason(_resolve(registry_v2, as_of)) == reason


def test_v2_has_no_month_before_an_edition_published_it(registry_v2: StesRegistry) -> None:
    # Edition 202610 ends at September 2026; October first appears in edition 202611.
    assert _reason(_resolve(registry_v2, date(2026, 10, 8), period="2026-10")) == (
        "missing_selected_row"
    )
    evidence = _resolve(registry_v2, date(2026, 11, 10), period="2026-10").payload
    assert evidence is not None
    assert evidence.observation.raw_value == "101.98"
