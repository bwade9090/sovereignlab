# SovereignLab agent guide

This file applies to the entire repository. It is the onboarding contract for human contributors and AI agents.

## Mission

Build **KOR-RTD**, a provenance-contracted point-in-time (vintage) data layer for Korean macroeconomic statistics, and **K-VINTAGE**, a bilingual Korean/English benchmark whose gold answers depend on the data vintage available at each question's `as_of` date — with the SovereignLab briefing pipeline as the reference implementation and public baseline suite. Preserve evaluation-first rigor without overstating results: techniques (fine-tuning, RAG, deterministic tools) are means, not the mission, and temporal-leakage rate is the headline metric.

## Current handoff checkpoint

This repository is between work units and is ready to continue on the Windows workstation.

- Current milestone: **M2 — benchmark and baselines**.
- Approved human-reviewed core: **6/40** records. The frozen 40-record matrix must not be edited
  merely to accelerate authoring.
- Completed: fail-closed vintage resolver, weekly append-only harvester, approved ECOS/KOSIS/OECD
  captures, number normalization, offline bilingual temporal retrieval, strict Korean/English Bank
  of Korea May-2026 Outlook manifests, the approved `kv-core-doc-01` documentary pair, and strict
  execution/trace contract 1.0.0 with 13 deterministic public schemas. The trusted latest-only
  snapshot registry, deterministic `read_snapshot_as_of` adapter, trusted synthetic retrieval
  registry, typed `retrieve_temporal_documents` adapter, trusted historical STES registry, and
  flat `resolve_stes_as_of` adapter are also complete. The snapshot boundary now revalidates exact
  bytes and rebuilt models at call time, and the frozen three-tool callable registry plus explicit
  dispatcher are complete. The offline one-shot planner protocol and its scripted and immutable
  recorded/replay implementations are complete as well.
- Exact next outcome: the minimal offline **typed function-calling question-to-evidence-packet
  path** required by ADR 0008, with committed machine-readable traces.
- Exact next reviewable slice: the deterministic evidence-packet assembler only.
- Not implemented yet: the packet assembler, offline end-to-end executor, committed end-to-end
  replay traces, or live model integration. The contract fixture is not an end-to-end replay
  result.
- The planner boundary now exists under `src/sovereignlab/execution/planner.py`; its recording
  registry and entry format are intentionally private and no committed provider recording path
  exists under `data/` yet.
- The bounded tool loop is not part of this milestone; ADR 0008 defers it to v1.1.

The authoritative live checkpoint and acceptance criteria are in
`docs/project/04_macbook_handoff.md`. The filename is retained for history, but the document is now
the cross-machine Windows continuation handoff.

## Exact next slice — evidence-packet assembler only

The next reviewable outcome is an entirely offline deterministic assembler. Keep it separate from
tool dispatch, route coordination, trace construction, and later execution work.

- Consume only an already validated `ExecutionRequest`, its validated `RoutePlan` 1.0.0, and the
  ordered typed results produced elsewhere. Produce only the already frozen
  `ExecutionEvidencePacket` 1.0.0; do not invent a new public assembler or execution wrapper.
- Preserve the plan's four route meanings, result order, typed payloads, cutoff bindings, and
  fail-closed behavior. Planned abstention must reproduce the plan reason. A tool abstention must
  produce an empty packet bound to the terminal result's call ID and reason. Complete packets must
  expose exactly the evidence from complete successful results, with no partial-evidence leakage.
- Reject request/plan/result drift, a non-prefix or reordered result sequence, mismatched call IDs
  or tools, post-cutoff evidence, incomplete success, tool errors presented as packet evidence,
  and any assembled payload that does not round-trip through the existing strict model.
- The exact internal function name and private error wrapper are not frozen. Keep them private or
  record a focused specification if the choice becomes consequential; reuse the existing public
  packet schema and invariants in `src/sovereignlab/schemas/execution.py`.
- Stop after the assembler slice and a green full baseline. Do not call the planner or dispatcher,
  coordinate route execution, create the offline executor or end-to-end traces, add a live model
  call, change sources/benchmark records/public schemas, or start the deferred bounded loop.

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
5. Start with one reviewable implementation slice inside the ADR 0008 unit. Do not combine source
   expansion, new benchmark authoring, a live model call, or a paid operation with onboarding.

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
7. `docs/project/07_core_authoring_matrix.md` — approved 40-record allocation, 6/40 review state,
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
    recording boundary, request binding, deterministic replay, and next assembler boundary.
15. The closest additional `AGENTS.md`, if a subdirectory adds one later.

For the exact assembler slice, also read `src/sovereignlab/schemas/execution.py`,
`tests/schemas/test_execution.py`, `src/sovereignlab/execution/planner.py`, and
`tests/execution/test_planner.py`. The first pair contains the packet/result/trace invariants to
reuse; the second pair is the completed planner boundary that this slice must not invoke.

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

The handoff baseline is 13 deterministic public schemas, 65 formatted Python files, 1,007 passing
tests, and 100% SovereignLab statement/branch coverage (4,238 statements, 1,414 branches). A
different result is a diagnostic signal: stop before implementation and record the discrepancy
in `docs/PROJECT_STATUS.md`.

## Repository map

- `src/sovereignlab/` — importable application and evaluation code.
- `src/sovereignlab/snapshots/` — trusted latest-only registry and deterministic ECOS/KOSIS reader.
- `src/sovereignlab/retrieval/` — cutoff-safe lexical retrieval, trusted synthetic corpus, and
  typed document adapter.
- `src/sovereignlab/execution/` — frozen three-tool callable registry, explicit deterministic
  dispatcher, and offline one-shot planner boundary. Packet assembly and route execution do not
  exist yet.
- `tests/` — offline tests; network calls must be mocked or replayed unless explicitly marked.
- `data/` — public benchmark and metadata policy; ignored raw/interim material. The KOR-RTD archive layer (edition consolidations, harvester snapshots, manifests) lives here.
- `artifacts/` — generated outputs policy; generated content is ignored by default.
- `docs/project/` — charter and customer-facing scope.
- `docs/discovery/` — role-gap and project-selection research.
- `docs/application/` — milestone-gated CV/application language.
- `docs/decisions/` — architecture decision records.
