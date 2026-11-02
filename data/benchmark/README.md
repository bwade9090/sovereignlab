# K-VINTAGE benchmark artifacts

`core-authoring-matrix-v1.json` is the frozen structural allocation for the 40-record,
human-reviewed core. It contains 20 bilingual pairs and is validated by
`CoreAuthoringMatrix` 1.0.0.

Files under `drafts/` are review candidates, not approved gold records. In particular,
they must remain `annotation.status=draft` until a named human reviewer verifies them. Never merge
draft counts with the human-reviewed core or with machine-generated tier-2 probes.

The Korean/English `kv-core-data-02` pair was completed as
`drafts/core-draft-003.jsonl` on 2026-08-19 in feature commit `f2d2523`. Hyungbae Cho approved both
records on 2026-08-20 with review timestamp `2026-08-20T00:24:18Z`; approval feature commit
`473a733` moved them unchanged in substance to `core/core-batch-003.jsonl` and changed the
lifecycle tag to `batch-003`. Both records use the frozen `data` route, `train` split,
`eg-data-ecos-gdp-20260717` evidence group, and `ecos-200y108-snapshot-20260717` data-unit binding.
They reproduce the 2026 Q1 value of `596,692.8` billion won through `read_snapshot_as_of`. The
matrix, source bundle, rights decisions, public schemas, and execution runtime were not changed.

Files under `core/` are human-reviewed records. `core/core-batch-001.jsonl` contains the first four
owner-approved core records, and `core/core-batch-002.jsonl` contains the first two documentary
core records, whose cutoffs ADR 0011 moved to 2026-06-12 (Korean) and 2026-07-06 (English)
before Hyungbae Cho re-approved them on 2026-11-02. `core/core-batch-003.jsonl` contains the two approved ECOS GDP records,
`core/core-batch-004.jsonl` contains the two approved ECOS current-account records,
`core/core-batch-005.jsonl` contains the two approved KOSIS CPI records,
`core/core-batch-006.jsonl` contains the two approved OECD scope abstention records,
`core/core-batch-007.jsonl` contains the two approved CPI revision false-premise abstention
records, `core/core-batch-008.jsonl` contains the two approved missing-as-of abstention
records, `core/core-batch-009.jsonl` contains the two approved ledger frontier abstention
records, and `core/core-batch-010.jsonl` contains the two approved BOK outlook CLI combined
records. Their annotations preserve the AI author and name the human reviewer and review
timestamp. `core/core-batch-011.jsonl` contains the two approved November 2025 outlook inflation
records. Together they total 24/40 approved records.

The Korean/English `kv-core-data-03` pair was completed as
`drafts/core-draft-004.jsonl` on 2026-08-20 in feature commit `50c4d9c`. Hyungbae Cho approved both
records on 2026-08-21 with review timestamp `2026-08-21T07:14:13Z`; approval feature commit
`db6700e` moved them unchanged in substance to `core/core-batch-004.jsonl` and changed the
lifecycle tag to `batch-004`. Both records use the frozen `data` route, `train` split,
`eg-data-ecos-current-account-20260717` evidence group, and `ecos-301y017-snapshot-20260717`
data-unit binding. They reproduce the May 2026 seasonally adjusted current-account value as raw and
normalized `38121.1` `million_usd` through `read_snapshot_as_of`. The matrix, source bundle, rights
decisions, public schemas, and execution runtime were not changed.

The approval renamed `tests/benchmark/test_ecos_current_account_draft.py` to
`tests/benchmark/test_ecos_current_account_core.py` with approved expectations and raised the
approved-count assertions in `test_bok_outlook_core.py` and `test_ecos_gdp_core.py` from 8 to 10.

The Korean/English `kv-core-data-04` pair was completed as
`drafts/core-draft-005.jsonl` on 2026-08-21 in feature commit `5e0da06`. Hyungbae Cho approved both
records on 2026-08-25 with review timestamp `2026-08-25T07:10:15Z`; approval feature commit
`95c5e61` moved them unchanged in substance to `core/core-batch-005.jsonl` and changed the
lifecycle tag to `batch-005`. Both records use the frozen `data` route, `dev` split,
`eg-data-kosis-cpi-20260717` evidence group, and `kosis-cpi-snapshot-20260717` data-unit binding,
whose use in KOR-RTD is owner-approved (ADR 0007). They read the June 2026 (period `2026-06`)
national all-items consumer price index (2020=100) as raw and normalized `119.99`
`index_2020_100` through `read_snapshot_as_of`. The approval completes the data route's four
authorable pairs (`kv-core-data-01`..`kv-core-data-04`); the fifth data pair `kv-core-data-05`
stays reserved on the deliberately unauthored test-split unit. The matrix, source bundle, rights
decisions, public schemas, and execution runtime were not changed.

The approval renamed `tests/benchmark/test_kosis_cpi_draft.py` to
`tests/benchmark/test_kosis_cpi_core.py` with approved expectations and raised the approved-count
assertions in `test_bok_outlook_core.py`, `test_ecos_gdp_core.py`, and
`test_ecos_current_account_core.py` from 10 to 12.

The Korean/English `kv-core-abstain-02` pair was completed as
`drafts/core-draft-006.jsonl` on 2026-08-25 in feature commit `c20619d`. Hyungbae Cho approved both
records on 2026-08-26 with review timestamp `2026-08-26T01:49:45Z`; approval feature commit
`4c29b1d` moved them unchanged in substance to `core/core-batch-006.jsonl` and changed the
lifecycle tag to `batch-006`. Both records use the frozen `abstain` route, `train` split,
`eg-abstain-unapproved-neighboring-oecd-scope` evidence group, and parallel group
`kv-core-abstain-02`. The pair binds no document or data units and carries no tool expectations
and no reference answer — only a language-matched `abstention_reason`. Both questions ask for
Korea's OECD normalised CLI value for May 2026 using only the vintage available as of 2026-07-09.
The normalised CLI is a neighboring measure outside the sole owner-approved OECD raw-data scope —
Korea's monthly amplitude-adjusted CLI (`KOR.M.LI_AA.IX._T`, ADR 0007) — so the gold behavior is
abstention on the missing rights basis: the abstention reasons name the approved scope, forbid
substituting the approved series or exposing an unapproved observation, and leak no observation
value. The cutoff is deliberately one where the approved amplitude-adjusted scope does resolve
(edition `202607`, value `102.66`), so the approved abstention is rights-driven, not
availability-driven. This is the second approved abstain pair (after `kv-core-abstain-01`) and the
first approved pair whose fail-closed basis is a rights boundary rather than the availability
ledger. The matrix, source bundle, rights decisions, public schemas, and execution runtime were
not changed.

The approval renamed `tests/benchmark/test_oecd_scope_abstain_draft.py` to
`tests/benchmark/test_oecd_scope_abstain_core.py` with approved expectations and raised the
approved-count assertions in `test_bok_outlook_core.py`, `test_ecos_gdp_core.py`,
`test_ecos_current_account_core.py`, and `test_kosis_cpi_core.py` from 12 to 14.

The Korean/English `kv-core-abstain-03` pair was completed as
`drafts/core-draft-007.jsonl` on 2026-08-26 in feature commit `77d247d`. Hyungbae Cho approved both
records on 2026-08-26 with review timestamp `2026-08-26T07:34:50Z`; approval feature commit
`5e14119` moved them unchanged in substance to `core/core-batch-007.jsonl` and changed the
lifecycle tag to `batch-007`. Both records use the frozen `abstain` route, `train` split,
`eg-abstain-korean-cpi-revision-false-premise` evidence group, and parallel group
`kv-core-abstain-03`. The pair binds no document or data units and carries no tool expectations
and no reference answer — only a language-matched `abstention_reason`. Both questions rest on the
false premise that the many archived OECD editions of Korea's consumer price index prove the
Korean CPI was revised just as many times, and ask for before-and-after November 2019 CPI values
using only the vintage available as of 2026-07-17. The gold behavior is to reject the premise and
abstain: archived edition counts measure archive coverage, not actual revisions, and KOR-RTD
holds no owner-approved raw-data decision for the OECD Korea CPI revision series — raw OECD
observations outside the sole approved Korea monthly amplitude-adjusted CLI scope
(`KOR.M.LI_AA.IX._T`) remain metadata-only — so no before-and-after CPI observation can be
served, and the system must not fabricate revision values or expose an unapproved observation.
This is the third approved abstain pair (after the availability-frontier `kv-core-abstain-01` and
the unapproved-neighboring-scope `kv-core-abstain-02`) and the first approved false-premise
rejection pair. The matrix, source bundle, rights decisions, public schemas, and execution
runtime were not changed.

The approval renamed `tests/benchmark/test_cpi_revision_abstain_draft.py` to
`tests/benchmark/test_cpi_revision_abstain_core.py` with approved expectations and raised the
approved-count assertions in `test_bok_outlook_core.py`, `test_ecos_gdp_core.py`,
`test_ecos_current_account_core.py`, `test_kosis_cpi_core.py`, and
`test_oecd_scope_abstain_core.py` from 14 to 16.

The Korean/English `kv-core-abstain-04` pair was completed as
`drafts/core-draft-008.jsonl` on 2026-08-26 in feature commit `fd7640b`. Hyungbae Cho approved both
records on 2026-08-27 with review timestamp `2026-08-27T06:37:54Z`; approval feature commit
`dfcd191` moved them unchanged in substance to `core/core-batch-008.jsonl` and changed the
lifecycle tag to `batch-008`. Both records use the frozen `abstain` route, `dev` split (the
second dev-split pair after `kv-core-data-04`), `eg-abstain-missing-as-of` evidence group, and
parallel group `kv-core-abstain-04`. The pair binds no document or data units and carries no
tool expectations and no reference answer — only a language-matched `abstention_reason`. Both
questions ask for Korea's OECD amplitude-adjusted CLI value for May 2026 using the vintage
available at the time, while omitting the as-of date the vintage request depends on; the
record-level `as_of` field is 2026-07-17. The gold behavior is to ask for the missing as-of and
abstain: a vintage answer depends on its as-of cutoff, and KOR-RTD's fail-closed contract never
executes without an explicit `effective_as_of` and never guesses or defaults the cutoff, because
an assumed cutoff can expose the wrong vintage and create temporal leakage. A focused contrast
test shows the same request resolves once an explicit cutoff of 2026-07-09 is supplied (edition
`202607`, value `102.66` from the owner-approved CLI scope), so the approved abstention is
missing-cutoff driven, not availability- or rights-driven. This is the fourth approved abstain
pair (the availability-frontier `kv-core-abstain-01`, the unapproved-neighboring-scope
`kv-core-abstain-02`, the false-premise-rejection `kv-core-abstain-03`, and now this
missing-as-of clarification pair) and the first approved dev-split abstain pair. The matrix,
source bundle, rights decisions, public schemas, and execution runtime were not changed.

The approval renamed `tests/benchmark/test_missing_as_of_abstain_draft.py` to
`tests/benchmark/test_missing_as_of_abstain_core.py` with approved expectations and raised the
approved-count assertions in `test_bok_outlook_core.py`, `test_ecos_gdp_core.py`,
`test_ecos_current_account_core.py`, `test_kosis_cpi_core.py`, `test_oecd_scope_abstain_core.py`,
and `test_cpi_revision_abstain_core.py` from 16 to 18.

The Korean/English `kv-core-abstain-05` pair was completed as
`drafts/core-draft-009.jsonl` on 2026-08-27 in feature commit `d1eb5ea`. Hyungbae Cho approved both
records on 2026-08-27 with review timestamp `2026-08-27T07:51:13Z`; approval feature commit
`16d3dfd` moved them unchanged in substance to `core/core-batch-009.jsonl` and changed the
lifecycle tag to `batch-009`. Both records use the frozen `abstain` route, `test` split (the
first approved test-split pair), `eg-abstain-cutoff-after-complete-through` evidence group, and
parallel group `kv-core-abstain-05`. The pair binds no document or data units and carries no
tool expectations and no reference answer — only a language-matched `abstention_reason`. Both
questions ask for Korea's OECD amplitude-adjusted CLI value for May 2026 using only the vintage
available as of August 15, 2026 (record-level `as_of` 2026-08-15), a cutoff beyond the committed
edition-availability ledger's completeness frontier (`complete_through`, the 2026-07-17 capture
instant). The gold behavior is abstention with `cutoff_beyond_complete_through`: past the
frontier the ledger cannot certify which editions had become available or when, and the
fail-closed resolver must not infer editions beyond the frontier or expose a value. A focused
contrast test shows a pre-frontier cutoff of 2026-07-09 still selects edition `202607`, so the
approved abstention is frontier-driven, not rights- or premise-driven. This is the fifth
approved abstain pair (the availability-frontier `kv-core-abstain-01`, the
unapproved-neighboring-scope `kv-core-abstain-02`, the false-premise-rejection
`kv-core-abstain-03`, the missing-as-of `kv-core-abstain-04`, and now this ledger-frontier
pair), completing approval of all five abstain-route pairs, and the first approved test-split
pair. The matrix, source bundle, rights decisions, public schemas, and execution runtime were
not changed.

The approval renamed `tests/benchmark/test_ledger_frontier_abstain_draft.py` to
`tests/benchmark/test_ledger_frontier_abstain_core.py` with approved expectations and raised the
approved-count assertions in `test_bok_outlook_core.py`, `test_ecos_gdp_core.py`,
`test_ecos_current_account_core.py`, `test_kosis_cpi_core.py`, `test_oecd_scope_abstain_core.py`,
`test_cpi_revision_abstain_core.py`, and `test_missing_as_of_abstain_core.py` from 18 to 20.

Feature commit `933c0e9` added exactly `kv-core-both-01-ko` and `kv-core-both-01-en` at
`annotation.status=draft` in `drafts/core-draft-010.jsonl`. Both records use the frozen
`documents_and_data` route — the first combined pair authored in the core — `train` split,
`eg-both-outlook-2026-05-cli-202607` evidence group, parallel group `kv-core-both-01`, document
unit `bok-outlook-release-2026-05`, and data unit `oecd-stes-edition-202607`, exactly as the
frozen matrix allocates. Each record carries exactly one page-anchored document evidence entry
and one `resolve_stes_as_of` tool expectation. Both records share `as_of` 2026-07-09: both
document publications precede that cutoff (under ADR 0011, the Korean report's bytes date from
2026-06-12 and the official English translation's from 2026-07-06), and the committed
edition-availability ledger proves CLI
edition `202607` was demonstrably available by it. The document claim is the report's 2026 GDP
growth projection of 2.6%, well above the February forecast of 2.0%, anchored to the Korean
summary page 8 (요약 2/10 — 경제전망 요약) and the official English executive summary page 6,
located in the owner-approved, hash-verified local PDF bodies re-fetched earlier into the
Git-ignored `data/raw/`; the reference answers disclose summarization/paraphrase and attribute
the Bank of Korea. The tool expectation mirrors the approved `kv-core-data-01` convention: CLI
source `oecd-stes-cli-kor-li-aa-20260717t115302688498z` with vintage ledger
`oecd-stes-ledger-20260717t115242998550z`, selected edition `202607`, raw and normalized value
`102.66`, canonical unit `oecd_amplitude_adjusted_index`, two display places, and normalization
rule `oecd-stes-kor-li-aa-index-v1`. The matrix, source bundle, rights decisions, public
schemas, and execution runtime were not changed, and no PDF body or extracted text entered Git.

Hyungbae Cho approved both records on 2026-11-02 with review timestamp `2026-11-02T11:04:32Z`.
The review re-fetched both official PDFs with owner approval into the Git-ignored `data/raw/`,
confirmed both match their manifests byte-for-byte, and found the claimed projection, February
forecast, and comparison wording on both anchored pages. It found one label defect. The English
locator section's suffix `Economic outlook summary` translated the Korean heading and does not
appear on page 6, so commit `4365096` corrected the section to the literal `Executive Summary ii`
before approval. Approval feature commit `8bc88a1` then added the reviewer metadata and the
`batch-010` lifecycle tag and moved the pair to `core/core-batch-010.jsonl`. No other field
changed. The focused module is now `tests/benchmark/test_bok_cli_both_core.py`; it pins both
literal section labels and raises the approved-count assertions in the other focused benchmark
files from 20 to 22.

At that approval checkpoint, the combined focused benchmark suite passed 70 tests across ten
files, and the full suite passed 1,184 at 100% SovereignLab statement/branch coverage across 80
Ruff-formatted Python files. The 13 public schemas and five committed traces were unchanged.

Feature commit `5465eca` added exactly `kv-core-doc-02-ko` and `kv-core-doc-02-en` at
`annotation.status=draft` in `drafts/core-draft-011.jsonl`. Both use the frozen `documents` route,
`train` split, `eg-doc-bok-outlook-2025-11` evidence group, parallel group `kv-core-doc-02`, and
document unit `bok-outlook-release-2025-11`. Matching the frozen intent, they recover one
inflation-outlook rationale from the November 2025 report: CPI inflation of 2.1% in both 2025
and 2026, as the higher exchange rate and easing domestic-demand weakness outweigh lower oil
prices. The anchors are the Korean summary page 5 (`요약 1/7`) and the English executive summary
page 5 (`Executive Summary i`). Each `as_of` equals its edition's ADR 0011 date: 2026-03-31 for
Korean and 2026-01-22 for English. Six focused tests in
`tests/benchmark/test_bok_outlook_2025_11_draft.py` brought the focused benchmark suite to 76
tests across 11 files, and the full suite passes 1,193 tests across 82 Ruff-formatted Python
files.

Hyungbae Cho approved both records on 2026-11-02 without a substantive change, with review
timestamp `2026-11-02T13:44:04Z`. Approval feature commit `6cdd13d` moved them to
`core/core-batch-011.jsonl` and renamed the focused module to
`tests/benchmark/test_bok_outlook_2025_11_core.py`. The approved count is now 24/40, no draft
is pending, and 16 records remain unauthored. No later pair or slice is selected; choosing the
next one is an owner decision.

The matrix assigns every planned documentary or data source unit to one dataset split. Do not
replace a reserved unit or move a pair between splits without a versioned matrix change, tests, and
an update to `docs/PROJECT_STATUS.md`.
