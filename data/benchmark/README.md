# K-VINTAGE benchmark artifacts

`core-authoring-matrix-v1.json` is the frozen structural allocation for the 40-record,
human-reviewed core. It contains 20 bilingual pairs and is validated by
`CoreAuthoringMatrix` 1.0.0.

Files under `drafts/` are review candidates, not approved gold records. In particular,
they must remain `annotation.status=draft` until a named human reviewer verifies them. Never merge
draft counts with the human-reviewed core or with machine-generated tier-2 probes.

`drafts/core-draft-003.jsonl` contains the Korean/English `kv-core-data-02` pair completed on
2026-08-19. Both records use the frozen `data` route, `train` split,
`eg-data-ecos-gdp-20260717` evidence group, and
`ecos-200y108-snapshot-20260717` data-unit binding. They reproduce the 2026 Q1 value of `596,692.8`
billion won from the latest-only ECOS snapshot that the owner approved for use in KOR-RTD through
`read_snapshot_as_of`, and remain pending named human review. The matrix, source bundle, rights
decisions, and public schemas were not changed.

Files under `core/` are human-reviewed records. `core/core-batch-001.jsonl` contains the first four
owner-approved core records, and `core/core-batch-002.jsonl` contains the first two documentary
core records. Their annotations preserve the AI author and name the human reviewer and review
timestamp. Together they total 6/40 approved records.

The focused benchmark acceptance suite, including `tests/benchmark/test_ecos_gdp_draft.py`,
passes 27 tests. The draft pair remains excluded from the 6/40 approved count.

The matrix assigns every planned documentary or data source unit to one dataset split. Do not
replace a reserved unit or move a pair between splits without a versioned matrix change, tests, and
an update to `docs/PROJECT_STATUS.md`.
