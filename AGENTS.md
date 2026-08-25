# SovereignLab agent guide

This file applies to the entire repository. It is the onboarding contract for human contributors and AI agents.

## Mission

Build **KOR-RTD**, a provenance-contracted point-in-time (vintage) data layer for Korean macroeconomic statistics, and **K-VINTAGE**, a bilingual Korean/English benchmark whose gold answers depend on the data vintage available at each question's `as_of` date — with the SovereignLab briefing pipeline as the reference implementation and public baseline suite. Preserve evaluation-first rigor without overstating results: techniques (fine-tuning, RAG, deterministic tools) are means, not the mission, and temporal-leakage rate is the headline metric.

## Current handoff checkpoint

This repository is between work units and is ready to continue on the Windows workstation.

- Current milestone: **M2 — benchmark and baselines**.
- Approved human-reviewed core: **12/40** records. The frozen 40-record matrix must not be edited
  merely to accelerate authoring.
- The Korean/English `kv-core-data-02` pair is approved in
  `data/benchmark/core/core-batch-003.jsonl`. Hyungbae Cho approved both records on 2026-08-20;
  their review timestamp is `2026-08-20T00:24:18Z`.
- The Korean/English `kv-core-data-03` pair is approved in
  `data/benchmark/core/core-batch-004.jsonl`. Hyungbae Cho approved both records on 2026-08-21;
  their review timestamp is `2026-08-21T07:14:13Z`.
- The Korean/English `kv-core-data-04` pair is approved in
  `data/benchmark/core/core-batch-005.jsonl`. Hyungbae Cho approved both records on 2026-08-25;
  their review timestamp is `2026-08-25T07:10:15Z`. No draft review candidate remains. This
  approval completes the data route's four authorable pairs (`kv-core-data-01`..`kv-core-data-04`);
  the fifth data pair `kv-core-data-05` stays reserved on the deliberately unauthored test-split
  unit.
- Completed: fail-closed vintage resolver, weekly append-only harvester, approved ECOS/KOSIS/OECD
  captures, number normalization, offline bilingual temporal retrieval, strict Korean/English Bank
  of Korea May-2026 Outlook manifests, the approved `kv-core-doc-01` documentary pair, and strict
  execution/trace contract 1.0.0 with 13 deterministic public schemas. The trusted latest-only
  snapshot registry, deterministic `read_snapshot_as_of` adapter, trusted synthetic retrieval
  registry, typed `retrieve_temporal_documents` adapter, trusted historical STES registry, and
  flat `resolve_stes_as_of` adapter are also complete. The snapshot boundary revalidates exact
  bytes and rebuilt models at call time; the frozen three-tool callable registry, explicit
  dispatcher, offline one-shot scripted/recorded/replay planner, internal deterministic
  evidence-packet assembler, private offline executor, and five committed machine-readable
  real-digest replay traces are complete as the first nine ADR 0008 slices and work unit C. The
  traces were generated through the real private executor, `ScriptedPlanner`, callable and artifact
  registries, and retrieval corpus; they cover all four routes, all three tools, Korean and English,
  explicit and implicit cutoffs, complete execution, planned abstention, and terminal tool
  abstention. They stop at the first terminal result and expose no partial evidence. The source
  package and 13 public schemas remain unchanged.
  The completed 2026-08-11 replay-trace feature commit is `883815b`; the source descriptor pins 32
  entries and executor digest
  `08f45dab6a36a49cb7d0b588a69236942cd61534540bd4de0772010402dada64`.
- The 2026-08-19 draft-pair feature commit is `f2d2523`. It adds exactly the two draft records and
  their focused tests; the frozen matrix, source bundle, rights decisions, public schemas, and
  source package are unchanged.
- The 2026-08-20 approval feature commit is `473a733`. It records only the named review decision,
  approval metadata, lifecycle tag, file move into `core/`, and focused-test transition; the
  record substance, frozen matrix, source bundle, rights decisions, public schemas, source
  package, and execution runtime are unchanged.
- The 2026-08-20 current-account draft feature commit is `50c4d9c`. It adds exactly
  `kv-core-data-03-ko` and `kv-core-data-03-en` plus six focused tests, using only the existing
  `ecos-301y017-snapshot-20260717` evidence whose use in KOR-RTD is owner-approved. The frozen
  matrix, approved core, source bundle, rights decisions, public schemas, traces, source package,
  and execution runtime are unchanged.
- The 2026-08-21 approval feature commit is `db6700e`. It records only the named review decision,
  approval metadata, lifecycle tag, file move into `core/`, and focused-test transition; the
  record substance, frozen matrix, source bundle, rights decisions, public schemas, source
  package, and execution runtime are unchanged.
- The 2026-08-21 KOSIS CPI draft feature commit is `5e0da06`. It adds exactly
  `kv-core-data-04-ko` and `kv-core-data-04-en` plus six focused tests, using only the existing
  `kosis-cpi-snapshot-20260717` evidence whose use in KOR-RTD is owner-approved (ADR 0007). The
  frozen matrix, approved core, source bundle, rights decisions, public schemas, traces, source
  package, and execution runtime are unchanged.
- The 2026-08-25 approval feature commit is `95c5e61`. It records only the named review decision,
  approval metadata, lifecycle tag, file move into `core/`, and focused-test transition; the
  record substance, frozen matrix, source bundle, rights decisions, public schemas, source
  package, and execution runtime are unchanged.
- Exact next outcome: an owner-directed draft-only Korean/English `kv-core-abstain-02` pair
  (train-split abstention) whose question asks for a neighboring OECD observation scope (Korea's
  normalised CLI) with no owner-approved raw-data decision, so the gold behavior is abstention.
  Abstain pairs bind no source units; the slice uses no new evidence, only the committed rights
  catalog as the fail-closed basis.
- Exact next reviewable slice: the two draft records only. Human approval is a later separate
  gate, so the approved core count remains 12/40.
- Not implemented yet: a provider or live-model integration or the bounded tool loop. The five
  committed traces are deterministic offline replay artifacts, not provider recordings.
- The planner boundary exists under `src/sovereignlab/execution/planner.py`; its recording registry
  and entry format remain intentionally private. The assembler exists under
  `src/sovereignlab/execution/assembler.py`; its function and error boundary remain internal and
  are not package-level public exports. The executor exists under
  `src/sovereignlab/execution/executor.py`; its function and error boundary are likewise private.
  No committed provider recording path exists under `data/`.
- The bounded tool loop is not part of this milestone; ADR 0008 defers it to v1.1.

The authoritative live checkpoint and acceptance criteria are in
`docs/project/04_macbook_handoff.md`. The filename is retained for history, but the document is now
the cross-machine Windows continuation handoff.

## Exact next slice — draft `kv-core-abstain-02` Korean/English pair only

The Korean/English pair assigned to `kv-core-data-04` in the frozen core-authoring matrix was
drafted on 2026-08-21 and approved by Hyungbae Cho on 2026-08-25. It now lives in
`data/benchmark/core/core-batch-005.jsonl`. The approved core count is 12/40; the other 28 slots
are unauthored and unapproved. The owner-directed next reviewable outcome is only the draft
Korean/English pair assigned to `kv-core-abstain-02` (train-split abstention) in the frozen
matrix. Its question asks for a neighboring OECD observation scope (Korea's normalised CLI) that
has no owner-approved raw-data decision, so the gold behavior is abstention. Abstain pairs bind
no source units, so the slice uses no new evidence — only the committed rights catalog as the
fail-closed basis.

- Preserve the frozen matrix row, route, split, evidence group, data-unit binding, and record IDs;
  do not edit the matrix to make authoring easier.
- Bind no source unit and add no evidence. The abstention rationale rests only on the committed
  rights catalog as the fail-closed basis; do not add, refresh, or re-fetch a source.
- Author exactly the two draft records and their focused tests. Keep them at
  `annotation.status=draft` and do not raise the approved count above 12/40; named human review
  remains a separate later action.
- Stop after the draft pair and a green full baseline. Do not add probes, alter the matrix, source,
  rights decisions, or public schemas, add a provider or live-model call, start the deferred
  bounded loop, or initiate a paid operation.

## New-session onboarding procedure

Before editing:

1. From the repository root, run `git status --short --branch` **before** any switch or pull. If
   the worktree is dirty, preserve the changes and investigate; do not switch, pull, reset, or
   overwrite. Only from a clean worktree, switch to `main`, fast-forward from `origin`, and confirm
   the worktree is still clean and aligned.
2. Read the authority files below in order. Do not rely on a prior chat transcript.
3. Create or verify the machine-local Python 3.12 environment and run the full offline baseline
   under "Local setup and required checks."
4. State back four facts before implementation: current milestone, approved core count, exact next
   work unit, and hard stops.
5. Start only with the draft `kv-core-abstain-02` Korean/English pair, which binds no source unit
   and uses only the committed rights catalog as the fail-closed basis. Do not combine source
   expansion, human approval, probe generation, a provider or live-model call, or a paid
   operation with onboarding.

## Read before changing anything

1. `docs/project/01_project_charter.md` — approved product and evaluation contract (v2.5).
2. `docs/PROJECT_STATUS.md` — current milestone, completed work, next action, blockers, and validation evidence.
3. `docs/decisions/` — accepted architecture and process decisions (ADR 0003 records the v2
   reorientation; ADR 0004 records the v2.1 source-rights amendment; ADR 0005 records the v2.2
   fail-closed edition-availability contract; ADR 0006 records the owner's employer-risk review;
   ADR 0007 records the v2.3 exact KOSIS CPI and OECD CLI rights amendment; ADR 0008 records the
   v2.4 typed function-calling execution contract and the v1.1 deferral of the bounded tool
   loop; ADR 0009 records the v2.5 Bank of Korea Economic Outlook public-data rights amendment).
4. `docs/project/04_macbook_handoff.md` — cross-machine Windows setup, exact continuation order,
   and next-unit acceptance criteria (legacy filename; skip files it lists that you already read
   this session).
5. `docs/discovery/01_concept_upgrade_proposal.md` — background rationale for v2: verified data facts, judged alternatives, risk register.
6. `docs/project/05_evidence_contract_2_0_migration.md` — implemented evidence/rights contract
   that the execution path must not change.
7. `docs/project/07_core_authoring_matrix.md` — approved 40-record allocation, 12/40 review state,
   and frozen human-review boundary.
8. `docs/project/08_temporal_document_retrieval.md` — implemented cutoff-before-scoring retrieval
   contract.
9. `docs/project/09_typed_execution_trace_contract.md` — frozen execution surface, flat tool
   arguments, replay provenance, and trace invariants.
10. `docs/project/10_snapshot_reader_contract.md` — trusted latest-only registry, cutoff selection,
   provider parsers, and failure taxonomy.
11. `docs/project/11_temporal_retrieval_adapter_contract.md` — trusted synthetic corpus, typed
   adapter, replay digest, and failure taxonomy.
12. `docs/project/12_stes_adapter_contract.md` — trusted historical registry, ledger/rights/archive
   joins and flat typed adapter.
13. `docs/project/13_callable_dispatcher_contract.md` — frozen three-tool registry, explicit
    dispatcher, composite replay provenance, and snapshot call-time hardening.
14. `docs/project/14_offline_planner_contract.md` — implemented planner protocol, private exact-byte
    recording boundary, request binding, and deterministic replay.
15. `docs/project/15_evidence_packet_assembler_contract.md` — implemented private assembler,
    ordered-result binding, abstention semantics, and no-partial-evidence boundary.
16. `docs/project/16_offline_executor_contract.md` — implemented private executor, one-shot state
    machine, sanitized failure mapping, real source-tree provenance, and validation evidence.
17. `traces/README.md` — committed replay-artifact policy, deterministic regeneration command, and
    the boundary between public replay artifacts and private recordings.
18. The closest additional `AGENTS.md`, if a subdirectory adds one later.

For the current post-review checkpoint, also read `data/benchmark/core-authoring-matrix-v1.json`,
`data/benchmark/README.md`, the approved records in
`data/benchmark/core/core-batch-001.jsonl`, `core-batch-002.jsonl`, `core-batch-003.jsonl`,
`core-batch-004.jsonl`, and `core-batch-005.jsonl`, the benchmark model and normalization code in
`src/sovereignlab/schemas/benchmark.py` and `src/sovereignlab/normalization.py`, and
`tests/benchmark/test_core_batch.py`, `test_bok_outlook_core.py`,
`test_ecos_gdp_core.py`, `test_ecos_current_account_core.py`, and `test_kosis_cpi_core.py`. Treat
the matrix allocation, approved records, source bundle, and human-review boundary as frozen.

The charter is the scope authority. Do not expand sources, agents, UI, or infrastructure before the current milestone gate passes.

## Working protocol

- Work in small, reviewable units with one stated outcome.
- Update `docs/PROJECT_STATUS.md` whenever a milestone state, blocker, cost, or next action changes.
- Record consequential technical choices as an ADR in `docs/decisions/`.
- Add or update tests in the same change as behavior.
- Run the relevant offline checks before committing and record the commands in the status document.
- Use conventional commit prefixes: `docs:`, `chore:`, `feat:`, `fix:`, `test:`, `refactor:`, `eval:`.
- After green checks, commit in semantic units, push the current branch to `origin`, and confirm
  the local/remote commit IDs match and the worktree is clean.
- Do not rewrite or discard unrelated user changes.

## Evidence and evaluation rules

- Freeze evaluation schemas and evidence-disjoint splits before model optimization.
- Keep Korean and English results separately reportable.
- Never let an `as_of` evidence packet include a source published after its cutoff — nor a data vintage/edition that did not exist at the cutoff.
- Harvester outputs are append-only: never rewrite, backdate, or backfill a committed snapshot; public commit history is the proof of capture dates.
- Never commit raw ECOS/KOSIS observations unless the exact series has an owner-approved
  source-specific classification and attribution ruling. Bank of Korea-produced ECOS statistics
  and in-scope KOSIS domestic macro statistics may be `allowed` under their official use guides;
  other-producer ECOS raw redistribution fails closed without an express producer-specific basis.
  KOSIS international/North Korea statistics are not redistributed, and publications follow their
  individual KOGL notices.
- Raw OECD observations remain metadata-only except the exact owner-approved, OECD-produced Korea
  monthly amplitude-adjusted CLI revision scope in ADR 0007. That exception does not authorize any
  neighboring measure, geography, dataflow, or third-party component.
- Official Bank of Korea-produced Economic Outlook reports and their official English full
  translations are `allowed` public data under the owner-approved family ruling in ADR 0009 and
  the Bank of Korea copyright policy's Public Data Act Article 19 branch. Attribute the Bank of
  Korea, disclose modification/processing/transformation, and honor separately marked third-party
  rights. Do not fabricate a KOGL type. Permission does not require automatic full-document
  ingestion.
- `SourceManifest` 2.0.0 requires a typed rights-decision link on every `allowed` data snapshot,
  and bundle validation cross-checks it against the committed rights catalog. No raw observation
  may be committed unless that link validates and the referenced decision is owner-approved
  `allowed`.
- Treat the project and its public data artifacts as non-commercial. Any future commercial-use path
  requires an owner review and a superseding rights decision before collection or publication.
- Report the two gold-set tiers separately (40 human-reviewed core vs machine-generated probes); never merge them into one count.
- Qualify every "first" claim: "to our knowledge" + "for official statistics" + cite prior art (arXiv 2605.23497, Dallas Fed real-time OECD dataset, OECD MEI revisions database). Never claim "first Korean macro benchmark."
- Do not claim OECD edition/backfill ranges beyond what a recorded verification spike confirmed.
- When mentioning Korea's AI Basic Act, describe it precisely: it regulates "high-impact" (고영향) AI under a voluntary verification/certification regime — not "high-risk" AI with mandatory testing.
- Frame the project as complementing public statistical infrastructure; never as exposing defects in official APIs.
- Treat LLM judges as secondary diagnostics until calibrated against human review.
- Describe the MVP briefing path as "typed function calling with committed traces" only, and only
  after the minimal path ships. Do not use "agent", "agentic", "multi-step", "orchestration", or
  "autonomous" in public-facing descriptions of in-window artifacts (README, CV, datasheets,
  release notes, commit messages); the bounded tool loop is deferred to v1.1 (ADR 0008). Naming
  the deferred loop in planning and decision documents is permitted.
- Derive every CV number and README performance claim from committed artifacts and a reproducible command.
- Preserve negative results and failure taxonomies.
- Fine-tuning must target measurable behavior; changing facts belong in retrieval or deterministic tools.

## Data, security, and cost

- Use public sources only. Never add confidential Bank of Korea or applicant data.
- Repository Apache-2.0 terms cover original project code and documentation unless noted; they do
  not relicense source observations, which retain their recorded provider terms and attribution.
- Do not commit downloaded source documents until redistribution rights are documented.
- Never commit API keys, tokens, `.env`, credentials, private traces, or model weights.
- Paid API, OCR, embedding, or GPU operations require a smoke test and an entry in the project status/cost record.
- The approved initial external-spend ceiling is USD 100. Do not exceed it without Hyungbae's review.
- Do not imply endorsement by the Bank of Korea, OECD, Mistral, or any other institution.

## Local setup and required checks

Development happens on multiple machines; `.venv` is machine-local and must be recreated on each. Nothing in the repository may depend on machine-specific paths.

Windows PowerShell:

```powershell
git status --short --branch
git switch main
git pull --ff-only origin main
git status --short --branch

$python312 = (Get-Command python -CommandType Application -ErrorAction Stop).Source
& $python312 -c "import sys; assert sys.version_info[:2] == (3, 12), sys.version"
if (-not (Test-Path .\.venv\Scripts\python.exe)) {
    & $python312 -m venv .venv
}
$venvPython = (Resolve-Path .\.venv\Scripts\python.exe).Path
& $venvPython -c "import sys; assert sys.version_info[:2] == (3, 12), sys.version"
& $venvPython -m pip install -r requirements.txt
& $venvPython scripts/export_json_schemas.py
& $venvPython -m ruff check --no-cache .
& $venvPython -m ruff format --check .
& $venvPython -m pytest --cov=sovereignlab --cov-branch --cov-report=term-missing -p no:cacheprovider
git diff --exit-code
```

macOS or Linux:

```bash
git status --short --branch
git switch main
git pull --ff-only origin main
git status --short --branch
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python scripts/export_json_schemas.py
python -m ruff check --no-cache .
python -m ruff format --check .
python -m pytest --cov=sovereignlab --cov-branch --cov-report=term-missing -p no:cacheprovider
git diff --exit-code
```

The Windows user-level launcher has been unreliable. If `Get-Command python` does not resolve a
working Python 3.12 runtime, use `where.exe python` or the workstation's installed-app inventory,
then set `$python312` to the verified executable's full path for the current shell only. Never
commit that machine-specific path. Do not reuse a `.venv` whose interpreter check fails.
The Windows requirements include a `win32`-only `tzdata` pin because a standard Windows Python
installation has no system IANA timezone database.

The 2026-08-25 handoff baseline is 13 deterministic public schemas, 74 formatted Python files,
1,147 passing tests, and 100% SovereignLab statement/branch coverage (4,679 statements, 1,568
branches). The focused benchmark acceptance run is 39 passing tests. A different result is a
diagnostic signal: stop before implementation and record the discrepancy in
`docs/PROJECT_STATUS.md`.

## Repository map

- `src/sovereignlab/` — importable application and evaluation code.
- `src/sovereignlab/snapshots/` — trusted latest-only registry and deterministic ECOS/KOSIS reader.
- `src/sovereignlab/retrieval/` — cutoff-safe lexical retrieval, trusted synthetic corpus, and
  typed document adapter.
- `src/sovereignlab/execution/` — frozen three-tool callable registry, explicit deterministic
  dispatcher, offline one-shot planner boundary, private deterministic evidence-packet assembler,
  and private offline executor. The source package remains unchanged by the completed ninth ADR
  0008 slice.
- `scripts/export_execution_replay_traces.py` — fixed-scenario deterministic writer/checker for the
  committed real-digest replay set.
- `traces/` — public machine-readable replay artifacts and their publication/privacy policy. The
  five v1 traces cover all routes and tools plus complete, planned-abstention, and terminal
  tool-abstention outcomes without exposing private planner recordings.
- `tests/` — offline tests; network calls must be mocked or replayed unless explicitly marked.
- `data/` — public benchmark and metadata policy; ignored raw/interim material. The KOR-RTD archive layer (edition consolidations, harvester snapshots, manifests) lives here.
- `artifacts/` — generated outputs policy; generated content is ignored by default.
- `docs/project/` — charter and customer-facing scope.
- `docs/discovery/` — role-gap and project-selection research.
- `docs/application/` — milestone-gated CV/application language.
- `docs/decisions/` — architecture decision records.
