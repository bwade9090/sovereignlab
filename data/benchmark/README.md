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
core records. `core/core-batch-003.jsonl` contains the two approved ECOS GDP records. Their
annotations preserve the AI author and name the human reviewer and review timestamp. Together they
total 8/40 approved records.

Feature commit `50c4d9c` adds exactly `kv-core-data-03-ko` and `kv-core-data-03-en` at
`annotation.status=draft` in `drafts/core-draft-004.jsonl`. Both records use the frozen `data`
route, `train` split, `eg-data-ecos-current-account-20260717` evidence group, and
`ecos-301y017-snapshot-20260717` data-unit binding. They reproduce the May 2026 seasonally adjusted
current-account value as raw and normalized `38121.1` `million_usd` through
`read_snapshot_as_of`. The existing source, manifest, checksum, rights decision, attribution, and
normalization boundaries are unchanged. These two records remain pending named human review and do
not count toward the approved core: 8/40 records are approved, two of the other 32 are drafts, and
30 remain unauthored and unapproved.

The preceding approval checkpoint passed 27 focused benchmark tests and 1,135 full-suite tests
across 72 formatted Python files. The current draft checkpoint adds six focused tests:
`tests/benchmark/test_ecos_current_account_draft.py` passes all six, the combined focused benchmark
suite passes 33, and the full suite passes 1,141 at 100% SovereignLab statement/branch coverage
across 73 Ruff-formatted Python files. The 13 public schemas and five committed traces are
unchanged. The exact next action is named human review of only these two drafts; do not pre-approve
them or select another pair.

The matrix assigns every planned documentary or data source unit to one dataset split. Do not
replace a reserved unit or move a pair between splits without a versioned matrix change, tests, and
an update to `docs/PROJECT_STATUS.md`.
