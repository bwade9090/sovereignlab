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
`core/core-batch-004.jsonl` contains the two approved ECOS current-account records, and
`core/core-batch-005.jsonl` contains the two approved KOSIS CPI records. Their annotations
preserve the AI author and name the human reviewer and review timestamp. Together they
total 12/40 approved records; the other 28 matrix slots remain unauthored and unapproved, and no
draft review candidate remains.

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
`test_ecos_current_account_core.py` from 10 to 12. The focused benchmark acceptance suite passes
39 tests across five files and confirms the approved count is 12/40, and the full suite passes
1,147 at 100% SovereignLab statement/branch coverage across 74 Ruff-formatted Python files. The 13
public schemas and five committed traces are unchanged. The exact next outcome is an owner-directed
draft-only authoring slice for the frozen `kv-core-abstain-02` pair — an abstention pair (`train`
split) whose question asks for a neighboring OECD observation scope (Korea's normalised CLI) that
has no owner-approved raw-data decision, so the gold behavior is abstention. Abstain pairs bind no
source units, so the slice uses no new evidence, only the committed rights catalog as the
fail-closed basis; the new drafts must remain `annotation.status=draft` pending a separate named
human review.

The matrix assigns every planned documentary or data source unit to one dataset split. Do not
replace a reserved unit or move a pair between splits without a versioned matrix change, tests, and
an update to `docs/PROJECT_STATUS.md`.
