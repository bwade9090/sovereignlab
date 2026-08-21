# K-VINTAGE human-reviewed core authoring matrix 1.0.0

- Status: structural allocation frozen; first ten records owner-approved; `kv-core-data-04`
  drafted and pending named human review
- Date: 2026-08-21
- Scope authority: charter v2.5 §5 and M2 continuation order
- Canonical matrix: `data/benchmark/core-authoring-matrix-v1.json`
- Public schema: `data/schemas/core-authoring-matrix-v1.schema.json`

## 1. Frozen allocation

The tier-1 core contains exactly 40 records represented as 20 Korean/English pairs. The matrix
freezes structure before further question authoring:

| Route | Korean | English | Train | Dev | Test | Total |
|---|---:|---:|---:|---:|---:|---:|
| `documents` | 5 | 5 | 6 | 2 | 2 | 10 |
| `data` | 5 | 5 | 6 | 2 | 2 | 10 |
| `documents_and_data` | 5 | 5 | 6 | 2 | 2 | 10 |
| `abstain` | 5 | 5 | 6 | 2 | 2 | 10 |
| **Total** | **20** | **20** | **24** | **8** | **8** | **40** |

Every pair has one route, split, evidence group, Korean record ID, English record ID, and question
intent. Documentary and data source units are assigned to one split globally. Reusing a planned
source unit across train/dev/test makes `CoreAuthoringMatrix` validation fail, while reuse inside
one split is permitted. This supplements the record-level `BenchmarkBundle` checks by freezing the
source-release allocation before all manifests and questions exist.

The test-held data unit is deliberately reserved rather than fabricated. Its two data records and
the combined pair that depends on it must not be authored until an independently captured,
owner-approved release has a committed manifest and, where required, availability evidence.

## 2. First approved batch

`data/benchmark/core/core-batch-001.jsonl` contains four owner-approved records initially authored
by AI:

1. one Korean/English `data` pair asking for Korea's May 2026 amplitude-adjusted CLI as of
   2026-07-09; and
2. one Korean/English `abstain` pair asking the same value as of 2026-06-30, when the committed
   ledger has no definitely available edition.

The data pair is grounded in the committed OECD Korea CLI archive, its typed rights decision, and
the active edition-availability ledger. Offline validation reproduces edition `202607`, raw and
normalized value `102.66`, canonical unit `oecd_amplitude_adjusted_index`, and two-decimal display.
For the earlier cutoff, the ledger mechanically returns `no_edition_definitely_available`; the
record therefore never substitutes the later edition or invents an older publication date.

All four annotations record `status=approved`, reviewer `Hyungbae Cho`, and the aware review
timestamp. They count as four human-reviewed core records.

## 3. First approved documentary pair

`data/benchmark/core/core-batch-002.jsonl` contains the frozen `kv-core-doc-01` Korean/English
pair. Both records use the `documents` route, `train` split,
`eg-doc-bok-outlook-2026-05` evidence group, and `kv-core-doc-01` parallel group. The Korean record
is bounded to the Korean report's 2026-05-28 publication date and cites PDF page 10; the English
record is independently bounded to the full translation's 2026-06-30 publication date and cites
PDF page 9.

Both answers paraphrase one stated driver: stronger-than-expected IT exports contributed `+0.7%p`
to the `0.6%p` upward revision of the 2026 GDP growth forecast. They attribute the Bank of Korea
and disclose summarization/paraphrase. On 2026-07-29, Hyungbae Cho approved both records without a
question, answer, route, evidence, `as_of`, or frozen-allocation change. Their annotations preserve
the AI author and record the named human reviewer and aware review timestamp. The lifecycle tag
changed from `draft-002` to `batch-002` when the file moved into `core/`.

At the 2026-07-29 checkpoint, these two records brought the approved human-reviewed core to 6/40.
The later ECOS GDP and ECOS current-account approvals described below bring the current total to
10/40. The KOSIS CPI draft described after them accounts for two of the 30 unapproved records; the
other 28 remain unauthored and unapproved.

## 4. Approved ECOS GDP pair

The frozen `kv-core-data-02` Korean/English pair was completed as
`data/benchmark/drafts/core-draft-003.jsonl` on 2026-08-19 in feature commit `f2d2523`. Hyungbae
Cho approved both records on 2026-08-20 with review timestamp `2026-08-20T00:24:18Z`; approval
feature commit `473a733` moved the pair to `data/benchmark/core/core-batch-003.jsonl`. Both records
use the `data` route, `train` split,
`eg-data-ecos-gdp-20260717` evidence group, and `kv-core-data-02` parallel group. Their only
data-unit binding remains `ecos-200y108-snapshot-20260717`.

Both questions ask for Korea's seasonally adjusted real expenditure on GDP in 2026 Q1 as available
at the inclusive end of 2026-07-17 in Asia/Seoul. The reference answers and typed tool expectations
reproduce raw and normalized value `596692.8`, canonical unit `billion_krw`, one-decimal display,
the committed snapshot checksum, rights catalog, rights decision, and Bank of Korea attribution.
The approved records preserve the original AI author, add the named reviewer and aware review
timestamp, record `annotation.status=approved`, and use the `batch-003` lifecycle tag. The
questions, answers, cutoff, route, split, evidence group, data-unit binding, record IDs, tool
expectations, attribution, and normalization did not change during review.

At the ECOS GDP approval checkpoint, the focused benchmark acceptance suite passed 27 tests. Those
tests validated the two records against the frozen matrix and committed source bytes, rebuilt the
manifest and rights bundle, called `read_snapshot_as_of` at the record cutoff, verified
normalization and bilingual parity, and confirmed the approved count was eight. The matrix,
source bundle, rights decisions, public schemas,
source package, and execution runtime are unchanged. At that approval checkpoint, no subsequent
pair or implementation slice had been selected.

## 5. Approved ECOS current-account pair

The frozen `kv-core-data-03` Korean/English pair was completed as
`data/benchmark/drafts/core-draft-004.jsonl` on 2026-08-20 in feature commit `50c4d9c`. Hyungbae
Cho approved both records on 2026-08-21 with review timestamp `2026-08-21T07:14:13Z`; approval
feature commit `db6700e` moved the pair to `data/benchmark/core/core-batch-004.jsonl`. Both
records use the `data` route, `train` split, `eg-data-ecos-current-account-20260717` evidence
group, and `kv-core-data-03` parallel group. Their only data-unit binding remains the existing
`ecos-301y017-snapshot-20260717` evidence whose use in KOR-RTD is owner-approved.

Both questions ask for Korea's seasonally adjusted current account in May 2026 as available at the
inclusive end of 2026-07-17 in Asia/Seoul. The reference answers and typed tool expectations
reproduce raw and normalized value `38121.1`, canonical unit `million_usd`, one-decimal display,
the committed snapshot checksum, rights catalog, rights decision, and Bank of Korea attribution.
The approved records preserve the original AI author, add the named reviewer and aware review
timestamp, record `annotation.status=approved`, and use the `batch-004` lifecycle tag. The
questions, answers, cutoff, route, split, evidence group, data-unit binding, record IDs, tool
expectations, attribution, and normalization did not change during review.

At the ECOS current-account approval checkpoint, the focused benchmark acceptance suite passed 33
tests across the first four files listed in the reproduction commands, and the full suite passed
1,141 tests at 100% SovereignLab statement/branch coverage (4,679 statements, 1,568 branches)
across 73 Ruff-formatted Python files using a fresh OS `--basetemp`. The 13 public schemas
regenerated deterministically, the five committed traces remained unchanged, the working tree diff
was clean, and the slice cost $0.00. The record substance, frozen matrix, source bundle, rights
decisions, source package, and execution runtime did not change.

That approval brought the approved core to 10/40, leaving no draft review candidate in the
committed tree at that checkpoint. The owner-directed next slice was a bounded draft-only
authoring pass for the frozen `kv-core-data-04` pair (KOSIS national CPI) using only the existing
committed `kosis-cpi-snapshot-20260717` evidence, whose use in KOR-RTD is owner-approved
(ADR 0007); the resulting drafts are described below and stay `annotation.status=draft` pending a
separate named human review.

## 6. Draft KOSIS CPI pair

Feature commit `5e0da06` adds exactly the frozen `kv-core-data-04` Korean/English pair to
`data/benchmark/drafts/core-draft-005.jsonl` at `annotation.status=draft`. Both records use the
`data` route, `dev` split, `eg-data-kosis-cpi-20260717` evidence group, and `kv-core-data-04`
parallel group. Their only data-unit binding is the existing `kosis-cpi-snapshot-20260717`
evidence whose use in KOR-RTD is owner-approved under ADR 0007. This is the first authored pair on
the KOSIS CPI snapshot and the first `dev`-split data pair, and it completes authored coverage of
all three frozen `read_snapshot_as_of` bindings (ECOS GDP, ECOS current account, KOSIS CPI).

Both questions ask for Korea's June 2026 national all-items consumer price index (2020=100) as
available at the inclusive end of 2026-07-17 in Asia/Seoul, read from the committed July 2026
KOSIS forward snapshot `kosis-101-dt-1j22003-t-t10-20260717t115242998550z` (KOSIS table
`DT_1J22003`, item `T/T10`). The reference answers and typed tool expectations reproduce raw and
normalized value `119.99`, canonical unit `index_2020_100`, two-decimal display, normalization
rule `kosis-101-dt-1j22003-t-t10-index-v1`, the committed snapshot checksum, rights catalog,
rights decision, and 국가데이터처 producer attribution. Their annotations preserve
`annotated_by="Claude AI draft"` at `2026-08-21T07:17:23Z`, contain no reviewer metadata, and use
only the `draft-005` lifecycle tag.

The pair-specific focused test passes six tests, the combined focused benchmark suite passes 39,
and the full suite passes 1,147 tests at 100% SovereignLab statement/branch coverage (4,679
statements, 1,568 branches) across 74 Ruff-formatted Python files using a fresh OS `--basetemp`.
The 13 public schemas regenerate deterministically, the five committed traces remain unchanged,
the working tree diff is clean, and the slice cost $0.00. The frozen matrix, approved core, source
bundle, rights decisions, source package, and execution runtime did not change.

The approved core remains 10/40. These two drafts and the 28 unauthored slots comprise the other
30 unapproved records. The exact next action is named human review of only `kv-core-data-04-ko`
and `kv-core-data-04-en`; do not pre-approve them or select another pair.

## 7. Approval records

On 2026-07-25, Hyungbae Cho explicitly approved:

1. the unchanged 40-record structural allocation in
   `data/benchmark/core-authoring-matrix-v1.json`; and
2. all four records in `core-batch-001.jsonl` without question, answer, route, or evidence changes.

The filenames and existing matrix field names remain unchanged. The approved record file keeps its
filename and moves from `drafts/` to `core/` so the directory reflects its review state.

On 2026-07-29, Hyungbae Cho explicitly approved both records in the `kv-core-doc-01` documentary
pair. The substantive record fields and frozen matrix remain unchanged; the second batch moved
from `drafts/core-draft-002.jsonl` to `core/core-batch-002.jsonl` with approval metadata and the
corresponding lifecycle tag.

On 2026-08-20, Hyungbae Cho explicitly approved both records in the `kv-core-data-02` ECOS GDP
pair. The substantive record fields and frozen matrix remain unchanged; approval feature commit
`473a733` records reviewer `Hyungbae Cho`, review timestamp `2026-08-20T00:24:18Z`,
`annotation.status=approved`, the `batch-003` lifecycle tag, and the move from
`drafts/core-draft-003.jsonl` to `core/core-batch-003.jsonl`.

On 2026-08-21, Hyungbae Cho explicitly approved both records in the `kv-core-data-03` ECOS
current-account pair. The substantive record fields and frozen matrix remain unchanged; approval
feature commit `db6700e` records reviewer `Hyungbae Cho`, review timestamp `2026-08-21T07:14:13Z`,
`annotation.status=approved`, the `batch-004` lifecycle tag, and the move from
`drafts/core-draft-004.jsonl` to `core/core-batch-004.jsonl`.

## 8. Human-review checklist

For each bilingual pair, the reviewer must verify:

1. Korean and English questions ask the same task without answer-bearing translation differences.
2. The route and source-unit allocation match the frozen matrix.
3. `as_of`, source scope, edition, period, unit, normalization rule, and display precision are
   exact.
4. The reference answer contains no fact that the committed evidence packet cannot reproduce.
5. Abstention wording states the actual fail-closed reason and does not expose post-cutoff values.
6. Tags, split, evidence group, and parallel group are correct.

Future corrections remain in their draft batch until review is complete. An approval records the
reviewer and review timestamp in each `BenchmarkRecord`; it does not rewrite the frozen matrix
allocation.

## 9. Reproduction

```bash
python scripts/export_json_schemas.py
python -m pytest tests/benchmark/test_core_batch.py
python -m pytest tests/benchmark/test_bok_outlook_core.py
python -m pytest tests/benchmark/test_ecos_gdp_core.py
python -m pytest tests/benchmark/test_ecos_current_account_core.py
python -m pytest tests/benchmark/test_kosis_cpi_draft.py
python -m ruff check .
python -m ruff format --check .
```

The batch test validates the matrix, constructs a real `BenchmarkBundle` from committed manifests,
ledger, and rights catalog, reruns the fail-closed resolver over the committed CLI bytes, applies
normalization 1.0.0, and checks the earlier-cutoff abstention.

The documentary-core test validates both records against their strict manifests and the frozen
matrix, enforces language-specific publication cutoffs and split-group integrity, verifies the
named reviewer metadata, and confirms the current approved count is ten.

The ECOS GDP core test validates both approved records and named-review metadata against the frozen
matrix, existing snapshot, manifest, checksum, rights decision, and normalization rule. At its
approval checkpoint, the first three focused benchmark files passed 27 tests; the approved count it
verifies is now ten.

The ECOS current-account core test validates both approved records and named-review metadata
against the frozen allocation, existing snapshot, manifest, checksum, rights decision, exact
`202605` observation, normalization rule, attribution, and prior-day abstention. At its approval
checkpoint, the first four focused benchmark files passed 33 tests while the approved count is
ten.

The KOSIS CPI draft test validates the two unapproved records against the frozen allocation,
existing snapshot, manifest, checksum, rights decision, exact `202606` observation, normalization
rule, attribution, and prior-day abstention. It adds six tests, bringing the current focused
benchmark suite to 39 while the approved count remains ten.
