"""Tier-2 probes: deterministic Korea CLI as-of questions whose golds the resolver computes.

Two families, each as a Korean/English pair:

- *as-of value*: the CLI for one month, as the newest demonstrably available edition read on
  the cutoff day. It is tagged ``revision-trap`` when any later edition in the archive, whether
  or not a cutoff can select it, holds a different value, so an answer from that edition is
  detectably wrong.
- *future period*: a month that the newest available edition did not yet contain. The gold is
  abstention, since any number would come from a later vintage.

Cutoffs come from the availability ledger and every gold from a resolver call, so the probe set
regenerates byte for byte from committed evidence (``scripts/generate_probes.py``).
"""

import csv
import io
import json
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

from sovereignlab.schemas import (
    AnnotationProvenance,
    AnnotationStatus,
    BenchmarkRecord,
    BenchmarkSplit,
    EditionAvailabilityLedger,
    EvidenceRoute,
    LanguageCode,
    StesAsOfArguments,
    StesAsOfCall,
    ToolExpectation,
    ToolName,
    ToolOutcomeStatus,
    VintageEvidence,
)
from sovereignlab.vintage import (
    CLI_STES_BINDING,
    StesRegistry,
    execute_stes_as_of_call,
    load_committed_stes_registry,
)

PROBE_SET_ID = "kv-probes-oecd-cli-v1"
PROBE_SET_PATH = Path("data/benchmark/probes") / f"{PROBE_SET_ID}.jsonl"
EVIDENCE_VERSION = 2
GENERATED_AT = datetime(2026, 11, 24, tzinfo=UTC)
GENERATOR = "sovereignlab probe generator v1"
# Months asked per edition: every month from FIRST_PERIOD to the edition's last month, then the
# FUTURE_MONTHS months that the edition did not yet contain.
FIRST_PERIOD = "2023-01"
FUTURE_MONTHS = 2
# Each edition is one evidence unit, so it belongs to exactly one split. 202607 is train because
# the core matrix already uses it there; the owner chose 202610 for test on 2026-11-24 (ADR 0014).
EDITION_SPLITS = {
    "202607": BenchmarkSplit.TRAIN,
    "202610": BenchmarkSplit.TEST,
    "202611": BenchmarkSplit.DEVELOPMENT,
}

_MONTHS_EN = (
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
)
_SOURCE_EN = (
    "Source: OECD, Composite leading indicator (CLI), amplitude adjusted — Korea, as preserved "
    "in the KOR-RTD vintage archive; no OECD endorsement is implied."
)
_SOURCE_KO = (
    "출처: OECD, 경기선행지수(CLI, 진폭조정) — 한국, KOR-RTD 빈티지 아카이브 보존본. "
    "OECD의 보증을 의미하지 않는다."
)


def answerable_windows(ledger: EditionAvailabilityLedger) -> dict[str, tuple[date, ...]]:
    """Return, for each edition, the cutoff days on which the ledger selects it."""

    day = min(record.available_by for record in ledger.editions if record.available_by).date()
    windows: dict[str, list[date]] = {}
    while day <= ledger.complete_through.date():
        selected = ledger.select_edition(ledger.cutoff_exclusive(day)).selected_edition
        if selected is not None:
            windows.setdefault(selected, []).append(day)
        day += timedelta(days=1)
    return {edition: tuple(days) for edition, days in windows.items()}


def generate_probe_records(repository_root: Path) -> tuple[BenchmarkRecord, ...]:
    """Build every probe from the admitted evidence version, computing each gold by a tool call."""

    registry = load_committed_stes_registry(repository_root, version=EVIDENCE_VERSION)
    archive = registry.entry_for(CLI_STES_BINDING.scope).data_artifact
    assert archive is not None  # the CLI is the one STES series with approved raw data
    values = _edition_values(archive.archive_bytes)
    windows = answerable_windows(registry.active_ledger)
    if set(windows) != set(EDITION_SPLITS):
        raise RuntimeError(f"answerable editions changed: {sorted(windows)}")

    records: list[BenchmarkRecord] = []
    for edition in sorted(EDITION_SPLITS):
        months = sorted(period for period in values[edition] if period >= FIRST_PERIOD)
        items = [
            *((period, False) for period in months),
            *((period, True) for period in _following_months(months[-1], FUTURE_MONTHS)),
        ]
        window = windows[edition]
        for index, (period, future) in enumerate(items):
            # Cycling through the window exercises both of its edges.
            as_of = window[index % len(window)]
            later = {
                values[other][period]
                for other in values
                if other > edition and period in values[other]
            }
            records.extend(
                _probe_pair(
                    registry=registry,
                    edition=edition,
                    period=period,
                    as_of=as_of,
                    last_period=months[-1],
                    future=future,
                    revised=any(value != values[edition].get(period) for value in later),
                )
            )
    return tuple(records)


def render_probe_set(records: tuple[BenchmarkRecord, ...]) -> bytes:
    """Serialize records as sorted-key JSON lines, the format of the committed benchmark files."""

    lines = (
        json.dumps(
            record.model_dump(mode="json", exclude_none=True), ensure_ascii=False, sort_keys=True
        )
        for record in records
    )
    return "".join(f"{line}\n" for line in lines).encode("utf-8")


def _probe_pair(
    *,
    registry: StesRegistry,
    edition: str,
    period: str,
    as_of: date,
    last_period: str,
    future: bool,
    revised: bool,
) -> tuple[BenchmarkRecord, BenchmarkRecord]:
    family = "future" if future else "asof"
    pair_id = f"kv-probe-cli-{family}-{edition}-{period}"
    call = StesAsOfCall(
        call_id=f"{pair_id}-call",
        tool_name=ToolName.RESOLVE_STES_AS_OF,
        arguments=StesAsOfArguments(
            ref_area=CLI_STES_BINDING.ref_area,
            freq=CLI_STES_BINDING.freq,
            measure=CLI_STES_BINDING.measure,
            unit_measure=CLI_STES_BINDING.unit_measure,
            activity=CLI_STES_BINDING.activity,
            period=period,
            as_of=as_of,
            normalization_rule_id=CLI_STES_BINDING.normalization_rule_id,
        ),
    )
    result = execute_stes_as_of_call(call=call, registry=registry)

    common = {
        "split": EDITION_SPLITS[edition],
        "evidence_group_id": f"eg-probe-oecd-cli-{edition}",
        "parallel_group_id": pair_id,
        "as_of": as_of,
        "annotation": AnnotationProvenance(
            status=AnnotationStatus.DRAFT,
            annotated_by=GENERATOR,
            annotated_at=GENERATED_AT,
        ),
    }
    questions = {
        LanguageCode.KOREAN: (
            f"{_date_ko(as_of)} 현재 이용 가능했던 빈티지만 사용해, {_month_ko(period)} 한국의 "
            "OECD 진폭조정 경기선행지수(CLI)는 얼마였는가?"
        ),
        LanguageCode.ENGLISH: (
            f"Using only the data vintage available as of {_date_en(as_of)}, what was Korea's "
            f"OECD composite leading indicator (CLI, amplitude adjusted) for {_month_en(period)}?"
        ),
    }

    if future:
        if (
            result.status is not ToolOutcomeStatus.ABSTAINED
            or result.abstention is None
            or result.abstention.reason_code != "missing_selected_row"
        ):
            raise RuntimeError(f"{pair_id}: the resolver did not abstain for a future month")
        # The reason claims only what the evidence proves: the newest available edition lacks the
        # month. Whether OECD published the month elsewhere is outside the archive.
        reasons = {
            LanguageCode.KOREAN: (
                f"{_date_ko(as_of)} 말(Asia/Seoul) 기준으로 가용성이 확인된 최신 빈티지는 "
                f"{edition} 에디션이며, 이 빈티지의 시계열은 {_month_ko(last_period)}에서 끝나 "
                f"{_month_ko(period)} 값이 없다. 어떤 수치든 이후 빈티지에서 가져온 것이 된다."
            ),
            LanguageCode.ENGLISH: (
                f"At the end of {_date_en(as_of)} (Asia/Seoul), the newest demonstrably available "
                f"edition was {edition}, and its series ends at {_month_en(last_period)}, so it "
                f"holds no value for {_month_en(period)}. Any number would have to come from a "
                "later vintage."
            ),
        }
        tags = ("probe", "temporal", "vintage", "oecd-cli", "future-period")
        return tuple(
            BenchmarkRecord(
                record_id=f"{pair_id}-{language.value}",
                language=language,
                question=questions[language],
                expected_route=EvidenceRoute.ABSTAIN,
                abstention_reason=reasons[language],
                tags=tags,
                **common,
            )
            for language in (LanguageCode.KOREAN, LanguageCode.ENGLISH)
        )

    evidence = result.payload
    if result.status is not ToolOutcomeStatus.SUCCESS or evidence is None:
        raise RuntimeError(f"{pair_id}: the resolver returned no value")
    if evidence.selected_edition != edition:
        raise RuntimeError(f"{pair_id}: the resolver selected edition {evidence.selected_edition}")
    observation = evidence.observation
    display = observation.display_value
    expectation = ToolExpectation(
        source_id=evidence.source_id,
        tool_name=ToolName.RESOLVE_STES_AS_OF.value,
        arguments=call.arguments.model_dump(mode="json"),
        expected_facts=(
            f"selected_edition={evidence.selected_edition}",
            f"raw_value={observation.raw_value}",
            f"normalization_rule_id={observation.normalization_rule_id}",
            f"normalized_value={observation.normalized_value}",
            f"canonical_unit={observation.canonical_unit}",
            f"display_places={observation.display_places}",
            f"display_value={display}",
        ),
        vintage=VintageEvidence(ledger_id=evidence.ledger_id, selected_edition=edition),
    )
    answers = {
        LanguageCode.KOREAN: (
            f"{_date_ko(as_of)} 말(Asia/Seoul) 기준으로 가용성이 확인된 최신 빈티지는 {edition} "
            f"에디션이며, 이 빈티지의 {_month_ko(period)} 한국 진폭조정 경기선행지수(CLI)는 "
            f"{display}이다. {_SOURCE_KO}"
        ),
        LanguageCode.ENGLISH: (
            f"At the end of {_date_en(as_of)} (Asia/Seoul), the newest edition demonstrably "
            f"available was {edition}. In that vintage, Korea's amplitude-adjusted composite "
            f"leading indicator for {_month_en(period)} was {display}. {_SOURCE_EN}"
        ),
    }
    tags = (
        "probe",
        "temporal",
        "vintage",
        "oecd-cli",
        "as-of-value",
        "revision-trap" if revised else "unrevised",
    )
    return tuple(
        BenchmarkRecord(
            record_id=f"{pair_id}-{language.value}",
            language=language,
            question=questions[language],
            expected_route=EvidenceRoute.DATA,
            tool_expectations=(expectation,),
            reference_answer=answers[language],
            tags=tags,
            **common,
        )
        for language in (LanguageCode.KOREAN, LanguageCode.ENGLISH)
    )


def _edition_values(archive_bytes: bytes) -> dict[str, dict[str, str]]:
    """Map each edition to its month-to-value series; the registry admits only the CLI here."""

    values: dict[str, dict[str, str]] = {}
    reader = csv.DictReader(io.StringIO(archive_bytes.decode("utf-8-sig"), newline=""))
    for row in reader:
        values.setdefault(row["EDITION"], {})[row["TIME_PERIOD"]] = row["OBS_VALUE"]
    return values


def _following_months(period: str, count: int) -> tuple[str, ...]:
    year, month = int(period[:4]), int(period[5:])
    following = []
    for _ in range(count):
        year, month = (year + 1, 1) if month == 12 else (year, month + 1)
        following.append(f"{year:04d}-{month:02d}")
    return tuple(following)


def _date_en(day: date) -> str:
    return f"{_MONTHS_EN[day.month - 1]} {day.day}, {day.year}"


def _date_ko(day: date) -> str:
    return f"{day.year}년 {day.month}월 {day.day}일"


def _month_en(period: str) -> str:
    return f"{_MONTHS_EN[int(period[5:]) - 1]} {period[:4]}"


def _month_ko(period: str) -> str:
    return f"{period[:4]}년 {int(period[5:])}월"
