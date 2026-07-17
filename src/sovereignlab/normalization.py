"""Frozen exact-decimal normalization rules for KOR-RTD numeric observations."""

import re
from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal
from enum import StrEnum

from sovereignlab.schemas import SourceSystem

_PLAIN_DECIMAL = re.compile(r"^[+-]?[0-9]+(?:\.[0-9]+)?$")


class NormalizedUnit(StrEnum):
    """Canonical units that benchmark gold values may declare."""

    KRW = "krw"
    MILLION_KRW = "million_krw"
    HUNDRED_MILLION_KRW = "hundred_million_krw"
    BILLION_KRW = "billion_krw"
    TRILLION_KRW = "trillion_krw"
    MILLION_USD = "million_usd"
    INDEX_2020_100 = "index_2020_100"
    OECD_AMPLITUDE_ADJUSTED_INDEX = "oecd_amplitude_adjusted_index"


_KRW_PER_UNIT = {
    NormalizedUnit.KRW: Decimal("1"),
    NormalizedUnit.MILLION_KRW: Decimal("1000000"),
    NormalizedUnit.HUNDRED_MILLION_KRW: Decimal("100000000"),
    NormalizedUnit.BILLION_KRW: Decimal("1000000000"),
    NormalizedUnit.TRILLION_KRW: Decimal("1000000000000"),
}


@dataclass(frozen=True)
class NormalizationRule:
    """One exact source-series mapping into a canonical unit."""

    rule_id: str
    source_system: SourceSystem
    table_id: str
    item_id: str
    source_unit: str
    canonical_unit: NormalizedUnit
    canonical_multiplier: Decimal
    recommended_display_places: int


@dataclass(frozen=True)
class NormalizedValue:
    """A source value preserved alongside its exact normalized decimal."""

    rule_id: str
    raw_text: str
    exact_value: Decimal
    unit: NormalizedUnit


NORMALIZATION_RULES = (
    NormalizationRule(
        rule_id="ecos-200y108-10601-billion-krw-v1",
        source_system=SourceSystem.ECOS,
        table_id="200Y108",
        item_id="10601",
        source_unit="십억원",
        canonical_unit=NormalizedUnit.BILLION_KRW,
        canonical_multiplier=Decimal("1"),
        recommended_display_places=1,
    ),
    NormalizationRule(
        rule_id="ecos-301y017-sa000-million-usd-v1",
        source_system=SourceSystem.ECOS,
        table_id="301Y017",
        item_id="SA000",
        source_unit="백만달러",
        canonical_unit=NormalizedUnit.MILLION_USD,
        canonical_multiplier=Decimal("1"),
        recommended_display_places=1,
    ),
    NormalizationRule(
        rule_id="kosis-101-dt-1j22003-t-t10-index-v1",
        source_system=SourceSystem.KOSIS,
        table_id="DT_1J22003",
        item_id="T/T10",
        source_unit="2020=100",
        canonical_unit=NormalizedUnit.INDEX_2020_100,
        canonical_multiplier=Decimal("1"),
        recommended_display_places=2,
    ),
    NormalizationRule(
        rule_id="oecd-stes-kor-li-aa-index-v1",
        source_system=SourceSystem.OECD,
        table_id="DSD_STES_REVISIONS@DF_STES_REVISIONS",
        item_id="KOR.M.LI_AA.IX._T",
        source_unit="amplitude-adjusted index",
        canonical_unit=NormalizedUnit.OECD_AMPLITUDE_ADJUSTED_INDEX,
        canonical_multiplier=Decimal("1"),
        recommended_display_places=2,
    ),
    NormalizationRule(
        rule_id="oecd-stes-kor-b1gq-q-xdc-billion-krw-v1",
        source_system=SourceSystem.OECD,
        table_id="DSD_STES_REVISIONS@DF_STES_REVISIONS",
        item_id="KOR.Q.B1GQ_Q.XDC._T",
        source_unit="XDC national currency, units",
        canonical_unit=NormalizedUnit.BILLION_KRW,
        canonical_multiplier=Decimal("0.000000001"),
        recommended_display_places=1,
    ),
)

_RULES_BY_SCOPE = {
    (rule.source_system, rule.table_id, rule.item_id): rule for rule in NORMALIZATION_RULES
}


def normalization_rule(
    source_system: SourceSystem,
    table_id: str,
    item_id: str,
) -> NormalizationRule:
    """Return the frozen rule for one exact scope, failing closed for neighbors."""

    try:
        return _RULES_BY_SCOPE[(source_system, table_id, item_id)]
    except KeyError as error:
        raise ValueError("no frozen normalization rule for the exact source scope") from error


def parse_source_decimal(raw_text: str) -> Decimal:
    """Parse a plain finite source decimal without locale or binary-float ambiguity."""

    value = raw_text.strip()
    if _PLAIN_DECIMAL.fullmatch(value) is None:
        raise ValueError("source value must be a plain finite decimal")
    return Decimal(value)


def normalize_source_value(rule: NormalizationRule, raw_text: str) -> NormalizedValue:
    """Apply only the exact multiplier declared by a frozen series rule."""

    return NormalizedValue(
        rule_id=rule.rule_id,
        raw_text=raw_text,
        exact_value=parse_source_decimal(raw_text) * rule.canonical_multiplier,
        unit=rule.canonical_unit,
    )


def convert_krw_unit(
    value: Decimal,
    *,
    from_unit: NormalizedUnit,
    to_unit: NormalizedUnit,
) -> Decimal:
    """Convert exactly among 원/백만원/억원/십억원/조원 units."""

    try:
        return value * _KRW_PER_UNIT[from_unit] / _KRW_PER_UNIT[to_unit]
    except KeyError as error:
        raise ValueError("KRW unit conversion requires two KRW-denominated units") from error


def format_display(value: Decimal, *, places: int) -> str:
    """Round once for presentation using decimal ROUND_HALF_UP."""

    if places < 0 or places > 12:
        raise ValueError("display places must be between 0 and 12")
    quantum = Decimal(1).scaleb(-places)
    rounded = value.quantize(quantum, rounding=ROUND_HALF_UP)
    return f"{rounded:.{places}f}"


def display_tolerance(*, places: int) -> Decimal:
    """Return half one displayed unit for numeric answer grading."""

    if places < 0 or places > 12:
        raise ValueError("display places must be between 0 and 12")
    return Decimal(1).scaleb(-places) / 2


def within_display_tolerance(
    candidate: Decimal,
    expected: Decimal,
    *,
    places: int,
) -> bool:
    """Grade numbers only after the question has fixed one unit and precision."""

    return abs(candidate - expected) <= display_tolerance(places=places)
