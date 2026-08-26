# Cross-machine continuation handoff

- Legacy filename: retained so existing links and onboarding instructions do not break.
- Prepared: 2026-07-16; refreshed 2026-08-26 after the bilingual missing-as-of abstention draft
  slice (twenty-eighth refresh: two review candidates complete, named human review next)
- Target continuation machine: Windows workstation
- Authority: charter v2.5; accepted ADRs 0001–0009
- Branch to continue: `main` from `origin`
- Current milestone: M2
- Session state: work unit C and its first nine ADR 0008 slices are complete and reviewable; all
  three deterministic runtime adapters, the explicit dispatcher, offline planner boundary, private
  deterministic evidence-packet assembler, private offline executor, and five committed real-
  digest replay traces are complete; Hyungbae Cho approved the unchanged `kv-core-abstain-03`
  Korean/English pair, so the core remains 16/40; the `kv-core-abstain-04` Korean/English pair is
  now complete at `status=draft` and awaits named human review, while no later pair or slice is
  selected
- Completed missing-as-of abstention draft functional checkpoint: `fd7640b` (`feat: add missing-as-of abstention bilingual drafts`).
- Completed CPI revision false-premise abstention approval feature checkpoint: `5e14119` (`feat: approve CPI revision false-premise abstention pair`).
- Completed CPI revision false-premise abstention draft functional checkpoint: `77d247d` (`feat: add CPI revision false-premise abstention drafts`).
- Completed OECD scope abstention approval feature checkpoint: `4c29b1d` (`feat: approve OECD scope abstention bilingual pair`).
- Completed OECD scope abstention draft functional checkpoint: `c20619d` (`feat: add OECD scope abstention bilingual drafts`).
- Completed KOSIS CPI approval feature checkpoint: `95c5e61` (`feat: approve KOSIS CPI bilingual pair`).
- Completed KOSIS CPI draft functional checkpoint: `5e0da06` (`feat: add KOSIS CPI bilingual drafts`).
- Completed ECOS current-account approval feature checkpoint: `db6700e` (`feat: approve ECOS current-account bilingual pair`).
- Completed ECOS current-account draft functional checkpoint: `50c4d9c` (`feat: add ECOS current-account bilingual drafts`).
- Completed ECOS GDP approval feature checkpoint: `473a733` (`feat: approve ECOS GDP bilingual pair`).
- Completed ECOS GDP draft functional checkpoint: `f2d2523` (`feat: add ECOS GDP bilingual drafts`).
- Completed replay-trace functional checkpoint: `883815b` (`feat: add committed execution replay traces`).
- Completed offline-executor functional checkpoint: `550b591` (`feat: add offline executor`).
- Completed assembler functional checkpoint: `ff96710` (`feat: add deterministic evidence packet assembler`).
- Completed planner functional checkpoint: `272dd7f` (`feat: add offline planner boundary`).
- Prior dispatcher functional checkpoint: `834065e` (`feat: add frozen callable dispatcher`).
- Dispatcher documentation checkpoint: `dd6381a` (`docs: record callable dispatcher checkpoint`).
- Historical clean `origin/main` baseline before the Windows work-unit-C slices: `6fe447b`
  (`docs: prepare Windows continuation handoff`). Preserve the current reviewable worktree; do not
  reset to the historical checkpoint.

## 0. Start here

The repository is the source of truth; do not rely on a prior chat transcript or any uncommitted
state from the Mac. At the beginning of the Windows session:

1. Run `git status --short --branch` before any switch or pull. If any path is dirty, stop and
   preserve/investigate it. Only from a clean worktree, switch to `main`, fast-forward from
   `origin`, and confirm the final status is clean and aligned.
2. Read the files in section 3 in order, in full.
3. Create or verify the Windows-local `.venv` and run the PowerShell baseline in section 2 before
   changing files.
4. State back the current milestone, approved core count, exact next work unit, and hard stops.
5. Do not start a new work unit. Section 5 names only the pending human review of the
   `kv-core-abstain-04` Korean/English drafts; do not pre-approve them or select another pair.

If the worktree is dirty, preserve the existing changes and determine their owner before editing.
If local `main` has diverged from `origin/main`, stop rather than rewriting history.

## 1. What is complete

- The charter v2–v2.3 amendments and ADRs 0003–0007 recorded the K-VINTAGE/KOR-RTD direction,
  source-rights policy, and fail-closed edition-availability contract (all carried forward into
  the current charter v2.5).
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
  `202607` CLI answer and the pre-July abstention. Hyungbae approved the two-record documentary
  pair on 2026-07-29, bringing the approved core count to 6/40.
- The offline bilingual temporal document retriever is implemented under
  `src/sovereignlab/retrieval/`. It validates chunk-to-manifest language/hash linkage, removes
  post-`as_of` and other-language documents before computing corpus statistics or scores, and
  returns manifest-bound locators. Synthetic Korean/English fixtures prove future passages cannot
  change eligible results or scores. No official document body or paid embedding was used.
- The first real document-manifest unit is complete for `bok-outlook-release-2026-05`. The official
  Korean report page independently records `2026-05-28`; the English full-translation page records
  `2026-06-30`. Direct official PDF captures under `/tmp` supplied real sizes and SHA-256 values.
  Neither page supplied a publication-specific KOGL label. The owner subsequently confirmed that
  official Bank of Korea Economic Outlook reports and official English full translations are
  public data freely usable without a separate procedure under the copyright policy's Public Data
  Act Article 19 branch. ADR 0009 and charter v2.5 correct both strict manifests to `allowed`,
  subject to Bank of Korea attribution, transformation disclosure, and separately marked
  third-party rights. The PDFs, extracted text, and real searchable chunks remain outside Git by
  repository-scope choice. `docs/discovery/04_bok_outlook_2026_05_manifest_log.md` preserves the
  exact URLs, capture facts, initial negative finding, superseding conclusion, and reproduction
  boundary.
- Work unit B and its owner-review boundary are complete.
  `data/benchmark/core/core-batch-002.jsonl` contains exactly the frozen `kv-core-doc-01` Korean
  and English records at `status=approved`, with reviewer `Hyungbae Cho`, the actual aware review
  timestamp, and no matrix or substantive record change. The Korean record uses its 2026-05-28
  edition and PDF page 10 (`요약 4/10`); the
  English record uses its independently published 2026-06-30 translation and PDF page 9 (printed
  page `v`). Both summarize the `+0.7%p` IT-export upside contribution, attribute the Bank of
  Korea, and disclose paraphrase/transformation. The official PDFs were re-fetched only into a
  temporary directory, matched the committed byte sizes and hashes, and had both evidence pages
  rendered and visually inspected before all temporary files were deleted. Bundle tests enforce
  language matching, publication cutoffs, frozen allocation, split-group integrity, and the
  current 16/40 approved-core count.
- **Execution-contract adjustment (2026-07-28, ADR 0008 / charter v2.4, documentation only):**
  after a four-lens review with adversarial verification, the owner approved implementing the
  minimal question-to-evidence-packet path as a typed function-calling artifact (model-emitted
  typed plan and tool calls against pydantic-derived schemas, deterministic execution, committed
  traces, recorded/replayable model interface) with a three-tool surface — temporal retrieval,
  the as-of resolver behind the frozen flat gold-argument convention via an adapter, and a new
  deterministic latest-only snapshot-read tool. The bounded multi-step tool loop is deferred to
  post-window v1.1 as an execution-mode ablation; the LoRA target stays the single-shot router;
  contracts stay 2.0.0. No code changed in this round.
- **Execution/trace contract slice 1.0.0 (2026-07-29):**
  `src/sovereignlab/schemas/execution.py` and
  `docs/project/09_typed_execution_trace_contract.md` freeze the strict bilingual request,
  four-route plan, three typed calls/results, packet and trace semantics, digest-linked replay
  provenance, and the six-field `read_snapshot_as_of` gold convention for the three exact approved
  ECOS/KOSIS units. Six new schemas bring the public total to 13. A committed contract fixture
  round-trips with synthetic documentary text; its illustrative registry hashes are not claimed
  as an end-to-end execution. `BenchmarkRecord`/`BenchmarkBundle` remain 2.0.0.
- **Trusted latest-only snapshot adapter (2026-07-29):**
  `src/sovereignlab/snapshots/` implements an explicitly injected, digest-linked registry and
  deterministic `read_snapshot_as_of` adapter for the three owner-approved ECOS/KOSIS scopes.
  Registry construction eagerly freezes and verifies the explicitly admitted manifest, catalog,
  and archive bytes. The adapter filters trusted metadata by the inclusive Asia/Seoul cutoff
  before parsing only one unique latest payload, cross-validates active rights catalogs, parses
  exact provider rows and hidden KOSIS selectors, applies frozen Decimal normalization, and
  returns selected-row-only evidence or sanitized structured failures. It never falls back to an
  older capture when the selected frontier is invalid. The call boundary now also requires exact
  built-in bytes, rebuilds manifest and rights-catalog models from those bytes, and revalidates
  binding and immutable-container structure before every read. The detailed contract is
  `docs/project/10_snapshot_reader_contract.md`.
- **Trusted temporal-document adapter (2026-07-29):**
  `src/sovereignlab/retrieval/registry.py` freezes the exact synthetic four-manifest/six-chunk
  corpus behind ID `synthetic-temporal-retrieval-corpus-v1` and descriptor SHA-256
  `823117ee29a191bc306843e44ccd9d37e063db79cc87e15dcb7f2a11f5b5bf7e`.
  The loader confines two explicit JSONL inputs, freezes exact built-in bytes, and rejects path,
  size, count, JSON, and corpus-binding drift. Every typed call reparses those bytes, preserves
  language/cutoff filtering before scoring, verifies each selected field and exact deterministic
  result, and returns only typed selected evidence or a sanitized abstention/error. No real
  document body or searchable provider text was added. The detailed contract is
  `docs/project/11_temporal_retrieval_adapter_contract.md`.
- **Trusted historical STES adapter (2026-07-30):**
  `src/sovereignlab/vintage/registry.py` freezes the exact CLI archive, five manifests and
  archives, two-generation ledger chain, and two-generation rights-catalog chain behind registry
  ID `kor-rtd-stes-resolver-registry-v1` and descriptor SHA-256
  `103eb3bea7beebadeb0a7e193ff76fc95b518a8a7bed6825d9eb1f25431fb420`.
  The flat typed adapter preserves ledger-first selection, returns only the normalized selected
  row, and reproduces edition `202607` / value `102.66` for the approved core call. The frozen GDP
  shape abstains before resolution because its public raw evidence remains unavailable. The
  detailed contract is `docs/project/12_stes_adapter_contract.md`.
- **Frozen callable registry and explicit dispatcher (2026-07-30):**
  `src/sovereignlab/execution/dispatcher.py` freezes exactly the three typed adapter registrations,
  explicitly maps each exact call model to its adapter and trusted dependency, and rejects unknown,
  mismatched, subclassed, or mutated calls without name-based attribute lookup. Its provenance
  exposes the frozen callable registry, composite snapshot/STES artifact registry, and separate
  temporal-corpus ID/digest pairs required by the later execution trace. The detailed contract is
  `docs/project/13_callable_dispatcher_contract.md`.
- **Offline one-shot planner boundary (2026-08-02):**
  `src/sovereignlab/execution/planner.py` implements the minimal `Planner` protocol and exact
  scripted/recorded/replay modes over the existing `RoutePlan` 1.0.0. Scripted candidates carry
  digest-linked provenance without a model ID; recorded/replay candidates resolve opaque IDs
  through a private immutable harness registry, verify exact bytes and SHA-256 on every call, and
  preserve full provenance for invalid-candidate audit. The boundary rejects malformed/extra
  fields, missing/tampered recordings, unknown or mismatched tools, duplicate IDs, inconsistent
  routes, and request cutoff/question/language drift before dispatch. It adds no public schema,
  provider call, packet assembly, or executor. The detailed contract is
  `docs/project/14_offline_planner_contract.md`.
- **Deterministic evidence-packet assembler (2026-08-07):**
  `src/sovereignlab/execution/assembler.py` implements one private, entirely offline boundary over
  an exact validated request, route plan, and immutable ordered result tuple. It strictly
  revalidates all inputs, request/call bindings, ordered prefixes, typed payloads, cutoffs, and the
  final existing packet model. Planned and terminal-tool abstention reasons are copied exactly;
  tool abstention produces an empty packet without leaking an earlier successful payload; complete
  packets preserve result order and repeated cross-call evidence. The function/error boundary is
  not a package-level export, the public schema count remains 13, and no planner/dispatcher call,
  executor, trace fixture, provider call, source, benchmark, or paid operation was added. The
  detailed contract is `docs/project/15_evidence_packet_assembler_contract.md`.
- **Private offline executor (2026-08-11):**
  Functional commit `550b591` adds `src/sovereignlab/execution/executor.py`. The private boundary
  accepts one exact request plus harness-owned trace metadata, invokes the existing planner once,
  dispatches calls through the frozen committed registry in order, stops after the first terminal
  result, and invokes the assembler only for eligible terminal states. It returns only the existing
  strict `ExecutionTrace` 1.0.0, preserves sanitized planner/tool/packet failure phases without
  partial evidence, and rechecks real registry, corpus, planner, and canonical source-tree
  provenance before terminal return. The executor ID is `sovereignlab-offline-executor-v1`; its
  32-source descriptor SHA-256 is
  `08f45dab6a36a49cb7d0b588a69236942cd61534540bd4de0772010402dada64`. The function and error remain
  private, the public schema count stays 13, and no committed end-to-end replay trace, provider/live
  call, source capture, benchmark record, GPU, network, or paid operation was added. The detailed
  contract is
  `docs/project/16_offline_executor_contract.md`.
- **Committed real-digest replay traces (2026-08-11):**
  Functional commit `883815b` adds five deterministic `ExecutionTrace` 1.0.0 artifacts under
  `traces/replay/v1/`, generated only by `scripts/export_execution_replay_traces.py` through the
  real private executor, `ScriptedPlanner`, frozen callable registry, composite artifact registry,
  and committed retrieval corpus. The matrix covers all four routes and all three tools across
  Korean/English and explicit/implicit cutoffs, including complete, planned-abstention, and
  terminal tool-abstention outcomes. The terminal case retains its successful prefix, does not run
  the trailing STES call, and exposes no partial evidence. Healthy-stack tool- and packet-failure
  traces were intentionally not fabricated because injected faults would not be bound by the real
  executor digest; strict executor/schema tests continue to cover those mappings. The descriptor
  stays at 32 sources with SHA-256
  `08f45dab6a36a49cb7d0b588a69236942cd61534540bd4de0772010402dada64`, and public schemas stay at
  13. Work unit C is complete; the minimal offline path is now **typed function calling with
  committed traces**. Provider/live-model integration and the bounded loop remain absent.
- macOS baseline validated 2026-08-02 on Python 3.12.13: 1,007 tests passed with 100% SovereignLab
  statement/branch coverage (4,238 statements, 1,414 branches); ruff check/format clean (65 Python
  files); `python scripts/export_json_schemas.py` deterministic (13 contracts). The win32-only
  `tzdata==2026.3` pin and short ECOS pytest IDs repair two Windows-only baseline failures.
- Windows baseline validated 2026-08-07 on Python 3.12.13: all 13 schemas regenerated without a
  diff; ruff check passed; ruff format check passed across 67 Python files; all 1,049 tests passed
  with 100% SovereignLab statement/branch coverage (4,353 statements, 1,470 branches); and the 42
  focused assembler tests reached 100% assembler coverage (115 statements, 56 branches). The full
  suite used an explicit fresh OS `--basetemp` because the unchanged ignored `.pytest_tmp` on this
  workstation retains its documented access-denying ACL. No source/provider read, secret, live
  model call, GPU operation, or paid operation occurred.
- Windows baseline validated 2026-08-11 on Python 3.12.13: all 13 schemas regenerated without a
  diff; Ruff check passed; Ruff format check passed across 69 Python files; all 1,115 tests passed
  with 100% SovereignLab statement/branch coverage (4,679 statements, 1,568 branches); and the 66
  focused executor tests reached 100% executor coverage (326 statements, 98 branches). Focused and
  full suites used fresh OS `--basetemp` directories because the unchanged ignored `.pytest_tmp`
  retains its documented access-denying ACL. The directory and ACL were not modified. Functional
  commit `550b591` matched `origin/main` before this documentation checkpoint. No network/provider
  call, secret, live model integration, GPU operation, or paid operation occurred.
- Replay-trace slice validated 2026-08-11 on Windows/Python 3.12.13: all 13 schemas regenerated
  without a diff; all five traces reproduced byte-for-byte; Ruff check passed; and Ruff format
  check passed across 71 Python files. The focused executor-plus-replay suite passed all 80 tests
  with 100% executor coverage (326 statements, 98 branches). The full suite passed all 1,129 tests
  with 100% SovereignLab statement/branch coverage (4,679 statements, 1,568 branches) under a fresh
  OS `--basetemp`. The executor descriptor remains 32 entries at SHA-256
  `08f45dab6a36a49cb7d0b588a69236942cd61534540bd4de0772010402dada64`; schema and Git whitespace
  diffs are clean. The canonical onboarding attempt had collected 1,115 baseline tests and reported
  1,009 passed plus 106 setup errors, all the documented `.pytest_tmp` `WinError 5`; the same
  baseline passed 1,115/1,115 with a fresh OS `--basetemp`. The directory and ACL were not touched.
  Functional commit `883815b` contains the trace slice. No network, provider/live-model integration,
  source or rights change, secret, GPU operation, or paid operation occurred; cost was $0.00.
- ECOS GDP draft slice validated 2026-08-19 on Windows/Python 3.12.13: all 13 public schemas and five
  committed replay traces remained unchanged; Ruff check passed; and Ruff format check passed
  across 72 Python files. The focused benchmark slice passed all 27 tests. The full suite passed all
  1,135 tests with 100% SovereignLab statement/branch coverage (4,679 statements, 1,568 branches)
  under a fresh OS `--basetemp`. The canonical onboarding attempt collected 1,129 tests and
  reported 1,023 passed plus 106 setup errors, all the documented `.pytest_tmp` `WinError 5`; the
  same baseline passed 1,129/1,129 with a fresh OS `--basetemp`. The directory and ACL were not
  touched. Functional commit `f2d2523` contains exactly the two drafts and focused tests. No
  network, provider/live-model call, source refresh, GPU operation, or paid operation occurred;
  cost was $0.00.
- ECOS GDP approval transition validated 2026-08-20 on Windows/Python 3.12.13: the three focused
  benchmark files passed all 27 tests; the full suite passed all 1,135 tests with 100% SovereignLab
  statement/branch coverage (4,679 statements, 1,568 branches) under a fresh OS `--basetemp`; and
  Ruff check plus format check passed across 72 Python files. The 13 public schemas and five
  committed traces remained unchanged. The repository `.pytest_tmp` directory and ACL were not
  touched. Feature commit `473a733` contains the two-record approval lifecycle transition and
  focused test updates only; the matrix, source, rights, schema, and runtime boundaries are
  unchanged. No network, provider/live-model call, GPU operation, or paid operation occurred; cost
  was $0.00.
- ECOS current-account draft slice validated 2026-08-20 on Windows/Python 3.12.13: all six new
  focused tests passed, the four focused benchmark files passed all 33 tests, and the full suite
  passed all 1,141 tests with 100% SovereignLab statement/branch coverage (4,679 statements, 1,568
  branches) under a fresh OS `--basetemp`. Ruff check plus format check passed across 73 Python
  files. All 13 public schemas regenerated deterministically and all five committed replay traces
  remained unchanged. The repository `.pytest_tmp` directory and ACL were not touched. Functional
  commit `50c4d9c` contains exactly the two drafts and focused tests; the matrix, approved core,
  source, rights, schema, trace, and runtime boundaries are unchanged. No network, provider/live-
  model call, GPU operation, or paid operation occurred; cost was $0.00.
- ECOS current-account approval transition validated 2026-08-21 on Windows/Python 3.12.13: the
  four focused benchmark files passed all 33 tests; the full suite passed all 1,141 tests with
  100% SovereignLab statement/branch coverage (4,679 statements, 1,568 branches) under a fresh OS
  `--basetemp`; and Ruff check plus format check passed across 73 Python files. The 13 public
  schemas regenerated deterministically and the five committed traces remained unchanged. The
  repository `.pytest_tmp` directory and ACL were not touched. Feature commit `db6700e` contains
  the two-record approval lifecycle transition and focused test updates only; the matrix, source,
  rights, schema, and runtime boundaries are unchanged. No network, provider/live-model call, GPU
  operation, or paid operation occurred; cost was $0.00.
- KOSIS CPI draft slice validated 2026-08-21 on Windows/Python 3.12.13: all six new focused tests
  passed, the five focused benchmark files passed all 39 tests, and the full suite passed all
  1,147 tests with 100% SovereignLab statement/branch coverage (4,679 statements, 1,568 branches)
  under a fresh OS `--basetemp`. Ruff check plus format check passed across 74 Python files. All
  13 public schemas regenerated deterministically and all five committed replay traces remained
  unchanged. The repository `.pytest_tmp` directory and ACL were not touched. Functional commit
  `5e0da06` contains exactly the two drafts and focused tests; the matrix, approved core, source,
  rights, schema, trace, and runtime boundaries are unchanged. No network, provider/live-model
  call, GPU operation, or paid operation occurred; cost was $0.00.
- KOSIS CPI approval transition validated 2026-08-25 on Windows/Python 3.12.13: the five focused
  benchmark files passed all 39 tests; the full suite passed all 1,147 tests with 100%
  SovereignLab statement/branch coverage (4,679 statements, 1,568 branches) under a fresh OS
  `--basetemp`; and Ruff check plus format check passed across 74 Python files. The 13 public
  schemas regenerated deterministically and the five committed traces remained unchanged. The
  repository `.pytest_tmp` directory and ACL were not touched. Feature commit `95c5e61` contains
  the two-record approval lifecycle transition and focused test updates only; the matrix, source,
  rights, schema, and runtime boundaries are unchanged. No network, provider/live-model call, GPU
  operation, or paid operation occurred; cost was $0.00.
- OECD scope abstention draft slice validated 2026-08-25 on Windows/Python 3.12.13: all six new
  focused tests passed, the six focused benchmark files passed all 45 tests, and the full suite
  passed all 1,153 tests with 100% SovereignLab statement/branch coverage (4,679 statements,
  1,568 branches) under a fresh OS `--basetemp`. Ruff check plus format check passed across 75
  Python files. All 13 public schemas regenerated deterministically and all five committed replay
  traces remained unchanged. The repository `.pytest_tmp` directory and ACL were not touched.
  Functional commit `c20619d` contains exactly the two drafts and focused tests; the matrix,
  approved core, source, rights, schema, trace, and runtime boundaries are unchanged. No network,
  provider/live-model call, GPU operation, or paid operation occurred; cost was $0.00.
- OECD scope abstention approval transition validated 2026-08-26 on Windows/Python 3.12.13: the
  six focused benchmark files passed all 45 tests; the full suite passed all 1,153 tests with
  100% SovereignLab statement/branch coverage (4,679 statements, 1,568 branches) under a fresh OS
  `--basetemp`; and Ruff check plus format check passed across 75 Python files. The 13 public
  schemas regenerated deterministically and the five committed traces remained unchanged. The
  repository `.pytest_tmp` directory and ACL were not touched. Feature commit `4c29b1d` contains
  the two-record approval lifecycle transition and focused test updates only; the matrix, source,
  rights, schema, and runtime boundaries are unchanged. No network, provider/live-model call, GPU
  operation, or paid operation occurred; cost was $0.00.
- CPI revision false-premise abstention draft slice validated 2026-08-26 on Windows/Python
  3.12.13: all six new focused tests passed, the seven focused benchmark files passed all 51
  tests, and the full suite passed all 1,159 tests with 100% SovereignLab statement/branch
  coverage (4,679 statements, 1,568 branches) under a fresh OS `--basetemp`. Ruff check plus
  format check passed across 76 Python files. All 13 public schemas regenerated deterministically
  and all five committed replay traces remained unchanged. The repository `.pytest_tmp` directory
  and ACL were not touched. Functional commit `77d247d` contains exactly the two drafts and
  focused tests; the matrix, approved core, source, rights, schema, trace, and runtime boundaries
  are unchanged. No network, provider/live-model call, GPU operation, or paid operation occurred;
  cost was $0.00.
- CPI revision false-premise abstention approval transition validated 2026-08-26 on Windows/Python
  3.12.13: the seven focused benchmark files passed all 51 tests; the full suite passed all 1,159
  tests with 100% SovereignLab statement/branch coverage (4,679 statements, 1,568 branches) under
  a fresh OS `--basetemp`; and Ruff check plus format check passed across 76 Python files. The 13
  public schemas regenerated deterministically and the five committed traces remained unchanged.
  The repository `.pytest_tmp` directory and ACL were not touched. Feature commit `5e14119`
  contains the two-record approval lifecycle transition and focused test updates only; the matrix,
  source, rights, schema, and runtime boundaries are unchanged. No network, provider/live-model
  call, GPU operation, or paid operation occurred; cost was $0.00.
- Missing-as-of abstention draft slice validated 2026-08-26 on Windows/Python 3.12.13: all six
  new focused tests passed, the eight focused benchmark files passed all 57 tests, and the full
  suite passed all 1,165 tests with 100% SovereignLab statement/branch coverage (4,679
  statements, 1,568 branches) under a fresh OS `--basetemp`. Ruff check plus format check passed
  across 77 Python files. All 13 public schemas regenerated deterministically and all five
  committed replay traces remained unchanged. The repository `.pytest_tmp` directory and ACL were
  not touched. Functional commit `fd7640b` contains exactly the two drafts and focused tests; the
  matrix, approved core, source, rights, schema, trace, and runtime boundaries are unchanged. No
  network, provider/live-model call, GPU operation, or paid operation occurred; cost was $0.00.

## 2. Set up and validate the Windows machine

`.venv` is machine-local; never copy it from the Mac or another clone. Run from the repository root
in PowerShell. Calling the venv interpreter directly avoids activation-policy differences:

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

Expected handoff baseline: Python 3.12, 13 deterministic public schemas, 77 formatted Python
files, 1,165 passing tests, 100% SovereignLab statement/branch coverage (4,679 statements, 1,568
branches), and no unexpected Git diff.
On this workstation, the ignored repository-root `.pytest_tmp` can retain an access-denying ACL
and make the canonical pytest command report only tmp-path setup errors. Do not treat that known
ACL failure as a source regression or alter the directory during repository work. Rerun the exact
suite with `--basetemp` set to a new OS temporary path, and record both the canonical attempt and
the full fallback result.
The Windows
user-level launcher was unreliable in an earlier session. If `python` does not resolve to 3.12,
discover the installed executable with `where.exe python` or the installed-app inventory, set
`$python312` to that verified full path for the current shell only, and rerun the checks. Never
commit a workstation path. If an existing `.venv` fails its interpreter check, stop and recreate it
deliberately rather than silently reusing it. The requirements install `tzdata` only on `win32`;
do not remove it merely because another operating system supplies an IANA timezone database.

## 3. Read before continuing

1. `AGENTS.md`.
2. `docs/project/01_project_charter.md`.
3. `docs/PROJECT_STATUS.md`.
4. Accepted ADRs 0001–0009 under `docs/decisions/` (ADR 0008 fixes how the join work unit must
   be implemented; ADR 0009 records the BOK Economic Outlook public-data family ruling).
5. `docs/discovery/01_concept_upgrade_proposal.md` — the verified background and risk register
   behind the v2 direction.
6. `docs/project/05_evidence_contract_2_0_migration.md` — the implemented contract surface the
   next work units build on.
7. `docs/project/07_core_authoring_matrix.md` — the approved 40-record allocation, first seven
   approved batches (16/40), and human-review boundary.
8. `docs/project/08_temporal_document_retrieval.md` — the implemented document cutoff and
   filter-before-scoring contract.
9. `docs/project/09_typed_execution_trace_contract.md` — the frozen execution/trace contract.
10. `docs/project/10_snapshot_reader_contract.md` — the implemented trusted registry, cutoff-safe
    reader, provider parsers, and failure taxonomy.
11. `docs/project/11_temporal_retrieval_adapter_contract.md` — the implemented trusted synthetic
    corpus registry, typed adapter, and digest/replay boundary.
12. `docs/project/12_stes_adapter_contract.md` — the implemented trusted historical registry,
    rights/ledger/archive joins, and typed adapter.
13. `docs/project/13_callable_dispatcher_contract.md` — the frozen three-tool registry, explicit
    dispatcher, composite replay provenance, and snapshot call-time hardening.
14. `docs/project/14_offline_planner_contract.md` — the implemented planner, private exact-byte
    recording boundary, request binding, and deterministic replay.
15. `docs/project/15_evidence_packet_assembler_contract.md` — the implemented private assembler,
    ordered-result binding, abstention semantics, and no-partial-evidence boundary.
16. `docs/project/16_offline_executor_contract.md` — the implemented private executor, one-shot
    state machine, sanitized trace/failure mapping, and real provenance construction.
17. `traces/README.md` — the public/private trace boundary, committed replay matrix, exact-byte
    reproduction commands, and rationale for not fabricating healthy-stack failure traces.
18. `scripts/export_execution_replay_traces.py`, `tests/execution/test_replay_traces.py`, and the
    five JSON files under `traces/replay/v1/` — the deterministic exporter, real-boundary checks,
    and committed machine-readable outcomes that complete work unit C.
19. `src/sovereignlab/schemas/execution.py` and `tests/schemas/test_execution.py` — the exact
    request/plan/result/packet/trace invariants reused by the executor and committed traces.
20. `src/sovereignlab/execution/executor.py` and `tests/execution/test_executor.py` — the completed
    private executor and its real-registry, state-machine, provenance, drift, sanitization, and
    deterministic round-trip coverage.
21. The dispatcher, planner, and assembler source/test pairs under `src/sovereignlab/execution/`
    and `tests/execution/` — completed frozen boundaries coordinated by the executor and replay
    traces without reopening.
22. `data/benchmark/core/core-batch-003.jsonl` and
    `tests/benchmark/test_ecos_gdp_core.py` — the approved two-record ECOS GDP core batch and its
    focused frozen-allocation, evidence, cutoff, bilingual-parity, and approval-lifecycle checks.
23. `data/benchmark/core/core-batch-004.jsonl` and
    `tests/benchmark/test_ecos_current_account_core.py` — the approved two-record ECOS current-
    account core batch and its focused frozen-allocation, evidence, cutoff, bilingual-parity,
    approval-lifecycle, and no-future-leak checks.
24. `data/benchmark/core/core-batch-005.jsonl` and
    `tests/benchmark/test_kosis_cpi_core.py` — the approved two-record KOSIS CPI core batch and
    its focused frozen-allocation, evidence, cutoff, bilingual-parity, approval-lifecycle, and
    no-future-leak checks.
25. `data/benchmark/core/core-batch-006.jsonl` and
    `tests/benchmark/test_oecd_scope_abstain_core.py` — the approved two-record OECD scope
    abstention core batch and its focused frozen-allocation, abstention-reason, bilingual-parity,
    approval-lifecycle, no-value-leak, and rights-versus-availability contrast checks.
26. `data/benchmark/core/core-batch-007.jsonl` and
    `tests/benchmark/test_cpi_revision_abstain_core.py` — the approved two-record CPI revision
    false-premise abstention core batch and its focused frozen-allocation, abstention-reason,
    bilingual-parity, approval-lifecycle, no-value/no-snapshot-leak, sole-approved-OECD-scope, and
    latest-only vintage-semantics checks.
27. `data/benchmark/drafts/core-draft-008.jsonl` and
    `tests/benchmark/test_missing_as_of_abstain_draft.py` — the pending two-record missing-as-of
    abstention draft pair and its focused frozen-allocation, no-as-of-phrase,
    explicit-cutoff-demand, bilingual-parity, draft-lifecycle,
    no-value/no-snapshot-or-ledger-leak, and explicit-cutoff-contrast checks.

Only when changing source/resolver/harvester behavior, also read
`docs/discovery/03_week1_verification_log.md` and the relevant resolver, retrieval, registry,
adapter, or harvester source/tests. They are not prerequisites for the current named human-review
gate.

## 4. External state for the new session

- GitHub Actions repository secrets `ECOS_API_KEY` and `KOSIS_API_KEY` are configured. Their
  plaintext cannot be retrieved; another machine still needs its own ignored local `.env`.
- No secret-backed manual harvester run has been dispatched. Do not trigger one without separate
  owner authorization; the next weekly schedule can exercise the secrets normally.
- RunPod CLI 2.7.2 and its dedicated SSH key are configured on this Mac. The successful smoke and
  every discarded provisioning Pod were deleted; the account reports zero current hourly spend and
  a remaining balance of USD `19.7641547592`. Do not start another paid Pod without a new explicit
  authorization and cost estimate.
- Do not assume the Mac's RunPod CLI, SSH key, GitHub CLI login, local `.env`, or virtual
  environment exists on Windows. They are machine-local and are not needed for the pending
  offline human-review gate.
- No model weights or adapter were copied from RunPod. The repository contains only the harness,
  synthetic fixture, and recorded compatibility evidence.
- The application-ready detailed and brief English descriptions are in
  `docs/application/01_project_description.md`. They intentionally make no model-performance claim.
- The approved core count is exactly 16/40. The four records in
  `data/benchmark/core/core-batch-001.jsonl`, the two records in
  `data/benchmark/core/core-batch-002.jsonl`, the two records in
  `data/benchmark/core/core-batch-003.jsonl`, the two records in
  `data/benchmark/core/core-batch-004.jsonl`, the two records in
  `data/benchmark/core/core-batch-005.jsonl`, the two records in
  `data/benchmark/core/core-batch-006.jsonl`, and the two records in
  `data/benchmark/core/core-batch-007.jsonl` are approved. The two `kv-core-abstain-04` records
  in `data/benchmark/drafts/core-draft-008.jsonl` are pending named human review and do not
  increase the approved count. The other 24 matrix slots remain unapproved: two are drafts and 22
  are unauthored.
- The field names and allocation in the approved matrix and seven core batches are intentionally
  unchanged. Do not rename them or alter the frozen allocation.
- Two real BOK document manifests are committed, but no provider report body or extracted provider
  text has been added. ADR 0009 classifies the manifests as `allowed`; their absence is a
  repository-scope choice, and the committed searchable retrieval corpus remains entirely
  synthetic.

## 5. Exact continuation order

### Completed work unit A — do not redo

`kv-core-doc-01` now has strict Korean and English source manifests with independently supported
dates, real hashes/sizes, exact official links, and an owner-approved `allowed` public-data rights
conclusion under ADR 0009. The provider PDFs and extracted text are not committed by
repository-scope choice. Re-fetch a PDF only into ignored `data/raw/` or an OS temporary directory
when the next unit needs local inspection, and verify the committed size/hash before use.

### Completed work unit B and owner review — do not redo

Target only the same frozen documentary pair:

- pair: `kv-core-doc-01`;
- Korean record: `kv-core-doc-01-ko`;
- English record: `kv-core-doc-01-en`;
- evidence group: `eg-doc-bok-outlook-2026-05`;
- document unit: `bok-outlook-release-2026-05`;
- split/route: `train` / `documents`;
- intent: explain one stated driver from the May 2026 Bank of Korea outlook release family.

Both records validate against the committed manifests and frozen matrix. Hyungbae approved them on
2026-07-29 and moved them to `core/core-batch-002.jsonl`; at that checkpoint, the approved count
was 6/40. The source
PDFs and extracted text remain outside Git, and the synthetic fixture remains the only searchable
corpus.

### Completed work unit C

Work unit C delivered one offline, replayable path from a bilingual question and optional `as_of`
to a validated single-shot route plan, deterministic tool execution, evidence packet, and committed
machine-readable trace under ADR 0008. The shipped minimal offline path is **typed function calling
with committed traces**.

It was completed in this order:

1. **Complete.** Read ADR 0008, charter §§3/6/7, the frozen benchmark models, and the existing
   resolver, retriever, harvester snapshot formats, and tests. The original discovery recorded
   that no router/model-call/replay package or snapshot-read tool existed at that time; the
   snapshot reader, all three adapters, dispatcher, offline planner, private assembler, and private
   offline executor now exist. The planner's recording registry remains private and no provider
   recording path exists under `data/`.
2. **Complete.** Freeze strict typed contracts for the route plan, tool calls/results, evidence packet, and
   trace, plus the latest-only snapshot reader's flat gold-argument convention. Derive callable
   JSON schemas from Pydantic. Do not change `BenchmarkRecord` or `BenchmarkBundle` 2.0.0. Record
   any consequential choice not already fixed by ADR 0008 as a focused ADR or specification.
3. **Complete.** Expose exactly three registered deterministic offline tool adapters:
   - **Complete.** `read_snapshot_as_of` is limited to committed owner-approved scopes and backed
     by a trusted, digest-linked registry;
   - **Complete.** `retrieve_temporal_documents` uses the existing filter-before-scoring
     implementation and trusted, digest-linked synthetic corpus;
   - **Complete.** `resolve_stes_as_of` through an adapter matching the exact flat arguments in
     `core-batch-001.jsonl`.
4. **Complete.** Inject trusted manifests, ledgers, archive bytes, snapshot locations, and
   registries from the harness through the frozen three-tool registry and explicit dispatcher.
   Reject model-supplied paths, raw bytes, manifests, ledgers, unknown tool names, extra fields,
   or invalid arguments.
5. **Complete.** Put the planner boundary behind a one-shot protocol with scripted and
   immutable recorded/replay implementations:
   - consume one already validated `ExecutionRequest`; the harness fixes `effective_as_of` before
     invocation and owns callable schemas and recordings;
   - yield a Pydantic-validated `RoutePlan` 1.0.0 containing only the three exact typed call
     variants, and expose `PlannerProvenance`-compatible metadata without inventing a public
     `PlannerResult`/`PlannerOutput`;
   - bind every call cutoff to `effective_as_of` and copy document question/language exactly;
   - keep scripted mode deterministic/offline with no `model_id`; resolve recorded/replay
     candidates through an opaque harness-owned `recording_id`, verify the SHA-256 of the exact
     candidate bytes, require complete recording metadata plus `model_id`, and never call a
     provider;
   - fail before dispatch on missing/tampered recordings, malformed or extra fields, unknown or
     mismatched tools, duplicate IDs, inconsistent route shape, or request-binding drift, while
     preserving digest-linked invalid-candidate metadata for a later plan-validation trace; and
   - cover four routes, Korean/English, explicit/implicit cutoff, provenance, deterministic
     model-equivalent replay from exact-byte-verified recordings, and mutation cases with focused
     tests, then run the full baseline.
   Reuse the existing `route-plan-v1` and three argument schemas. Do not add a public planner or
   recording schema unless a newly recorded focused decision proves it necessary. Commit and stop
   after this slice.
6. **Complete.** Add only the deterministic evidence-packet assembler over an already validated
   request, route plan, and ordered typed results. Reuse `ExecutionEvidencePacket` 1.0.0, preserve
   planned/tool abstention semantics, expose no partial evidence, reject identity, order, cutoff,
   or payload drift, and do not invoke the planner or dispatcher. The implementation is private
   under `docs/project/15_evidence_packet_assembler_contract.md` and passed focused/full validation.
7. **Complete.** Add only the private offline executor that coordinates the validated planner,
   dispatcher, and private packet assembler in order with real registry/corpus and execution-
   environment provenance. Functional commit `550b591` implements this boundary under
   `docs/project/16_offline_executor_contract.md` without a public wrapper or schema and passes
   focused/full validation.
8. **Complete.** Functional commit `883815b` adds five small machine-readable real-digest replay
   traces generated only through the real executor, registry/corpus, and `ScriptedPlanner`
   provenance boundaries. They preserve exact plans, ordered calls/results, abstentions, and final
   packets for deterministic replay and audit; the older contract fixture remains only a schema
   fixture.
9. **Complete.** Focused tests cover all four routes, all three tool adapters, bilingual input,
   explicit/implicit `as_of`, deterministic byte reproduction, trace round-tripping, cutoff
   enforcement, successful-prefix terminal abstention, and strict invalid/failure mappings. The
   full 1,129-test offline baseline is green and `docs/PROJECT_STATUS.md` records the commands and
   results.

The first nine reviewable slices and work unit C are complete: the typed execution/trace surface is
frozen in `docs/project/09_typed_execution_trace_contract.md`; the trusted snapshot registry plus
`read_snapshot_as_of` adapter are implemented under
`docs/project/10_snapshot_reader_contract.md`; and the trusted synthetic retrieval registry plus
typed `retrieve_temporal_documents` adapter are implemented under
`docs/project/11_temporal_retrieval_adapter_contract.md`. The trusted historical registry plus
flat `resolve_stes_as_of` adapter are implemented under
`docs/project/12_stes_adapter_contract.md`; and the frozen three-tool callable registry plus
explicit dispatcher are implemented under `docs/project/13_callable_dispatcher_contract.md`.
The planner protocol with scripted and immutable recorded/replay implementations is complete under
`docs/project/14_offline_planner_contract.md`, the private deterministic evidence-packet assembler
is complete under `docs/project/15_evidence_packet_assembler_contract.md`, and the private offline
executor is complete under `docs/project/16_offline_executor_contract.md`. Five committed real-
digest traces under `traces/replay/v1/` exercise these frozen components through the real private
executor. The subsequent draft slice is also complete in functional commit `f2d2523`; provider/
live-model integration remains absent.

The completed STES adapter slice:

- copies the eight frozen flat arguments without accepting a path, manifest, ledger, catalog,
  archive, edition, URL, source ID, or credential from the call;
- resolves explicitly injected immutable archive/manifest/availability-ledger/rights-catalog
  inputs through a digest-linked trusted registry;
- preserves ledger-first fail-closed edition selection and selected-row-only normalization;
- permits public raw evidence only for the owner-approved Korea monthly amplitude-adjusted CLI
  scope, while the frozen GDP call shape remains unavailable as public raw evidence under the
  current rights catalog;
- emits only the typed STES observation evidence, sanitized abstention, or call-bound error; and
- passes focused 100% statement/branch coverage plus the full offline baseline without adding a
  source capture, benchmark record, live model call, or paid operation.

Work unit C passed its gate: the minimal path runs offline end to end, calls and results are present
in replayable committed traces, existing temporal-leakage protections still pass, all three tools
are exercised, and the full offline suite is green. Provider/live-model integration, additional
source ingestion, and the v1.1 bounded loop remain separate units.

### Completed `kv-core-data-02` draft and owner-approval slices

Functional commit `f2d2523` adds exactly `kv-core-data-02-ko` and `kv-core-data-02-en` at
`status=draft` in `data/benchmark/drafts/core-draft-003.jsonl`. Both records preserve the frozen
`train` / `data` allocation and `eg-data-ecos-gdp-20260717` evidence group, use only the existing
`ecos-200y108-snapshot-20260717` snapshot whose use in KOR-RTD is owner-approved, and answer its
2026Q1 real-GDP
observation as `596692.8` `billion_krw`. Focused and full validation are green. The matrix, source
bundle, rights decision, normalization contract, 13 public schemas, and five committed traces are
unchanged. At that checkpoint, the approved count remained 6/40.

On 2026-08-20, Hyungbae Cho approved the unchanged Korean/English pair. Approval feature commit
`473a733` moves the two records to `data/benchmark/core/core-batch-003.jsonl`, records reviewer
`Hyungbae Cho` and aware review timestamp `2026-08-20T00:24:18Z`, and replaces only the lifecycle
tag `draft-003` with `batch-003`. The questions, answers, cutoff, route, split, evidence group,
data-unit binding, tool expectations, attribution, and normalization are unchanged from `f2d2523`.
At that approval checkpoint, the approved core was 8/40, the remaining 32 slots were unauthored
and unapproved, and no draft was pending. The matrix, source bundle, rights decisions, 13 public
schemas, five committed traces, and runtime source remained unchanged.

The approval transition passed 27 focused benchmark tests and the full 1,135-test suite with 100%
SovereignLab statement/branch coverage (4,679 statements, 1,568 branches) under a fresh OS
`--basetemp`; Ruff check and format check passed across 72 Python files. The repository
`.pytest_tmp` directory and ACL were untouched, and the slice cost $0.00.

### Completed `kv-core-data-03` draft and owner-approval slices

Functional commit `50c4d9c` adds exactly `kv-core-data-03-ko` and `kv-core-data-03-en` at
`status=draft` in `data/benchmark/drafts/core-draft-004.jsonl`, together with six focused tests.
Both records preserve the frozen `train` / `data` allocation,
`eg-data-ecos-current-account-20260717` evidence group, and
`ecos-301y017-snapshot-20260717` data-unit binding. They use only that existing snapshot whose
use in KOR-RTD is owner-approved and reproduce the 2026-05 seasonally adjusted current account as
`38121.1` `million_usd`. The matrix, approved core, source bundle, rights decisions,
normalization contract, 13 public schemas, five committed traces, and runtime source are
unchanged. At that checkpoint, the approved count remained 8/40; of the other 32 unapproved
slots, these two were pending drafts and 30 remained unauthored.

On 2026-08-21, Hyungbae Cho approved the unchanged Korean/English pair. Approval feature commit
`db6700e` moves the two records to `data/benchmark/core/core-batch-004.jsonl`, records reviewer
`Hyungbae Cho` and aware review timestamp `2026-08-21T07:14:13Z`, and replaces only the lifecycle
tag `draft-004` with `batch-004`. The questions, answers, cutoff, route, split, evidence group,
data-unit binding, tool expectations, attribution, and normalization are unchanged from `50c4d9c`.
At that approval checkpoint, the approved core was 10/40, the remaining 30 slots were unauthored
and unapproved, and no draft was pending. The matrix, source bundle, rights decisions, 13 public
schemas, five committed traces, and runtime source remained unchanged.

The approval transition passed 33 focused benchmark tests across four files and the full
1,141-test suite with 100% SovereignLab statement/branch coverage (4,679 statements, 1,568
branches) under a fresh OS `--basetemp`; Ruff check and format check passed across 73 Python
files. The repository `.pytest_tmp` directory and ACL were untouched, and the slice cost $0.00.

### Completed `kv-core-data-04` draft and owner-approval slices

Functional commit `5e0da06` adds exactly `kv-core-data-04-ko` and `kv-core-data-04-en` at
`status=draft` in `data/benchmark/drafts/core-draft-005.jsonl`, together with six focused tests.
Both records preserve the frozen `dev` / `data` allocation, `eg-data-kosis-cpi-20260717` evidence
group, and `kosis-cpi-snapshot-20260717` data-unit binding. They use only that existing snapshot
whose use in KOR-RTD is owner-approved under ADR 0007 and reproduce the June 2026 national
all-items consumer price index (2020=100) as `119.99` `index_2020_100`. The matrix, approved
core, source bundle, rights decisions, normalization contract, 13 public schemas, five committed
traces, and runtime source are unchanged. At that checkpoint, the approved count remained 10/40;
of the other 30 unapproved slots, these two were pending drafts and 28 remained unauthored.

On 2026-08-25, Hyungbae Cho approved the unchanged Korean/English pair. Approval feature commit
`95c5e61` moves the two records to `data/benchmark/core/core-batch-005.jsonl`, records reviewer
`Hyungbae Cho` and aware review timestamp `2026-08-25T07:10:15Z`, and replaces only the lifecycle
tag `draft-005` with `batch-005`. The questions, answers, cutoff, route, split, evidence group,
data-unit binding, tool expectations, attribution, and normalization are unchanged from `5e0da06`,
and the annotations preserve the AI author `Claude AI draft`. At that approval checkpoint, the
approved core was 12/40, the remaining 28 slots were unauthored and unapproved, and no draft was
pending. This approval completes the data route's four authorable pairs
(`kv-core-data-01`–`kv-core-data-04`); the fifth data pair `kv-core-data-05` stays reserved on
the deliberately unauthored test-split unit. The matrix, source bundle, rights decisions, 13
public schemas, five committed traces, and runtime source remained unchanged.

The approval transition passed 39 focused benchmark tests across five files and the full
1,147-test suite with 100% SovereignLab statement/branch coverage (4,679 statements, 1,568
branches) under a fresh OS `--basetemp`; Ruff check and format check passed across 74 Python
files. The repository `.pytest_tmp` directory and ACL were untouched, and the slice cost $0.00.

### Completed `kv-core-abstain-02` draft and owner-approval slices

Functional commit `c20619d` adds exactly `kv-core-abstain-02-ko` and `kv-core-abstain-02-en` at
`status=draft` in `data/benchmark/drafts/core-draft-006.jsonl`, together with six focused tests.
Both records preserve the frozen `train` / `abstain` allocation, the
`eg-abstain-unapproved-neighboring-oecd-scope` evidence group, and the `kv-core-abstain-02`
parallel group. The pair binds no document or data units and carries no tool expectations and no
reference answer — only a language-matched abstention reason. Both questions ask for Korea's OECD
normalised CLI value for May 2026 using only the vintage available as of 2026-07-09; that
neighboring measure lies outside the sole owner-approved OECD raw-data scope (Korea's monthly
amplitude-adjusted CLI, `KOR.M.LI_AA.IX._T`, ADR 0007), so the gold behavior is abstention on the
missing rights basis. The abstention reasons name the approved scope, forbid substituting the
approved series or exposing an unapproved observation, and leak no observation value; the focused
tests assert the serialized records contain neither `102.66` nor the CLI source/ledger IDs. The
2026-07-09 cutoff is deliberately one where the approved amplitude-adjusted scope does resolve
(edition `202607`, value `102.66`), and a focused contrast test proves the drafted abstention is
rights-driven, not availability-driven. This is the second abstain pair after
`kv-core-abstain-01` and the first authored pair whose fail-closed basis is a rights boundary
rather than the availability ledger. The matrix, approved core, source bundle, rights decisions,
13 public schemas, five committed traces, and runtime source are unchanged. At that checkpoint,
the approved count remained 12/40; of the other 28 unapproved slots, these two were pending
drafts and 26 remained unauthored.

On 2026-08-26, Hyungbae Cho approved the unchanged Korean/English pair. Approval feature commit
`4c29b1d` moves the two records to `data/benchmark/core/core-batch-006.jsonl`, records reviewer
`Hyungbae Cho` and aware review timestamp `2026-08-26T01:49:45Z`, and replaces only the lifecycle
tag `draft-006` with `batch-006`. The questions, abstention reasons, cutoff, route, split,
evidence group, and parallel-group binding are unchanged from `c20619d`, and the annotations
preserve the AI author `Claude AI draft`. At that approval checkpoint, the approved core was
14/40, the remaining 26 slots were unauthored and unapproved, and no draft was pending. This
approval makes `kv-core-abstain-02` the second approved abstain pair after `kv-core-abstain-01`
and the first approved pair whose fail-closed basis is a rights boundary rather than the
availability ledger. The matrix, source bundle, rights decisions, 13 public schemas, five
committed traces, and runtime source remained unchanged.

The approval transition passed 45 focused benchmark tests across six files and the full
1,153-test suite with 100% SovereignLab statement/branch coverage (4,679 statements, 1,568
branches) under a fresh OS `--basetemp`; Ruff check and format check passed across 75 Python
files. The repository `.pytest_tmp` directory and ACL were untouched, and the slice cost $0.00.

### Completed `kv-core-abstain-03` draft and owner-approval slices

Functional commit `77d247d` adds exactly `kv-core-abstain-03-ko` and `kv-core-abstain-03-en` at
`status=draft` in `data/benchmark/drafts/core-draft-007.jsonl`, together with six focused tests.
Both records preserve the frozen `train` / `abstain` allocation, the
`eg-abstain-korean-cpi-revision-false-premise` evidence group, and the `kv-core-abstain-03`
parallel group. The pair binds no document or data units and carries no tool expectations and no
reference answer — only a language-matched abstention reason. Both questions rest on the false
premise that the many archived OECD editions of Korea's consumer price index prove the Korean CPI
was revised just as many times, and ask for before-and-after November 2019 CPI values using only
the vintage available as of 2026-07-17. The gold behavior is to reject the premise and abstain:
archived edition counts measure archive coverage, not actual revisions, and KOR-RTD holds no
owner-approved raw-data decision for the OECD Korea CPI revision series — raw OECD observations
outside the sole approved Korea monthly amplitude-adjusted CLI scope (`KOR.M.LI_AA.IX._T`) remain
metadata-only — so no before-and-after CPI observation can be served, and the system must not
fabricate revision values or expose an unapproved observation. The focused tests additionally
prove that the rights catalog's only OECD decision is the approved CLI scope, that the serialized
records leak no observation value and no snapshot identifier, and that the only approved CPI
evidence in KOR-RTD (the KOSIS latest-only snapshot) carries `vintage_semantics=latest_only`, so
committed evidence cannot serve any CPI revision by construction. This is the third authored
abstain pair after `kv-core-abstain-01` and `kv-core-abstain-02` and the first false-premise
rejection pair. The matrix, approved core, source bundle, rights decisions, 13 public schemas,
five committed traces, and runtime source are unchanged. At that checkpoint, the approved count
remained 14/40; of the other 26 unapproved slots, these two were pending drafts and 24 remained
unauthored.

On 2026-08-26, Hyungbae Cho approved the unchanged Korean/English pair. Approval feature commit
`5e14119` moves the two records to `data/benchmark/core/core-batch-007.jsonl`, records reviewer
`Hyungbae Cho` and aware review timestamp `2026-08-26T07:34:50Z`, and replaces only the lifecycle
tag `draft-007` with `batch-007`. The questions, abstention reasons, cutoff, route, split,
evidence group, and parallel-group binding are unchanged from `77d247d`, and the annotations
preserve the AI author `Claude AI draft`. At that approval checkpoint, the approved core was
16/40, the remaining 24 slots were unauthored and unapproved, and no draft was pending. This
approval makes `kv-core-abstain-03` the third approved abstain pair after `kv-core-abstain-01`
and `kv-core-abstain-02` and the first approved false-premise rejection pair. The matrix, source
bundle, rights decisions, 13 public schemas, five committed traces, and runtime source remained
unchanged.

The approval transition passed 51 focused benchmark tests across seven files and the full
1,159-test suite with 100% SovereignLab statement/branch coverage (4,679 statements, 1,568
branches) under a fresh OS `--basetemp`; Ruff check and format check passed across 76 Python
files. The repository `.pytest_tmp` directory and ACL were untouched, and the slice cost $0.00.

### Completed `kv-core-abstain-04` draft slice — named human review only

Functional commit `fd7640b` adds exactly `kv-core-abstain-04-ko` and `kv-core-abstain-04-en` at
`status=draft` in `data/benchmark/drafts/core-draft-008.jsonl`, together with six focused tests.
Both records preserve the frozen `dev` / `abstain` allocation, the `eg-abstain-missing-as-of`
evidence group, and the `kv-core-abstain-04` parallel group; this is the second `dev`-split pair
after `kv-core-data-04`. The pair binds no document or data units and carries no tool
expectations and no reference answer — only a language-matched abstention reason. Both questions
ask for Korea's OECD amplitude-adjusted CLI value for May 2026 using the vintage available at the
time, while omitting the as-of date the vintage request depends on; the record-level `as_of`
field is `2026-07-17`. The gold behavior is to ask for the missing as-of and abstain: a vintage
answer depends on its as-of cutoff, and KOR-RTD's fail-closed contract never executes without an
explicit `effective_as_of` and never guesses or defaults the cutoff, because an assumed cutoff
can expose the wrong vintage and create temporal leakage. The focused tests additionally prove
that the questions contain no as-of phrase while both abstention reasons demand an explicit
`effective_as_of`, that the serialized records leak no observation value and no snapshot or
ledger identifier, and that a contrast test resolves the same request once an explicit cutoff of
`2026-07-09` is supplied (edition `202607`, value `102.66` from the owner-approved CLI scope) —
so the drafted abstention is missing-cutoff-driven, not availability- or rights-driven. This is
the fourth authored abstain pair after the approved `kv-core-abstain-01`, `kv-core-abstain-02`,
and `kv-core-abstain-03`, and the first missing-as-of clarification pair. The matrix, approved
core, source bundle, rights decisions, 13 public schemas, five committed traces, and runtime
source are unchanged. The approved count remains 16/40; of the other 24 unapproved slots, these
two are pending drafts and 22 remain unauthored.

The exact continuation order is therefore:

1. Review only `kv-core-abstain-04-ko` and `kv-core-abstain-04-en` against the frozen matrix and
   the fail-closed `effective_as_of` execution contract.
2. Do not mark either record approved, move it into `core/`, or raise the approved count without
   an explicit named human decision. Stop after recording that decision and a green full baseline;
   do not select or author another pair.
3. Preserve the frozen matrix, approved core, source, rights, schema, trace, and runtime boundaries;
   do not begin provider/live-model integration, probes, paid work, or the deferred bounded loop.

Open operational check, not an M2 blocker: manually dispatch one append-only secret-backed
workflow smoke only after separate owner authorization; otherwise let the weekly schedule exercise
the configured secrets.

## 6. What not to redo

- Do not rebuild or rename the 40-record matrix, the approved four-record first batch, the approved
  two-record documentary batch, the approved two-record ECOS GDP third batch, the approved
  two-record ECOS current-account fourth batch, the approved two-record KOSIS CPI fifth batch, the
  approved two-record OECD scope abstention sixth batch, or the approved two-record CPI revision
  false-premise abstention seventh batch.
- Do not re-author or pre-approve the two `kv-core-abstain-04` missing-as-of abstention drafts,
  or select a later pair before their separate named human review is complete.
- Do not re-author or re-review the approved `kv-core-abstain-03` CPI revision false-premise
  abstention pair; its separate named human review is complete.
- Do not redo the first real BOK document manifests, revert their ADR 0009 `allowed` conclusion, or
  merge full-document/corpus ingestion into the completed GDP authoring or approval units.
- Do not replace the retrieval baseline with embeddings yet. Its filter-before-scoring invariant
  and synthetic future-document regression are already complete.
- Do not rerun the paid QLoRA compatibility spike. It passed, all Pods were deleted, and it is not
  a model-quality result.
- Do not manually dispatch the secret-backed harvester as part of onboarding.
- Do not revise the now-frozen snapshot gold convention or combine dependent benchmark authoring
  with the runtime-adapter slice.
- Do not replace the planner, dispatcher, assembler, or executor boundaries; expose their private
  recording, assembly, or execution internals as public wrappers/schemas; or merge provider/live
  integration into an unselected future slice.
- Do not reopen accepted ADRs 0003–0009 without new evidence that requires a superseding decision.
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
