"""Behaviour of the latest-only snapshot registry and reader."""

import hashlib
import json
import shutil
from collections.abc import Callable
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

import pytest

from sovereignlab.artifacts import SourceArtifact
from sovereignlab.schemas import (
    SnapshotAsOfArguments,
    SnapshotAsOfCall,
    SnapshotAsOfResult,
    SourceManifest,
    ToolOutcomeStatus,
)
from sovereignlab.snapshots import (
    COMMITTED_RIGHTS_CATALOG_PATHS,
    COMMITTED_SNAPSHOT_LOCATIONS,
    ECOS_CURRENT_ACCOUNT_BINDING,
    ECOS_GDP_BINDING,
    KOSIS_CPI_BINDING,
    SNAPSHOT_REGISTRY_DESCRIPTOR_SHA256,
    SnapshotAbstentionReason,
    SnapshotRegistry,
    SnapshotRegistryEntry,
    SnapshotSeriesBinding,
    load_committed_snapshot_registry,
    load_snapshot_registry,
    read_snapshot_as_of,
)

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
CAPTURE_DAY = date(2026, 7, 17)


@pytest.fixture(scope="module")
def registry() -> SnapshotRegistry:
    return load_committed_snapshot_registry(REPOSITORY_ROOT)


def _read(
    registry: SnapshotRegistry,
    binding: SnapshotSeriesBinding,
    period: str,
    as_of: date = CAPTURE_DAY,
) -> SnapshotAsOfResult:
    return read_snapshot_as_of(
        call=SnapshotAsOfCall(
            call_id="snapshot-call-01",
            tool_name="read_snapshot_as_of",
            arguments=SnapshotAsOfArguments(
                source_system=binding.source_system,
                table_id=binding.table_id,
                item_id=binding.item_id,
                period=period,
                as_of=as_of,
                normalization_rule_id=binding.normalization_rule_id,
            ),
        ),
        registry=registry,
    )


def _committed_artifact(
    registry: SnapshotRegistry, binding: SnapshotSeriesBinding
) -> SourceArtifact:
    (artifact,) = registry.entry_for(*binding.scope).artifacts
    return artifact


def _artifact(base: SourceArtifact, payload: bytes, **manifest_updates: Any) -> SourceArtifact:
    """Clone a committed artifact around new archive bytes and manifest fields."""

    data = base.manifest.model_dump(mode="python")
    data.update(
        byte_size=len(payload),
        content_sha256=hashlib.sha256(payload).hexdigest(),
        **manifest_updates,
    )
    manifest = SourceManifest.model_validate(data)
    return SourceArtifact(
        manifest=manifest,
        manifest_bytes=manifest.model_dump_json().encode("utf-8"),
        archive_bytes=payload,
    )


def _registry_with(
    base: SnapshotRegistry,
    binding: SnapshotSeriesBinding,
    *artifacts: SourceArtifact,
) -> SnapshotRegistry:
    return SnapshotRegistry(
        registry_id="test-snapshot-registry",
        entries=(SnapshotRegistryEntry(binding=binding, artifacts=artifacts),),
        catalog_artifacts=base.catalog_artifacts,
    )


def _edited_ecos_payload(
    base: SourceArtifact, edit: Callable[[list[dict[str, Any]]], None]
) -> bytes:
    document = json.loads(base.archive_bytes)
    edit(document["StatisticSearch"]["row"])
    document["StatisticSearch"]["list_total_count"] = len(document["StatisticSearch"]["row"])
    return json.dumps(document, ensure_ascii=False).encode("utf-8")


@pytest.mark.parametrize(
    ("binding", "period", "raw_value", "display_value", "unit"),
    [
        (ECOS_GDP_BINDING, "2026Q1", "596692.8", "596692.8", "billion_krw"),
        (ECOS_CURRENT_ACCOUNT_BINDING, "202605", "38121.1", "38121.1", "million_usd"),
        (KOSIS_CPI_BINDING, "202606", "119.99", "119.99", "index_2020_100"),
    ],
    ids=["ecos-gdp", "ecos-current-account", "kosis-cpi"],
)
def test_reads_each_approved_series_with_its_provenance(
    registry: SnapshotRegistry,
    binding: SnapshotSeriesBinding,
    period: str,
    raw_value: str,
    display_value: str,
    unit: str,
) -> None:
    result = _read(registry, binding, period)

    assert result.status is ToolOutcomeStatus.SUCCESS
    evidence = result.payload
    assert evidence is not None
    assert evidence.observation.raw_value == raw_value
    assert evidence.observation.display_value == display_value
    assert evidence.observation.canonical_unit == unit
    manifest = _committed_artifact(registry, binding).manifest
    assert evidence.source_id == manifest.source_id
    assert evidence.source_sha256 == manifest.content_sha256
    assert evidence.rights_decision_id == binding.rights_decision_id
    assert evidence.source_retrieved_at == manifest.retrieved_at


def test_cutoff_before_the_capture_abstains_without_exposing_the_value(
    registry: SnapshotRegistry,
) -> None:
    result = _read(registry, ECOS_GDP_BINDING, "2026Q1", as_of=date(2026, 7, 16))

    assert result.status is ToolOutcomeStatus.ABSTAINED
    assert result.payload is None
    assert result.abstention is not None
    assert result.abstention.reason_code == "no_snapshot_available_by_cutoff"
    assert "596692.8" not in result.model_dump_json()


def test_a_capture_after_the_seoul_end_of_day_is_not_visible_at_that_cutoff(
    registry: SnapshotRegistry,
) -> None:
    # 16:00 UTC on the 17th is already the 18th in Seoul, although the UTC date is the 17th.
    base = _committed_artifact(registry, ECOS_GDP_BINDING)
    late = _artifact(
        base,
        base.archive_bytes,
        retrieved_at=datetime(2026, 7, 17, 16, 0, tzinfo=UTC),
    )
    late_registry = _registry_with(registry, ECOS_GDP_BINDING, late)

    assert _read(late_registry, ECOS_GDP_BINDING, "2026Q1", as_of=date(2026, 7, 17)).status is (
        ToolOutcomeStatus.ABSTAINED
    )
    assert _read(late_registry, ECOS_GDP_BINDING, "2026Q1", as_of=date(2026, 7, 18)).status is (
        ToolOutcomeStatus.SUCCESS
    )


def test_reads_the_newest_snapshot_captured_by_the_cutoff(registry: SnapshotRegistry) -> None:
    base = _committed_artifact(registry, ECOS_GDP_BINDING)

    def revise(rows: list[dict[str, Any]]) -> None:
        next(row for row in rows if row["TIME"] == "2026Q1")["DATA_VALUE"] = "600000.5"

    later = _artifact(
        base,
        _edited_ecos_payload(base, revise),
        source_id="ecos-200y108-10601-20260801t000000000000z",
        published_on=date(2026, 8, 1),
        retrieved_at=datetime(2026, 8, 1, 0, 0, tzinfo=UTC),
    )
    two_captures = _registry_with(registry, ECOS_GDP_BINDING, later, base)

    before = _read(two_captures, ECOS_GDP_BINDING, "2026Q1", as_of=date(2026, 7, 31))
    after = _read(two_captures, ECOS_GDP_BINDING, "2026Q1", as_of=date(2026, 8, 1))

    assert before.payload is not None and before.payload.observation.raw_value == "596692.8"
    assert after.payload is not None and after.payload.observation.raw_value == "600000.5"
    assert after.payload.source_id == later.manifest.source_id


def _drop_item_code(rows: list[dict[str, Any]]) -> None:
    rows[0]["ITEM_CODE1"] = "10602"


def _add_sub_item(rows: list[dict[str, Any]]) -> None:
    rows[0]["ITEM_CODE2"] = "A"


def _change_unit(rows: list[dict[str, Any]]) -> None:
    rows[0]["UNIT_NAME"] = "조원"


def _duplicate_period(rows: list[dict[str, Any]]) -> None:
    rows.append(dict(next(row for row in rows if row["TIME"] == "2026Q1")))


def _set_value(value: object) -> Callable[[list[dict[str, Any]]], None]:
    def edit(rows: list[dict[str, Any]]) -> None:
        next(row for row in rows if row["TIME"] == "2026Q1")["DATA_VALUE"] = value

    return edit


@pytest.mark.parametrize(
    ("edit", "reason"),
    [
        (_drop_item_code, SnapshotAbstentionReason.SOURCE_SCOPE_MISMATCH),
        (_add_sub_item, SnapshotAbstentionReason.SOURCE_SCOPE_MISMATCH),
        (_change_unit, SnapshotAbstentionReason.SOURCE_UNIT_MISMATCH),
        (_duplicate_period, SnapshotAbstentionReason.DUPLICATE_SELECTED_ROW),
        (_set_value(""), SnapshotAbstentionReason.BLANK_SELECTED_OBSERVATION),
        (_set_value(None), SnapshotAbstentionReason.BLANK_SELECTED_OBSERVATION),
        (_set_value("596,692.8"), SnapshotAbstentionReason.INVALID_SOURCE_VALUE),
        (_set_value(596692.8), SnapshotAbstentionReason.INVALID_SOURCE_VALUE),
    ],
    ids=[
        "neighbor-item",
        "sub-item",
        "unit",
        "duplicate",
        "blank",
        "null",
        "grouped-digits",
        "float",
    ],
)
def test_unusable_ecos_rows_abstain(
    registry: SnapshotRegistry,
    edit: Callable[[list[dict[str, Any]]], None],
    reason: SnapshotAbstentionReason,
) -> None:
    base = _committed_artifact(registry, ECOS_GDP_BINDING)
    edited = _registry_with(
        registry,
        ECOS_GDP_BINDING,
        _artifact(base, _edited_ecos_payload(base, edit)),
    )

    result = _read(edited, ECOS_GDP_BINDING, "2026Q1")

    assert result.status is ToolOutcomeStatus.ABSTAINED
    assert result.abstention is not None
    assert result.abstention.reason_code == reason.value


def test_a_period_absent_from_the_snapshot_abstains(registry: SnapshotRegistry) -> None:
    result = _read(registry, ECOS_GDP_BINDING, "2030Q1")

    assert result.abstention is not None
    assert result.abstention.reason_code == "missing_selected_row"


def test_non_json_archive_abstains(registry: SnapshotRegistry) -> None:
    base = _committed_artifact(registry, ECOS_GDP_BINDING)
    broken = _registry_with(registry, ECOS_GDP_BINDING, _artifact(base, b"<html>error</html>"))

    result = _read(broken, ECOS_GDP_BINDING, "2026Q1")

    assert result.abstention is not None
    assert result.abstention.reason_code == "invalid_snapshot_json"


def test_a_rebased_kosis_index_abstains_instead_of_mixing_base_years(
    registry: SnapshotRegistry,
) -> None:
    base = _committed_artifact(registry, KOSIS_CPI_BINDING)
    rows = json.loads(base.archive_bytes)
    for row in rows:
        row["UNIT_NM"] = "2025＝100"  # noqa: RUF001 - provider-native fullwidth sign.
    rebased = _registry_with(
        registry,
        KOSIS_CPI_BINDING,
        _artifact(base, json.dumps(rows, ensure_ascii=False).encode("utf-8")),
    )

    result = _read(rebased, KOSIS_CPI_BINDING, "202606")

    assert result.abstention is not None
    assert result.abstention.reason_code == "source_unit_mismatch"


def test_committed_registry_digest_is_pinned_and_covers_every_artifact(
    registry: SnapshotRegistry,
) -> None:
    assert registry.descriptor_sha256 == SNAPSHOT_REGISTRY_DESCRIPTOR_SHA256
    base = _committed_artifact(registry, ECOS_GDP_BINDING)
    edited = _registry_with(registry, ECOS_GDP_BINDING, _artifact(base, b"{}"))
    assert edited.descriptor_sha256 != registry.descriptor_sha256


def _copied_inputs(tmp_path: Path) -> Path:
    for relative in ("data/manifests", "data/archive/ecos", "data/archive/kosis", "data/rights"):
        shutil.copytree(REPOSITORY_ROOT / relative, tmp_path / relative)
    return tmp_path


def test_loader_rejects_an_archive_that_differs_from_its_manifest(tmp_path: Path) -> None:
    root = _copied_inputs(tmp_path)
    archive = root / "data/archive/ecos/ecos-200y108-10601-20260717t115242998550z.json"
    archive.write_bytes(archive.read_bytes() + b"\n")

    with pytest.raises(ValueError, match="does not match its manifest"):
        load_committed_snapshot_registry(root)


def test_loader_rejects_a_snapshot_without_an_allowed_rights_link(tmp_path: Path) -> None:
    root = _copied_inputs(tmp_path)
    path = root / "data/manifests/ecos-200y108-10601-20260717t115242998550z.json"
    manifest = json.loads(path.read_bytes())
    del manifest["rights_decision"]
    manifest["redistribution"] = {"status": "metadata_only", "notes": "No ruling."}
    path.write_text(json.dumps(manifest, ensure_ascii=False), encoding="utf-8")

    with pytest.raises(ValueError, match="approved series binding"):
        load_committed_snapshot_registry(root)


def test_loader_rejects_two_snapshots_of_one_series_at_the_same_instant() -> None:
    with pytest.raises(ValueError, match="repeats a capture instant"):
        load_snapshot_registry(
            REPOSITORY_ROOT,
            registry_id="test-snapshot-registry",
            artifact_locations=(*COMMITTED_SNAPSHOT_LOCATIONS, COMMITTED_SNAPSHOT_LOCATIONS[0]),
            rights_catalog_paths=COMMITTED_RIGHTS_CATALOG_PATHS,
        )
