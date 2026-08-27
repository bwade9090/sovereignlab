# SovereignLab

> What did the data say *then*? Vintage-conditioned evaluation and auditable briefings for Korean/English economic research.

**Status:** M1b verification and vintage-contract groundwork are complete; M2 benchmark and
baseline development is in progress with a frozen 40-record core matrix and 18/40 records
owner-approved. Hyungbae Cho approved the Korean/English `kv-core-abstain-04` pair on 2026-08-27;
the two records now live in `data/benchmark/core/core-batch-008.jsonl`. No draft review candidate
is pending, and the other 22 matrix slots remain unauthored and unapproved. The
first nine ADR 0008 slices and work unit C are complete: five machine-readable real-digest traces
were generated through the actual private offline executor, `ScriptedPlanner`, and committed
registries and corpora in feature commit `883815b`. The trace set covers all four
routes, all three deterministic evidence tools, Korean and English, explicit and implicit cutoffs,
complete execution, planned abstention, and terminal tool abstention with no partial evidence. The
source package is unchanged, the public surface remains 13 deterministic JSON Schemas, and the
executor descriptor still pins 32 source entries and digest
`08f45dab6a36a49cb7d0b588a69236942cd61534540bd4de0772010402dada64`.
The focused executor/replay-trace acceptance run passes 80 tests at 100% coverage over 326
statements and 98 branches, and the focused benchmark acceptance run passes 57 tests. The full
offline baseline is 1,165 tests at 100% statement/branch coverage (4,679 statements, 1,568
branches) across 77 Ruff-formatted Python files. The shipped
minimal reference path is described only as `typed function calling with committed traces`. These
are deterministic offline replays, not provider or live outputs; no provider/live integration or
bounded tool loop exists, and no model-quality or briefing-performance claim is made. Searchable
document evidence remains synthetic, while the trace catalog records the ECOS/OECD attribution and
rights boundaries for embedded data evidence.

For the project's in-scope series, Korea's official statistics APIs (ECOS, KOSIS) expose latest
values without an "as-of" query path. SovereignLab complements Korea's public statistical
infrastructure by building three things in four weeks:

1. **KOR-RTD** — a provenance-contracted point-in-time data layer for Korean macroeconomics: consolidated OECD edition histories plus a scheduled public harvester that forward-captures the latest-only official APIs (append-only, checksummed; commit history is the proof of capture dates).
2. **K-VINTAGE** — a bilingual Korean/English benchmark whose gold answers are computed from the data vintage available at each question's `as_of` date. To our knowledge, for official statistics, this is the first such benchmark (prior art cited in the datasheet: arXiv 2605.23497 statutory as-of QA, the Dallas Fed real-time OECD dataset, the OECD MEI revisions database).
3. **The reference briefing target** — given a bilingual policy question and an optional `as_of`
   date, it will route to temporally filtered document retrieval, a deterministic vintage-resolving
   data tool, both, or a justified abstention, and return a cited briefing with a machine-readable
   evidence and verification trace.

## What will be tested

The project will compare four variants under one frozen benchmark:

1. Closed-book Mistral generation.
2. Temporal hybrid RAG.
3. Temporal RAG plus the deterministic offline data tools (the vintage-resolving as-of resolver
   and the latest-only snapshot reader).
4. The same system with a LoRA-tuned evidence router/tool planner.

**Temporal-leakage rate is the headline per-variant metric** — a system that answers from revised values that did not exist at `as_of` is caught mechanically, with no LLM judge. Further measurements: routing macro-F1, tool-argument validity, Korean/English retrieval recall, citation correctness, numerical provenance, abstention, latency, and cost.

## Current milestone

Charter v2.5 (the K-VINTAGE on KOR-RTD reorientation, source-rights amendments, fail-closed
edition-availability contract, and typed function-calling execution contract) is approved and
documented; see
[ADR 0003](docs/decisions/0003-kvintage-reorientation.md),
[ADR 0004](docs/decisions/0004-source-specific-redistribution-evidence.md),
[ADR 0005](docs/decisions/0005-edition-availability-and-vintage-contract.md),
[ADR 0007](docs/decisions/0007-kosis-cpi-oecd-cli-rights.md),
[ADR 0008](docs/decisions/0008-function-calling-execution-contract.md), and
[ADR 0009](docs/decisions/0009-bok-economic-outlook-public-data-rights.md), with background in
[the proposal](docs/discovery/01_concept_upgrade_proposal.md). M1a froze strict source-manifest and
benchmark-record models with synchronized JSON Schema, synthetic fixtures, and dataset-wide
temporal/split leakage checks. M1b has now verified the primary OECD examples, fixed the claimable
recent Economic Outlook range at EO114–EO119, and converted two evidence-boundary assumptions into
fail-closed contracts: monthly edition labels do not prove day-level availability, and ECOS/KOSIS
do not expose the assumed per-series KOGL field.
Their official use guides instead govern reuse through the original producer or content category.
The current-account candidate is directly identified as Bank of Korea-produced; official
title/frequency evidence supports the same classification for the GDP candidate. The owner approved
ADR 0004, that mapping, and `allowed` rulings for both candidates on 2026-07-16; charter v2.1 records
the source-rights amendment. The standalone rights catalog and both approved metadata records are
implemented. On 2026-07-17 the owner-authored employer-risk review was recorded as
[ADR 0006](docs/decisions/0006-employer-risk-review.md), and accepted ADR 0005 was implemented as
one contract unit ([migration notes](docs/project/05_evidence_contract_2_0_migration.md)): the
`EditionAvailabilityLedger` 1.0.0 with fail-closed edition selection, evidence/benchmark contract
`2.0.0`, and the typed manifest-to-rights-decision link with bundle cross-validation. The offline
as-of resolver and weekly append-only harvester are implemented. The first real, metadata-only OECD
availability capture mechanically records all 330 current edition codes while resolving only
`202607`. ADR 0007 and the current rights catalog additionally authorize only the national KOSIS
total CPI (`101/DT_1J22003/T/T10`) and OECD Korea monthly amplitude-adjusted CLI revision series;
all neighboring scopes remain blocked. The default-branch weekly workflow is active; repository
ECOS/KOSIS Actions secrets are configured; the first manual secret-backed harvester run remains an
optional separately authorized operational check. The paid QLoRA compatibility step passed on a
RunPod A40/CUDA 13 host, closing the M1b gate. The exact `Decimal` unit, variant, rounding, and
grading rules are frozen in the
[number-normalization specification](docs/project/06_number_normalization_spec.md). Charter v2.4
([ADR 0008](docs/decisions/0008-function-calling-execution-contract.md), 2026-07-28) additionally
fixes the minimal briefing execution contract as one typed route and exact calls over three
deterministic offline tools. The first nine independent ADR 0008 slices and work unit C completed
on 2026-08-11 in feature commit `883815b` without changing the source package or 13 public schemas;
see the [private executor contract](docs/project/16_offline_executor_contract.md) and
[committed replay-trace catalog](traces/README.md). The five traces bind the real source tree,
registries, corpus, and planner provenance and stop at the first terminal result without partial
evidence. The minimal path is now described as `typed function calling with committed traces`.
No provider/live integration exists, and ADR 0008 separately defers the bounded tool loop to
post-window v1.1. On 2026-08-19, feature commit `f2d2523` added only the draft Korean/English
`kv-core-data-02` pair and its focused tests using `ecos-200y108-snapshot-20260717`, whose use in
KOR-RTD is owner-approved. The matrix, source bundle, rights decisions, source package, and
13 public schemas remained unchanged. On 2026-08-20, Hyungbae Cho approved both records without a
substantive change; feature commit `473a733` records the named-review metadata, `batch-003`
lifecycle tag, move to `data/benchmark/core/core-batch-003.jsonl`, and focused-test transition.
At that approval checkpoint, the focused benchmark suite passed 27 tests and the full baseline
passed 1,135 tests across 72 formatted Python files. Later on 2026-08-20, feature commit `50c4d9c`
added only the draft Korean/English `kv-core-data-03` pair and six focused tests using the existing
`ecos-301y017-snapshot-20260717` evidence. The pair reproduces the May 2026 seasonally adjusted
current-account value as `38121.1` `million_usd`. On 2026-08-21, Hyungbae Cho approved both
records without a substantive change; feature commit `db6700e` records the named-review metadata,
`batch-004` lifecycle tag, move to `data/benchmark/core/core-batch-004.jsonl`, and focused-test
transition. At that approval checkpoint, the focused benchmark suite passed 33 tests and the full
baseline passed 1,141 tests across 73 formatted Python files. Later on 2026-08-21, feature commit
`5e0da06` added only the draft Korean/English `kv-core-data-04` pair and six focused tests using
the existing committed `kosis-cpi-snapshot-20260717` evidence, whose use in KOR-RTD is
owner-approved (ADR 0007). The pair reads the June 2026 national all-items CPI (2020=100) as
`119.99` `index_2020_100` and completes coverage of all three frozen `read_snapshot_as_of`
bindings. On 2026-08-25, Hyungbae Cho approved both records without a substantive change; feature
commit `95c5e61` records the named-review metadata, `batch-005` lifecycle tag, move to
`data/benchmark/core/core-batch-005.jsonl`, and focused-test transition. The approval completes
the data route's four authorable pairs (`kv-core-data-01`..`kv-core-data-04`); the fifth data pair
`kv-core-data-05` stays reserved on the deliberately unauthored test-split unit. At that approval
checkpoint, the focused benchmark suite passed 39 tests and the full baseline passed 1,147 tests
across 74 formatted Python files. Later on 2026-08-25, feature commit `c20619d` added only the
draft Korean/English `kv-core-abstain-02` pair and six focused tests. The abstention pair
(`train` split) binds no document or data units, carries no tool expectations and no reference
answer, and asks for Korea's OECD normalised CLI value for May 2026 using only the vintage
available as of 2026-07-09 — a neighboring measure outside the sole owner-approved OECD raw-data
scope, Korea's monthly amplitude-adjusted CLI (`KOR.M.LI_AA.IX._T`, ADR 0007) — so each record
carries only a language-matched abstention reason on the missing rights basis and leaks no
observation value. The approved scope deliberately does resolve at that cutoff, so the drafted
abstention is rights-driven, not availability-driven. On 2026-08-26, Hyungbae Cho approved both
records without a substantive change; feature commit `4c29b1d` records the named-review metadata,
`batch-006` lifecycle tag, move to `data/benchmark/core/core-batch-006.jsonl`, and focused-test
transition. This is the second approved abstain pair (after `kv-core-abstain-01`) and the first
approved pair whose fail-closed basis is a rights boundary rather than the availability ledger.
At that approval checkpoint, the focused benchmark suite passed 45 tests and the full baseline
passed 1,153 tests across 75 formatted Python files. Later on 2026-08-26, feature commit `77d247d`
added only the draft Korean/English `kv-core-abstain-03` pair and six focused tests. The
abstention pair (`train` split) binds no document or data units, carries no tool expectations and
no reference answer, and rests on the false premise that the many archived OECD editions of
Korea's consumer price index prove the Korean CPI was revised just as many times; both questions
ask for before-and-after November 2019 CPI values using only the vintage available as of
2026-07-17. The gold behavior is to reject the premise and abstain: archived edition counts
measure archive coverage, not actual revisions, and KOR-RTD holds no owner-approved raw-data
decision for the OECD Korea CPI revision series — raw OECD observations outside the sole approved
Korea monthly amplitude-adjusted CLI scope (`KOR.M.LI_AA.IX._T`) remain metadata-only — so each
record carries only a language-matched abstention reason, and the system must not fabricate
revision values or expose an unapproved observation. On 2026-08-26, Hyungbae Cho approved both
records without a substantive change; feature commit `5e14119` records the named-review metadata,
`batch-007` lifecycle tag, move to `data/benchmark/core/core-batch-007.jsonl`, and focused-test
transition. This is the third approved abstain pair (after the availability-frontier
`kv-core-abstain-01` and the unapproved-neighboring-scope `kv-core-abstain-02`) and the first
approved false-premise rejection pair. At that approval checkpoint, the focused benchmark suite
passed 51 tests and the full baseline passed 1,159 tests across 76 formatted Python files. Later
on 2026-08-26, feature commit `fd7640b` added only the draft Korean/English `kv-core-abstain-04`
pair and six focused tests. The abstention pair (`dev` split) binds no document or data units,
carries no tool expectations and no reference answer; both questions ask for Korea's OECD
amplitude-adjusted CLI value for May 2026 using the vintage available at the time while omitting
the as-of date the vintage request depends on, and the record-level `as_of` field is 2026-07-17.
The gold behavior is to ask for the missing as-of and abstain: a vintage answer depends on its
as-of cutoff, and KOR-RTD's fail-closed contract never executes without an explicit
`effective_as_of` and never guesses or defaults the cutoff, because an assumed cutoff can expose
the wrong vintage and create temporal leakage — so each record carries only a language-matched
abstention reason. A focused contrast test shows the same request resolves once an explicit
cutoff of 2026-07-09 is supplied (edition `202607`, value `102.66` from the owner-approved CLI
scope), so the drafted abstention is missing-cutoff driven, not availability- or rights-driven.
On 2026-08-27, Hyungbae Cho approved both records without a substantive change; feature commit
`dfcd191` records the named-review metadata, `batch-008` lifecycle tag, move to
`data/benchmark/core/core-batch-008.jsonl`, and focused-test transition. This is the fourth
approved abstain pair (the availability-frontier `kv-core-abstain-01`, the
unapproved-neighboring-scope `kv-core-abstain-02`, the false-premise-rejection
`kv-core-abstain-03`, and now this missing-as-of clarification pair) and the first approved
dev-split abstain pair. The approved count is now 18/40, and current validation is 57 focused
benchmark tests and 1,165 full-suite tests across 77 formatted Python files. The exact next
outcome is an owner-directed draft-only authoring slice for the frozen `kv-core-abstain-05`
pair — an abstention pair (`test` split) whose question asks for Korea's OECD amplitude-adjusted
CLI value for May 2026 as of August 15, 2026, a cutoff later than the committed
edition-availability ledger's completeness frontier (`complete_through`, the 2026-07-17 capture
instant), so the gold behavior is abstention with `cutoff_beyond_complete_through` because past
the frontier the ledger cannot certify which editions had become available. The pair binds no
source units and is fully offline; it is the last matrix slot authorable without a new capture
or an owner decision, and the new drafts must remain `annotation.status=draft` pending a
separate named human review.
Charter v2.5 and
[ADR 0009](docs/decisions/0009-bok-economic-outlook-public-data-rights.md) additionally record the
owner-approved `allowed` public-data ruling for official Bank of Korea Economic Outlook
publications, subject to attribution, transformation disclosure, and separately marked
third-party rights; see
[project status](docs/PROJECT_STATUS.md) for the continuation order.

The QLoRA spike's free checkpoint/fixture preflight and isolated paid-GPU one-step harness live in
[`experiments/qlora/`](experiments/qlora/README.md). Both the preflight and one-step compatibility
run pass. This proves the selected training path can load, update, and save an adapter; it is not a
benchmark training or model-quality result.

## Quick start

Requires Python 3.12.

### Windows PowerShell

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python scripts/export_execution_replay_traces.py --check
python -m ruff check .
python -m ruff format --check .
python -m pytest
```

### macOS or Linux

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python scripts/export_execution_replay_traces.py --check
python -m ruff check .
python -m ruff format --check .
python -m pytest
```

Copy `.env.example` to `.env` only when an API-backed experiment is approved. Offline checks and
the OECD constraint-metadata capture do not require an API key. `ECOS_API_KEY` activates only the
two exact ECOS series authorized by the committed rights catalog; `KOSIS_API_KEY` activates only
the national total-CPI scope. A missing key is an explicit skip. Local `.env` values are ignored by
Git; the two Actions secrets were separately registered on 2026-07-17 and cannot be used to rebuild
a local `.env` on another machine.

## Documentation

- [Approved project charter (v2.5)](docs/project/01_project_charter.md)
- [Concept upgrade proposal (v2 rationale)](docs/discovery/01_concept_upgrade_proposal.md)
- [Evidence schema contract (1.0, superseded)](docs/project/02_evidence_schema_contract.md)
- [Source-rights catalog contract](docs/project/03_rights_catalog_contract.md)
- [Evidence contract 2.0.0 and availability-ledger migration](docs/project/05_evidence_contract_2_0_migration.md)
- [Number-normalization specification 1.0.0](docs/project/06_number_normalization_spec.md)
- [Private offline-executor contract](docs/project/16_offline_executor_contract.md)
- [Committed replay traces and regeneration policy](traces/README.md)
- [Cross-machine continuation handoff](docs/project/04_macbook_handoff.md)
- [Current status and handoff](docs/PROJECT_STATUS.md)
- [Week-1 verification log](docs/discovery/03_week1_verification_log.md)
- [Role-gap and project-selection analysis](docs/discovery/00_role_gap_analysis.md)
- [Milestone-gated CV bullets](docs/application/00_cv_bullets.md)
- [Application-ready project descriptions](docs/application/01_project_description.md)
- [Architecture decisions](docs/decisions/README.md)
- [Contributor rules](AGENTS.md)

## Responsible disclosure

This project is conducted in a personal capacity and is not affiliated with the Bank of Korea. It is an independent open-source project using public information, and it is not affiliated with or endorsed by the OECD or Mistral AI either. Source redistribution and model/data licenses will be documented before artifacts are published.

## License

Original project code and documentation are licensed under Apache-2.0 unless noted otherwise; see
[LICENSE](LICENSE). Third-party source data and redistributed observations are not relicensed under
Apache-2.0. They remain subject to the originating provider's terms and attribution requirements
recorded in their manifests and rights decisions. Benchmark, model, and generated-data artifacts
will state their own licences when published; see the
[data licensing boundary](data/README.md#licensing-boundary).
