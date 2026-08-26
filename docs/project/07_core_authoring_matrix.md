# K-VINTAGE human-reviewed core authoring matrix 1.0.0

- Status: structural allocation frozen; first fourteen records owner-approved; `kv-core-abstain-03`
  drafted and pending named human review
- Date: 2026-08-26
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
The later ECOS GDP, ECOS current-account, KOSIS CPI, and OECD scope abstention approvals
described below bring the current total to 14/40. The CPI revision false-premise abstention
draft described after them accounts for two of the 26 unapproved records; the other 24 remain
unauthored and unapproved.

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
(ADR 0007); the resulting pair is described below and completed named human review on 2026-08-25.

## 6. Approved KOSIS CPI pair

The frozen `kv-core-data-04` Korean/English pair was completed as
`data/benchmark/drafts/core-draft-005.jsonl` on 2026-08-21 in feature commit `5e0da06`. Hyungbae
Cho approved both records on 2026-08-25 with review timestamp `2026-08-25T07:10:15Z`; approval
feature commit `95c5e61` moved the pair to `data/benchmark/core/core-batch-005.jsonl`. Both
records use the `data` route, `dev` split, `eg-data-kosis-cpi-20260717` evidence group, and
`kv-core-data-04` parallel group. Their only data-unit binding remains the existing
`kosis-cpi-snapshot-20260717` evidence whose use in KOR-RTD is owner-approved under ADR 0007.
This is the first approved pair on the KOSIS CPI snapshot and the first `dev`-split data pair; it
completes approved coverage of all three frozen `read_snapshot_as_of` bindings (ECOS GDP, ECOS
current account, KOSIS CPI) and the data route's four authorable pairs
(`kv-core-data-01`..`kv-core-data-04`), while the fifth data pair `kv-core-data-05` stays
reserved on the deliberately unauthored test-split unit.

Both questions ask for Korea's June 2026 national all-items consumer price index (2020=100) as
available at the inclusive end of 2026-07-17 in Asia/Seoul, read from the committed July 2026
KOSIS forward snapshot `kosis-101-dt-1j22003-t-t10-20260717t115242998550z` (KOSIS table
`DT_1J22003`, item `T/T10`). The reference answers and typed tool expectations reproduce raw and
normalized value `119.99`, canonical unit `index_2020_100`, two-decimal display, normalization
rule `kosis-101-dt-1j22003-t-t10-index-v1`, the committed snapshot checksum, rights catalog,
rights decision, and 국가데이터처 producer attribution. The approved records preserve the original AI
author, add the named reviewer and aware review timestamp, record `annotation.status=approved`,
and use the `batch-005` lifecycle tag. The questions, answers, cutoff, route, split, evidence
group, data-unit binding, record IDs, tool expectations, attribution, and normalization did not
change during review.

At the KOSIS CPI approval checkpoint, the focused benchmark acceptance suite passed 39 tests
across the first five files listed in the reproduction commands, and the full suite passed 1,147
tests at 100% SovereignLab statement/branch coverage (4,679 statements, 1,568 branches) across 74
Ruff-formatted Python files using a fresh OS `--basetemp`. The 13 public schemas regenerated
deterministically, the five committed traces remained unchanged, the working tree diff was clean,
and the slice cost $0.00. The record substance, frozen matrix, source bundle, rights decisions,
source package, and execution runtime did not change.

That approval brought the approved core to 12/40, leaving no draft review candidate in the
committed tree at that checkpoint. The owner-directed next slice was a bounded draft-only
authoring pass for the frozen `kv-core-abstain-02` pair, a `train`-split abstention pair whose
question asks for a neighboring OECD observation scope (Korea's normalised CLI) that has no
owner-approved raw-data decision, so the gold behavior is abstention. Abstain pairs bind no
source units, so the slice used no new evidence and relied only on the committed rights catalog
as the fail-closed basis; the resulting pair is described below and completed named human review
on 2026-08-26.

## 7. Approved OECD scope abstention pair

The frozen `kv-core-abstain-02` Korean/English pair was completed as
`data/benchmark/drafts/core-draft-006.jsonl` on 2026-08-25 in feature commit `c20619d`. Hyungbae
Cho approved both records on 2026-08-26 with review timestamp `2026-08-26T01:49:45Z`; approval
feature commit `4c29b1d` moved the pair to `data/benchmark/core/core-batch-006.jsonl`. Both
records use the `abstain` route, `train` split, `eg-abstain-unapproved-neighboring-oecd-scope`
evidence group, and `kv-core-abstain-02` parallel group. The pair binds no document or data units
and carries no tool expectations and no reference answer — only a language-matched
`abstention_reason`. This is the second approved abstain pair after `kv-core-abstain-01` and the
first approved pair whose fail-closed basis is a rights boundary rather than the availability
ledger.

Both questions ask for Korea's OECD normalised CLI value for May 2026 using only the vintage
available as of 2026-07-09. The normalised CLI is a neighboring measure outside the sole
owner-approved OECD raw-data scope, Korea's monthly amplitude-adjusted CLI `KOR.M.LI_AA.IX._T`
(ADR 0007), so the gold behavior is abstention on the missing rights basis. The abstention
reasons name the approved scope, forbid substituting the approved series or exposing an
unapproved observation, and leak no observation value. The cutoff 2026-07-09 is deliberately one
where the approved amplitude-adjusted scope does resolve (edition `202607`, value `102.66`), so a
focused contrast test proves the approved abstention is rights-driven, not availability-driven.
The approved records preserve the original AI author, add the named reviewer and aware review
timestamp, record `annotation.status=approved`, and use the `batch-006` lifecycle tag. The
questions, abstention reasons, cutoff, route, split, evidence group, parallel group, and record
IDs did not change during review.

The pair-specific focused test file was renamed to
`tests/benchmark/test_oecd_scope_abstain_core.py` with approved expectations, keeping the
assertions that the serialized records contain neither the `102.66` observation nor the CLI
source or ledger identifiers; at that approval checkpoint the combined focused benchmark
acceptance suite passed 45 tests across the first six files listed in the reproduction commands,
and the full suite passed 1,153 tests at 100% SovereignLab statement/branch coverage (4,679
statements, 1,568 branches) across 75 Ruff-formatted Python files using a fresh OS `--basetemp`.
The 13 public schemas regenerated deterministically, the five committed traces remained
unchanged, the working tree diff was clean, and the slice cost $0.00. The record substance, frozen matrix, source bundle, rights decisions,
source package, and execution runtime did not change.

That approval brought the approved core to 14/40, leaving no draft review candidate in the
committed tree at that checkpoint. The owner-directed next slice was a bounded draft-only
authoring pass for the frozen `kv-core-abstain-03` pair, a `train`-split abstention pair whose
question rests on the false premise that archived OECD edition counts prove the Korean CPI was
revised; the gold behavior is to reject that premise and abstain, because edition counts measure
archive coverage and no owner-approved raw-data decision covers the OECD Korea CPI revision
series. The pair binds no source units and is fully offline; the resulting drafts are described
below and stay `annotation.status=draft` pending a separate named human review.

## 8. Draft CPI revision false-premise abstention pair

Feature commit `77d247d` adds exactly the frozen `kv-core-abstain-03` Korean/English pair to
`data/benchmark/drafts/core-draft-007.jsonl` at `annotation.status=draft`. Both records use the
`abstain` route, `train` split, `eg-abstain-korean-cpi-revision-false-premise` evidence group,
and `kv-core-abstain-03` parallel group. The pair binds no document or data units and carries no
tool expectations and no reference answer — only a language-matched `abstention_reason`. This is
the third authored abstain pair after the approved availability-frontier `kv-core-abstain-01`
and unapproved-neighboring-scope `kv-core-abstain-02` pairs, and the first false-premise
rejection pair.

Both questions rest on the false premise that the many archived OECD editions of Korea's consumer
price index prove the Korean CPI was revised just as many times, and ask for before-and-after
November 2019 CPI values using only the vintage available as of 2026-07-17. The gold behavior is
to reject the premise and abstain: archived edition counts measure archive coverage, not actual
revisions, and KOR-RTD holds no owner-approved raw-data decision for the OECD Korea CPI revision
series — raw OECD observations outside the sole approved Korea monthly amplitude-adjusted CLI
scope `KOR.M.LI_AA.IX._T` remain metadata-only — so no before-and-after CPI observation can be
served, and the system must not fabricate revision values or expose an unapproved observation.
Their annotations preserve `annotated_by="Claude AI draft"` at `2026-08-26T01:51:11Z`, contain no
reviewer metadata, and carry the `core`, `temporal`, `vintage`, `abstention`, `false-premise`,
and `draft-007` tags.

The pair-specific focused test file `tests/benchmark/test_cpi_revision_abstain_draft.py` passes
six tests, including assertions that the rights catalog's only OECD decision is the approved CLI
scope, that the serialized records leak no observation value and no snapshot identifier, and that
the only approved CPI evidence in KOR-RTD — the KOSIS latest-only snapshot — has
`vintage_semantics=latest_only`, so committed evidence cannot serve any CPI revision by
construction. The combined focused benchmark suite passes 51 tests across the seven files listed
in the reproduction commands. The full suite passes 1,159 tests at 100% SovereignLab
statement/branch coverage (4,679 statements, 1,568 branches) across 76 Ruff-formatted Python
files using a fresh OS `--basetemp`. The 13 public schemas regenerate deterministically, the five
committed traces remain unchanged, the working tree diff is clean, and the slice cost $0.00. The
frozen matrix, approved core, source bundle, rights decisions, source package, and execution
runtime did not change.

The approved core remains 14/40. These two drafts and the 24 unauthored slots comprise the other
26 unapproved records. The exact next action is named human review of only `kv-core-abstain-03-ko`
and `kv-core-abstain-03-en`; do not pre-approve them or select another pair.

## 9. Approval records

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

On 2026-08-25, Hyungbae Cho explicitly approved both records in the `kv-core-data-04` KOSIS CPI
pair. The substantive record fields and frozen matrix remain unchanged; approval feature commit
`95c5e61` records reviewer `Hyungbae Cho`, review timestamp `2026-08-25T07:10:15Z`,
`annotation.status=approved`, the `batch-005` lifecycle tag, and the move from
`drafts/core-draft-005.jsonl` to `core/core-batch-005.jsonl`.

On 2026-08-26, Hyungbae Cho explicitly approved both records in the `kv-core-abstain-02` OECD
scope abstention pair. The substantive record fields and frozen matrix remain unchanged; approval
feature commit `4c29b1d` records reviewer `Hyungbae Cho`, review timestamp `2026-08-26T01:49:45Z`,
`annotation.status=approved`, the `batch-006` lifecycle tag, and the move from
`drafts/core-draft-006.jsonl` to `core/core-batch-006.jsonl`.

## 10. Human-review checklist

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

## 11. Reproduction

```bash
python scripts/export_json_schemas.py
python -m pytest tests/benchmark/test_core_batch.py
python -m pytest tests/benchmark/test_bok_outlook_core.py
python -m pytest tests/benchmark/test_ecos_gdp_core.py
python -m pytest tests/benchmark/test_ecos_current_account_core.py
python -m pytest tests/benchmark/test_kosis_cpi_core.py
python -m pytest tests/benchmark/test_oecd_scope_abstain_core.py
python -m pytest tests/benchmark/test_cpi_revision_abstain_draft.py
python -m ruff check .
python -m ruff format --check .
```

The batch test validates the matrix, constructs a real `BenchmarkBundle` from committed manifests,
ledger, and rights catalog, reruns the fail-closed resolver over the committed CLI bytes, applies
normalization 1.0.0, and checks the earlier-cutoff abstention.

The documentary-core test validates both records against their strict manifests and the frozen
matrix, enforces language-specific publication cutoffs and split-group integrity, verifies the
named reviewer metadata, and confirms the current approved count is fourteen.

The ECOS GDP core test validates both approved records and named-review metadata against the frozen
matrix, existing snapshot, manifest, checksum, rights decision, and normalization rule. At its
approval checkpoint, the first three focused benchmark files passed 27 tests; the approved count it
verifies is now fourteen.

The ECOS current-account core test validates both approved records and named-review metadata
against the frozen allocation, existing snapshot, manifest, checksum, rights decision, exact
`202605` observation, normalization rule, attribution, and prior-day abstention. At its approval
checkpoint, the first four focused benchmark files passed 33 tests; the approved count it verifies
is now fourteen.

The KOSIS CPI core test validates both approved records and named-review metadata against the
frozen allocation, existing snapshot, manifest, checksum, rights decision, exact `202606`
observation, normalization rule, attribution, and prior-day abstention. At its approval
checkpoint, the first five focused benchmark files passed 39 tests; the approved count it verifies
is now fourteen.

The OECD scope abstention core test validates both approved records and named-review metadata
against the frozen allocation and the committed rights decisions, confirms they bind no source
units and carry no tool expectations or reference answers, proves through the approved-scope
contrast that the abstention is rights-driven rather than availability-driven, and asserts the
serialized records contain neither the `102.66` observation nor the CLI source or ledger
identifiers. At its approval checkpoint, the first six focused benchmark files passed 45 tests
while the approved count is fourteen.

The CPI revision abstention draft test validates the two unapproved records against the frozen
allocation and the committed rights decisions, confirms they bind no source units and carry no
tool expectations or reference answers, proves the rights catalog's only OECD decision is the
approved CLI scope, asserts the serialized records leak no observation value and no snapshot
identifier, and proves the only approved CPI evidence in KOR-RTD — the KOSIS latest-only
snapshot — carries `vintage_semantics=latest_only`, so committed evidence cannot serve any CPI
revision by construction. It adds six tests, bringing the current focused benchmark suite to 51
while the approved count remains fourteen.
