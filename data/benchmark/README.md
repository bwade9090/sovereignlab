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
core records. `core/core-batch-003.jsonl` contains the two approved ECOS GDP records,
`core/core-batch-004.jsonl` contains the two approved ECOS current-account records,
`core/core-batch-005.jsonl` contains the two approved KOSIS CPI records, and
`core/core-batch-006.jsonl` contains the two approved OECD scope abstention records. Their
annotations preserve the AI author and name the human reviewer and review timestamp. Together they
total 14/40 approved records.

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

Feature commit `77d247d` adds exactly `kv-core-abstain-03-ko` and `kv-core-abstain-03-en` at
`annotation.status=draft` in `drafts/core-draft-007.jsonl`. Both records use the frozen `abstain`
route, `train` split, `eg-abstain-korean-cpi-revision-false-premise` evidence group, and parallel
group `kv-core-abstain-03`. The pair binds no document or data units and carries no tool
expectations and no reference answer — only a language-matched `abstention_reason`. Both questions
rest on the false premise that the many archived OECD editions of Korea's consumer price index
prove the Korean CPI was revised just as many times, and ask for before-and-after November 2019
CPI values using only the vintage available as of 2026-07-17. The gold behavior is to reject the
premise and abstain: archived edition counts measure archive coverage, not actual revisions, and
KOR-RTD holds no owner-approved raw-data decision for the OECD Korea CPI revision series — raw
OECD observations outside the sole approved Korea monthly amplitude-adjusted CLI scope
(`KOR.M.LI_AA.IX._T`) remain metadata-only — so no before-and-after CPI observation can be
served, and the system must not fabricate revision values or expose an unapproved observation.
This is the third authored abstain pair (after the approved `kv-core-abstain-01` and
`kv-core-abstain-02`) and the first false-premise rejection pair. The matrix, source bundle,
rights decisions, public schemas, and execution runtime were not changed. These two records
remain pending named human review and do not count toward the approved core: 14/40 records are
approved, two of the other 26 are drafts, and 24 remain unauthored and unapproved.

The preceding approval checkpoint passed 45 focused benchmark tests and 1,153 full-suite tests
across 75 formatted Python files. The current draft checkpoint adds six focused tests:
`tests/benchmark/test_cpi_revision_abstain_draft.py` passes all six and asserts that the rights
catalog's only OECD decision is the approved CLI scope, that the serialized records leak no
observation value and no snapshot identifier, and that the only approved CPI evidence in KOR-RTD
(the KOSIS latest-only snapshot) carries `vintage_semantics=latest_only`, so committed evidence
cannot serve any CPI revision by construction. The combined focused benchmark suite passes 51
across seven files, and the full suite passes 1,159 at 100% SovereignLab statement/branch
coverage across 76 Ruff-formatted Python files. The 13 public schemas and five committed traces
are unchanged. The exact next action is named human review of only these two drafts; do not
pre-approve them or select another pair.

The matrix assigns every planned documentary or data source unit to one dataset split. Do not
replace a reserved unit or move a pair between splits without a versioned matrix change, tests, and
an update to `docs/PROJECT_STATUS.md`.
