"""Contract tests for the frozen KOR-RTD numeric normalization rules."""

from decimal import Decimal

import pytest

from sovereignlab.normalization import (
    NORMALIZATION_RULES,
    NormalizedUnit,
    convert_krw_unit,
    display_tolerance,
    format_display,
    normalization_rule,
    normalize_source_value,
    parse_source_decimal,
    within_display_tolerance,
)
from sovereignlab.schemas import SourceSystem


def test_rules_have_unique_exact_scopes_and_ids() -> None:
    scopes = {(rule.source_system, rule.table_id, rule.item_id) for rule in NORMALIZATION_RULES}
    identifiers = {rule.rule_id for rule in NORMALIZATION_RULES}

    assert len(scopes) == len(NORMALIZATION_RULES)
    assert len(identifiers) == len(NORMALIZATION_RULES)


def test_verified_oecd_gdp_value_normalizes_to_billion_krw() -> None:
    rule = normalization_rule(
        SourceSystem.OECD,
        "DSD_STES_REVISIONS@DF_STES_REVISIONS",
        "KOR.Q.B1GQ_Q.XDC._T",
    )
    normalized = normalize_source_value(rule, "574984300000000")

    assert normalized.raw_text == "574984300000000"
    assert normalized.exact_value == Decimal("574984.300000000")
    assert normalized.unit is NormalizedUnit.BILLION_KRW
    assert (
        format_display(
            normalized.exact_value,
            places=rule.recommended_display_places,
        )
        == "574984.3"
    )


@pytest.mark.parametrize(
    ("source_system", "table_id", "item_id", "raw_text", "expected", "unit"),
    [
        (
            SourceSystem.ECOS,
            "200Y108",
            "10601",
            "596692.8",
            Decimal("596692.8"),
            NormalizedUnit.BILLION_KRW,
        ),
        (
            SourceSystem.ECOS,
            "301Y017",
            "SA000",
            "38121.1",
            Decimal("38121.1"),
            NormalizedUnit.MILLION_USD,
        ),
        (
            SourceSystem.KOSIS,
            "DT_1J22003",
            "T/T10",
            "119.99",
            Decimal("119.99"),
            NormalizedUnit.INDEX_2020_100,
        ),
        (
            SourceSystem.OECD,
            "DSD_STES_REVISIONS@DF_STES_REVISIONS",
            "KOR.M.LI_AA.IX._T",
            "102.66",
            Decimal("102.66"),
            NormalizedUnit.OECD_AMPLITUDE_ADJUSTED_INDEX,
        ),
    ],
)
def test_live_capture_examples_preserve_exact_decimals(
    source_system: SourceSystem,
    table_id: str,
    item_id: str,
    raw_text: str,
    expected: Decimal,
    unit: NormalizedUnit,
) -> None:
    rule = normalization_rule(source_system, table_id, item_id)
    result = normalize_source_value(rule, raw_text)

    assert result.exact_value == expected
    assert result.unit is unit


def test_neighboring_series_and_non_plain_values_fail_closed() -> None:
    with pytest.raises(ValueError, match="no frozen normalization rule"):
        normalization_rule(
            SourceSystem.OECD,
            "DSD_STES_REVISIONS@DF_STES_REVISIONS",
            "KOR.Q.B1GQ_D.XDC._T",
        )

    for raw_text in ("", "-", "1,000", "1e3", "NaN", ".5"):
        with pytest.raises(ValueError, match="plain finite decimal"):
            parse_source_decimal(raw_text)
    assert parse_source_decimal(" -0.50 ") == Decimal("-0.50")


def test_korean_krw_units_convert_exactly() -> None:
    assert convert_krw_unit(
        Decimal("1"),
        from_unit=NormalizedUnit.TRILLION_KRW,
        to_unit=NormalizedUnit.BILLION_KRW,
    ) == Decimal("1000")
    assert convert_krw_unit(
        Decimal("1"),
        from_unit=NormalizedUnit.BILLION_KRW,
        to_unit=NormalizedUnit.HUNDRED_MILLION_KRW,
    ) == Decimal("10")
    assert convert_krw_unit(
        Decimal("1"),
        from_unit=NormalizedUnit.HUNDRED_MILLION_KRW,
        to_unit=NormalizedUnit.MILLION_KRW,
    ) == Decimal("100")
    assert convert_krw_unit(
        Decimal("1"),
        from_unit=NormalizedUnit.MILLION_KRW,
        to_unit=NormalizedUnit.KRW,
    ) == Decimal("1000000")

    with pytest.raises(ValueError, match="two KRW-denominated"):
        convert_krw_unit(
            Decimal("1"),
            from_unit=NormalizedUnit.MILLION_USD,
            to_unit=NormalizedUnit.KRW,
        )


def test_display_rounding_and_tolerance_are_explicit() -> None:
    assert format_display(Decimal("1.005"), places=2) == "1.01"
    assert format_display(Decimal("-1.005"), places=2) == "-1.01"
    assert display_tolerance(places=2) == Decimal("0.005")
    assert within_display_tolerance(Decimal("102.665"), Decimal("102.66"), places=2)
    assert not within_display_tolerance(Decimal("102.666"), Decimal("102.66"), places=2)

    for places in (-1, 13):
        with pytest.raises(ValueError, match="between 0 and 12"):
            format_display(Decimal("1"), places=places)
        with pytest.raises(ValueError, match="between 0 and 12"):
            display_tolerance(places=places)
