# KOR-RTD number-normalization specification 1.0.0

- Status: frozen
- Date: 2026-07-17
- Scope authority: charter v2.3 §5 and ADR 0003
- Canonical implementation: `src/sovereignlab/normalization.py`

## 1. Purpose and non-negotiable rules

This contract prevents numerically correct source observations from becoming ambiguous benchmark
answers through binary floating point, hidden scaling, Korean large-number conventions, variant
mixing, or inconsistent rounding.

1. Preserve the source numeric string in provenance and parse it with `Decimal`, never `float`.
2. Accept only plain finite decimals. Locale commas, scientific notation, missing-value markers,
   `NaN`, and infinity fail closed before normalization.
3. Select a rule by the exact case-sensitive source system/table/item scope. Titles do not select a
   rule. A neighboring geography, seasonal-adjustment variant, measure, unit, or table fails closed.
4. Apply the rule's exact decimal multiplier once. Keep the resulting exact decimal for gold
   regeneration and comparison; round only the presentation copy.
5. Every numerical benchmark record must state the normalization `rule_id`, canonical unit, and
   display precision. A bare number without a unit is not gradable.

## 2. Frozen MVP series rules

| Rule | Exact scope | Source unit | Canonical transformation | Recommended display |
|---|---|---|---|---:|
| `ecos-200y108-10601-billion-krw-v1` | ECOS `200Y108/10601` | 십억원 | identity → billion KRW | 1 decimal |
| `ecos-301y017-sa000-million-usd-v1` | ECOS `301Y017/SA000` | 백만달러 | identity → million USD | 1 decimal |
| `kosis-101-dt-1j22003-t-t10-index-v1` | KOSIS `DT_1J22003/T/T10` | 2020=100 | identity → 2020=100 index | 2 decimals |
| `oecd-stes-kor-li-aa-index-v1` | OECD STES revisions `KOR.M.LI_AA.IX._T` | amplitude-adjusted index | identity → amplitude-adjusted index | 2 decimals |
| `oecd-stes-kor-b1gq-q-xdc-billion-krw-v1` | OECD STES revisions `KOR.Q.B1GQ_Q.XDC._T` | XDC national-currency units | value × `10^-9` → billion KRW | 1 decimal |

The OECD GDP rule reproduces the verified value `574984300000000 XDC` as exactly
`574984.300000000` billion KRW, displayed as `574984.3`. It applies only to quarterly,
seasonally-adjusted real GDP measure `B1GQ_Q`, total activity `_T`, and unit `XDC`. It does not
authorize or normalize `B1GQ_D`, `B1GQ_V`, another activity, annual frequency, or an unadjusted
series. Likewise, the CLI rule applies to revision measure `LI_AA`, not a similarly named current
flow code or trend-restored component.

## 3. Korean KRW conventions

Conversions are exact powers of ten:

| Korean unit | Canonical name | KRW per unit | Relation to 십억원 |
|---|---|---:|---:|
| 원 | `krw` | `1` | `10^-9` |
| 백만원 | `million_krw` | `10^6` | `10^-3` |
| 억원 | `hundred_million_krw` | `10^8` | `0.1` |
| 십억원 | `billion_krw` | `10^9` | `1` |
| 조원 | `trillion_krw` | `10^12` | `1000` |

Currency conversion is outside this contract. A million-USD value cannot be converted to KRW
without a separately evidenced exchange-rate observation and its own vintage.

## 4. Rounding and grading

- Presentation uses decimal `ROUND_HALF_UP` exactly once at the precision declared by the item.
- The recommended precision is a default for authoring, not permission to discard source
  precision. Gold regeneration stores the raw string and exact normalized decimal before display.
- A numeric answer is accepted within half of one unit at the declared final decimal place:
  `0.5 × 10^-places`, inclusive. At two decimals the tolerance is `0.005`; at one decimal it is
  `0.05`.
- Comparison happens only after candidate and gold use the same declared canonical unit. There is
  no automatic inference from commas, `조`, `억`, `%`, prose, or an omitted unit.
- Revision equality is evaluated on exact normalized decimals, not on rounded display strings. Two
  vintages that display the same rounded number may still be a real revision and must remain
  separately reportable.

## 5. Change control

This specification is frozen before K-VINTAGE question authoring. Adding a scope or changing a
unit, multiplier, variant, precision, rounding mode, or tolerance requires a new version, tests, and
an entry in `docs/PROJECT_STATUS.md`. Rights approval and numeric normalization are separate gates:
a normalization rule never grants collection or redistribution permission.
