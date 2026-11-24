"""Tier-2 probes: exact regeneration, composition, evidence, and gold reproduction.

The probes are machine-generated drafts. They never count toward the human-reviewed core.
"""

from collections import Counter
from collections.abc import Callable
from pathlib import Path

from sovereignlab.execution import CallableToolRegistry
from sovereignlab.probes import (
    EDITION_SPLITS,
    EVIDENCE_VERSION,
    GENERATOR,
    PROBE_SET_PATH,
    generate_probe_records,
    render_probe_set,
)
from sovereignlab.schemas import (
    AnnotationStatus,
    BenchmarkRecord,
    BenchmarkSplit,
    EvidenceRoute,
    LanguageCode,
)

ROOT = Path(__file__).resolve().parents[2]
PROBES = tuple(
    BenchmarkRecord.model_validate_json(line)
    for line in (ROOT / PROBE_SET_PATH).read_text(encoding="utf-8").splitlines()
)
BY_ID = {probe.record_id: probe for probe in PROBES}


def test_the_committed_probe_set_regenerates_byte_for_byte() -> None:
    # Every gold is a resolver result on admitted evidence. Drift means the evidence, the
    # resolver, or the generator changed: run `python scripts/generate_probes.py --write`.
    assert render_probe_set(generate_probe_records(ROOT)) == (ROOT / PROBE_SET_PATH).read_bytes()


def test_the_probe_set_has_the_documented_composition() -> None:
    counts = Counter(
        (probe.split, probe.expected_route, "revision-trap" in probe.tags) for probe in PROBES
    )
    train, dev, test = BenchmarkSplit.TRAIN, BenchmarkSplit.DEVELOPMENT, BenchmarkSplit.TEST
    data, abstain = EvidenceRoute.DATA, EvidenceRoute.ABSTAIN
    assert counts == {
        (train, data, True): 84,
        (train, abstain, False): 4,
        (dev, data, False): 92,
        (dev, abstain, False): 4,
        (test, data, True): 40,
        (test, data, False): 50,
        (test, abstain, False): 4,
    }
    assert Counter(probe.language for probe in PROBES) == {
        LanguageCode.KOREAN: 139,
        LanguageCode.ENGLISH: 139,
    }


def test_every_probe_is_a_draft_in_a_complete_language_pair_split_by_edition() -> None:
    assert len(BY_ID) == len(PROBES)
    pairs: dict[str, list[BenchmarkRecord]] = {}
    for probe in PROBES:
        assert probe.annotation.status is AnnotationStatus.DRAFT, probe.record_id
        assert probe.annotation.annotated_by == GENERATOR, probe.record_id
        assert "probe" in probe.tags and "core" not in probe.tags, probe.record_id
        pairs.setdefault(probe.parallel_group_id, []).append(probe)

    for pair_id, records in pairs.items():
        assert [record.record_id for record in records] == [f"{pair_id}-ko", f"{pair_id}-en"]
        korean, english = records
        assert (korean.language, english.language) == (LanguageCode.KOREAN, LanguageCode.ENGLISH)
        for field in ("split", "evidence_group_id", "as_of", "expected_route", "tags"):
            assert getattr(korean, field) == getattr(english, field), (pair_id, field)
        assert korean.tool_expectations == english.tool_expectations, pair_id

        edition = pair_id.split("-")[4]  # kv-probe-cli-{family}-{edition}-{period}
        assert korean.split is EDITION_SPLITS[edition], pair_id
        assert korean.evidence_group_id == f"eg-probe-oecd-cli-{edition}", pair_id
        for expectation in korean.tool_expectations:
            assert expectation.vintage is not None, pair_id
            assert expectation.vintage.selected_edition == edition, pair_id


def test_probes_and_their_evidence_form_one_valid_bundle(
    tool_registries: dict[int, CallableToolRegistry],
    evidence_bundle: Callable[[tuple[BenchmarkRecord, ...], CallableToolRegistry], object],
) -> None:
    evidence_bundle(PROBES, tool_registries[EVIDENCE_VERSION])


def test_the_offline_tools_reproduce_every_data_probe(
    tool_registries: dict[int, CallableToolRegistry],
    assert_reproduced: Callable[[BenchmarkRecord, CallableToolRegistry], None],
) -> None:
    # The generator calls the resolver directly; this replays each record's stored arguments
    # through the typed tool dispatcher, the path an evaluated model's calls take.
    registry = tool_registries[EVIDENCE_VERSION]
    for probe in PROBES:
        assert bool(probe.tool_expectations) == (probe.expected_route is EvidenceRoute.DATA)
        assert_reproduced(probe, registry)


def test_known_probes_carry_the_values_each_edition_published() -> None:
    # The May 2026 CLI as three editions published it, checked by hand against the archive.
    # Edition 202607's value is also the gold of the approved core pair kv-core-data-01.
    for record_id, value, tag in (
        ("kv-probe-cli-asof-202607-2026-05-en", "102.66", "revision-trap"),
        ("kv-probe-cli-asof-202610-2026-05-en", "102.33", "revision-trap"),
        ("kv-probe-cli-asof-202611-2026-05-en", "102.29", "unrevised"),
    ):
        probe = BY_ID[record_id]
        (expectation,) = probe.tool_expectations
        assert f"display_value={value}" in expectation.expected_facts, record_id
        assert tag in probe.tags, record_id

    # Edition 202610 ends at September 2026, so October 2026 is not yet knowable.
    future = BY_ID["kv-probe-cli-future-202610-2026-10-en"]
    assert future.expected_route is EvidenceRoute.ABSTAIN
    assert future.split is BenchmarkSplit.TEST
    assert "September 2026" in future.abstention_reason
