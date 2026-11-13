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
from sovereignlab.snapshots import load_committed_snapshot_registry
from sovereignlab.vintage import (
    CLI_STES_BINDING,
    COMMITTED_ACTIVE_STES_LEDGER_ID,
    GDP_STES_BINDING,
    STES_REGISTRY_DESCRIPTOR_SHA256,
    StesRegistry,
    StesRegistryEntry,
    StesSeriesBinding,
    execute_stes_as_of_call,
    load_committed_stes_registry,
)

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
CLI_SOURCE_ID = "oecd-stes-cli-kor-li-aa-20260717t115302688498z"
_CSV_HEADER = "REF_AREA,FREQ,MEASURE,UNIT_MEASURE,ACTIVITY,EDITION,TIME_PERIOD,OBS_VALUE"


@pytest.fixture(scope="module")
def registry() -> StesRegistry:
    return load_committed_stes_registry(REPOSITORY_ROOT)


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
    assert evidence.ledger_id == COMMITTED_ACTIVE_STES_LEDGER_ID
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
    assert registry.descriptor_sha256 == STES_REGISTRY_DESCRIPTOR_SHA256
    assert registry.active_ledger.ledger_id == COMMITTED_ACTIVE_STES_LEDGER_ID
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
        load_committed_stes_registry(tmp_path)


def test_a_later_weekly_capture_stays_archive_only(
    weekly_capture_after_v1: tuple[Path, HarvestSummary],
) -> None:
    # ADR 0010: the v1 registries list their files explicitly, so a new capture changes nothing
    # the tools or the benchmark can see until a new registry version admits it.
    root, _ = weekly_capture_after_v1

    assert load_committed_stes_registry(root).descriptor_sha256 == STES_REGISTRY_DESCRIPTOR_SHA256
    load_committed_snapshot_registry(root)
