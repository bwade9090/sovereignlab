"""Integrity of every committed KOR-RTD artifact, including each weekly capture.

The weekly workflow runs this file as its gate before it commits a capture, so nothing here
may depend on how many captures exist.
"""

import hashlib
from datetime import date
from pathlib import Path

from sovereignlab.harvest.weekly import (
    HarvestSummary,
    _parse_constraint,
    _validate_constraint_join,
)
from sovereignlab.schemas import (
    BenchmarkBundle,
    EditionAvailabilityLedger,
    RedistributionStatus,
    RightsCatalog,
    SourceKind,
    SourceManifest,
)

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
# ADR 0011: a document manifest is dated no earlier than its exact attachment bytes.
BOK_OUTLOOK_PUBLICATION_DATES = {
    "bok-outlook-2025-11-en": date(2026, 1, 22),
    "bok-outlook-2025-11-ko": date(2026, 3, 31),
    "bok-outlook-2026-05-en": date(2026, 7, 6),
    "bok-outlook-2026-05-ko": date(2026, 6, 12),
}


def check_kor_rtd_data(root: Path) -> None:
    """Assert the archive layer under ``root`` is self-consistent."""

    manifests = {
        path.stem: SourceManifest.model_validate_json(path.read_bytes())
        for path in (root / "data" / "manifests").glob("*.json")
    }
    archives = {path.stem: path for path in (root / "data" / "archive").glob("*/*")}
    assert all(source_id == manifest.source_id for source_id, manifest in manifests.items())

    # Every archived payload has a manifest, and its bytes match that manifest.
    assert set(archives) <= set(manifests)
    for source_id, path in archives.items():
        payload = path.read_bytes()
        assert len(payload) == manifests[source_id].byte_size, source_id
        assert hashlib.sha256(payload).hexdigest() == manifests[source_id].content_sha256

    # Only documents may be manifest-only: their bodies are not redistributed through Git.
    for source_id in set(manifests) - set(archives):
        assert manifests[source_id].source_kind is SourceKind.DOCUMENT, source_id

    ledgers = {
        path.stem: EditionAvailabilityLedger.model_validate_json(path.read_bytes())
        for path in (root / "data" / "availability").glob("*.json")
    }
    assert all(ledger_id == ledger.ledger_id for ledger_id, ledger in ledgers.items())

    # ADR 0005: a ledger's edition inventory is derived from its own constraint capture and is
    # never edited by hand.
    for ledger_id, ledger in ledgers.items():
        token = ledger_id.removeprefix("oecd-stes-ledger-")
        available = _parse_constraint(
            archives[f"oecd-stes-availableconstraint-{token}"].read_bytes(),
            require_valid_from=False,
        )
        content = _parse_constraint(
            archives[f"oecd-stes-contentconstraint-{token}"].read_bytes(),
            require_valid_from=True,
        )
        _validate_constraint_join(available, content)
        assert tuple(sorted(record.edition for record in ledger.editions)) == available.editions

    # Ledgers form one append-only chain: each successor keeps every earlier edition record.
    superseded = [ledger.supersedes_ledger_id for ledger in ledgers.values()]
    assert superseded.count(None) == 1
    assert len(set(superseded)) == len(superseded)
    for ledger in ledgers.values():
        if ledger.supersedes_ledger_id is not None:
            predecessor = ledgers[ledger.supersedes_ledger_id]
            assert predecessor.complete_through <= ledger.complete_through
            successor_records = {record.edition: record for record in ledger.editions}
            assert all(
                successor_records[record.edition] == record for record in predecessor.editions
            )

    catalogs = tuple(
        RightsCatalog.model_validate_json(path.read_bytes())
        for path in (root / "data" / "rights").glob("*.json")
    )
    # The bundle validator checks rights links and that ledger evidence cites known manifests.
    BenchmarkBundle(
        sources=tuple(manifests.values()),
        records=(),
        availability_ledgers=tuple(ledgers.values()),
        rights_catalogs=catalogs,
    )


def test_committed_archive_layer_is_self_consistent() -> None:
    check_kor_rtd_data(REPOSITORY_ROOT)


def test_a_fresh_weekly_capture_keeps_the_archive_consistent(
    weekly_capture_after_v1: tuple[Path, HarvestSummary],
) -> None:
    root, summary = weekly_capture_after_v1

    assert len(summary.manifest_paths) == len(summary.archive_paths) == 5
    check_kor_rtd_data(root)


def test_bok_outlook_manifests_carry_the_family_ruling_and_exact_byte_dates() -> None:
    manifests = {
        path.stem: SourceManifest.model_validate_json(path.read_bytes())
        for path in (REPOSITORY_ROOT / "data" / "manifests").glob("bok-outlook-*.json")
    }

    assert {
        source_id: manifest.published_on for source_id, manifest in manifests.items()
    } == BOK_OUTLOOK_PUBLICATION_DATES
    for manifest in manifests.values():
        # ADR 0009: an allowed public-data family ruling, not a per-series rights decision.
        assert manifest.source_kind is SourceKind.DOCUMENT
        assert manifest.publisher == "Bank of Korea"
        assert manifest.document_family == "bok-economic-outlook"
        assert manifest.redistribution.status is RedistributionStatus.ALLOWED
        assert manifest.rights_decision is None
