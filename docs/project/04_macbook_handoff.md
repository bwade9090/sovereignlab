# Continuation handoff

- Prepared: 2026-07-16; refreshed 2026-07-28 for a clean new-agent session (second refresh the
  same day: ADR 0008 / charter v2.4 execution-contract adjustment, documentation only)
- Authority: charter v2.4; accepted ADRs 0001–0008
- Branch to continue: `main` from `origin`
- Current milestone: M2
- Session state: closed; no implementation is intentionally left in progress
- Last functional baseline: `a92c44d` (`feat: add temporal document retrieval`)

## 0. Start here

The repository is the source of truth; do not rely on a prior chat transcript. At the beginning of
the new session:

1. Fetch and fast-forward `main`, then confirm `git status --short --branch` is clean and aligned
   with `origin/main`.
2. Read the files in section 3 in order, in full.
3. Run the baseline commands in section 2 before changing files.
4. State back the current milestone, approved core count, exact next work unit, and hard stops.
5. Start only section 5 work unit A. Do not redo the completed retrieval baseline or broaden scope.

If the worktree is dirty, preserve the existing changes and determine their owner before editing.
If local `main` has diverged from `origin/main`, stop rather than rewriting history.

## 1. What is complete

- The charter v2–v2.3 amendments and ADRs 0003–0007 recorded the K-VINTAGE/KOR-RTD direction,
  source-rights policy, and fail-closed edition-availability contract (all carried forward into
  the current charter v2.4).
- ADR 0006 (2026-07-17) commits the owner-authored employer-risk review: proceed unchanged, a
  single English personal-capacity disclaimer in the README, no Git-history rewrite. All week-1
  owner decisions are closed.
- The ADR 0005 contract unit is implemented
  (`docs/project/05_evidence_contract_2_0_migration.md`): `EditionAvailabilityLedger` 1.0.0 with
  fail-closed edition selection, `SourceManifest`/`BenchmarkRecord`/`BenchmarkBundle` 2.0.0, and
  the typed manifest-to-rights-decision link with bundle cross-validation (including catalog/ledger
  supersession and instant-based expiry). A 23-agent adversarial review's seven confirmed findings
  were fixed before commit.
- The offline STES as-of resolver is implemented under `src/sovereignlab/vintage/`: exact
  case-sensitive code-header parsing, manifest size/hash verification, canonical manifest URL to
  ledger dataflow/version joining, ledger-first fail-closed selection, and selected-row-only output.
  The official GDP and CPI verification responses were re-read through temporary files and matched
  the recorded hashes/examples; no response body was committed. The check also corrected the
  ledger's `constraint_id` pattern so real OECD IDs containing `@` validate.
- RightsCatalog 1.0 now has an append-only two-catalog chain. The current catalog preserves the two
  ECOS decisions and adds only KOSIS national CPI `101/DT_1J22003/T/T10` and OECD Korea monthly
  amplitude-adjusted CLI `KOR.M.LI_AA.IX._T`, per ADR 0007. Other OECD observations remain
  `metadata_only`.
- The weekly append-only harvester and GitHub Actions schedule are implemented. The first real
  key-free OECD constraint capture and manifest-backed ledger contain no observations; `202607` is
  resolved at the official constraint `validFrom`, while the other 329 mechanically inventoried
  editions remain unresolved. A later local run captured the two exact ECOS series and exact KOSIS
  CPI scope; the separate one-time CLI capture stored 75,060 rows across 239 editions. Local keys
  remain ignored and are absent from publishable files. Repository `ECOS_API_KEY` and
  `KOSIS_API_KEY` Actions secrets were registered on 2026-07-17 without exposing their values; the
  first manually dispatched secret-backed workflow run remains an optional separately authorized
  check.
- Number-normalization 1.0.0 is frozen in `docs/project/06_number_normalization_spec.md` and
  `sovereignlab.normalization`: exact Decimal rules cover the two ECOS scopes, KOSIS CPI, OECD CLI,
  and the verified OECD GDP XDC-to-billion-KRW transform; Korean unit conversion, presentation
  rounding, tolerance, and variant fail-closed behavior are tested.
- `experiments/qlora/` contains the pinned Ministral 3 BF16/NF4 one-step compatibility harness. Its
  zero-cost public-Hub preflight and paid RunPod A40/CUDA 13 step pass: one optimizer step, loss
  `5.192200660705566`, 4,210,338,304 peak CUDA bytes, and adapter-only output. All disposable Pods
  and remote artifacts were deleted. Finalized external spend is USD `0.23584524099715054`; this is
  a training-path compatibility result, not a model-quality claim.
- The 40-record human-reviewed-core allocation is frozen as 20 bilingual pairs in
  `data/benchmark/core-authoring-matrix-v1.json`. Hyungbae Cho approved the unchanged allocation and
  the first four initially AI-authored records on 2026-07-25. They live under
  `data/benchmark/core/` with named reviewer metadata; real committed evidence reproduces the
  `202607` CLI answer and the pre-July abstention. The approved core count is 4/40.
- The offline bilingual temporal document retriever is implemented under
  `src/sovereignlab/retrieval/`. It validates chunk-to-manifest language/hash linkage, removes
  post-`as_of` and other-language documents before computing corpus statistics or scores, and
  returns manifest-bound locators. Synthetic Korean/English fixtures prove future passages cannot
  change eligible results or scores. No official document body or paid embedding was used.
- **Execution-contract adjustment (2026-07-28, ADR 0008 / charter v2.4, documentation only):**
  after a four-lens review with adversarial verification, the owner approved implementing the
  minimal question-to-evidence-packet path as a typed function-calling artifact (model-emitted
  typed plan and tool calls against pydantic-derived schemas, deterministic execution, committed
  traces, recorded/replayable model interface) with a three-tool surface — temporal retrieval,
  the as-of resolver behind the frozen flat gold-argument convention via an adapter, and a new
  deterministic latest-only snapshot-read tool. The bounded multi-step tool loop is deferred to
  post-window v1.1 as an execution-mode ablation; the LoRA target stays the single-shot router;
  contracts stay 2.0.0. No code changed in this round.
- macOS validation at handoff (2026-07-28, Python 3.12.13 via Homebrew): 368 tests passed with
  100% statement/branch coverage; ruff check/format clean;
  `python scripts/export_json_schemas.py` deterministic (seven contracts).

## 2. Set up the machine

`.venv` is machine-local; never copy it between machines. On the macOS laptop it already exists
(Homebrew `python@3.12`, created 2026-07-17) — activate and validate. On any other machine,
recreate it per the README quick start. From an existing clone:

```bash
git switch main
git pull --ff-only origin main
source .venv/bin/activate  # or recreate: python3.12 -m venv .venv && pip install -r requirements.txt
python scripts/export_json_schemas.py
python -m ruff check --no-cache .
python -m ruff format --check .
python -m pytest --cov=sovereignlab --cov-branch --cov-report=term-missing -p no:cacheprovider
git diff --exit-code
```

## 3. Read before continuing

1. `AGENTS.md`.
2. `docs/project/01_project_charter.md`.
3. `docs/PROJECT_STATUS.md`.
4. Accepted ADRs 0001–0008 under `docs/decisions/` (ADR 0008 fixes how the join work unit must
   be implemented).
5. `docs/discovery/01_concept_upgrade_proposal.md` — the verified background and risk register
   behind the v2 direction.
6. `docs/project/05_evidence_contract_2_0_migration.md` — the implemented contract surface the
   next work units build on.
7. `docs/project/07_core_authoring_matrix.md` — the approved 40-record allocation, first approved
   batch, and human-review boundary.
8. `docs/project/08_temporal_document_retrieval.md` — the implemented document cutoff and
   filter-before-scoring contract.
9. `docs/discovery/03_week1_verification_log.md` — the verified example values the resolver must
   reproduce.
10. `src/sovereignlab/vintage/resolver.py`, `src/sovereignlab/retrieval/temporal.py`,
   `src/sovereignlab/harvest/weekly.py`, and their tests —
   the implemented resolver and append-only capture boundaries.

## 4. External state for the new session

- GitHub Actions repository secrets `ECOS_API_KEY` and `KOSIS_API_KEY` are configured. Their
  plaintext cannot be retrieved; another machine still needs its own ignored local `.env`.
- No secret-backed manual harvester run has been dispatched. Do not trigger one without separate
  owner authorization; the next weekly schedule can exercise the secrets normally.
- RunPod CLI 2.7.2 and its dedicated SSH key are configured on this Mac. The successful smoke and
  every discarded provisioning Pod were deleted; the account reports zero current hourly spend and
  a remaining balance of USD `19.7641547592`. Do not start another paid Pod without a new explicit
  authorization and cost estimate.
- No model weights or adapter were copied from RunPod. The repository contains only the harness,
  synthetic fixture, and recorded compatibility evidence.
- The application-ready detailed and brief English descriptions are in
  `docs/application/01_project_description.md`. They intentionally make no model-performance claim.
- The approved core count is exactly 4/40. Only `data/benchmark/core/core-batch-001.jsonl` is
  approved. The remaining 36 matrix slots are neither authored nor approved.
- The filenames and field names in the approved matrix and first core batch are intentionally
  unchanged. Do not rename them or alter the frozen allocation.
- No real report body or extracted report text has been added for document retrieval. The committed
  retrieval corpus is entirely synthetic.

## 5. Exact continuation order

### Work unit A — first real document manifests

Target only the first frozen documentary pair:

- pair: `kv-core-doc-01`;
- Korean record: `kv-core-doc-01-ko`;
- English record: `kv-core-doc-01-en`;
- evidence group: `eg-doc-bok-outlook-2026-05`;
- document unit: `bok-outlook-release-2026-05`;
- split/route: `train` / `documents`;
- intent: explain one stated driver from the May 2026 Bank of Korea outlook release family.

Complete this sequence:

1. Locate the official Korean and English publication landing pages and exact attachment URLs.
2. Record each language edition's actual public date independently. Do not copy the Korean date to
   a later English translation or infer a date from the release label.
3. Verify the publication-specific reuse/redistribution notice and attribution basis from official
   pages. Existing ECOS/KOSIS data-series rulings do not automatically apply to BOK publications.
4. Only after that read-only rights check, capture each attachment locally under ignored
   `data/raw/` or an OS temporary directory to compute its real byte size and SHA-256. Never invent
   manifest hashes or sizes.
5. Commit `SourceManifest` records under `data/manifests/`. Use `source_kind=document`, the actual
   language/date/date basis, and a conservative `redistribution` value. Leave `rights_decision`
   null: the typed series-rights link is for data/API sources and rejects document sources.
6. Do not commit the report bodies or extracted text unless the exact publication notice clearly
   authorizes that redistribution. If it is ambiguous, keep the manifests `metadata_only`, record
   the uncertainty, and stop before creating real searchable chunks.
7. Add manifest/retrieval-boundary tests, update `docs/PROJECT_STATUS.md`, run the full offline
   checks, make one conventional commit, and push it to `origin/main`.

Work unit A is complete only when both language sources have official URLs, independently supported
publication dates, real local-capture hashes/sizes, an auditable redistribution conclusion, strict
manifest validation, and no unauthorized body in Git. If an official English edition does not
exist, or its date/rights cannot be established, report that as a blocker instead of substituting
the Korean source or machine translation.

### Later work units — do not merge into A

1. After work unit A passes, author the `kv-core-doc-01` Korean/English records as a small draft
   batch under `data/benchmark/drafts/`. Do not change the frozen matrix and do not label the
   records reviewed or approved without a new explicit Hyungbae review.
2. After the next draft unit, build the minimal question-to-evidence-packet path under the
   ADR 0008 execution contract: the model emits the typed route plan and typed tool calls as
   native function calls against pydantic-derived schemas; the pipeline validates and executes
   them deterministically and commits a machine-readable trace of every call and result. This
   unit includes the recorded/replayable external model interface (charter §6), the resolver
   adapter behind the frozen flat gold-argument convention, and the new deterministic
   latest-only snapshot-read tool (freeze its gold argument convention before authoring the
   matrix records that depend on it). Offline scripted-planner tests land before any paid live
   model call; a live call needs a smoke test and a spend-ledger entry first.
3. Manually dispatch one append-only secret-backed workflow smoke only after separate owner
   authorization; otherwise let the weekly schedule exercise the configured secrets.

## 6. What not to redo

- Do not rebuild or rename the 40-record matrix or the approved four-record batch.
- Do not replace the retrieval baseline with embeddings yet. Its filter-before-scoring invariant
  and synthetic future-document regression are already complete.
- Do not rerun the paid QLoRA compatibility spike. It passed, all Pods were deleted, and it is not
  a model-quality result.
- Do not manually dispatch the secret-backed harvester as part of onboarding.
- Do not reopen accepted ADRs 0003–0008 without new evidence that requires a superseding decision.
- Do not implement the bounded multi-step tool loop in-window; ADR 0008 defers it to v1.1. Do
  not re-litigate that deferral — the supporting matrix/schema arithmetic is recorded in the ADR.

## 7. Hard stops

- Do not reinterpret `EDITION=YYYYMM` as a publication date.
- Do not implement a heuristic fallback across an unknown availability frontier; abstention is the
  correct answer.
- Do not assume bilingual document editions share a publication date, URL, hash, or licence.
- Do not fabricate `published_on`, `content_sha256`, `byte_size`, or an attribution basis to make a
  manifest validate.
- Do not commit raw ECOS/KOSIS observations unless the manifest's typed `rights_decision` link
  cross-validates against the committed owner-approved catalog under `BenchmarkBundle` 2.0.0
  rules.
- Do not publish raw OECD archive observations beyond ADR 0007's exact CLI exception; all other
  OECD scopes remain metadata-only.
- Do not run paid APIs, OCR, embeddings, or GPU work without a smoke test and spend-ledger entry.
- Do not count a draft as part of the human-reviewed core before explicit owner review.
- Do not let any tool accept model-chosen file paths, manifests, ledgers, or raw bytes; the
  harness injects committed artifacts (ADR 0008 decision 2).
- Do not use "agent", "agentic", "multi-step", "orchestration", or "autonomous" in public-facing
  descriptions of in-window artifacts (ADR 0008 decision 7); naming the deferred loop in planning
  and decision documents is permitted.
- Do not weaken the qualification rules for "first" claims or the append-only rules in
  `AGENTS.md`.
