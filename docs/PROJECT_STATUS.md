# SovereignLab project status

- Last updated: 2026-08-27
- Owner: Hyungbae Cho (`bwade9090`)
- Delivery window: four weeks, approximately 80 hours
- Current milestone: M2 — week-2 benchmark and baselines (charter v2.5 §7, Week 2)
- Overall state: source-rights policy, two ECOS plus exact KOSIS CPI and OECD CLI rulings, strict
  append-only rights catalogs,
  the edition-availability decision, the owner-authored employer-risk review (ADR 0006), and the
  implemented contract unit — `EditionAvailabilityLedger` 1.0.0, evidence/benchmark `2.0.0`, typed
  manifest-rights link — plus the offline fail-closed as-of resolver and weekly append-only
  harvester implementation are complete. Real append-only ECOS/KOSIS forward snapshots and the
  one-time OECD Korea CLI revision archive now validate against their manifests and rights
  decisions. The harvester is on the default branch, so the key-free OECD metadata schedule is
  active. Repository `ECOS_API_KEY` and `KOSIS_API_KEY` Actions secrets are configured; the first
  manually dispatched secret-backed run remains an optional separately authorized operational
  check. Number-normalization 1.0.0, the zero-cost QLoRA preflight, and the paid A40/CUDA 13
  one-step compatibility run are complete. The M1b week-1 gate passed on 2026-07-18. In M2, the
  40-record core authoring allocation and the first eight core batch files are owner-approved.
  The approved human-reviewed core count is 18/40: the first four data/abstention records, the
  first Korean/English documentary pair, the `kv-core-data-02` Korean/English ECOS GDP pair in
  `data/benchmark/core/core-batch-003.jsonl`, the `kv-core-data-03` Korean/English ECOS
  current-account pair in `data/benchmark/core/core-batch-004.jsonl`, the `kv-core-data-04`
  Korean/English KOSIS CPI pair in `data/benchmark/core/core-batch-005.jsonl`, the
  `kv-core-abstain-02` Korean/English OECD scope abstention pair in
  `data/benchmark/core/core-batch-006.jsonl`, the `kv-core-abstain-03` Korean/English CPI
  revision false-premise abstention pair in `data/benchmark/core/core-batch-007.jsonl`, and the
  `kv-core-abstain-04` Korean/English missing-as-of abstention pair now in
  `data/benchmark/core/core-batch-008.jsonl`. The `kv-core-abstain-05` Korean/English ledger
  frontier abstention pair is complete at `status=draft` in
  `data/benchmark/drafts/core-draft-009.jsonl` and awaits named human review. The other 22
  matrix slots remain unapproved: two are the pending drafts and 20 are unauthored. The offline
  bilingual temporal document retriever is now
  implemented with manifest-bound chunks and publication-date filtering before scoring; only
  synthetic fixtures were used. The first real bilingual document-manifest unit is also complete:
  the Korean May 2026
  Bank of Korea outlook is independently dated 2026-05-28 and the later English full translation
  2026-06-30; both official PDFs were captured only under `/tmp` for real byte-size/SHA-256
  measurement. Their landing pages supplied no publication-specific KOGL label, but the owner
  confirmed that the official Economic Outlook family is public data freely usable without a
  separate procedure under the Bank of Korea copyright policy's Public Data Act Article 19 branch.
  ADR 0009 and charter v2.5 correct both manifests to `allowed`, with Bank of Korea attribution,
  transformation disclosure, and separately marked third-party rights preserved. No report body,
  extracted text, or real searchable chunk is committed by repository-scope choice. The first
  documentary pair uses stable, language-matched locators to the same stated driver while preserving
  the Korean report's 2026-05-28 cutoff and the English translation's later 2026-06-30 cutoff.
  On 2026-07-28 the owner also approved ADR 0008 and charter v2.4. Its first implementation slice
  is now complete: execution contract 1.0.0 freezes the bilingual request, four-route plan,
  exactly three typed calls/results, evidence packet, replay provenance, trace invariants, and
  `read_snapshot_as_of` six-field gold arguments; six new schemas bring the public total to 13.
  The second implementation slice is also complete: a trusted, digest-linked latest-only registry
  and deterministic `read_snapshot_as_of` adapter now validate the three committed ECOS/KOSIS
  scopes through cutoff, manifest, rights, hash, provider-row, and normalization gates. The third
  implementation slice is now complete as well: the trusted exact-byte synthetic retrieval
  registry and typed `retrieve_temporal_documents` adapter preserve filtering before scoring,
  deterministic replay, and selected-evidence-only results. The fourth implementation slice is
  now complete too: the digest-linked historical STES registry and typed flat adapter preserve
  ledger-first selection, the exact approved CLI rights boundary, selected-row-only
  normalization, and sanitized GDP raw-evidence abstention. The fifth implementation slice is now
  complete: the frozen three-tool callable registry and explicit dispatcher bind the exact typed
  schemas and committed dependency digests, independently replay every call through its frozen
  reference adapter, compare the complete typed result, and revalidate the selected dependency
  immediately before return. The sixth implementation slice is now complete: the offline one-shot
  planner protocol and scripted/immutable recorded-replay implementations validate exact candidate
  bytes, preserve digest-linked provenance, and bind every typed call back to the request before
  dispatch. The seventh implementation slice is now complete: the internal deterministic
  evidence-packet assembler strictly revalidates the request, plan, and ordered typed results;
  preserves all four routes, exact cutoff/call/result bindings, ordered and repeated evidence, and
  planned/tool abstention; and returns only the frozen `ExecutionEvidencePacket` without partial
  evidence. The eighth implementation slice is complete: the private offline executor invokes the
  existing planner once, dispatches validated calls in order through the frozen registry, stops on
  the first abstention or error, assembles only eligible packets, and returns the existing strict
  `ExecutionTrace` with real executor/registry/corpus and planner provenance. The ninth
  implementation slice is also complete: five committed machine-readable real-digest end-to-end
  replay traces are generated only through the real private executor, `ScriptedPlanner`, and
  committed registry/corpus boundaries. They cover all four routes, all three tools, Korean and
  English, explicit and implicit cutoffs, complete execution, planned abstention, and terminal tool
  abstention without partial evidence. Work unit C and its first nine ADR 0008 slices are complete,
  so the shipped minimal offline path may now be described exactly as **typed function calling with
  committed traces**. Provider/live-model integration remains absent, and the bounded tool loop
  remains deferred to post-window v1.1.

## Approved baseline

- Product direction: **K-VINTAGE on KOR-RTD** (charter v2.5; source-rights and
  edition-availability amendments approved 2026-07-16–17; execution-contract amendment approved
  2026-07-28; BOK Economic Outlook public-data rights amendment approved 2026-07-28; core rationale
  in `docs/discovery/01_concept_upgrade_proposal.md`; decisions recorded as ADRs 0003–0009).
  - KOR-RTD: point-in-time data layer — OECD edition-history consolidation + weekly append-only forward-capture harvester for the latest-only ECOS/KOSIS APIs.
  - K-VINTAGE: two-tier bilingual benchmark (40 human-reviewed core + 200–300 machine-generated
    data-route probes, always reported separately) with regenerable point-in-time gold answers and a
    public script. Accepted ADR 0005 replaces the charter's original
    `max(EDITION <= as_of)` shorthand with edition-level availability evidence and fail-closed
    resolution; ledger selection and the manifest-bound selected-row resolver are implemented.
  - The briefing pipeline remains as reference implementation and four-variant public baseline suite; temporal-leakage rate is the headline metric.
- Evaluation contract: 40 reviewed Korean/English core questions across `documents`, `data`, `documents_and_data`, and `abstain` (unchanged) + tier-2 probes.
- Fine-tuning plan: Ministral 3 3B QLoRA first, documented Mistral 7B/Nemo fallback; hyperparameter matrix capped at 2–3 configurations.
- Initial spend ceiling: USD 100.
- Repository: public at `https://github.com/bwade9090/sovereignlab`.

## Completed

- Role-gap analysis and project selection (`docs/discovery/00_role_gap_analysis.md`).
- Charter v1; reproducible Python 3.12 foundation; M0 offline validation; public repo on `main`.
- M1a evidence schema contract: strict `SourceManifest`, `BenchmarkRecord`, `BenchmarkBundle` (Pydantic v2, `extra="forbid"`), synchronized public JSON Schema + synthetic fixtures, temporal-cutoff and split-leakage checks, ADR 0002, 45 tests at 100% statement/branch coverage.
- **Concept reorientation (2026-07-14):** multi-agent study of novelty/value gaps; proposal `docs/discovery/01_concept_upgrade_proposal.md` approved in full by Hyungbae; charter rewritten to v2; ADR 0003 recorded; AGENTS.md mission and evidence rules updated; CV bullet bank rewritten; README updated.
- **Source-rights amendment (2026-07-16):** charter v2.1 and ADR 0004 replace the unverified
  KOGL-only premise with official producer/category and attribution mappings. The owner confirmed
  the non-commercial project profile and approved `allowed` rulings for `200Y108/10601` and
  `301Y017/SA000`.
- **Standalone rights catalog 1.0 (2026-07-16):** strict `RightsInstrument`,
  `SeriesRightsDecision`, and `RightsCatalog` models; official-evidence and operation-status
  invariants; synchronized public JSON Schemas and synthetic fixtures; append-only owner-approved
  catalog metadata under `data/rights/`. Existing `SourceManifest`/benchmark 1.0 contracts remain
  unchanged and no observation payload was added.
- **Edition-availability decision (2026-07-16):** ADR 0005 and charter v2.2 approve an immutable
  availability ledger, `Asia/Seoul` inclusive end-of-day semantics, a fail-closed resolver,
  evidence/benchmark contract `2.0.0`, and the narrow ADR 0002/0003 supersessions. The owner also
  approved OECD `metadata_only pending dataset-specific and third-party-rights confirmation`.
  These are governance outcomes only; the ledger, resolver, parser, migration, and manifest link are
  not implemented in this handoff.
- **Employer-risk review (2026-07-17):** ADR 0006 records the owner's verbatim answers covering
  workplace rules, disclaimers, the public harvester, automated release notes, Bank of Korea
  branding, and the Git-history workstation path. Outcomes: proceed unchanged; a single English
  personal-capacity disclaimer added to the README; no history rewrite (the remediation question is
  closed); charter §9's release-note labeling rule remains in force. The sole owner-authored week-1
  artifact is complete.
- **Contract 2.0.0 + availability ledger 1.0.0 (2026-07-17):** accepted ADR 0005 implemented as one
  work unit (`docs/project/05_evidence_contract_2_0_migration.md`): strict
  `EditionAvailabilityLedger` with the four approved evidence bases, UTC canonical instants,
  window/evidence equality invariants, `Asia/Seoul` end-of-day cutoff computation, ADR 0005 state
  derivation, and structured fail-closed edition selection; `SourceManifest` 2.0.0 with
  `vintage_semantics` and the typed `rights_decision` link (required for `allowed` data snapshots);
  `BenchmarkRecord` 2.0.0 with per-tool-expectation vintage evidence; `BenchmarkBundle` 2.0.0
  cross-validating ledgers, rights links, and gold vintages against ledger-resolved selections while
  keeping the 1.0 cutoff rule for documents and latest-only sources. A 23-agent adversarial review
  then confirmed and closed seven findings before commit: superseded catalogs/ledgers can no longer
  authorize links or vintages, one series scope cannot span multiple active bundled catalogs,
  rights expiry compares instants (`valid_until` inclusive through end-of-day `Asia/Seoul`)
  independent of serialization offset, conservative publisher-date evidence survives DST gaps via
  UTC-instant comparison, calendar overflows raise validation errors instead of raw
  `OverflowError`, the ADR-mandated mid-day-capture/same-day-cutoff and `complete_through`
  boundary tests were added, and the edition-inventory-must-match-constraint rule is disclosed as
  an operational harvester obligation. Rights contracts stay 1.0.0 byte-identical; v1 evidence
  schemas removed (history preserves them); 226 tests at 100% statement/branch coverage. No real
  ledger, manifest, or observation was committed.
- **Offline fail-closed as-of resolver (2026-07-17):** `sovereignlab.vintage` adds strict STES
  query/result types, exact case-sensitive SDMX-CSV code-column parsing (including safe coexistence
  of `MEASURE`/`Measure`), manifest byte-size/SHA-256 verification, canonical URL-to-ledger
  `agency:dataflow` and explicit-version joining, ledger-first selection, and selected-row-only
  evidence packets. Missing, duplicate, or blank selected rows; malformed CSV; unverifiable or
  mismatched dataflows; content mismatch; unsupported source semantics/media; incomplete ledger
  frontiers; and calendar overflow all return structured abstentions without edition codes or
  values. Synthetic tests prove later rows never appear in success or abstention output. A
  temporary, uncommitted official-response regression reproduced the previously recorded GDP
  response hash and selected `202607` for `as_of=2026-07-09`, returning only the verified raw XDC
  value `574984300000000`; the CPI response again contained 258 editions (`200502`–`202607`) with
  its recorded hash. The temporary response files were deleted. This check also found and fixed a
  ledger-schema bug: real OECD constraint IDs contain `@`, so `constraint_id` now uses the approved
  SDMX artefact-reference pattern; the public schema and synthetic fixture were regenerated. No
  real ledger, manifest, or observation was committed.
- **Weekly append-only harvester + first real ledger (2026-07-17):**
  `sovereignlab.harvest.weekly` and `.github/workflows/weekly-harvest.yml` implement a weekly and
  manually dispatchable capture. Every run joins the key-free OECD exact-availability and content
  constraints, validates the canonical STES dataflow/version and identical mechanically derived
  edition inventories, creates checksummed `SourceManifest` 2.0.0 records, advances an immutable
  availability ledger monotonically, verifies all referenced historical bytes, and refuses an
  existing path before writing. The initial committed capture contains 330 edition codes
  (`199902`–`202607`): only `202607` is resolved, with
  `available_by=2026-07-08T09:33:35.737Z`; the other 329 codes remain unresolved rather than being
  backfilled. Its two XML artifacts are constraint metadata without observations and carry the
  owner-approved `metadata_only` policy. Optional ECOS capture is restricted in code to the two
  owner-approved scopes (`200Y108/10601`, `301Y017/SA000`), validates the rights catalog via
  `BenchmarkBundle`, sanitizes the key from committed URLs, and skips explicitly when no key is
  configured. At that capture, no KOSIS scope had an owner-approved exact-series ruling and neither
  the local nor GitHub environment had `ECOS_API_KEY`, so it intentionally contained no raw
  observation. ADR 0007 and the later capture below supersede that operational state.
- **ADR 0007 exact-scope activation + first observation captures (2026-07-17):** the owner approved
  KOSIS national monthly total CPI `101/DT_1J22003/T/T10` and OECD Korea monthly
  amplitude-adjusted CLI revision series
  `DSD_STES_REVISIONS@DF_STES_REVISIONS/KOR.M.LI_AA.IX._T`. Charter v2.3 and a new append-only
  rights catalog preserve the two ECOS decisions and narrowly supersede the OECD metadata-only
  ruling for that single first-party series. The weekly harvester now validates and captures the
  KOSIS scope when `KOSIS_API_KEY` exists; local ECOS/KOSIS keys produced real snapshots of 265
  quarterly GDP rows (`1960Q1`–`2026Q1`), 557 monthly current-account rows
  (`198001`–`202605`), and 738 monthly CPI rows (`196501`–`202606`). A separate one-time/manual
  CLI capture stored 75,060 rows, 239 editions (`200604`–`202607`), and periods
  `1990-01`–`2026-06` in a 21,734,727-byte consolidated CSV. All four observation artifacts pass
  typed rights-bundle, byte-size, and SHA-256 validation. A real resolver check selected only
  edition `202607`, period `2026-05`, value `102.66` for `as_of=2026-07-09`. A repository-wide
  secret comparison confirmed neither local key appears in tracked or untracked publishable files.
- **Number-normalization specification 1.0.0 (2026-07-17):**
  `docs/project/06_number_normalization_spec.md` and `sovereignlab.normalization` freeze
  exact-`Decimal` parsing, case-sensitive exact-scope rule selection, source-string preservation,
  Korean 원/백만원/억원/십억원/조원 powers-of-ten conversions, explicit canonical units,
  `ROUND_HALF_UP` presentation, and half-one-displayed-unit grading tolerance. The verified OECD
  GDP XDC example maps by `10^-9` to billion KRW; neighboring GDP/CLI variants fail closed. Five
  exact MVP rules cover the two approved ECOS series, KOSIS national CPI, OECD Korea CLI, and the
  verified OECD quarterly real-GDP revision series. Rights approval remains a separate gate.
- **Ministral 3 QLoRA zero-cost preflight (2026-07-17):** an isolated spike under
  `experiments/qlora/` pins the public BF16 checkpoint
  `mistralai/Ministral-3-3B-Instruct-2512-BF16` at commit
  `b6d637bef2393152b3da2b2fde72eecdee30557e` plus direct GPU dependencies. The free preflight
  verifies public/ungated state, Apache-2.0 model-card license, architecture and text/vision
  dimensions, required Hub files, and four synthetic bilingual route examples without downloading
  weights. The paid harness uses NF4 double quantization, language-model-only all-linear LoRA,
  exactly one optimizer step, finite/nonzero-gradient checks, adapter-change verification, and
  adapter-only safetensors output. Local preflight passed; the separately recorded paid result
  below subsequently closed the compatibility gate.
- **Ministral 3 QLoRA paid GPU compatibility (2026-07-18):** the pinned harness passed on a
  RunPod Secure Cloud NVIDIA A40 (46,068 MiB), driver 580.159.04, CUDA 13.0, and Python 3.12.3.
  `torch 2.13.0+cu130`, `transformers 5.14.1`, `peft 0.19.1`, and `bitsandbytes 0.49.2` loaded the
  public BF16 checkpoint, attached language-model-only NF4/all-linear LoRA, and completed exactly
  one optimizer step in 23.439 seconds. The finite loss was `5.192200660705566`; 12,353,536
  parameters were trainable; peak CUDA allocation was 4,210,338,304 bytes; and the 49,474,005-byte
  output contained only `adapter_config.json`, `adapter_model.safetensors`, and the generated
  adapter README. The adapter and base-model cache stayed on the disposable Pod and were deleted.
  Provisioning preserved three negative operational findings: a custom image without a suitable
  startup/template path never reached container uptime; RunPod's dedicated SSH key must exist
  before Pod creation; and the pinned PyTorch wheel requires a host created with minimum CUDA 13.0.
  Installing the virtual environment on the container disk rather than the network-mounted
  `/workspace` removed severe metadata-I/O delay. All attempted Pods were deleted, the account
  returned to `$0` current hourly spend, and finalized RunPod billing was
  `$0.23584524099715054`.
- **Core authoring matrix + first approved batch (2026-07-24–25):**
  `CoreAuthoringMatrix` 1.0.0 freezes 20 bilingual pairs/40 records with exactly ten records per
  route, 20 Korean/20 English, and train/dev/test counts of 24/8/8. The contract rejects a planned
  source release or snapshot assigned across splits. On 2026-07-25, Hyungbae Cho approved the
  unchanged matrix and all four initially AI-authored records: one Korean/English OECD CLI data
  pair resolves edition `202607`, May-2026 value `102.66` as of 2026-07-09; one Korean/English pair
  abstains for 2026-06-30 because no edition is definitely available. Their annotations preserve
  the AI author and record the named human reviewer and timestamp. Real manifest/ledger/rights
  bundle validation, resolver replay, exact normalization, and the earlier-cutoff abstention are
  covered offline. The held-out data slot remains reserved until an independently captured
  approved release exists.
- **Offline bilingual temporal document retrieval (2026-07-28):**
  `sovereignlab.retrieval` adds strict corpus/query/result types and deterministic BM25-style
  lexical retrieval for Korean and English. Chunks must match a document manifest's ID, language,
  and SHA-256. The retriever removes other-language and post-`as_of` manifests before selecting
  chunks, building document frequencies, computing average length, or scoring. Synthetic fixtures
  place unusually strong matches after the cutoff; regression tests prove the full-corpus result,
  including scores, equals the result after those future documents are physically removed.
  Inclusive publication dates, stable limits, empty/no-overlap results, and every corpus-binding
  rejection are covered. No official document body, network request, paid embedding, OCR, or model
  call was used.

- **First real bilingual document manifests (2026-07-28):** the official May 2026 Bank of Korea
  outlook pages independently establish the Korean report at `2026-05-28` (`nttId=10098209`) and
  the English full translation at `2026-06-30` (`nttId=11062493`). Direct official attachment
  captures under `/tmp` measured the Korean PDF at 10,711,393 bytes / SHA-256
  `71f78145d30190ea6bb7e2eb3bdb919c1ae4730973d1f63bed641ec12660fd97` and the English
  PDF at 3,711,417 bytes / SHA-256
  `c30dd8fae88ba62db18b38484985aad457f658a22a899de58918d7581465986d`. Neither page
  carried a publication-specific KOGL label. The first commit provisionally treated that absence
  as `metadata_only`; the owner then supplied the exact source-family classification that official
  Bank of Korea Economic Outlook publications are Article 19 public data freely usable without a
  separate procedure. ADR 0009 and charter v2.5 therefore correct both strict manifests to
  `allowed`, subject to Bank of Korea attribution, modification/processing/transformation
  disclosure, and separately marked third-party rights. Their PDFs and extracted text remain
  absent from Git by repository-scope choice. Offline tests bind the manifests to the retriever,
  prove the later English date is enforced independently, assert the approved rights basis, and
  prove manifests alone create no searchable content. Full metadata, the initial negative finding,
  and the superseding conclusion are preserved in
  `docs/discovery/04_bok_outlook_2026_05_manifest_log.md`.

- **BOK Economic Outlook public-data rights correction — ADR 0009 / charter v2.5 (2026-07-28):**
  the owner confirmed that the official Korean Economic Outlook publication family and official
  English full translations are public data under the Bank of Korea copyright policy's Public Data
  Act Article 19 branch and may be used without a separate procedure. The public-data portal web
  view did not expose an individual report-family row during verification; that interface result
  is retained as a limitation rather than promoted into a contrary rights conclusion. The ruling
  does not fabricate a KOGL type, does not authorize adjacent publication families or separately
  marked third-party content, and does not change the project's non-commercial profile.

- **First bilingual documentary pair (drafted 2026-07-28; approved 2026-07-29):**
  `data/benchmark/core/core-batch-002.jsonl` contains exactly the frozen `kv-core-doc-01`
  Korean/English pair at `status=approved`. The Korean
  record cites PDF page 10 (`요약 4/10`) at `as_of=2026-05-28`; the English record cites PDF page 9
  (printed page `v`) at `as_of=2026-06-30`. Both paraphrase the report's stated
  stronger-than-expected IT export contribution of `+0.7%p` to the `0.6%p` upward revision,
  identify the Bank of Korea as the source, and disclose summarization/paraphrase. The official
  PDFs were re-fetched into a temporary directory, matched the committed sizes and SHA-256 values,
  and the cited pages were rendered and visually checked. No PDF, extracted full text, or real
  searchable chunk entered Git. Offline tests validate the pair against the strict manifests and
  frozen matrix, enforce the independent publication cutoffs and language match, reject both
  evidence-group and parallel-group split leakage. Hyungbae Cho approved both records without a
  substantive record or matrix change; the annotations now record the named reviewer and aware
  review timestamp. At that 2026-07-29 checkpoint, the approved count became 6/40.

- **Execution-contract adjustment — ADR 0008 and charter v2.4 (2026-07-28):** the owner asked
  whether the plan could also build agent-orchestration (tool/function calling, multi-step)
  experience. A four-lens review (governance, technical, schedule, portfolio) with two
  adversarial verification passes was run against the repository; key verified findings: only
  `kv-core-data-01`/`kv-core-both-01` (both train) exercise the vintage resolver, so a loop
  ablation has no dev/test slice; abstain records cannot carry tool expectations under contract
  2.0.0; six of ten data-bearing matrix pairs need a not-yet-built latest-only snapshot-read
  tool; no router/model-call/replay harness exists; trajectory-level leakage is structurally
  zero over the fail-closed tools; and the week-2 gate stood at the cut-ladder boundary. The
  owner accepted the recommendation in full: implement the minimal path as a typed
  function-calling artifact (model-emitted typed plan and tool calls against pydantic-derived
  schemas, deterministic execution, committed traces, recorded/replayable model interface,
  three-tool surface), defer the bounded multi-step loop to post-window v1.1 as an
  execution-mode ablation, keep the single-shot LoRA target and contract 2.0.0, and reserve
  agent/orchestration wording for the evaluated v1.1 loop. Recorded as ADR 0008 with charter
  v2.4 (§§3, 7, 12); AGENTS.md, the README milestone text, the handoff, the decisions index, and
  the CV wording-bank guard rule were synchronized. Documentation only; no source or test file
  changed.

- **Typed execution/trace contract 1.0.0 — work unit C slice 1 (2026-07-29):**
  `sovereignlab.schemas.execution` freezes an independent strict request/plan/call/result/packet/
  trace boundary without changing `BenchmarkRecord` or `BenchmarkBundle` 2.0.0. The route plan
  preserves all four routes and exposes exactly `retrieve_temporal_documents`,
  `resolve_stes_as_of`, and `read_snapshot_as_of`; calls cannot select paths, manifests, ledgers,
  bytes, source IDs, or credentials. The snapshot gold convention has exactly six flat fields
  and cross-binds the three owner-approved ECOS/KOSIS units, provider-native frequency, and frozen
  normalization rule. STES calls/results likewise bind the two frozen Korea normalization units.
  Evidence validates exact decimal normalization and Asia/Seoul cutoff-safe capture time; traces
  bind ordered results and abstentions to calls and digest-link the executor, tool registry,
  artifact registry, retrieval corpus, and recorded planner output. Six new deterministic JSON
  Schemas bring the public total from seven to 13. The committed round-trip trace fixture uses
  synthetic documentary text and explicitly illustrative environment hashes; it is a contract
  fixture, not an end-to-end executor result. An adversarial read-only review's confirmed findings
  were closed before schema export. Full details and the two-stage JSON-Schema-then-Pydantic
  validation boundary are in `docs/project/09_typed_execution_trace_contract.md`.

- **Trusted latest-only snapshot registry/reader — work unit C slice 2 (2026-07-29):**
  `sovereignlab.snapshots` explicitly registers only the three already committed owner-approved
  ECOS/KOSIS captures and keeps paths, manifests, catalogs, raw bytes, capture IDs, and hidden
  KOSIS selectors outside model arguments. Its canonical, order-independent descriptor binds the
  exact scope definitions, manifest/archive hashes and sizes, and rights catalog hashes; the
  current descriptor SHA-256 is
  `67ebecf0aa15b5a2d53aff737cd28bd8779e3993abebca9e6c3d840f2006aa5b`.
  The canonical loader verifies and freezes the exact manifest, catalog, and archive bytes behind
  that digest. `read_snapshot_as_of` then applies `published_on` and inclusive Asia/Seoul retrieval
  cutoffs before parsing only the selected immutable payload, rejects ambiguous latest frontiers,
  validates active rights and manifest/content integrity, parses exact ECOS/KOSIS scopes and raw
  units, and emits only the selected normalized observation. A corrupt or missing newest eligible
  capture never falls back to an older one. Known evidence gaps return stable sanitized
  abstentions; harness or unexpected implementation failures are sanitized at their respective
  boundaries. The public schema count stays 13; full details are in
  `docs/project/10_snapshot_reader_contract.md`.

- **Trusted temporal-document registry/adapter — work unit C slice 3 (2026-07-29):**
  `sovereignlab.retrieval.registry` freezes the exact four-manifest/six-chunk synthetic corpus
  behind ID `synthetic-temporal-retrieval-corpus-v1` and descriptor SHA-256
  `823117ee29a191bc306843e44ccd9d37e063db79cc87e15dcb7f2a11f5b5bf7e`.
  The loader admits only two explicit repository-confined JSONL inputs and rejects path, size,
  count, UTF-8/JSON, duplicate-key, non-finite, and corpus-binding drift. Registry construction,
  descriptor calculation, and every adapter call reparse exact built-in immutable bytes and
  compare the complete corpus model. `execute_temporal_document_call` copies the four flat typed
  arguments unchanged, preserves language/cutoff filtering before scoring, validates every
  selected field against the registry, and requires exact equality with a fresh deterministic
  retrieval before emitting selected-match evidence. Empty matches abstain; corruption,
  fabricated evidence, and unexpected failures return stable sanitized errors. Query-feature
  ordering and 12-significant-digit score canonicalization make trace scores replay-stable. No
  official document body or real searchable chunk was added. Full details are in
  `docs/project/11_temporal_retrieval_adapter_contract.md`.

- **Trusted historical STES registry/adapter — work unit C slice 4 (2026-07-30):**
  `sovereignlab.vintage.registry` freezes the exact approved CLI archive, four constraint-support
  captures, two-generation availability-ledger chain, and two-generation rights-catalog chain
  behind ID `kor-rtd-stes-resolver-registry-v1` and descriptor SHA-256
  `103eb3bea7beebadeb0a7e193ff76fc95b518a8a7bed6825d9eb1f25431fb420`.
  Construction and each call reparse exact immutable bytes; semantic validation joins paired XML
  inventories and `validFrom` evidence to the ledgers, enforces connected append-only
  ledger/catalog chains, scans the full CSV for exact scope/keys/plain decimals, and
  cross-validates the active owner-approved CLI rights decision. `execute_stes_as_of_call` copies
  the eight flat arguments, requires exact equality with a fresh reference resolution, applies
  frozen Decimal normalization, and emits only selected typed evidence. The approved
  `as_of=2026-07-09`, `period=2026-05` regression returns edition `202607` and value `102.66`;
  the frozen GDP shape abstains before resolution because public raw evidence is unavailable.
  Full details are in `docs/project/12_stes_adapter_contract.md`.

- **Frozen callable registry/dispatcher — work unit C slice 5 (2026-07-30):**
  `sovereignlab.execution` registers exactly `retrieve_temporal_documents`,
  `resolve_stes_as_of`, and `read_snapshot_as_of` behind callable registry ID
  `sovereignlab-deterministic-tool-registry-v1` and descriptor SHA-256
  `cd00b5c543cffc53024f98b9fafa73ed3fecd519fde81a826d060c8af4d2ad91`.
  Composite artifact registry `kor-rtd-execution-artifact-registry-v1` binds the committed
  snapshot and STES registries behind descriptor SHA-256
  `7b42027c1034789bd46a881fd186f66ba1ba1250d94639ff5eed6c89a3cc2293`;
  the temporal corpus keeps its dedicated trace ID/digest pair. The dispatcher accepts only exact
  validated call models, injects only harness-owned dependencies, rejects raw/unknown/mismatched
  discriminators before execution, and never performs name-based callable lookup. Every call is
  independently replayed against a fresh original-call copy through the frozen reference adapter;
  the candidate receives a separate call copy, its call/result and selected dependency are
  revalidated after execution, and the dependency is checked again immediately before return.
  Temporary call or registry changes, result-comparison side effects, dependency
  replacement/corruption, and non-success substitution fail closed with sanitized call-bound
  errors. The prerequisite snapshot registry now also reparses exact built-in
  manifest/catalog/archive bytes and models on every call, closing timestamp, byte-subclass,
  binding, and call-ID mutation gaps. The public schema count remains 13. Full details are in
  `docs/project/13_callable_dispatcher_contract.md`.

- **Offline one-shot planner boundary — work unit C slice 6 (2026-08-02):**
  `sovereignlab.execution.planner` adds a minimal `Planner` protocol plus `ScriptedPlanner`,
  `RecordedPlanner`, and `ReplayPlanner` without adding a public result/provider-envelope/
  recording schema. Scripted plans freeze canonical candidate bytes and carry digest-linked
  provenance without a model ID. Recorded/replay planners resolve opaque IDs through a private
  harness-owned immutable registry, revalidate exact built-in bytes and SHA-256 on every call,
  require complete model metadata, strictly parse candidates as the existing `RoutePlan` 1.0.0,
  and preserve digest-linked provenance on invalid candidates. Before dispatch, every call cutoff
  is bound to `ExecutionRequest.effective_as_of`, and document calls preserve the request question
  and language exactly. Missing/tampered recordings, malformed JSON, duplicate keys/call IDs,
  extra fields, unknown/mismatched tools, inconsistent route shapes, and request drift fail closed
  with sanitized errors. No dispatcher, packet assembly, provider, source, benchmark, schema,
  live model, or paid operation was added. Full details are in
  `docs/project/14_offline_planner_contract.md`.

- **Deterministic evidence-packet assembler — work unit C slice 7 (2026-08-07):**
  Functional commit `ff96710` adds the private `sovereignlab.execution.assembler` boundary over
  one exact validated `ExecutionRequest`, its `RoutePlan` 1.0.0, and an immutable ordered tuple of
  typed tool results. The assembler strictly round-trips every input, reuses the frozen
  call/result validator, binds calls back to request cutoff/question/language, rejects non-prefix,
  reordered, mismatched, incomplete, erroneous, or drifted results, and strictly round-trips the
  final existing `ExecutionEvidencePacket` 1.0.0. Planned abstention reproduces the plan reason;
  terminal tool abstention produces an empty call-bound packet and never leaks earlier successful
  evidence; complete packets preserve exact result and payload order without global deduplication.
  The function and error remain private, public schemas remain at 13, and no planner, dispatcher,
  executor, trace fixture, provider, source, benchmark, live model, or paid operation was added.
  Full details are in `docs/project/15_evidence_packet_assembler_contract.md`.

- **Private offline executor — work unit C slice 8 (2026-08-11):**
  Functional commit `550b591` adds the private `sovereignlab.execution.executor` boundary over one
  exact validated request, explicit harness-owned trace metadata, the existing `Planner`, and the
  exact committed callable registry. It invokes the planner once, strictly revalidates the returned
  plan, dispatches calls once each in order, stops at the first abstention or error, skips assembly
  after tool error, and builds only the existing strict `ExecutionTrace` 1.0.0. Real executor,
  callable-registry, composite artifact-registry, retrieval-corpus, and planner provenance are
  rebuilt and rechecked before terminal return. Sanitized phase mapping preserves complete,
  planned/tool abstention, tool failure, planner/plan-validation failure, and eligible packet-
  assembly failure without partial packet evidence. The executor ID is
  `sovereignlab-offline-executor-v1`; its canonical 32-source descriptor digest is
  `08f45dab6a36a49cb7d0b588a69236942cd61534540bd4de0772010402dada64`. The function and error
  boundary remain private, public schemas remain at 13, and no committed end-to-end replay trace,
  provider/live-model call, source capture, benchmark record, GPU, network, or paid operation was
  added. Full
  details are in `docs/project/16_offline_executor_contract.md`.

- **Committed real-digest replay traces — work unit C slice 9 (2026-08-11):**
  Functional commit `883815b` adds five deterministic `ExecutionTrace` 1.0.0 artifacts under
  `traces/replay/v1/`, generated only by `scripts/export_execution_replay_traces.py` through the
  real private executor, `ScriptedPlanner`, frozen callable registry, composite artifact registry,
  and committed retrieval corpus. The matrix covers all four routes and all three tools across
  Korean/English and explicit/implicit cutoffs, with complete, planned-abstention, and terminal
  tool-abstention traces. The tool-abstention case records its successful prefix, leaves the trailing
  STES call unexecuted, and exposes no partial evidence packet. Healthy-stack tool- and packet-
  failure traces were intentionally not fabricated because runtime fault injection would not be
  bound by the real executor digest; those mappings remain covered by the strict executor and
  schema tests. The executor descriptor remains 32 canonical source entries with SHA-256
  `08f45dab6a36a49cb7d0b588a69236942cd61534540bd4de0772010402dada64`, and the public schema count
  remains 13. Work unit C is complete, and the minimal offline path is now **typed function calling
  with committed traces**. No provider/live-model integration, source capture, benchmark record,
  rights decision, public schema, network/GPU operation, or paid operation was added.

- **Windows baseline reproducibility repair (2026-07-29):** Windows now installs the IANA timezone
  database through the platform-guarded `tzdata==2026.3` requirement, which makes the existing
  `Asia/Seoul` tests and the new snapshot capture cutoff deterministic on a standard Python 3.12
  build. The four large ECOS invalid-response cases have short explicit pytest IDs, preventing
  `PYTEST_CURRENT_TEST` from exceeding Windows' 32,767-character environment-variable limit.
  Neither change alters Linux/macOS dependency resolution or test semantics.

- **Bilingual ECOS GDP draft pair (2026-08-19):** functional commit `f2d2523` adds exactly
  `kv-core-data-02-ko` and `kv-core-data-02-en` at `status=draft` in
  `data/benchmark/drafts/core-draft-003.jsonl`, plus focused contract tests. Both records preserve
  the frozen `train` / `data` allocation and `eg-data-ecos-gdp-20260717` evidence group, reuse only
  the existing `ecos-200y108-snapshot-20260717` snapshot, whose use in KOR-RTD is owner-approved,
  and answer its
  2026Q1 real-GDP observation as `596692.8` `billion_krw`. The matrix, source bytes, manifest,
  checksum, rights decision, normalization rule, 13 public schemas, and five committed traces are
  unchanged. At that checkpoint these were drafts only, so the approved human-reviewed core count
  remained 6/40.

- **Bilingual ECOS GDP owner approval (2026-08-20):** Hyungbae Cho explicitly approved the
  unchanged `kv-core-data-02` Korean/English pair. Approval feature commit `473a733` moves the two
  records to `data/benchmark/core/core-batch-003.jsonl`, records reviewer `Hyungbae Cho` and aware
  review timestamp `2026-08-20T00:24:18Z`, changes only the lifecycle tag from `draft-003` to
  `batch-003`, and updates the focused lifecycle assertions. At that approval checkpoint, the
  approved core was 8/40; the remaining 32 matrix slots were unauthored and unapproved, and no
  draft was pending.
  The frozen matrix, source bundle, rights decisions, normalization contract, 13 public schemas,
  five committed traces, and runtime source are unchanged.

- **Bilingual ECOS current-account draft pair (2026-08-20):** functional commit `50c4d9c` adds
  exactly `kv-core-data-03-ko` and `kv-core-data-03-en` at `status=draft` in
  `data/benchmark/drafts/core-draft-004.jsonl`, plus focused contract tests. Both records preserve
  the frozen `train` / `data` allocation and `eg-data-ecos-current-account-20260717` evidence
  group, reuse only the existing `ecos-301y017-snapshot-20260717` snapshot whose use in KOR-RTD is
  owner-approved, and answer its 2026-05 seasonally adjusted current-account observation as
  `38121.1` `million_usd`. At that checkpoint the approved human-reviewed core remained 8/40; of
  the other 32 unapproved matrix slots, these two were pending drafts and 30 remained unauthored.
  The matrix, approved core, source bytes, manifest, rights decision, normalization rule, 13
  public schemas, five committed traces, and runtime source are unchanged.

- **Bilingual ECOS current-account owner approval (2026-08-21):** Hyungbae Cho explicitly approved
  the unchanged `kv-core-data-03` Korean/English pair. Approval feature commit `db6700e` moves the
  two records to `data/benchmark/core/core-batch-004.jsonl`, records reviewer `Hyungbae Cho` and
  aware review timestamp `2026-08-21T07:14:13Z`, changes only the lifecycle tag from `draft-004`
  to `batch-004`, renames the focused draft tests to `test_ecos_current_account_core.py` with
  approved expectations, and raises the approved-count assertions in `test_bok_outlook_core.py`
  and `test_ecos_gdp_core.py` from 8 to 10. At that approval checkpoint, the approved core was
  10/40 across `core-batch-001.jsonl` (4 records), `core-batch-002.jsonl` (2),
  `core-batch-003.jsonl` (2), and `core-batch-004.jsonl` (2); the remaining 30 matrix slots were
  unauthored and unapproved, and no draft was pending. The frozen matrix, source bundle, rights
  decisions, normalization contract, 13 public schemas, five committed traces, and runtime source
  are unchanged.

- **Bilingual KOSIS CPI draft pair (2026-08-21):** functional commit `5e0da06` adds exactly
  `kv-core-data-04-ko` and `kv-core-data-04-en` at `status=draft` in
  `data/benchmark/drafts/core-draft-005.jsonl`, plus focused contract tests. Both records preserve
  the frozen `dev` / `data` allocation and `eg-data-kosis-cpi-20260717` evidence group, reuse only
  the existing `kosis-cpi-snapshot-20260717` data unit — the July 2026 KOSIS forward snapshot
  `kosis-101-dt-1j22003-t-t10-20260717t115242998550z` (KOSIS table `DT_1J22003`, item `T/T10`,
  producer 국가데이터처), whose use in KOR-RTD is owner-approved under ADR 0007 — and answer its
  June 2026 (period `2026-06`) national all-items consumer price index (2020=100) observation as
  `119.99` `index_2020_100` at `as_of=2026-07-17`. This is the first authored pair on the KOSIS
  CPI snapshot and the first `dev`-split data pair, completing coverage of all three frozen
  `read_snapshot_as_of` bindings (ECOS GDP, ECOS current account, KOSIS CPI). At that checkpoint
  the approved human-reviewed core remained 10/40; of the other 30 unapproved matrix slots, these
  two were pending drafts and 28 remained unauthored. The matrix, approved core, source bytes,
  manifest, rights decision, normalization rule, 13 public schemas, five committed traces, and
  runtime source are unchanged.

- **KOSIS CPI draft attribution amendment (2026-08-21):** the owner supplied the official English
  name of 국가데이터처 — the Ministry of Data and Statistics. A follow-up draft-only amendment
  replaces the Korean agency name in the English record's rendered attribution with that official
  English name and updates the focused attribution assertions; the Korean record, gold values,
  tool expectations, and every frozen boundary are unchanged, both records stayed at
  `status=draft` pending named human review, and at that checkpoint the approved core remained
  10/40.

- **Bilingual KOSIS CPI owner approval (2026-08-25):** Hyungbae Cho explicitly approved the
  unchanged `kv-core-data-04` Korean/English pair. Approval feature commit `95c5e61` moves the
  two records to `data/benchmark/core/core-batch-005.jsonl`, records reviewer `Hyungbae Cho` and
  aware review timestamp `2026-08-25T07:10:15Z`, changes only the lifecycle tag from `draft-005`
  to `batch-005`, renames the focused draft tests to `test_kosis_cpi_core.py` with approved
  expectations, and raises the approved-count assertions in `test_bok_outlook_core.py`,
  `test_ecos_gdp_core.py`, and `test_ecos_current_account_core.py` from 10 to 12. At that
  approval checkpoint, the approved core was 12/40 across `core-batch-001.jsonl` (4 records),
  `core-batch-002.jsonl` (2), `core-batch-003.jsonl` (2), `core-batch-004.jsonl` (2), and
  `core-batch-005.jsonl` (2); the remaining 28 matrix slots were unauthored and unapproved, and
  no draft was pending. This approval completes the data route's four authorable pairs
  (`kv-core-data-01`–`kv-core-data-04`); the fifth data pair `kv-core-data-05` stays reserved on
  the deliberately unauthored test-split unit. The frozen matrix, source bundle, rights
  decisions, normalization contract, 13 public schemas, five committed traces, and runtime source
  are unchanged.

- **Bilingual OECD scope abstention draft pair (2026-08-25):** functional commit `c20619d` adds
  exactly `kv-core-abstain-02-ko` and `kv-core-abstain-02-en` at `status=draft` in
  `data/benchmark/drafts/core-draft-006.jsonl`, plus focused contract tests. Both records
  preserve the frozen `train` / `abstain` allocation, the
  `eg-abstain-unapproved-neighboring-oecd-scope` evidence group, and parallel group
  `kv-core-abstain-02`; they bind no document or data units and carry no tool expectations and no
  reference answer — only a language-matched abstention reason. Both questions ask for Korea's
  OECD normalised CLI value for May 2026 using only the vintage available as of 2026-07-09. The
  normalised CLI is a neighboring measure outside the sole owner-approved OECD raw-data scope —
  Korea's monthly amplitude-adjusted CLI, `KOR.M.LI_AA.IX._T` (ADR 0007) — so the gold behavior
  is abstention on the missing rights basis: the abstention reasons name the approved scope,
  forbid substituting the approved series or exposing an unapproved observation, and leak no
  observation value (the focused tests assert the serialized records contain neither `102.66`
  nor the CLI source/ledger IDs). The 2026-07-09 cutoff is deliberately one where the approved
  amplitude-adjusted scope does resolve (edition `202607`, value `102.66`), so a focused contrast
  test proves the drafted abstention is rights-driven, not availability-driven. This is the
  second abstain pair (after `kv-core-abstain-01`) and the first authored pair whose fail-closed
  basis is a rights boundary rather than the availability ledger. At that checkpoint the approved
  human-reviewed core remained 12/40; of the other 28 unapproved matrix slots, these two were
  pending drafts and 26 remained unauthored. The frozen matrix, approved core, source bundle,
  rights decisions, normalization contract, 13 public schemas, five committed traces, and runtime
  source are unchanged.

- **Bilingual OECD scope abstention owner approval (2026-08-26):** Hyungbae Cho explicitly
  approved the unchanged `kv-core-abstain-02` Korean/English pair. Approval feature commit
  `4c29b1d` moves the two records to `data/benchmark/core/core-batch-006.jsonl`, records reviewer
  `Hyungbae Cho` and aware review timestamp `2026-08-26T01:49:45Z`, changes only the lifecycle
  tag from `draft-006` to `batch-006`, renames the focused draft tests to
  `test_oecd_scope_abstain_core.py` with approved expectations, and raises the approved-count
  assertions in `test_bok_outlook_core.py`, `test_ecos_gdp_core.py`,
  `test_ecos_current_account_core.py`, and `test_kosis_cpi_core.py` from 12 to 14. At that
  approval checkpoint, the approved core was 14/40 across `core-batch-001.jsonl` (4 records),
  `core-batch-002.jsonl` (2), `core-batch-003.jsonl` (2), `core-batch-004.jsonl` (2),
  `core-batch-005.jsonl` (2), and `core-batch-006.jsonl` (2); the remaining 26 matrix slots were
  unauthored and unapproved, and no draft was pending. This is the second approved abstain pair
  (after `kv-core-abstain-01`) and the first approved pair whose fail-closed basis is a rights
  boundary rather than the availability ledger. The frozen matrix, source bundle, rights
  decisions, normalization contract, 13 public schemas, five committed traces, and runtime source
  are unchanged.

- **Bilingual CPI revision false-premise abstention draft pair (2026-08-26):** functional commit
  `77d247d` adds exactly `kv-core-abstain-03-ko` and `kv-core-abstain-03-en` at `status=draft` in
  `data/benchmark/drafts/core-draft-007.jsonl`, plus focused contract tests. Both records
  preserve the frozen `train` / `abstain` allocation, the
  `eg-abstain-korean-cpi-revision-false-premise` evidence group, and parallel group
  `kv-core-abstain-03`; they bind no document or data units and carry no tool expectations and no
  reference answer — only a language-matched abstention reason. Both questions rest on the false
  premise that the many archived OECD editions of Korea's consumer price index prove the Korean
  CPI was revised just as many times, and ask for before-and-after November 2019 CPI values using
  only the vintage available as of 2026-07-17. The gold behavior is to reject the premise and
  abstain: archived edition counts measure archive coverage, not actual revisions, and KOR-RTD
  holds no owner-approved raw-data decision for the OECD Korea CPI revision series — raw OECD
  observations outside the sole approved Korea monthly amplitude-adjusted CLI scope
  (`KOR.M.LI_AA.IX._T`) remain metadata-only — so no before-and-after CPI observation can be
  served, and the system must not fabricate revision values or expose an unapproved observation.
  The focused tests additionally prove that the rights catalog's only OECD decision is the
  approved CLI scope, that the serialized records leak no observation value and no snapshot
  identifier, and that the only approved CPI evidence in KOR-RTD — the KOSIS latest-only
  snapshot — has `vintage_semantics=latest_only`, so committed evidence cannot serve any CPI
  revision by construction. This is the third authored abstain pair (after the approved
  `kv-core-abstain-01` availability-frontier and `kv-core-abstain-02`
  unapproved-neighboring-scope pairs) and the first false-premise rejection pair. At that
  checkpoint the approved human-reviewed core remained 14/40; of the other 26 unapproved matrix
  slots, these two were pending drafts and 24 remained unauthored. The frozen matrix, approved
  core, source bundle, rights decisions, normalization contract, 13 public schemas, five
  committed traces, and runtime source are unchanged.

- **Bilingual CPI revision false-premise abstention owner approval (2026-08-26):** Hyungbae Cho
  explicitly approved the unchanged `kv-core-abstain-03` Korean/English pair. Approval feature
  commit `5e14119` moves the two records to `data/benchmark/core/core-batch-007.jsonl`, records
  reviewer `Hyungbae Cho` and aware review timestamp `2026-08-26T07:34:50Z`, changes only the
  lifecycle tag from `draft-007` to `batch-007`, renames the focused draft tests to
  `test_cpi_revision_abstain_core.py` with approved expectations, and raises the approved-count
  assertions in `test_bok_outlook_core.py`, `test_ecos_gdp_core.py`,
  `test_ecos_current_account_core.py`, `test_kosis_cpi_core.py`, and
  `test_oecd_scope_abstain_core.py` from 14 to 16. At that approval checkpoint, the approved core
  was 16/40 across `core-batch-001.jsonl` (4 records), `core-batch-002.jsonl` (2),
  `core-batch-003.jsonl` (2), `core-batch-004.jsonl` (2), `core-batch-005.jsonl` (2),
  `core-batch-006.jsonl` (2), and `core-batch-007.jsonl` (2); the remaining 24 matrix slots were
  unauthored and unapproved, and no draft was pending. This is the third approved abstain pair
  (after the `kv-core-abstain-01`
  availability-frontier and `kv-core-abstain-02` unapproved-neighboring-scope pairs) and the
  first approved false-premise rejection pair. The frozen matrix, source bundle, rights
  decisions, normalization contract, 13 public schemas, five committed traces, and runtime source
  are unchanged.

- **Bilingual missing-as-of abstention draft pair (2026-08-26):** functional commit `fd7640b`
  adds exactly `kv-core-abstain-04-ko` and `kv-core-abstain-04-en` at `status=draft` in
  `data/benchmark/drafts/core-draft-008.jsonl`, plus focused contract tests. Both records
  preserve the frozen `dev` / `abstain` allocation, the `eg-abstain-missing-as-of` evidence
  group, and parallel group `kv-core-abstain-04`; they bind no document or data units and carry
  no tool expectations and no reference answer — only a language-matched abstention reason. Both
  questions ask for Korea's OECD amplitude-adjusted CLI value for May 2026 using the vintage
  available at the time, while omitting the as-of date the vintage request depends on; the
  record-level `as_of` field is `2026-07-17`, while the question text supplies no cutoff. The
  gold behavior is to ask for the missing as-of and abstain: a vintage answer depends on its
  as-of cutoff, and KOR-RTD's fail-closed contract never executes without an explicit
  `effective_as_of` and never guesses or defaults the cutoff, because an assumed cutoff can
  expose the wrong vintage and create temporal leakage. The focused tests additionally prove
  that the questions contain no as-of phrase while both abstention reasons demand an explicit
  `effective_as_of`, that the serialized records leak no observation value and no snapshot or
  ledger identifier, and that the same request resolves once an explicit cutoff of 2026-07-09 is
  supplied (edition `202607`, value `102.66` from the owner-approved CLI scope) — so the drafted
  abstention is missing-cutoff driven, not availability- or rights-driven. This is the fourth
  authored abstain pair (three already approved), the first missing-as-of clarification pair,
  and the second `dev`-split pair after `kv-core-data-04`. At that checkpoint the approved
  human-reviewed core remained 16/40; of the other 24 unapproved matrix slots, these two were
  pending drafts and 22 remained unauthored. The frozen matrix, approved core, source bundle,
  rights decisions, normalization contract, 13 public schemas, five committed traces, and
  runtime source are unchanged.

- **Bilingual missing-as-of abstention owner approval (2026-08-27):** Hyungbae Cho explicitly
  approved the unchanged `kv-core-abstain-04` Korean/English pair. Approval feature commit
  `dfcd191` moves the two records to `data/benchmark/core/core-batch-008.jsonl`, records
  reviewer `Hyungbae Cho` and aware review timestamp `2026-08-27T06:37:54Z`, changes only the
  lifecycle tag from `draft-008` to `batch-008`, renames the focused draft tests to
  `test_missing_as_of_abstain_core.py` with approved expectations, and raises the approved-count
  assertions in `test_bok_outlook_core.py`, `test_ecos_gdp_core.py`,
  `test_ecos_current_account_core.py`, `test_kosis_cpi_core.py`,
  `test_oecd_scope_abstain_core.py`, and `test_cpi_revision_abstain_core.py` from 16 to 18. At
  that approval checkpoint, the approved core was 18/40 across `core-batch-001.jsonl` (4
  records), `core-batch-002.jsonl` (2), `core-batch-003.jsonl` (2), `core-batch-004.jsonl` (2),
  `core-batch-005.jsonl` (2), `core-batch-006.jsonl` (2), `core-batch-007.jsonl` (2), and
  `core-batch-008.jsonl` (2); the remaining 22 matrix slots were unauthored and unapproved, and
  no draft was pending. The approved questions still omit their as-of date while the record-level
  `as_of` field is `2026-07-17`, so the gold behavior remains asking for the missing as-of and
  abstaining under the fail-closed explicit-`effective_as_of` contract. This is the fourth
  approved abstain pair (after the `kv-core-abstain-01` availability-frontier,
  `kv-core-abstain-02` unapproved-neighboring-scope, and `kv-core-abstain-03` false-premise
  rejection pairs), the first approved missing-as-of clarification pair, and the first approved
  `dev`-split abstain pair. The frozen matrix, source bundle, rights decisions, normalization
  contract, 13 public schemas, five committed traces, and runtime source are unchanged.

- **Bilingual ledger frontier abstention draft pair (2026-08-27):** functional commit `d1eb5ea`
  adds exactly `kv-core-abstain-05-ko` and `kv-core-abstain-05-en` at `status=draft` in
  `data/benchmark/drafts/core-draft-009.jsonl`, plus focused contract tests. Both records
  preserve the frozen `test` / `abstain` allocation, the
  `eg-abstain-cutoff-after-complete-through` evidence group, and parallel group
  `kv-core-abstain-05`; they bind no document or data units and carry no tool expectations and
  no reference answer — only a language-matched abstention reason. Both questions ask for
  Korea's OECD amplitude-adjusted CLI value for May 2026 using only the vintage available as of
  August 15, 2026; the record-level `as_of` field is `2026-08-15`. That cutoff lies beyond the
  committed edition-availability ledger's completeness frontier (`complete_through`, the
  2026-07-17 capture instant), so the gold behavior is abstention with
  `cutoff_beyond_complete_through`: past the frontier the ledger cannot certify which editions
  had become available or when, and the fail-closed resolver must not infer editions beyond the
  frontier or expose a value. The focused tests additionally prove that the ledger's cutoff for
  2026-08-15 exceeds `complete_through` and `select_edition` abstains with
  `cutoff_beyond_complete_through`, that a pre-frontier cutoff of 2026-07-09 still selects
  edition `202607` — so the drafted abstention is frontier-driven, not rights- or
  premise-driven — and that the serialized records leak no edition code, no observation value,
  and no snapshot or ledger identifier. This is the fifth authored abstain pair — completing
  authoring of all five abstain pairs (four already approved) — the first authored `test`-split
  pair, and the last matrix slot authorable without a new capture or an owner decision: after
  its review, every remaining slot (`kv-core-doc-02`–`kv-core-doc-05`,
  `kv-core-both-01`–`kv-core-both-05`, and the reserved `kv-core-data-05`) needs either the
  Bank of Korea outlook PDF bodies re-fetched, a new manifest capture, or the reserved future
  release. The approved human-reviewed core remains 18/40; of the other 22 unapproved matrix
  slots, these two are pending drafts and 20 remain unauthored. The frozen matrix, approved
  core, source bundle, rights decisions, normalization contract, 13 public schemas, five
  committed traces, and runtime source are unchanged.

## Current validation evidence

Run from the repository root after activating `.venv` (any OS; see README quick start):

```bash
python -m ruff check .
python -m ruff format --check .
python -m pytest
```

Last validated 2026-07-14 on Windows (Python 3.12.13): ruff clean, format clean, `pytest --cov=sovereignlab` 45 passed with 100% statement and branch coverage (241 statements, 60 branches); `git check-ignore` confirmed exclusion of `.venv`, `.env`, `data/raw`, `models`, generated `artifacts`, `traces/private`; `python scripts/export_json_schemas.py` regenerates both public schemas deterministically.

The 2026-07-14 reorientation commit is documentation-only (charter, ADR, AGENTS.md, status, CV bullets, README, proposal); no source or test files changed. It was additionally smoke-checked on macOS with a throwaway Python 3.13.13 environment (pinned requirements installed cleanly; ruff clean, format clean, 45 tests passed) — the project standard remains Python 3.12 per ADR 0001.

Validated 2026-07-15 on Windows after recording the M1b spikes, reproducibility log, and proposed
ADRs 0004–0005: Python 3.12.13; `python -m ruff check .` clean;
`python -m ruff format --check .` clean (15 files already formatted);
`python -m pytest --cov=sovereignlab --cov-report=term-missing` passed all 45 tests with 100%
statement/branch coverage (241 statements, 60 branches); `git diff --check` clean.

Revalidated 2026-07-16 on Windows after correcting the ECOS/KOSIS rights basis and data-licensing
boundary: Python 3.12.13; `python -m ruff check .` clean; `python -m ruff format --check .` clean
(15 files already formatted); `python -m pytest --cov=sovereignlab --cov-report=term-missing` passed
all 45 tests with 100% statement/branch coverage (241 statements, 60 branches); `git diff --check`
clean.

Validated 2026-07-16 on Windows after charter v2.2 approval and strengthened rights-catalog
implementation: Python 3.12.13; `python scripts/export_json_schemas.py` regenerated five contracts;
`python -m ruff check .` clean; `python -m ruff format --check .` clean (17 files already
formatted); `python -m pytest --cov=sovereignlab --cov-report=term-missing` passed all 147 tests
with 100% statement/branch coverage (633 statements, 218 branches); `git diff --check` clean. No
raw observation endpoint or paid operation was used.

Validated 2026-07-17 on macOS after recording ADR 0006 and creating the Homebrew Python 3.12
environment: Python 3.12.13; `python scripts/export_json_schemas.py` regenerated all five contracts
with no diff; `python -m ruff check .` clean; `python -m ruff format --check .` clean (17 files
already formatted); `python -m pytest --cov=sovereignlab --cov-report=term-missing` passed all 147
tests with 100% statement/branch coverage (633 statements, 218 branches). Documentation-only
change; no observation endpoint or paid operation was used.

Validated 2026-07-17 on macOS after implementing the ADR 0005 contract unit and applying the
adversarial-review fixes: Python 3.12.13; `python scripts/export_json_schemas.py` exported six
contracts (`-v2` evidence schemas plus the new availability ledger; rights schemas byte-identical);
`python -m ruff check .` clean; `python -m ruff format --check .` clean (19 files);
`python -m pytest --cov=sovereignlab --cov-report=term-missing` passed all 226 tests with 100%
statement/branch coverage (923 statements, 350 branches); `git diff --check` clean. Offline
code/schema/tests only; no observation endpoint or paid operation was used.

Validated 2026-07-17 on macOS after implementing the offline as-of resolver and the constraint-ID
contract correction: Python 3.12.13; `python scripts/export_json_schemas.py` regenerated all six
contracts; `python -m ruff check .` clean; `python -m ruff format --check .` clean; `python -m
pytest --cov=sovereignlab --cov-report=term-missing` passed all 255 tests with 100% statement/branch
coverage. A read-only, key-free official-response regression used workstation temporary files only:
GDP 4,770 bytes / SHA-256 `484ba74366c07d1911e70988aa202fcbe1bc384b0f743aae2b70bf6d9dc497fa`;
CPI 63,799 bytes / SHA-256
`0e45f924a9c2a4742729f649893c54e836200ca268171e7897f1748cd7c3a572`. Both matched the
2026-07-15 verification log exactly; temporary files were deleted and no paid operation occurred.

Validated 2026-07-17 on macOS after implementing the weekly harvester and recording its first real
OECD metadata capture: Python 3.12.13; `python scripts/export_json_schemas.py` was deterministic;
`python -m ruff check .` and `python -m ruff format --check .` were clean; `python -m pytest
--cov=sovereignlab --cov-branch --cov-report=term-missing` passed all 288 tests with 100% statement
and branch coverage (1,371 statements, 478 branches); `git diff --check` was clean. The captured
availability-constraint XML is 17,827 bytes / SHA-256
`e7a3fab8730a2d9e4644ccb78844d721c263a2b235d4575fa850d1f0c71be06f`; the content-constraint
XML is 23,251 bytes / SHA-256
`40b9f6e25f0187992f679fd5e8ae8215182076d8e280b71ca74b737d204334e6`. Both are key-free
metadata-only responses and contain no observations. No paid operation occurred.

Validated 2026-07-17 on macOS after ADR 0007 implementation and the first approved observation
captures: Python 3.12.13; `python scripts/export_json_schemas.py` regenerated all six contracts;
`python -m ruff check .` and `python -m ruff format --check .` were clean; `python -m pytest
--cov=sovereignlab --cov-branch --cov-report=term-missing` passed all 314 tests with 100% statement
and branch coverage (1,535 statements, 528 branches); `git diff --check` was clean. Observation
SHA-256 values are GDP `75c96ce62270a8a6c2a3c6bebaef981945b41f37f62cab6911698ce64d8dd9ea`,
current account `8f71259c202ed7cc4d6b2eebea5123215547b6ffd3f653ef734fdd8564bd9389`,
KOSIS CPI `f1336aba6ea64fcb7d438d008ba564d25d35e6f0f4d6d8d0ef0f8ec1954834d6`, and
OECD CLI `ac7d0f9a2517870173885f1d45e2edea90f54cd485e2f539c73afddde566f058`.
Every manifest matches the committed bytes and exact owner-approved rights decision. API use and
the key-free OECD download cost $0; the local secrets remain ignored and absent from publishable
files.

Validated 2026-07-17 on macOS after freezing number-normalization 1.0.0: Python 3.12.13; ruff check
and format check were clean; `python -m pytest --cov=sovereignlab --cov-branch
--cov-report=term-missing` passed all 323 tests with 100% statement and branch coverage (1,598
statements, 534 branches); `git diff --check` was clean. One key-free in-memory OECD read confirmed
the exact GDP code dimensions `KOR.Q.B1GQ_Q.XDC._T`, raw XDC units, and the previously recorded
value; no response was saved and no paid operation occurred.

Validated 2026-07-17 on macOS after adding the isolated QLoRA compatibility harness: the 14
CPU-only harness tests and real public-Hub preflight passed; the latter returned
`preflight_passed`, four examples, zero weight downloads, and $0 cost. Full ruff and format checks
were clean; all 337 tests passed with 100% SovereignLab statement/branch coverage (1,598 statements,
534 branches); `git diff --check` was clean. The paid GPU step remains unexecuted.

Validated 2026-07-18 after the paid compatibility run and M2 handoff update. The remote RunPod
check used an NVIDIA A40, driver 580.159.04, CUDA 13.0, and Python 3.12.3; the pinned harness
returned `gpu_step_passed`, exactly one optimizer step, finite loss `5.192200660705566`, 12,353,536
trainable parameters, 4,210,338,304 peak CUDA bytes, and 49,474,005 bytes of adapter-only output.
The output and model cache were deleted with the Pod, all attempted Pods were removed, and current
hourly spend returned to `$0`. Locally on macOS/Python 3.12.13,
`python scripts/export_json_schemas.py` remained deterministic; `python -m ruff check .` and
`python -m ruff format --check .` passed; `python -m pytest --cov=sovereignlab --cov-branch
--cov-report=term-missing` passed all 337 tests with 100% statement/branch coverage (1,598
statements, 534 branches); and `git diff --check` was clean.

Validated 2026-07-24 on macOS after freezing the core authoring matrix and adding the first draft
batch: Python 3.12.13; `python scripts/export_json_schemas.py` regenerated seven contracts;
`python -m ruff check .` and `python -m ruff format --check .` passed; `python -m pytest
--cov=sovereignlab --cov-branch --cov-report=term-missing` passed all 353 tests with 100%
statement/branch coverage (1,689 statements, 576 branches). The new evidence test constructs a real
bundle from committed artifacts and reproduces CLI edition `202607`, value `102.66`, and the
pre-July fail-closed abstention. No network, secret, model, or paid operation was used.

Validated 2026-07-25 on macOS after recording owner approval of the matrix and first four records:
Python 3.12.13; schema export remained deterministic; ruff check and format check passed; all 353
tests passed with 100% statement/branch coverage (1,687 statements, 574 branches). The approved
records still form a real manifest/ledger/rights bundle and reproduce the same CLI value and
fail-closed abstention. No network, secret, model, or paid operation was used.

Validated 2026-07-28 on macOS after implementing offline bilingual temporal document retrieval:
Python 3.12.13; `python scripts/export_json_schemas.py` remained deterministic at seven public
contracts; `python -m ruff check --no-cache .` and `python -m ruff format --check .` passed;
`python -m pytest --cov=sovereignlab --cov-branch --cov-report=term-missing -p no:cacheprovider`
passed all 368 tests with 100% statement/branch coverage (1,794 statements, 608 branches);
`git diff --check` passed. Only synthetic fixtures were used, with no network, source-document
download, secret, model, or paid operation.

Revalidated 2026-07-28 after the session-close handoff documentation update: schema export remained
deterministic at seven contracts; ruff check and format check passed; all 368 tests again passed
with 100% statement/branch coverage (1,794 statements, 608 branches); `git diff --check` passed.
This was a documentation-only operation with no network, source download, secret, model, or cost.

Revalidated 2026-07-28 after recording ADR 0008 and charter v2.4:
`python scripts/export_json_schemas.py` remained deterministic at seven contracts;
`python -m ruff check --no-cache .` and `python -m ruff format --check .` passed (43 files);
`python -m pytest --cov=sovereignlab --cov-branch --cov-report=term-missing -p no:cacheprovider`
passed all 368 tests with 100% statement/branch coverage (1,794 statements, 608 branches);
`git diff --check` passed. Documentation-only change; no network, source download, secret, model,
or paid operation.

Validated 2026-07-28 after adding the first real bilingual document manifests:
`python scripts/export_json_schemas.py` remained deterministic at seven contracts;
`python -m ruff check --no-cache .` and `python -m ruff format --check .` passed (44 files);
`python -m pytest --cov=sovereignlab --cov-branch --cov-report=term-missing -p no:cacheprovider`
passed all 372 tests with 100% statement/branch coverage (1,794 statements, 608 branches);
`git diff --check` passed. The only network work was free, read-only verification of public Bank of
Korea pages and temporary PDF captures for size/hash measurement. No source body, extracted text,
secret, model call, or paid operation entered the repository.

Revalidated 2026-07-28 after the ADR 0009 / charter v2.5 document-rights correction:
schema export remained deterministic at seven contracts; ruff check and format check passed (44
files); all 372 tests passed with 100% statement/branch coverage (1,794 statements, 608 branches);
`git diff --check` passed. The only network work was free, read-only verification of the official
Bank of Korea copyright/public-data pages, the linked public-data portal view, and the current
Public Data Act text. No source download, secret, model call, or paid operation occurred.

Validated 2026-07-28 after authoring the first bilingual documentary draft pair:
`python scripts/export_json_schemas.py` remained deterministic at seven contracts;
`python -m ruff check --no-cache .` and `python -m ruff format --check .` passed (45 files);
`python -m pytest --cov=sovereignlab --cov-branch --cov-report=term-missing -p no:cacheprovider`
passed all 378 tests with 100% statement/branch coverage (1,794 statements, 608 branches);
`git diff --check` passed, and `git diff --exit-code -- data/schemas` proved schema export
deterministic. The official PDFs were re-fetched only into a temporary directory for hash
verification, local text inspection, and rendered-page visual QA; those temporary files were
deleted. No provider body, extracted text, secret, model call, or paid operation entered the
repository.

Revalidated 2026-07-29 after recording owner approval of the first documentary pair:
`python scripts/export_json_schemas.py` remained deterministic at seven contracts;
`python -m ruff check --no-cache .` and `python -m ruff format --check .` passed (45 files);
`python -m pytest --cov=sovereignlab --cov-branch --cov-report=term-missing -p no:cacheprovider`
passed all 378 tests with 100% statement/branch coverage (1,794 statements, 608 branches);
`git diff --check` passed, and `git diff --exit-code -- data/schemas` proved schema export
deterministic. This was an annotation, lifecycle, test, and governance update only; there was no
network source read, provider-body change, secret, model call, or paid operation.

Revalidated 2026-07-29 for the Windows continuation handoff:
`python scripts/export_json_schemas.py` remained deterministic at seven contracts;
`python -m ruff check --no-cache .` and `python -m ruff format --check .` passed (45 files);
`python -m pytest --cov=sovereignlab --cov-branch --cov-report=term-missing -p no:cacheprovider`
passed all 378 tests with 100% statement/branch coverage (1,794 statements, 608 branches);
`git diff --check` passed, and `git diff --exit-code -- data/schemas` proved schema export
deterministic. Documentation-only change; no implementation, source read, secret, model call, or
paid operation occurred. The incoming Windows agent must reproduce this baseline locally before
editing.

Validated 2026-07-29 on Windows after the baseline repair and typed execution/trace contract slice:
Python 3.12.13; `python -m pip install -r requirements.txt` confirmed the platform-guarded
`tzdata==2026.3`; `python scripts/export_json_schemas.py` generated 13 deterministic public
contracts; `python -m ruff check --no-cache .` passed; `python -m ruff format --check .` passed
(47 files); `python -m pytest --cov=sovereignlab --cov-branch --cov-report=term-missing -p
no:cacheprovider` passed all 483 tests with 100% SovereignLab statement/branch coverage (2,291
statements, 758 branches); and `git diff --check` passed. The execution module's 98 focused tests
also independently reached 100% statement/branch coverage (495 statements, 150 branches). Schema
export was rerun and the committed-schema equality plus two-pass byte-determinism tests passed.
Work was offline after the free PyPI environment repair; no provider source read, secret, live
model call, GPU operation, or paid operation occurred.

Validated 2026-07-29 on Windows after the trusted snapshot registry/reader slice:
Python 3.12.13; `python scripts/export_json_schemas.py` remained deterministic at 13 public
contracts; `python -m ruff check --no-cache .` passed; `python -m ruff format --check .` passed
(52 files); `python -m pytest --cov=sovereignlab --cov-branch --cov-report=term-missing -p
no:cacheprovider` passed all 595 tests with 100% SovereignLab statement/branch coverage (2,674
statements, 888 branches); and `git diff --check` passed. The 112 focused snapshot tests independently
reached 100% snapshot statement/branch coverage (383 statements, 130 branches). The three existing
committed archives were read offline and reproduced GDP `596692.8`, current account `38121.1`
(plus negative-value regression `-633.9`), and CPI `119.99`; their tracked bytes and manifests
were unchanged. No network, provider request, secret, live model call, GPU operation, or paid
operation occurred.

Validated 2026-07-29 on Windows after the trusted temporal-document registry/adapter slice:
Python 3.12.13; `python scripts/export_json_schemas.py` remained deterministic at 13 public
contracts; `python -m ruff check --no-cache .` passed; `python -m ruff format --check .` passed
(55 files); `python -m pytest --cov=sovereignlab --cov-branch --cov-report=term-missing -p
no:cacheprovider` passed all 646 tests with 100% SovereignLab statement/branch coverage (2,881
statements, 948 branches); and `git diff --check` passed for the implementation commit. The 70
focused retrieval tests independently reached 100% retrieval statement/branch coverage (314
statements, 94 branches). Both read-only final audits found no remaining actionable P0/P1/P2
after exact-byte/model mutation, byte-subclass, size-bound, fabricated-evidence, and score-drift
findings were closed. No network, provider read, secret, live model call, GPU operation, or paid
operation occurred.

Validated 2026-07-30 on Windows after the trusted historical STES registry/adapter slice:
Python 3.12.13; `python scripts/export_json_schemas.py` remained deterministic at 13 public
contracts; `python -m ruff check --no-cache .` passed; `python -m ruff format --check .` passed
(59 files); and `python -m pytest --cov=sovereignlab --cov-branch --cov-report=term-missing -p
no:cacheprovider` passed all 892 tests with 100% SovereignLab statement/branch coverage (3,680
statements, 1,240 branches). The 170 focused registry tests reached 100% registry coverage (682
statements, 264 branches), and the 67 focused adapter tests reached 100% adapter coverage (115
statements, 28 branches). `git diff --check` passed. Independent red-team reproduction closed XML
trust, append-only chain, archive-ledger join, shared-query/ledger mutation, rights-laundering,
invalid-model exception, deleted-field, and call-ID findings; the final audit found no remaining
reproducible P0/P1. No network, provider read, secret, live model call, GPU operation, or paid
operation occurred.

Validated 2026-07-30 on Windows after snapshot call-time hardening and the frozen callable
registry/dispatcher slice: Python 3.12.13; `python scripts/export_json_schemas.py` remained
deterministic at 13 public contracts; `python -m ruff check --no-cache .` passed;
`python -m ruff format --check .` passed (63 files); and
`python -m pytest --cov=sovereignlab --cov-branch --cov-report=term-missing -p
no:cacheprovider` passed all 976 tests with 100% SovereignLab statement/branch coverage (4,065
statements, 1,370 branches). The 127 focused snapshot tests reached 100% snapshot
registry/reader coverage (437 statements, 162 branches), and the 69 focused dispatcher tests
reached 100% dispatcher coverage (326 statements, 98 branches). Independent review reproduced and
closed exact-byte/model drift, call and selected-registry mutation/restore, result substitution,
post-call dependency corruption/replacement, result-comparison side effects, and malformed
discriminator findings; the final contract review found no remaining reproducible P1. No network,
provider read, secret, live model call, GPU operation, or paid operation occurred.

Revalidated 2026-07-30 after the post-dispatcher onboarding finalization:
`python scripts/export_json_schemas.py` reproduced all 13 public contracts;
`python -m ruff check --no-cache .` and `python -m ruff format --check .` passed across 63 Python
files; `python -m pytest --cov=sovereignlab --cov-branch --cov-report=term-missing -p
no:cacheprovider` passed all 976 tests with 100% SovereignLab statement/branch coverage (4,065
statements, 1,370 branches); and `git diff --check` passed. This close changed documentation only;
no source, test, schema behavior, source/provider read, secret, live model call, GPU operation, or
paid operation was added.

Revalidated 2026-07-30 after refreshing the application documents (CV bullet bank and project
description updated to the current 6/40 approved-core, 13-schema, 976-test state):
`python scripts/export_json_schemas.py` reproduced all 13 public contracts;
`python -m ruff check --no-cache .` and `python -m ruff format --check .` passed (63 files);
`python -m pytest --cov=sovereignlab --cov-branch --cov-report=term-missing -p no:cacheprovider`
passed all 976 tests with 100% SovereignLab statement/branch coverage (4,065 statements, 1,370
branches); and `git diff --exit-code` passed after schema export. The first pytest attempt on this
workstation reported 872 passed plus 104 tmp-path setup errors because the repository-root
`.pytest_tmp` directory (the configured pytest `--basetemp`) existed with an ACL that denies
listing, ownership transfer, and deletion to the current unelevated user; the suite was rerun
fully green with a CLI `--basetemp` override to a fresh temporary directory, so the discrepancy is
environmental, not a source or test regression. Removing the stale `.pytest_tmp` from an elevated
shell restores the canonical command. Documentation-only change; no network, provider read,
secret, live model call, GPU operation, or paid operation occurred.

Validated 2026-08-02 on macOS after the offline one-shot planner slice: Python 3.12.13;
`python scripts/export_json_schemas.py` reproduced all 13 public contracts;
`python -m ruff check --no-cache .` passed; `python -m ruff format --check .` passed across 65
Python files; and `python -m pytest --cov=sovereignlab --cov-branch
--cov-report=term-missing -p no:cacheprovider` passed all 1,007 tests with 100% SovereignLab
statement/branch coverage (4,238 statements, 1,414 branches). The 31 focused planner tests reached
100% planner coverage (172 statements, 44 branches). `git diff --check` passed, and schema export
introduced no diff. The slice was entirely offline and added no dispatcher invocation, source or
provider read, secret, live model call, GPU operation, or paid operation.

Validated 2026-08-07 on Windows after the deterministic evidence-packet assembler slice: Python
3.12.13; `python scripts/export_json_schemas.py` reproduced all 13 public contracts without a
schema diff; `python -m ruff check --no-cache .` passed; and `python -m ruff format --check .`
passed across 67 Python files. The 42 focused assembler tests reached 100% assembler
statement/branch coverage (115 statements, 56 branches). The full suite, run with an explicit
fresh OS `--basetemp` because the unchanged repository-root `.pytest_tmp` still has the documented
access-denying ACL, passed all 1,049 tests with 100% SovereignLab statement/branch coverage (4,353
statements, 1,470 branches). `git diff --check` passed, and functional commit `ff96710` matched
`origin/main` with a clean worktree before this documentation checkpoint. The stale temp directory
was not modified. The slice was entirely offline and added no source or provider read, secret,
live model call, GPU operation, or paid operation.

Validated 2026-08-11 on Windows after the private offline-executor slice: Python 3.12.13;
`python scripts/export_json_schemas.py` reproduced all 13 public contracts without a schema diff;
`python -m ruff check --no-cache .` passed; and `python -m ruff format --check .` passed across 69
Python files. The 66 focused executor tests reached 100% executor statement/branch coverage (326
statements, 98 branches). The full suite, run with an explicit fresh OS `--basetemp`, passed all
1,115 tests with 100% SovereignLab statement/branch coverage (4,679 statements, 1,568 branches).
The executor descriptor contains 32 canonical source entries and SHA-256
`08f45dab6a36a49cb7d0b588a69236942cd61534540bd4de0772010402dada64`. The ignored repository
`.pytest_tmp` ACL was left untouched. Functional commit `550b591` matched `origin/main` with a clean
worktree before this documentation checkpoint. The work was entirely offline and added no network
or provider call, secret, live model integration, GPU operation, or paid operation; project cost
was $0.00.

Validated 2026-08-11 on Windows after the committed real-digest replay-trace slice: Python 3.12.13;
`python scripts/export_json_schemas.py` reproduced all 13 public contracts without a schema diff;
`python scripts/export_execution_replay_traces.py --check` reproduced the five committed trace
artifacts byte-for-byte; `python -m ruff check --no-cache .` passed; and `python -m ruff format
--check .` passed across 71 Python files. The focused executor-plus-replay suite passed all 80 tests
with 100% executor statement/branch coverage (326 statements, 98 branches). The full suite, run
with an explicit fresh OS `--basetemp`, passed all 1,129 tests with 100% SovereignLab
statement/branch coverage (4,679 statements, 1,568 branches). The executor descriptor remains 32
canonical source entries with SHA-256
`08f45dab6a36a49cb7d0b588a69236942cd61534540bd4de0772010402dada64`. During onboarding, the
canonical command collected 1,115 baseline tests and reported 1,009 passed plus 106 setup errors,
all caused by the documented repository-root `.pytest_tmp` `WinError 5`; the unchanged baseline
then passed all 1,115 tests with a fresh OS `--basetemp`. The directory and ACL were left untouched.
`git diff --check` passed. Functional commit `883815b` contains the trace slice. The work was
entirely offline, used no provider/live-model integration, source or rights change, secret,
network/GPU operation, or paid operation, and cost $0.00.

Validated 2026-08-19 on Windows after the bilingual ECOS GDP draft slice: Python 3.12.13; all 13
public schemas and five committed replay traces remained unchanged; `python -m ruff check
--no-cache .` passed; and `python -m ruff format --check .` passed across 72 Python files. The
focused benchmark slice passed all 27 tests. The full suite, run with an explicit fresh OS
`--basetemp`, passed all 1,135 tests with 100% SovereignLab statement/branch coverage (4,679
statements, 1,568 branches). During onboarding, the canonical baseline collected 1,129 tests and
reported 1,023 passed plus 106 setup errors, all the documented repository-root `.pytest_tmp`
`WinError 5`; the same pre-change baseline passed 1,129/1,129 with a fresh OS `--basetemp`. The
directory and ACL were left untouched. Functional commit `f2d2523` contains exactly the two draft
records and their focused tests. The work was entirely offline, used no network, provider/live-
model call, source refresh, GPU, or paid operation, and cost $0.00.

Validated 2026-08-20 on Windows after recording Hyungbae Cho's approval of the bilingual ECOS GDP
pair: the three focused benchmark files passed all 27 tests; the full suite passed all 1,135 tests
with 100% SovereignLab statement/branch coverage (4,679 statements, 1,568 branches) under a fresh
OS `--basetemp`; and Ruff check plus format check passed across 72 Python files. The public schema
count remains 13 and all five committed replay traces remain unchanged. The repository
`.pytest_tmp` directory and ACL were untouched. Approval feature commit `473a733` contains only the
two-record lifecycle transition and focused test updates; the frozen matrix, source, rights,
schema, and runtime boundaries did not change. The work was entirely offline and cost $0.00.

Validated 2026-08-20 on Windows after the bilingual ECOS current-account draft slice: all six new
focused tests passed, the four focused benchmark files passed all 33 tests, and the full suite
passed all 1,141 tests with 100% SovereignLab statement/branch coverage (4,679 statements, 1,568
branches) under a fresh OS `--basetemp`. Ruff check and format check passed across 73 Python files.
All 13 public schemas regenerated deterministically and all five committed replay traces remained
unchanged. The repository `.pytest_tmp` directory and ACL were untouched. Functional commit
`50c4d9c` contains exactly the two draft records and focused tests; the frozen matrix, approved
core, source, rights, schema, trace, and runtime boundaries did not change. The work was entirely
offline and cost $0.00.

Validated 2026-08-21 on Windows after recording Hyungbae Cho's approval of the bilingual ECOS
current-account pair: the four focused benchmark files (`test_core_batch.py`,
`test_bok_outlook_core.py`, `test_ecos_gdp_core.py`, and `test_ecos_current_account_core.py`)
passed all 33 tests; the full suite passed all 1,141 tests with 100% SovereignLab statement/branch
coverage (4,679 statements, 1,568 branches) under a fresh OS `--basetemp`; and Ruff check plus
format check passed across 73 Python files. All 13 public schemas regenerated deterministically,
the five committed replay traces remained unchanged, and the git diff was clean. Approval feature
commit `db6700e` contains only the two-record lifecycle transition and focused test updates; the
frozen matrix, source, rights, schema, trace, and runtime boundaries did not change. The work was
entirely offline and cost $0.00.

Validated 2026-08-21 on Windows after the bilingual KOSIS CPI draft slice: all six new focused
tests passed, the five focused benchmark files (`test_core_batch.py`, `test_bok_outlook_core.py`,
`test_ecos_gdp_core.py`, `test_ecos_current_account_core.py`, and `test_kosis_cpi_draft.py`)
passed all 39 tests, and the full suite passed all 1,147 tests with 100% SovereignLab
statement/branch coverage (4,679 statements, 1,568 branches) under a fresh OS `--basetemp`. Ruff
check and format check passed across 74 Python files. All 13 public schemas regenerated
deterministically and the git diff was clean. Functional commit `5e0da06` contains exactly the two
draft records and their six focused tests (278 insertions, nothing else changed); the frozen
matrix, approved core, source, rights, schema, trace, and runtime boundaries did not change. The
work was entirely offline and cost $0.00.

Validated 2026-08-25 on Windows after recording Hyungbae Cho's approval of the bilingual KOSIS CPI
pair: the five focused benchmark files (`test_core_batch.py`, `test_bok_outlook_core.py`,
`test_ecos_gdp_core.py`, `test_ecos_current_account_core.py`, and `test_kosis_cpi_core.py`)
passed all 39 tests; the full suite passed all 1,147 tests with 100% SovereignLab statement/branch
coverage (4,679 statements, 1,568 branches) under a fresh OS `--basetemp`; and Ruff check plus
format check passed across 74 Python files. All 13 public schemas regenerated deterministically,
the five committed replay traces remained unchanged, and the git diff was clean. Approval feature
commit `95c5e61` contains only the two-record lifecycle transition and focused test updates; the
frozen matrix, source, rights, schema, trace, and runtime boundaries did not change. The work was
entirely offline and cost $0.00.

Validated 2026-08-25 on Windows after the bilingual OECD scope abstention draft slice: all six new
focused tests passed, the six focused benchmark files (`test_core_batch.py`,
`test_bok_outlook_core.py`, `test_ecos_gdp_core.py`, `test_ecos_current_account_core.py`,
`test_kosis_cpi_core.py`, and `test_oecd_scope_abstain_draft.py`) passed all 45 tests, and the
full suite passed all 1,153 tests with 100% SovereignLab statement/branch coverage (4,679
statements, 1,568 branches) under a fresh OS `--basetemp`. Ruff check and format check passed
across 75 Python files. All 13 public schemas regenerated deterministically and the git diff was
clean. Functional commit `c20619d` contains exactly the two draft records and their six focused
tests (175 insertions, nothing else changed); the frozen matrix, approved core, source, rights,
schema, trace, and runtime boundaries did not change. The work was entirely offline and cost
$0.00.

Validated 2026-08-26 on Windows after recording Hyungbae Cho's approval of the bilingual OECD
scope abstention pair: the six focused benchmark files (`test_core_batch.py`,
`test_bok_outlook_core.py`, `test_ecos_gdp_core.py`, `test_ecos_current_account_core.py`,
`test_kosis_cpi_core.py`, and `test_oecd_scope_abstain_core.py`) passed all 45 tests; the full
suite passed all 1,153 tests with 100% SovereignLab statement/branch coverage (4,679 statements,
1,568 branches) under a fresh OS `--basetemp`; and Ruff check plus format check passed across 75
Python files. All 13 public schemas regenerated deterministically, the five committed replay
traces remained unchanged, and the git diff was clean. Approval feature commit `4c29b1d` contains
only the two-record lifecycle transition and focused test updates; the frozen matrix, source,
rights, schema, trace, and runtime boundaries did not change. The work was entirely offline and
cost $0.00.

Validated 2026-08-26 on Windows after the bilingual CPI revision false-premise abstention draft
slice: all six new focused tests passed, the seven focused benchmark files (`test_core_batch.py`,
`test_bok_outlook_core.py`, `test_ecos_gdp_core.py`, `test_ecos_current_account_core.py`,
`test_kosis_cpi_core.py`, `test_oecd_scope_abstain_core.py`, and
`test_cpi_revision_abstain_draft.py`) passed all 51 tests, and the full suite passed all 1,159
tests with 100% SovereignLab statement/branch coverage (4,679 statements, 1,568 branches) under a
fresh OS `--basetemp`. Ruff check and format check passed across 76 Python files. All 13 public
schemas regenerated deterministically and the git diff was clean. Functional commit `77d247d`
contains exactly the two draft records and their six focused tests (159 insertions, nothing else
changed); the frozen matrix, approved core, source, rights, schema, trace, and runtime boundaries
did not change. The work was entirely offline and cost $0.00.

Validated 2026-08-26 on Windows after recording Hyungbae Cho's approval of the bilingual CPI
revision false-premise abstention pair: the seven focused benchmark files (`test_core_batch.py`,
`test_bok_outlook_core.py`, `test_ecos_gdp_core.py`, `test_ecos_current_account_core.py`,
`test_kosis_cpi_core.py`, `test_oecd_scope_abstain_core.py`, and
`test_cpi_revision_abstain_core.py`) passed all 51 tests; the full suite passed all 1,159 tests
with 100% SovereignLab statement/branch coverage (4,679 statements, 1,568 branches) under a fresh
OS `--basetemp`; and Ruff check plus format check passed across 76 Python files. All 13 public
schemas regenerated deterministically, the five committed replay traces remained unchanged, and
the git diff was clean. Approval feature commit `5e14119` contains only the two-record lifecycle
transition and focused test updates; the frozen matrix, source, rights, schema, trace, and
runtime boundaries did not change. The work was entirely offline and cost $0.00.

Validated 2026-08-26 on Windows after the bilingual missing-as-of abstention draft slice: all six
new focused tests passed, the eight focused benchmark files (`test_core_batch.py`,
`test_bok_outlook_core.py`, `test_ecos_gdp_core.py`, `test_ecos_current_account_core.py`,
`test_kosis_cpi_core.py`, `test_oecd_scope_abstain_core.py`, `test_cpi_revision_abstain_core.py`,
and `test_missing_as_of_abstain_draft.py`) passed all 57 tests, and the full suite passed all
1,165 tests with 100% SovereignLab statement/branch coverage (4,679 statements, 1,568 branches)
under a fresh OS `--basetemp`. Ruff check and format check passed across 77 Python files. All 13
public schemas regenerated deterministically and the git diff was clean. Functional commit
`fd7640b` contains exactly the two draft records and their six focused tests (175 insertions,
nothing else changed); the frozen matrix, approved core, source, rights, schema, trace, and
runtime boundaries did not change. The work was entirely offline and cost $0.00.

Validated 2026-08-27 on Windows after recording Hyungbae Cho's approval of the bilingual
missing-as-of abstention pair: the eight focused benchmark files (`test_core_batch.py`,
`test_bok_outlook_core.py`, `test_ecos_gdp_core.py`, `test_ecos_current_account_core.py`,
`test_kosis_cpi_core.py`, `test_oecd_scope_abstain_core.py`, `test_cpi_revision_abstain_core.py`,
and `test_missing_as_of_abstain_core.py`) passed all 57 tests; the full suite passed all 1,165
tests with 100% SovereignLab statement/branch coverage (4,679 statements, 1,568 branches) under a
fresh OS `--basetemp`; and Ruff check plus format check passed across 77 Python files. All 13
public schemas regenerated deterministically, the five committed replay traces remained
unchanged, and the git diff was clean. Approval feature commit `dfcd191` contains only the
two-record lifecycle transition and focused test updates; the frozen matrix, source, rights,
schema, trace, and runtime boundaries did not change. The work was entirely offline and cost
$0.00.

Validated 2026-08-27 on Windows after the bilingual ledger frontier abstention draft slice: all
six new focused tests passed, the nine focused benchmark files (`test_core_batch.py`,
`test_bok_outlook_core.py`, `test_ecos_gdp_core.py`, `test_ecos_current_account_core.py`,
`test_kosis_cpi_core.py`, `test_oecd_scope_abstain_core.py`, `test_cpi_revision_abstain_core.py`,
`test_missing_as_of_abstain_core.py`, and `test_ledger_frontier_abstain_draft.py`) passed all 63
tests, and the full suite passed all 1,171 tests with 100% SovereignLab statement/branch coverage
(4,679 statements, 1,568 branches) under a fresh OS `--basetemp`. Ruff check and format check
passed across 78 Python files. All 13 public schemas regenerated deterministically and the git
diff was clean. Functional commit `d1eb5ea` contains exactly the two draft records and their six
focused tests (161 insertions, nothing else changed); the frozen matrix, approved core, source,
rights, schema, trace, and runtime boundaries did not change. The work was entirely offline and
cost $0.00.

## M1b verification spike record (2026-07-15)

All network work below was read-only, key-free, and free of charge. Raw responses were written only
to the workstation's temporary directory for inspection and hashing; no downloaded observation file
was added to the repository. Timestamps are UTC. The Windows workstation required
`curl.exe --ssl-no-revoke` because Schannel could not reach its certificate-revocation service; this
kept normal TLS certificate validation enabled.

Exact request URLs, timestamps, status codes, byte counts, hashes, and parser commands are preserved
in `docs/discovery/03_week1_verification_log.md`; the log contains metadata only, not downloaded
response bodies.

### `DF_MEI_ARCHIVE` — accessible on the archive tenant only

- Exact data request:
  `https://sdmx.oecd.org/archive/rest/data/OECD,DF_MEI_ARCHIVE,/KOR.101..Q?format=csvfilewithlabels`
  — at 2026-07-15 05:11:31 it returned HTTP 200, SDMX-CSV v2, 10,581,205 bytes,
  44,138 rows, and SHA-256
  `0bf918fe7415787fb1f6a3ddf52a406527d6a09b76b00db53de3175354d61f80`. A separate repeat
  request also returned HTTP 200 with the same byte count and hash.
- The corresponding `public`-tenant data and structure requests returned HTTP 404. The current
  200/404 conflict is therefore reproducible as `archive=200`, `public=404`; the 2026-07-14 failing
  probe did not preserve its URL, so tenant confusion is the most direct explanation, not a proven
  historical cause.
- Exact structure request:
  `https://sdmx.oecd.org/archive/rest/dataflow/OECD/DF_MEI_ARCHIVE/latest?references=all`
  — HTTP 200, `OECD:DSD_MEI_ARCHIVE(1.0)`, `isFinal=true`, 65 `LOCATION` codes (including
  aggregates such as OECD/G20/EU, so **not 65 countries**), 24 `VAR` codes, and 300 monthly `EDI`
  codes from `199902` through `202401`.
- The KOR quarterly real-GDP slice contains 299 distinct editions, not 300: `200904` is declared in
  the codelist but returns `NoRecordsFound` for this slice. The reported KOR 2010-Q1 example is
  reproduced exactly as 165 editions from `201005` through `202401`, with ten distinct observation
  values.
- The dataflow carries `NonProductionDataflow=true`. Claim-safe conclusion: the archive is an
  accessible frozen cross-check as of this date, but it is not a guaranteed production endpoint.

### Economic Outlook range — recent KOR observation range fixed

- Archive listing `https://sdmx.oecd.org/archive/rest/dataflow/all/all/latest` returned HTTP 200 and
  112 `DF_EO*` definitions enumerate every EO number from 60 through 114 (55 editions, no numeric
  gap). This is catalog continuity, not observation continuity. Sampled KOR responses were HTTP 200
  for `DF_EO60_MAIN`, `DF_EO107_EDITIONS`, and `DF_EO114_INTERNET`; EO60 was sparse and contained
  only `EXCHUD` in the main flow, while EO107 and EO114 contained `GDPV`. The untested middle
  editions therefore cannot support a claim of continuous KOR observation backfill.
- Public edition-specific flows EO114–EO118 and current `DSD_EO@DF_EO` (named Economic Outlook 119,
  version 1.5) each returned an actual KOR observation response. All six contain nonblank annual and
  quarterly `GDPV`; the full-response row counts were respectively 56,331, 36,990, 36,898, 36,918,
  37,647, and 37,782. The EO117 long-term-scenario flow remains separate.
- Claim-safe forecast-vintage range for the MVP is therefore **public EO114–EO119**. The archive
  claim remains “catalog EO60–EO114 plus sampled KOR observations at EO60/107/114,” not continuous
  KOR coverage. Do not claim a literal archive ID `DF_EO114`; the boundary ID is
  `DF_EO114_INTERNET`. Deep EO60–EO113 backfill remains de-scoped.

### Primary live revisions flow — target examples reproduced

- Structure request
  `https://sdmx.oecd.org/public/rest/dataflow/OECD.SDD.STES/DSD_STES_REVISIONS%40DF_STES_REVISIONS/latest?references=all`
  returned HTTP 200 and confirms dimension order
  `REF_AREA.FREQ.MEASURE.UNIT_MEASURE.ACTIVITY.EDITION`, plus
  `NonProductionDataflow=true`.
- KOR 2025-Q1 quarterly real-GDP request
  `https://sdmx.oecd.org/public/rest/data/OECD.SDD.STES,DSD_STES_REVISIONS%40DF_STES_REVISIONS,/KOR.Q.B1GQ_Q...?startPeriod=2025-Q1&endPeriod=2025-Q1&format=csvfilewithlabels`
  returned HTTP 200, 15 editions (`202505`–`202607`), and SHA-256
  `484ba74366c07d1911e70988aa202fcbe1bc384b0f743aae2b70bf6d9dc497fa`. The June and July
  2026 raw XDC values are respectively `572057700000000` and `574984300000000`, reproducing
  572,057.7 and 574,984.3 billion KRW after division by `10^9`.
- KOR CPI 2005-01 request using measure `CP` returned HTTP 200 and exactly 258 editions from
  `200502` through `202607`, reproducing the reported archive-coverage count.
- Resolver design blocker confirmed: `EDITION=YYYYMM` is a monthly label, not a publication date.
  The codelist already includes future labels through `202812`, while current availability stops at
  `202607`. The current content constraint records
  `validFrom=2026-07-08T09:33:35.737Z`, which conservatively supports July's current availability
  region; it does not preserve June's historical region or prove an exact first-public instant.
- `updatedAfter` brackets current row update time, not first publication. HTTP response timestamps
  are generated at request time. Related official MEI issue dates also vary within their labeled
  month, although one-to-one STES mapping remains unverified. Accepted ADR 0005 therefore uses an
  edition-specific availability-window ledger and abstains across an unresolved frontier; first-day
  or month-end inference is prohibited for the reviewed core and headline leakage metric.
- A single `SourceManifest.published_on` cannot represent all historical editions in a consolidated
  response, and backdating a 2026 snapshot would violate ADR 0002. Mandatory vintage evidence and
  the corresponding bundle rule require the accepted `2.0.0` contract rather than ADR 0003's expected
  optional `1.1.0` field.

### OECD rights — base terms verified; exact CLI scope later approved

- The [OECD Open Access Policy](https://www.oecd.org/en/about/oecd-open-by-default-policy.html)
  says content published before 2024-07-01 is governed by OECD Terms & Conditions, not by the later
  default CC BY 4.0 licence.
- The [OECD Terms & Conditions](https://www.oecd.org/en/about/terms-conditions.html) Data section
  permits extraction, download, copying, adaptation, distribution, sharing, and embedding for any
  purpose, including commercial use, unless dataset-specific restrictions or third-party rights
  apply. It requires OECD attribution and propagation of that acknowledgement requirement to
  sublicensees.
- `DF_MEI_ARCHIVE` structure/CSV metadata exposed no licence, restriction, or third-party-rights
  field. It remains `metadata_only`, not `CC BY 4.0`. ADR 0007 later completed the exact
  first-party review only for Korea monthly amplitude-adjusted CLI
  `KOR.M.LI_AA.IX._T`; that decision does not extend to `DF_MEI_ARCHIVE` or another OECD series.

### ECOS/KOSIS rights — policy, initial rulings, and catalog implemented

- ECOS and KOSIS API schemas do not expose a per-series KOGL/licence field, but that absence does
  not imply missing permission. The official use guides are source-wide rights instruments whose
  applicable branch must be mapped to each exact producer or content category.
- The [ECOS Statistics Information Use Guide](https://ecos.bok.or.kr/) permits Bank of
  Korea-produced statistics to be used, processed, and redistributed free of charge for commercial
  and non-commercial purposes with source attribution. Other-producer statistics may be used
  non-commercially with attribution, while commercial use requires the producer's approval; because
  that branch does not expressly grant processing or redistribution, public raw commits fail closed
  without a more specific instrument.
- The [KOSIS Statistics Information Use Guide](https://kosis.kr/nsistN/kosisUseGuide.do) permits
  in-scope domestic macro statistics to be used, reused, and redistributed commercially or
  non-commercially with detailed attribution. Distortion and paid standalone sale of unchanged raw
  information are prohibited. International and North Korea statistics are non-commercial-only and
  may not be redistributed; publications follow their individual KOGL notices.
- Accepted ADR 0004 and charter v2.2 retain an owner-approved per-series audit gate, map the exact
  producer/category to the real publisher terms rather than fabricate a KOGL value, and define a
  reusable classification-and-attribution ruling instead of a fresh licence investigation for
  every capture.
- Exact ECOS metadata identifies quarterly SA real GDP as `200Y108/10601` (quarterly, billion KRW)
  and SA current account as `301Y017/SA000` (monthly, million USD). The latter directly names Bank
  of Korea as `ORG_NAME`. For the former, the ECOS item API maps the exact code to the named table;
  the [KOSIS official recent-data record](https://kosis.kr/serviceInfo/newContrainDataDetail.do?boardIdx=1976017&boardOrgId=301)
  assigns the same title/frequency to Bank of Korea, with an official
  [Bank of Korea GDP release](https://www.bok.or.kr/portal/bbs/B0000501/view.do?menuNo=200690&nttId=10097644)
  as corroboration. The GDP join is title/frequency-based, not a direct ECOS code-to-producer field;
  the owner accepted that mapping on 2026-07-16. Both series now have validated `allowed` records in
  `data/rights/kor-rtd-rights-2026-07-16.json` with exact scope, official evidence, permitted
  operations, attribution template, and aware approval-record timestamp.
- The independent catalog does not itself authorize raw publication. At the time of this spike,
  `SourceManifest` 1.0 had no typed decision link; the 2026-07-17 contract `2.0.0` implementation
  added that link and its bundle cross-validation. Source observations retain provider terms and
  are not relicensed under repository Apache-2.0.

### Owner decisions closed

- On 2026-07-16 the owner approved ADR 0005 in full: the edition-availability ledger, fail-closed
  resolver, `Asia/Seoul` end-of-day cutoff, evidence/benchmark contract `2.0.0` path, and narrow
  partial supersessions of ADR 0002 decision 5 and ADR 0003 decisions 1/3.
- The owner also approved `OECD metadata_only pending dataset-specific and third-party-rights
  confirmation`. ADR 0007 later superseded that interim ruling only for exact first-party CLI scope
  `KOR.M.LI_AA.IX._T`; all other OECD observation scopes retain it.
- On 2026-07-17 the owner completed the one-hour employer-risk review required by charter §7,
  answering an agent-provided question list in their own words; ADR 0006 commits those verbatim
  answers as the decision record.
- On 2026-07-17 the owner approved KOSIS CPI and OECD Composite leading indicator (Korea). ADR 0007
  translates those names to exact official scope IDs and records the narrow rights decisions;
  charter v2.3 and the append-only 2026-07-17 catalog are synchronized. All current week-1 owner
  decisions are closed.
- On 2026-07-29 the owner approved the unchanged `kv-core-doc-01` Korean/English documentary pair.
  Both records now carry the named reviewer and aware review timestamp in
  `data/benchmark/core/core-batch-002.jsonl`; the approved core count is 6/40.
- On 2026-08-20 Hyungbae Cho approved the unchanged `kv-core-data-02` Korean/English ECOS GDP pair.
  Both records carry reviewer `Hyungbae Cho` and aware timestamp `2026-08-20T00:24:18Z` in
  `data/benchmark/core/core-batch-003.jsonl`; the approved core count is now 8/40.
- On 2026-08-21 Hyungbae Cho approved the unchanged `kv-core-data-03` Korean/English ECOS
  current-account pair. Both records carry reviewer `Hyungbae Cho` and aware timestamp
  `2026-08-21T07:14:13Z` in `data/benchmark/core/core-batch-004.jsonl`; the approved core count is
  now 10/40.
- On 2026-08-25 Hyungbae Cho approved the unchanged `kv-core-data-04` Korean/English KOSIS CPI
  pair. Both records carry reviewer `Hyungbae Cho` and aware timestamp `2026-08-25T07:10:15Z` in
  `data/benchmark/core/core-batch-005.jsonl`; the approved core count is now 12/40.
- On 2026-08-26 Hyungbae Cho approved the unchanged `kv-core-abstain-02` Korean/English OECD
  scope abstention pair. Both records carry reviewer `Hyungbae Cho` and aware timestamp
  `2026-08-26T01:49:45Z` in `data/benchmark/core/core-batch-006.jsonl`; the approved core count
  is now 14/40.
- On 2026-08-26 Hyungbae Cho approved the unchanged `kv-core-abstain-03` Korean/English CPI
  revision false-premise abstention pair. Both records carry reviewer `Hyungbae Cho` and aware
  timestamp `2026-08-26T07:34:50Z` in `data/benchmark/core/core-batch-007.jsonl`; the approved
  core count is now 16/40.
- On 2026-08-27 Hyungbae Cho approved the unchanged `kv-core-abstain-04` Korean/English
  missing-as-of abstention pair. Both records carry reviewer `Hyungbae Cho` and aware timestamp
  `2026-08-27T06:37:54Z` in `data/benchmark/core/core-batch-008.jsonl`; the approved core count
  is now 18/40.

## Session-close snapshot (2026-08-02, fourteenth close: planner boundary complete)

- Work unit C remains active, but its first six independently reviewable slices are complete.
  Execution contract 1.0.0, six new public schemas, the committed contract fixture, the Windows
  baseline repair, all three trusted deterministic tool registries/adapters, and the frozen
  callable dispatcher validate. The one-shot planner protocol plus scripted and immutable
  recorded/replay implementations now validate as a separate offline boundary.
- M2 remains active. The frozen matrix was not changed, exactly six records are owner-approved, and
  the other 34 slots are not authored.
- All three deterministic tool adapters are implemented. `read_snapshot_as_of` covers the three
  exact approved snapshot units; `retrieve_temporal_documents` covers the frozen synthetic
  Korean/English corpus; and `resolve_stes_as_of` covers only the owner-approved CLI raw archive
  while the GDP shape abstains. Each emits only selected typed evidence. Dependent benchmark
  authoring remains outside this work unit.
- The contract fixture contains no real report text. No source artifact, provider body, secret,
  live model call, GPU operation, or paid operation was added.
- The minimal typed function-calling path is not yet complete: the packet assembler, offline
  executor, and committed end-to-end replay traces do not yet exist.
- The planner exists under `src/sovereignlab/execution/planner.py`; its recording entry and
  registry are intentionally private, and no provider recording path exists under `data/`. The
  next session starts from the completed planner boundary rather than inventing a public wrapper.

## Session-close snapshot (2026-08-07, fifteenth close: assembler boundary complete)

- Work unit C remains active, but its first seven independently reviewable slices are complete.
  Execution contract 1.0.0, all three trusted deterministic tool registries/adapters, the frozen
  callable dispatcher, the offline one-shot planner, and the private deterministic evidence-packet
  assembler validate independently.
- M2 remains active. The frozen matrix was not changed, exactly six records are owner-approved,
  and the other 34 slots are not authored.
- The assembler exists under `src/sovereignlab/execution/assembler.py`, consumes only validated
  request/plan/result models, and returns only the existing packet model. It does not invoke the
  planner or dispatcher, coordinate calls, construct traces, or expose a package-level public API.
- The minimal typed function-calling path is not yet complete: the offline executor and committed
  end-to-end replay traces do not yet exist. The contract fixture remains a schema fixture rather
  than an end-to-end replay result.
- No source artifact, provider body, secret, live model call, GPU operation, or paid operation was
  added. The next session starts from the completed assembler boundary and coordinates the frozen
  components without reopening them.

## Session-close snapshot (2026-08-11, sixteenth close: offline executor complete)

- Work unit C remains active, but its first eight independently reviewable ADR 0008 slices are
  complete. Execution contract 1.0.0, all three trusted deterministic tool registries/adapters, the
  frozen callable dispatcher, the offline one-shot planner, the private evidence-packet assembler,
  and the private offline executor validate independently and together.
- M2 remains active. The frozen matrix was not changed, exactly six records are owner-approved,
  and the other 34 slots are not authored.
- Functional commit `550b591` adds `src/sovereignlab/execution/executor.py`. The executor invokes
  one validated planner once, dispatches through the real committed registry in plan order, stops
  after a terminal abstention or error, invokes the assembler only for eligible terminal states,
  and returns only the existing `ExecutionTrace` model. Its function and private error are not
  package-level exports, and the public schema count remains 13.
- The executor binds real registry/corpus IDs and digests, exact planner provenance, and the
  32-source executor descriptor digest
  `08f45dab6a36a49cb7d0b588a69236942cd61534540bd4de0772010402dada64`.
- The minimal typed function-calling path is not yet complete or claimed as shipped: committed
  machine-readable real-digest end-to-end replay traces do not yet exist. The existing contract
  fixture remains a schema fixture rather than an end-to-end replay result, and live integration
  remains later work.
- No source artifact, provider body, secret, network or provider call, live model integration, GPU
  operation, or paid operation was added. The unchanged `.pytest_tmp` ACL was not touched; focused
  and full validation used fresh OS basetemp directories. The next session starts from the completed
  executor and adds replay traces only.

## Session-close snapshot (2026-08-11, seventeenth close: committed replay traces complete)

- Work unit C is complete. Its first nine independently reviewable ADR 0008 slices now include the
  frozen execution contract, three deterministic tool adapters, callable dispatcher, offline
  planner, private assembler, private executor, and committed real-digest replay artifacts.
- Functional commit `883815b` adds five machine-readable `ExecutionTrace` 1.0.0 files under
  `traces/replay/v1/`. The exporter generates them only through the real private executor,
  `ScriptedPlanner`, and committed registry/corpus boundaries; they are not hand-authored
  provenance substitutes.
- The five traces cover all four routes, all three tools, Korean and English, explicit and implicit
  cutoffs, complete execution, planned abstention, and terminal tool abstention. In the terminal
  case the successful prefix is retained, the trailing STES call is not run, and the evidence packet
  remains empty, so no partial evidence is exposed.
- Healthy-stack fault traces were not fabricated. Tool-failure and packet-assembly-failure mappings
  remain strict executor/schema-tested behavior, avoiding unbound runtime fault injection under a
  real source-tree digest.
- The minimal offline path is now **typed function calling with committed traces**. Provider/live-
  model integration and the bounded loop remain absent; the latter stays deferred to v1.1.
- M2 remains active, the frozen matrix remains unchanged, exactly 6/40 core records are owner-
  approved, and the public schema count remains 13. The executor descriptor still contains 32
  entries with digest
  `08f45dab6a36a49cb7d0b588a69236942cd61534540bd4de0772010402dada64`.
- Python 3.12.13 validation is green: 71 formatted Python files; 80 focused executor-plus-replay
  tests at 100% executor coverage (326 statements, 98 branches); and 1,129 full-suite tests at 100%
  SovereignLab coverage (4,679 statements, 1,568 branches) with a fresh OS `--basetemp`. Schema
  export and trace byte checks are clean. The documented repository `.pytest_tmp` ACL was untouched,
  and this slice cost $0.00.
- The exact next reviewable slice is only the draft `kv-core-data-02-ko` / `kv-core-data-02-en`
  pair using `ecos-200y108-snapshot-20260717`, whose use in KOR-RTD was already owner-approved. It
  must not be approved in the
  authoring change, and it must not alter the frozen matrix, source artifacts, or rights decisions.

## Session-close snapshot (2026-08-19, eighteenth close: ECOS GDP bilingual drafts complete)

- Functional commit `f2d2523` adds exactly two records, `kv-core-data-02-ko` and
  `kv-core-data-02-en`, to `data/benchmark/drafts/core-draft-003.jsonl` at `status=draft`, together
  with focused tests. No other benchmark record or frozen matrix row changed.
- Both drafts use only the existing `ecos-200y108-snapshot-20260717` evidence bundle, whose use in
  KOR-RTD is owner-approved, and preserve its exact snapshot, manifest, checksum, rights, cutoff,
  and
  normalization boundaries. Their gold observation is 2026Q1 real GDP at `596692.8`
  `billion_krw`.
- M2 remains active. Exactly 6/40 core records remain owner-approved; the new pair is not counted
  until a separate named human review explicitly approves it. The other 32 matrix slots remain
  unauthored and unapproved.
- Python 3.12.13 validation is green: 27 focused tests; 1,135 full-suite tests at 100%
  SovereignLab statement/branch coverage (4,679 statements, 1,568 branches) with a fresh OS
  `--basetemp`; and Ruff format checking across 72 Python files. The public schema count remains 13
  and the committed trace count remains five.
- The canonical onboarding failure remains environmental: 1,023 of 1,129 tests passed before 106
  `.pytest_tmp` `WinError 5` setup errors, then all 1,129 passed against a fresh OS basetemp. The
  repository `.pytest_tmp` directory and ACL were untouched.
- The exact next action is only a separate named human review of these two drafts. No source,
  rights, matrix, schema, trace, provider/live-model, GPU, paid, or deferred-loop work belongs in
  that review gate; this slice cost $0.00.

## Session-close snapshot (2026-08-20, nineteenth close: ECOS GDP bilingual pair approved)

- Approval feature commit `473a733` records Hyungbae Cho's approval of exactly
  `kv-core-data-02-ko` and `kv-core-data-02-en` at aware timestamp `2026-08-20T00:24:18Z`. The pair
  now lives in `data/benchmark/core/core-batch-003.jsonl` at `status=approved` with lifecycle tag
  `batch-003`; the former draft file is absent.
- The questions, answers, cutoff, route, split, evidence group, data-unit binding, tool
  expectations, attribution, and normalization remain byte-for-byte unchanged from functional
  draft commit `f2d2523`. The frozen matrix, source bundle, rights decisions, 13 public schemas,
  five committed traces, and runtime source are unchanged.
- M2 remains active with exactly 8/40 owner-approved core records. The remaining 32 matrix slots
  are unauthored and unapproved, no draft is pending, and no later pair or reviewable slice has
  been selected.
- Python 3.12.13 validation is green: 27 focused benchmark tests; 1,135 full-suite tests at 100%
  SovereignLab statement/branch coverage (4,679 statements, 1,568 branches) with a fresh OS
  `--basetemp`; and Ruff checking and format checking across 72 Python files. The public schema
  count remains 13 and the committed trace count remains five. The repository `.pytest_tmp`
  directory and ACL were untouched, and this approval transition cost $0.00.
- Stop here and await explicit owner instruction. Do not infer or start another benchmark pair,
  source, rights, schema, trace, runtime, provider/live-model, GPU, paid, or deferred-loop slice.

## Session-close snapshot (2026-08-20, twentieth close: ECOS current-account bilingual drafts complete)

- Functional commit `50c4d9c` adds exactly `kv-core-data-03-ko` and `kv-core-data-03-en` to
  `data/benchmark/drafts/core-draft-004.jsonl` at `status=draft`, together with six focused tests.
  No approved benchmark record or frozen matrix row changed.
- Both drafts use only the existing `ecos-301y017-snapshot-20260717` evidence bundle, whose use in
  KOR-RTD is owner-approved, and preserve its exact snapshot, manifest, checksum, rights, cutoff,
  and normalization boundaries. Their gold observation is the 2026-05 seasonally adjusted current
  account at `38121.1` `million_usd`.
- M2 remains active with exactly 8/40 owner-approved core records. The other 32 matrix slots remain
  unapproved: these two records are pending drafts and 30 slots remain unauthored. No subsequent
  pair or implementation slice is selected.
- Python 3.12.13 validation is green: six new focused tests; 33 focused benchmark tests; 1,141
  full-suite tests at 100% SovereignLab statement/branch coverage (4,679 statements, 1,568
  branches) with a fresh OS `--basetemp`; and Ruff checking and format checking across 73 Python
  files. The public schema count remains 13 and the committed trace count remains five. The
  repository `.pytest_tmp` directory and ACL were untouched, and this draft slice cost $0.00.
- The exact next action is only named human review of these two drafts. Do not pre-approve them,
  move them into `core/`, raise the approved count, select another pair, or change the source,
  rights, matrix, schema, trace, runtime, provider/live-model, GPU, paid, or deferred-loop scope.

## Session-close snapshot (2026-08-21, twenty-first close: ECOS current-account bilingual pair approved)

- Approval feature commit `db6700e` records Hyungbae Cho's approval of exactly
  `kv-core-data-03-ko` and `kv-core-data-03-en` at aware timestamp `2026-08-21T07:14:13Z`. The
  pair now lives in `data/benchmark/core/core-batch-004.jsonl` at `status=approved` with lifecycle
  tag `batch-004`; the former draft file is absent and `data/benchmark/drafts/` is empty in the
  committed tree.
- The questions, answers, cutoff, route, split, evidence group, data-unit binding, tool
  expectations, attribution, and normalization remain byte-for-byte unchanged from functional
  draft commit `50c4d9c`. Only `annotation.status`, `reviewed_by`, `reviewed_at`, and the
  lifecycle tag changed. The frozen matrix, source bundle, rights decisions, 13 public schemas,
  five committed traces, and runtime source are unchanged.
- M2 remains active with exactly 10/40 owner-approved core records. The remaining 30 matrix slots
  are unauthored and unapproved, and no draft is pending.
- Python 3.12.13 validation is green: 33 focused benchmark tests across four files; 1,141
  full-suite tests at 100% SovereignLab statement/branch coverage (4,679 statements, 1,568
  branches) with a fresh OS `--basetemp`; Ruff checking and format checking across 73 Python
  files; deterministic regeneration of all 13 public schemas; and a clean git diff. The committed
  trace count remains five, and this approval transition cost $0.00.
- The exact next owner-directed outcome is only a bounded draft-only authoring slice for the
  frozen `kv-core-data-04` pair (KOSIS national CPI) using only the existing committed
  `kosis-cpi-snapshot-20260717` evidence, whose use in KOR-RTD is owner-approved (ADR 0007). The
  new drafts must stay `status=draft` pending a separate named human review.

## Session-close snapshot (2026-08-21, twenty-second close: KOSIS CPI bilingual drafts complete)

- Functional commit `5e0da06` adds exactly `kv-core-data-04-ko` and `kv-core-data-04-en` to
  `data/benchmark/drafts/core-draft-005.jsonl` at `status=draft`, together with six focused tests
  in `tests/benchmark/test_kosis_cpi_draft.py` — 278 insertions and nothing else. No approved
  benchmark record or frozen matrix row changed.
- Both drafts use only the existing `kosis-cpi-snapshot-20260717` evidence bundle — the July 2026
  KOSIS forward snapshot `kosis-101-dt-1j22003-t-t10-20260717t115242998550z` (KOSIS table
  `DT_1J22003`, item `T/T10`, producer 국가데이터처), whose use in KOR-RTD is owner-approved under
  ADR 0007 — and preserve its exact snapshot, manifest, checksum, rights, cutoff, and
  normalization boundaries. Their gold observation is the June 2026 (period `2026-06`) national
  all-items consumer price index (2020=100) at `119.99` `index_2020_100`, normalized by frozen
  rule `kosis-101-dt-1j22003-t-t10-index-v1` with two display places, at `as_of=2026-07-17`
  (inclusive end of day Asia/Seoul). Their annotations record `Claude AI draft` at
  `2026-08-21T07:17:23Z` with no reviewer metadata.
- This is the first authored pair on the KOSIS CPI snapshot and the first `dev`-split data pair;
  it completes coverage of all three frozen `read_snapshot_as_of` bindings (ECOS GDP, ECOS
  current account, KOSIS CPI).
- M2 remains active with exactly 10/40 owner-approved core records. The other 30 matrix slots
  remain unapproved: these two records are pending drafts and 28 slots remain unauthored. No
  subsequent pair or implementation slice is selected.
- Python 3.12.13 validation is green: six new focused tests; 39 focused benchmark tests across
  five files; 1,147 full-suite tests at 100% SovereignLab statement/branch coverage (4,679
  statements, 1,568 branches) with a fresh OS `--basetemp`; Ruff checking and format checking
  across 74 Python files; deterministic regeneration of all 13 public schemas; and a clean git
  diff. The committed trace count remains five, and this draft slice cost $0.00.
- The exact next action is only named human review of these two drafts. Do not pre-approve them,
  move them into `core/`, raise the approved count, select another pair, or change the source,
  rights, matrix, schema, trace, runtime, provider/live-model, GPU, paid, or deferred-loop scope.

## Session-close snapshot (2026-08-25, twenty-third close: KOSIS CPI bilingual pair approved)

- Approval feature commit `95c5e61` records Hyungbae Cho's approval of exactly
  `kv-core-data-04-ko` and `kv-core-data-04-en` at aware timestamp `2026-08-25T07:10:15Z`. The
  pair now lives in `data/benchmark/core/core-batch-005.jsonl` at `status=approved` with lifecycle
  tag `batch-005`; the former draft file is absent and `data/benchmark/drafts/` is empty in the
  committed tree.
- The questions, answers, cutoff, route, split, evidence group, data-unit binding, tool
  expectations, attribution, and normalization remain byte-for-byte unchanged from the amended
  draft state (functional commit `5e0da06` plus the 2026-08-21 attribution amendment). Only
  `annotation.status`, `reviewed_by`, `reviewed_at`, and the lifecycle tag changed; the
  annotations preserve the AI author `Claude AI draft`. The frozen matrix, source bundle, rights
  decisions, 13 public schemas, five committed traces, and runtime source are unchanged.
- This approval completes the data route's four authorable pairs
  (`kv-core-data-01`–`kv-core-data-04`); the fifth data pair `kv-core-data-05` stays reserved on
  the deliberately unauthored test-split unit.
- M2 remains active with exactly 12/40 owner-approved core records. The remaining 28 matrix slots
  are unauthored and unapproved, and no draft is pending.
- Python 3.12.13 validation is green: 39 focused benchmark tests across five files; 1,147
  full-suite tests at 100% SovereignLab statement/branch coverage (4,679 statements, 1,568
  branches) with a fresh OS `--basetemp`; Ruff checking and format checking across 74 Python
  files; deterministic regeneration of all 13 public schemas; and a clean git diff. The committed
  trace count remains five, and this approval transition cost $0.00.
- The exact next owner-directed outcome is only a bounded draft-only authoring slice for the
  frozen `kv-core-abstain-02` pair — an abstention pair (`train` split) whose question asks for a
  neighboring OECD observation scope (Korea's normalised CLI) that has no owner-approved raw-data
  decision, so the gold behavior is abstention. Abstain pairs bind no source units, so the slice
  uses no new evidence, only the committed rights catalog as the fail-closed basis. The new
  drafts must stay `status=draft` pending a separate named human review.

## Session-close snapshot (2026-08-25, twenty-fourth close: OECD scope abstention bilingual drafts complete)

- Functional commit `c20619d` adds exactly `kv-core-abstain-02-ko` and `kv-core-abstain-02-en` to
  `data/benchmark/drafts/core-draft-006.jsonl` at `status=draft`, together with six focused tests
  in `tests/benchmark/test_oecd_scope_abstain_draft.py` — 175 insertions and nothing else. No
  approved benchmark record or frozen matrix row changed.
- Both drafts preserve the frozen `train` / `abstain` allocation, the
  `eg-abstain-unapproved-neighboring-oecd-scope` evidence group, and parallel group
  `kv-core-abstain-02`. They bind no document or data units and carry no tool expectations and no
  reference answer — only a language-matched abstention reason. Both questions ask for Korea's
  OECD normalised CLI value for May 2026 using only the vintage available as of 2026-07-09; the
  normalised CLI is a neighboring measure outside the sole owner-approved OECD raw-data scope —
  Korea's monthly amplitude-adjusted CLI, `KOR.M.LI_AA.IX._T` (ADR 0007) — so the gold behavior
  is abstention on the missing rights basis. The abstention reasons name the approved scope,
  forbid substituting the approved series or exposing an unapproved observation, and leak no
  observation value; the focused tests assert the serialized records contain neither `102.66` nor
  the CLI source/ledger IDs. Their annotations record `Claude AI draft` at `2026-08-25T07:14:19Z`
  with no reviewer metadata.
- The 2026-07-09 cutoff is deliberately one where the approved amplitude-adjusted scope does
  resolve (edition `202607`, value `102.66`); a focused contrast test proves the drafted
  abstention is rights-driven, not availability-driven. This is the second abstain pair (after
  `kv-core-abstain-01`) and the first authored pair whose fail-closed basis is a rights boundary
  rather than the availability ledger.
- M2 remains active with exactly 12/40 owner-approved core records. The other 28 matrix slots
  remain unapproved: these two records are pending drafts and 26 slots remain unauthored. No
  subsequent pair or implementation slice is selected.
- Python 3.12.13 validation is green: six new focused tests; 45 focused benchmark tests across
  six files; 1,153 full-suite tests at 100% SovereignLab statement/branch coverage (4,679
  statements, 1,568 branches) with a fresh OS `--basetemp`; Ruff checking and format checking
  across 75 Python files; deterministic regeneration of all 13 public schemas; and a clean git
  diff. The committed trace count remains five, and this draft slice cost $0.00.
- The exact next action is only named human review of these two drafts. Do not pre-approve them,
  move them into `core/`, raise the approved count, select another pair, or change the source,
  rights, matrix, schema, trace, runtime, provider/live-model, GPU, paid, or deferred-loop scope.

## Session-close snapshot (2026-08-26, twenty-fifth close: OECD scope abstention bilingual pair approved)

- Approval feature commit `4c29b1d` records Hyungbae Cho's approval of exactly
  `kv-core-abstain-02-ko` and `kv-core-abstain-02-en` at aware timestamp `2026-08-26T01:49:45Z`.
  The pair now lives in `data/benchmark/core/core-batch-006.jsonl` at `status=approved` with
  lifecycle tag `batch-006`; the former draft file is absent and `data/benchmark/drafts/` is
  empty in the committed tree.
- The questions, cutoff, route, split, evidence group, parallel group, absence of bound units,
  tool expectations, and reference answers, and the language-matched abstention reasons remain
  byte-for-byte unchanged from functional draft commit `c20619d`. Only `annotation.status`,
  `reviewed_by`, `reviewed_at`, and the lifecycle tag changed; the annotations preserve the AI
  author `Claude AI draft`. The frozen matrix, source bundle, rights decisions, 13 public
  schemas, five committed traces, and runtime source are unchanged.
- This is the second approved abstain pair (after `kv-core-abstain-01`) and the first approved
  pair whose fail-closed basis is a rights boundary rather than the availability ledger.
- M2 remains active with exactly 14/40 owner-approved core records. The remaining 26 matrix slots
  are unauthored and unapproved, and no draft is pending.
- Python 3.12.13 validation is green: 45 focused benchmark tests across six files; 1,153
  full-suite tests at 100% SovereignLab statement/branch coverage (4,679 statements, 1,568
  branches) with a fresh OS `--basetemp`; Ruff checking and format checking across 75 Python
  files; deterministic regeneration of all 13 public schemas; and a clean git diff. The committed
  trace count remains five, and this approval transition cost $0.00.
- The exact next owner-directed outcome is only a bounded draft-only authoring slice for the
  frozen `kv-core-abstain-03` pair — an abstention pair (`train` split) whose question rests on
  the false premise that archived OECD edition counts prove the Korean CPI was revised; the gold
  behavior is to reject that premise and abstain, because edition counts measure archive coverage
  and no owner-approved raw-data decision covers the OECD Korea CPI revision series. The pair
  binds no source units and is fully offline. The new drafts must stay `status=draft` pending a
  separate named human review.

## Session-close snapshot (2026-08-26, twenty-sixth close: CPI revision false-premise abstention bilingual drafts complete)

- Functional commit `77d247d` adds exactly `kv-core-abstain-03-ko` and `kv-core-abstain-03-en` to
  `data/benchmark/drafts/core-draft-007.jsonl` at `status=draft`, together with six focused tests
  in `tests/benchmark/test_cpi_revision_abstain_draft.py` — 159 insertions and nothing else. No
  approved benchmark record or frozen matrix row changed.
- Both drafts preserve the frozen `train` / `abstain` allocation, the
  `eg-abstain-korean-cpi-revision-false-premise` evidence group, and parallel group
  `kv-core-abstain-03`. They bind no document or data units and carry no tool expectations and no
  reference answer — only a language-matched abstention reason. Both questions rest on the false
  premise that the many archived OECD editions of Korea's consumer price index prove the Korean
  CPI was revised just as many times, and ask for before-and-after November 2019 CPI values using
  only the vintage available as of 2026-07-17; the gold behavior is to reject the premise and
  abstain, because archived edition counts measure archive coverage, not actual revisions, and
  KOR-RTD holds no owner-approved raw-data decision for the OECD Korea CPI revision series — raw
  OECD observations outside the sole approved Korea monthly amplitude-adjusted CLI scope
  (`KOR.M.LI_AA.IX._T`) remain metadata-only — so no before-and-after CPI observation can be
  served, and the system must not fabricate revision values or expose an unapproved observation.
  Their annotations record `Claude AI draft` at `2026-08-26T01:51:11Z` with no reviewer metadata.
- The focused tests additionally prove that the rights catalog's only OECD decision is the
  approved CLI scope, that the serialized records leak no observation value and no snapshot
  identifier, and that the only approved CPI evidence in KOR-RTD — the KOSIS latest-only
  snapshot — has `vintage_semantics=latest_only`, so committed evidence cannot serve any CPI
  revision by construction. This is the third authored abstain pair (after the approved
  `kv-core-abstain-01` availability-frontier and `kv-core-abstain-02`
  unapproved-neighboring-scope pairs) and the first false-premise rejection pair.
- M2 remains active with exactly 14/40 owner-approved core records. The other 26 matrix slots
  remain unapproved: these two records are pending drafts and 24 slots remain unauthored. No
  subsequent pair or implementation slice is selected.
- Python 3.12.13 validation is green: six new focused tests; 51 focused benchmark tests across
  seven files; 1,159 full-suite tests at 100% SovereignLab statement/branch coverage (4,679
  statements, 1,568 branches) with a fresh OS `--basetemp`; Ruff checking and format checking
  across 76 Python files; deterministic regeneration of all 13 public schemas; and a clean git
  diff. The committed trace count remains five, and this draft slice cost $0.00.
- The exact next action is only named human review of these two drafts. Do not pre-approve them,
  move them into `core/`, raise the approved count, select another pair, or change the source,
  rights, matrix, schema, trace, runtime, provider/live-model, GPU, paid, or deferred-loop scope.

## Session-close snapshot (2026-08-26, twenty-seventh close: CPI revision false-premise abstention bilingual pair approved)

- Approval feature commit `5e14119` records Hyungbae Cho's approval of exactly
  `kv-core-abstain-03-ko` and `kv-core-abstain-03-en` at aware timestamp `2026-08-26T07:34:50Z`.
  The pair now lives in `data/benchmark/core/core-batch-007.jsonl` at `status=approved` with
  lifecycle tag `batch-007`; the former draft file is absent and `data/benchmark/drafts/` is
  empty in the committed tree.
- The questions, cutoff, route, split, evidence group, parallel group, absence of bound units,
  tool expectations, and reference answers, and the language-matched abstention reasons remain
  byte-for-byte unchanged from functional draft commit `77d247d`. Only `annotation.status`,
  `reviewed_by`, `reviewed_at`, and the lifecycle tag changed; the annotations preserve the AI
  author `Claude AI draft`. The frozen matrix, source bundle, rights decisions, 13 public
  schemas, five committed traces, and runtime source are unchanged.
- This is the third approved abstain pair (after the `kv-core-abstain-01` availability-frontier
  and `kv-core-abstain-02` unapproved-neighboring-scope pairs) and the first approved
  false-premise rejection pair.
- M2 remains active with exactly 16/40 owner-approved core records. The remaining 24 matrix slots
  are unauthored and unapproved, and no draft is pending.
- Python 3.12.13 validation is green: 51 focused benchmark tests across seven files; 1,159
  full-suite tests at 100% SovereignLab statement/branch coverage (4,679 statements, 1,568
  branches) with a fresh OS `--basetemp`; Ruff checking and format checking across 76 Python
  files; deterministic regeneration of all 13 public schemas; and a clean git diff. The committed
  trace count remains five, and this approval transition cost $0.00.
- The exact next owner-directed outcome is only a bounded draft-only authoring slice for the
  frozen `kv-core-abstain-04` pair — an abstention pair (`dev` split) whose question asks for a
  historical-vintage value while omitting its as-of date; the gold behavior is to abstain (or ask
  for the missing as-of) because the fail-closed contract never executes without an explicit
  `effective_as_of` and never guesses or defaults the cutoff. The pair binds no source units and
  is fully offline. The new drafts must stay `status=draft` pending a separate named human
  review.

## Session-close snapshot (2026-08-26, twenty-eighth close: missing-as-of abstention bilingual drafts complete)

- Functional commit `fd7640b` adds exactly `kv-core-abstain-04-ko` and `kv-core-abstain-04-en` to
  `data/benchmark/drafts/core-draft-008.jsonl` at `status=draft`, together with six focused tests
  in `tests/benchmark/test_missing_as_of_abstain_draft.py` — 175 insertions and nothing else. No
  approved benchmark record or frozen matrix row changed.
- Both drafts preserve the frozen `dev` / `abstain` allocation, the `eg-abstain-missing-as-of`
  evidence group, and parallel group `kv-core-abstain-04`. They bind no document or data units
  and carry no tool expectations and no reference answer — only a language-matched abstention
  reason. Both questions ask for Korea's OECD amplitude-adjusted CLI value for May 2026 using the
  vintage available at the time, while omitting the as-of date the vintage request depends on;
  the gold behavior is to ask for the missing as-of and abstain, because a vintage answer depends
  on its as-of cutoff and KOR-RTD's fail-closed contract never executes without an explicit
  `effective_as_of` and never guesses or defaults the cutoff — an assumed cutoff can expose the
  wrong vintage and create temporal leakage. The record-level `as_of` field is `2026-07-17`,
  while the question text supplies no cutoff. Their annotations record `Claude AI draft` at
  `2026-08-26T07:36:05Z` with no reviewer metadata.
- The focused tests additionally prove that the questions contain no as-of phrase while both
  abstention reasons demand an explicit `effective_as_of`, that the serialized records leak no
  observation value and no snapshot or ledger identifier, and that a contrast test shows the same
  request resolves once an explicit cutoff of 2026-07-09 is supplied (edition `202607`, value
  `102.66` from the owner-approved CLI scope) — so the drafted abstention is missing-cutoff
  driven, not availability- or rights-driven. This is the fourth authored abstain pair (three
  already approved), the first missing-as-of clarification pair, and the second `dev`-split pair
  after `kv-core-data-04`.
- M2 remains active with exactly 16/40 owner-approved core records. The other 24 matrix slots
  remain unapproved: these two records are pending drafts and 22 slots remain unauthored. No
  subsequent pair or implementation slice is selected.
- Python 3.12.13 validation is green: six new focused tests; 57 focused benchmark tests across
  eight files; 1,165 full-suite tests at 100% SovereignLab statement/branch coverage (4,679
  statements, 1,568 branches) with a fresh OS `--basetemp`; Ruff checking and format checking
  across 77 Python files; deterministic regeneration of all 13 public schemas; and a clean git
  diff. The committed trace count remains five, and this draft slice cost $0.00.
- The exact next action is only named human review of these two drafts. Do not pre-approve them,
  move them into `core/`, raise the approved count, select another pair, or change the source,
  rights, matrix, schema, trace, runtime, provider/live-model, GPU, paid, or deferred-loop scope.

## Session-close snapshot (2026-08-27, twenty-ninth close: missing-as-of abstention bilingual pair approved)

- Approval feature commit `dfcd191` records Hyungbae Cho's approval of exactly
  `kv-core-abstain-04-ko` and `kv-core-abstain-04-en` at aware timestamp `2026-08-27T06:37:54Z`.
  The pair now lives in `data/benchmark/core/core-batch-008.jsonl` at `status=approved` with
  lifecycle tag `batch-008`; the former draft file is absent and `data/benchmark/drafts/` is
  empty in the committed tree.
- The questions, record-level `as_of`, route, split, evidence group, parallel group, absence of
  bound units, tool expectations, and reference answers, and the language-matched abstention
  reasons remain byte-for-byte unchanged from functional draft commit `fd7640b`. Only
  `annotation.status`, `reviewed_by`, `reviewed_at`, and the lifecycle tag changed; the
  annotations preserve the AI author `Claude AI draft`. The frozen matrix, source bundle, rights
  decisions, 13 public schemas, five committed traces, and runtime source are unchanged.
- The approved questions still omit their as-of date while the record-level `as_of` field is
  `2026-07-17`, so the gold behavior remains asking for the missing as-of and abstaining under
  the fail-closed explicit-`effective_as_of` contract.
- This is the fourth approved abstain pair (after the `kv-core-abstain-01`
  availability-frontier, `kv-core-abstain-02` unapproved-neighboring-scope, and
  `kv-core-abstain-03` false-premise rejection pairs), the first approved missing-as-of
  clarification pair, and the first approved `dev`-split abstain pair.
- M2 remains active with exactly 18/40 owner-approved core records. The remaining 22 matrix slots
  are unauthored and unapproved, and no draft is pending.
- Python 3.12.13 validation is green: 57 focused benchmark tests across eight files; 1,165
  full-suite tests at 100% SovereignLab statement/branch coverage (4,679 statements, 1,568
  branches) with a fresh OS `--basetemp`; Ruff checking and format checking across 77 Python
  files; deterministic regeneration of all 13 public schemas; and a clean git diff. The committed
  trace count remains five, and this approval transition cost $0.00.
- The exact next owner-directed outcome is only a bounded draft-only authoring slice for the
  frozen `kv-core-abstain-05` pair — the `test`-split abstention pair whose question asks for
  Korea's OECD amplitude-adjusted CLI for May 2026 as of August 15, 2026, a cutoff later than
  the committed edition-availability ledger's completeness frontier (`complete_through`, the
  2026-07-17 capture instant); the gold behavior is abstention with
  `cutoff_beyond_complete_through`, because past the frontier the ledger cannot certify which
  editions had become available. The pair binds no source units and is fully offline; it is the
  last matrix slot authorable without a new capture or an owner decision. The new drafts must
  stay `status=draft` pending a separate named human review.

## Session-close snapshot (2026-08-27, thirtieth close: ledger frontier abstention bilingual drafts complete)

- Functional commit `d1eb5ea` adds exactly `kv-core-abstain-05-ko` and `kv-core-abstain-05-en` to
  `data/benchmark/drafts/core-draft-009.jsonl` at `status=draft`, together with six focused tests
  in `tests/benchmark/test_ledger_frontier_abstain_draft.py` — 161 insertions and nothing else.
  No approved benchmark record or frozen matrix row changed.
- Both drafts preserve the frozen `test` / `abstain` allocation, the
  `eg-abstain-cutoff-after-complete-through` evidence group, and parallel group
  `kv-core-abstain-05`. They bind no document or data units and carry no tool expectations and no
  reference answer — only a language-matched abstention reason. Both questions ask for Korea's
  OECD amplitude-adjusted CLI value for May 2026 using only the vintage available as of August
  15, 2026; the record-level `as_of` field is `2026-08-15`. That cutoff lies beyond the committed
  edition-availability ledger's completeness frontier (`complete_through`, the 2026-07-17 capture
  instant), so the gold behavior is abstention with `cutoff_beyond_complete_through`: past the
  frontier the ledger cannot certify which editions had become available or when, and the
  fail-closed resolver must not infer editions beyond the frontier or expose a value. Their
  annotations record `Claude AI draft` at `2026-08-27T06:39:35Z` with no reviewer metadata.
- The focused tests additionally prove that the ledger's cutoff for 2026-08-15 exceeds
  `complete_through` and `select_edition` abstains with `cutoff_beyond_complete_through`, that a
  pre-frontier cutoff of 2026-07-09 still selects edition `202607` — so the drafted abstention is
  frontier-driven, not rights- or premise-driven — and that the serialized records leak no
  edition code, no observation value, and no snapshot or ledger identifier. This is the fifth
  authored abstain pair — completing authoring of all five abstain pairs, four already
  approved — and the first authored `test`-split pair.
- This was the last matrix slot authorable without a new capture or an owner decision: after this
  pair's review, every remaining slot (`kv-core-doc-02`–`kv-core-doc-05`,
  `kv-core-both-01`–`kv-core-both-05`, and the reserved `kv-core-data-05`) needs either the Bank
  of Korea outlook PDF bodies re-fetched, a new manifest capture, or the reserved future release.
- M2 remains active with exactly 18/40 owner-approved core records. The other 22 matrix slots
  remain unapproved: these two records are pending drafts and 20 slots remain unauthored. No
  subsequent pair or implementation slice is selected.
- Python 3.12.13 validation is green: six new focused tests; 63 focused benchmark tests across
  nine files; 1,171 full-suite tests at 100% SovereignLab statement/branch coverage (4,679
  statements, 1,568 branches) with a fresh OS `--basetemp`; Ruff checking and format checking
  across 78 Python files; deterministic regeneration of all 13 public schemas; and a clean git
  diff. The committed trace count remains five, and this draft slice cost $0.00.
- The exact next action is only named human review of these two drafts. Do not pre-approve them,
  move them into `core/`, raise the approved count, select another pair, or change the source,
  rights, matrix, schema, trace, runtime, provider/live-model, GPU, paid, or deferred-loop scope.

## Immediate next action (M2 — named human review of `kv-core-abstain-05` only)

1. Review only `kv-core-abstain-05-ko` and `kv-core-abstain-05-en` in
   `data/benchmark/drafts/core-draft-009.jsonl` against the frozen matrix: bilingual wording, the
   record-level `as_of` of `2026-08-15`, route, split, evidence group, parallel group, the
   absence of bound units, tool expectations, and reference answers, and the language-matched
   abstention reasons' completeness-frontier basis (`complete_through`, the 2026-07-17 capture
   instant), fail-closed no-inference-beyond-the-frontier boundary, and no-observation-leak
   boundary.
2. Do not mark either record approved, move it into `core/`, or raise the approved count above
   18/40 without an explicit named human decision. Stop after recording that decision and a green
   full baseline; do not select or author another pair.
3. Preserve the frozen matrix, approved core, source, rights, schema, trace, and runtime boundaries;
   do not begin provider/live-model integration, paid work, probes, or the deferred bounded loop.

Open operational check, not an M2 blocker: manually dispatch one secret-backed append-only
harvester run only with separate owner authorization; otherwise the next weekly schedule will use
the configured Actions secrets normally.

Week-1 gate (charter v2.3 §7): **passed 2026-07-18**. Endpoint/range spikes, exact source-rights
policy and four approved series decisions, strict catalogs, availability design, owner
employer-risk review, contract `2.0.0`/ledger 1.0.0/manifest-rights integration, resolver
regression, harvester, real forward snapshots, approved CLI consolidation, number normalization,
default-branch workflow activation, and the paid Ministral 3 3B QLoRA compatibility result are all
complete.

## Blockers and environment notes

- No development machine has a training GPU. The disposable RunPod A40/CUDA 13 path is verified,
  `runpodctl` and its dedicated SSH key are configured locally, and no Pod remains active. Any
  later multi-configuration training still requires a separate paid-operation authorization and
  spend estimate.
- Development spans multiple machines. `.venv` is machine-local — recreate it per the README quick start on whichever machine picks this up. Nothing in the repo may depend on machine-specific paths.
- Windows workstation note: the user-level Python launcher was unreliable. The PowerShell
  discovery and interpreter-validation procedure is now committed in `AGENTS.md` and the
  cross-machine handoff. The exact executable path remains machine-local and must never be added
  to the repository; ADR 0006 closed the historical path-remediation question. Standard Windows
  Python has no system IANA timezone database, so the pinned requirements now install `tzdata`
  only on `win32`; large parametrized payload tests must use short explicit IDs to stay below the
  Windows environment-variable limit.
- Windows workstation note (2026-07-30): a stale repository-root `.pytest_tmp` directory (the
  configured pytest `--basetemp`) can be left behind with an access-denying ACL that the current
  unelevated user cannot list, take ownership of, or delete; while present, every pytest run fails
  its tmp-path setup with `WinError 5`. Do not change its ACL or delete it during repository work;
  pass an explicit `--basetemp` override to a new OS temporary path. Any cleanup is a separate
  owner-managed workstation operation outside this workflow. The directory is git-ignored and
  contains no project data.
- Rights gate: ADRs 0004/0007/0009 and charter v2.5, the append-only catalog chain, two approved
  ECOS rows,
  exact KOSIS CPI and OECD CLI rows, and typed manifest-rights bundle validation are complete. The
  exact BOK Economic Outlook document family is separately `allowed` under ADR 0009 without a
  data-series rights link. The local snapshots are captured and the two exact GitHub Actions
  secrets are configured. They remain distinct from the ignored local `.env`; their plaintext
  cannot be retrieved from GitHub.
- Vintage semantics: OECD monthly `EDITION` codes do not encode availability dates. The
  `EditionAvailabilityLedger`, fail-closed selection, and selected-row resolver are implemented;
  unknown editions abstain mechanically. The first real ledger resolves only `202607`; all 329
  older codes remain unknown until acceptable historical evidence exists.
- macOS laptop note: `python@3.12` was installed via Homebrew on 2026-07-17 and is the interpreter
  for the machine-local `.venv` (project standard per ADR 0001).
- GitHub CLI is authenticated as `bwade9090` on the Mac only; the Windows workstation must use its
  own Git/GitHub authentication. `main` tracks `origin/main`.
- `main` tracks `origin/main`; the validated `codex/m1b-harvester` work was fast-forwarded to the
  default branch. The weekly workflow is active there; the remote feature branch is retained as
  non-authoritative review history and may be removed later by the owner.
- Live-event calendar: primary = the next observed OECD edition rollover (the exact date is not yet
  verified; append-only polling must detect it); fallback = the July-vs-June edition diff, subject to
  availability provenance; stretch = Korea Q2-2026 advance GDP release (~2026-07-23/24, tight — see
  charter §7).

## Spend ledger

| Date | Operation | Cost | Evidence |
|---|---|---:|---|
| 2026-07-14 | Local foundation and PyPI dependencies | $0.00 | No model/API/GPU call |
| 2026-07-14 | Concept reorientation (docs only) | $0.00 | No model/API/GPU call under project budget |
| 2026-07-15 | Week-1 public endpoint and rights verification spikes | $0.00 | Key-free OECD/BOK/KOSIS/public-policy reads; no paid call |
| 2026-07-16 | ECOS/KOSIS official use-guide and producer verification | $0.00 | Public policy/metadata reads only; no observation or paid call |
| 2026-07-16 | Rights catalog contract and two approved ECOS metadata rows | $0.00 | Offline code/schema/tests; no observation payload or paid call |
| 2026-07-16 | Charter v2.2 approval and cross-machine handoff | $0.00 | Documentation, offline validation, commit/push only |
| 2026-07-17 | Employer-risk review record (ADR 0006) and macOS 3.12 environment | $0.00 | Documentation and offline validation only; no paid call |
| 2026-07-17 | ADR 0005 contract unit implementation and adversarial review | $0.00 | Offline code/schema/tests; agent review under subscription, no project API/GPU call |
| 2026-07-17 | Offline as-of resolver + temporary official-response regression | $0.00 | Key-free OECD reads; temporary responses deleted; no paid call |
| 2026-07-17 | Weekly harvester implementation + first OECD constraint capture | $0.00 | Key-free metadata-only OECD reads; no observation or paid call |
| 2026-07-17 | Exact KOSIS CPI/CLI rights implementation + first approved captures | $0.00 | Free official APIs and key-free OECD download; no paid call |
| 2026-07-17 | Ministral 3 QLoRA metadata/fixture preflight | $0.00 | Public Hub metadata/config only; no weights or GPU |
| 2026-07-17 | ECOS/KOSIS GitHub Actions secret registration | $0.00 | Encrypted repository secrets; names/timestamps verified, values not read back |
| 2026-07-18 | RunPod A40/CUDA 13 Ministral 3 QLoRA compatibility | $0.23584524099715054 | Finalized billing for 1,832,105 ms across five A40 provisioning/success Pods; account balance `$20.0000000000` -> `$19.7641547592`; all Pods deleted, current spend `$0`/h |
| 2026-07-24 | Core authoring matrix and first four-record draft batch | $0.00 | Offline committed evidence replay only; no network, model, or paid call |
| 2026-07-25 | Owner approval of the core matrix and first four records | $0.00 | Annotation and governance update only; no network, model, or paid call |
| 2026-07-28 | Offline bilingual temporal document retrieval | $0.00 | Synthetic fixtures and local tests only; no source download, network, model, or paid call |
| 2026-07-28 | New-session handoff finalization | $0.00 | Documentation and offline validation only; no network, source download, model, or paid call |
| 2026-07-28 | Execution-contract review, ADR 0008, and charter v2.4 | $0.00 | Multi-agent review under subscription; documentation and offline validation only; no project API/GPU call |
| 2026-07-28 | First real BOK bilingual document manifests | $0.00 | Public official pages and direct PDF captures under `/tmp` for hashing only; provider bodies not committed |
| 2026-07-28 | BOK Economic Outlook rights correction, ADR 0009, and charter v2.5 | $0.00 | Owner ruling plus free read-only checks of official BOK policy/public-data pages and the public-data portal; no model/API/GPU call |
| 2026-07-28 | First bilingual BOK documentary draft pair | $0.00 | Free official PDF re-fetch into a temporary directory, local hash/text/page-render inspection, offline authoring/tests; temporary provider files deleted |
| 2026-07-29 | Owner approval of the first bilingual documentary pair | $0.00 | Annotation, lifecycle, tests, and governance update only; no network, model, or paid call |
| 2026-07-29 | Windows continuation onboarding refresh | $0.00 | Documentation and offline validation only; no source read, model, API, GPU, or paid call |
| 2026-07-29 | Windows baseline repair + typed execution/trace contract slice | $0.00 | Free PyPI `tzdata` install, offline schemas/fixture/tests/specification, and subscription red-team review; no provider read, live model API, GPU, or paid call |
| 2026-07-29 | Trusted latest-only snapshot registry/reader slice | $0.00 | Offline reuse of the three existing committed captures, tests/specification, and subscription review; no network, provider request, secret, live model API, GPU, or paid call |
| 2026-07-29 | Trusted temporal-document registry/adapter slice | $0.00 | Offline synthetic corpus, typed adapter, tests/specification, and subscription review; no network, provider read, secret, live model API, GPU, or paid call |
| 2026-07-30 | Trusted historical STES registry/adapter slice | $0.00 | Offline reuse of committed public artifacts, typed adapter, tests/specification, and subscription red-team review; no network, provider read, secret, live model API, GPU, or paid call |
| 2026-07-30 | Frozen callable registry/dispatcher + snapshot call-time hardening | $0.00 | Offline committed artifacts, typed dispatch/replay tests, specification, and subscription review; no network, provider read, secret, live model API, GPU, or paid call |
| 2026-07-30 | Post-dispatcher session-close onboarding finalization | $0.00 | Documentation and offline consistency review only; no source/provider read, secret, live model API, GPU, or paid call |
| 2026-08-02 | Offline one-shot planner boundary | $0.00 | Offline implementation, exact-byte replay tests, specification, and full validation only; no provider, live model API, GPU, or paid call |
| 2026-08-07 | Deterministic evidence-packet assembler | $0.00 | Offline private assembler, focused tests, specification, review, and full validation only; no provider, live model API, GPU, or paid call |
| 2026-08-11 | Private offline executor | $0.00 | Offline executor, real committed registry/corpus replay, focused tests, specification, review, and full fresh-OS-basetemp validation only; no network, provider, live model integration, GPU, or paid call; repository `.pytest_tmp` ACL untouched |
| 2026-08-11 | Committed real-digest replay traces | $0.00 | Five deterministic traces generated through the real private executor and committed registry/corpus, exact-byte checks, focused/full offline validation, and review only; no network, provider/live-model integration, source or rights change, GPU, or paid call; repository `.pytest_tmp` ACL untouched |
| 2026-08-19 | Bilingual ECOS GDP draft pair | $0.00 | Exactly two draft records from the existing ECOS snapshot whose KOR-RTD use is owner-approved, focused tests, and full fresh-OS-basetemp validation only; no network, provider/live-model call, source or rights change, GPU, or paid call; repository `.pytest_tmp` ACL untouched |
| 2026-08-20 | Owner approval of the bilingual ECOS GDP pair | $0.00 | Named reviewer metadata, lifecycle move to `core-batch-003`, focused/full offline validation, and governance update only; no matrix, source, rights, schema, trace, runtime, network, provider/live-model, GPU, or paid change; repository `.pytest_tmp` ACL untouched |
| 2026-08-20 | Bilingual ECOS current-account draft pair | $0.00 | Exactly two draft records from the existing ECOS snapshot whose KOR-RTD use is owner-approved, focused tests, and full fresh-OS-basetemp validation only; no matrix, approved-core, source, rights, schema, trace, runtime, network, provider/live-model, GPU, or paid change; repository `.pytest_tmp` ACL untouched |
| 2026-08-21 | Owner approval of the bilingual ECOS current-account pair | $0.00 | Named reviewer metadata, lifecycle move to `core-batch-004`, focused/full offline validation, and governance update only; no matrix, source, rights, schema, trace, runtime, network, provider/live-model, GPU, or paid change |
| 2026-08-21 | Bilingual KOSIS CPI draft pair | $0.00 | Exactly two draft records from the existing KOSIS snapshot whose KOR-RTD use is owner-approved, focused tests, and full fresh-OS-basetemp validation only; no matrix, approved-core, source, rights, schema, trace, runtime, network, provider/live-model, GPU, or paid change |
| 2026-08-25 | Owner approval of the bilingual KOSIS CPI pair | $0.00 | Named reviewer metadata, lifecycle move to `core-batch-005`, focused/full offline validation, and governance update only; no matrix, source, rights, schema, trace, runtime, network, provider/live-model, GPU, or paid change |
| 2026-08-25 | Bilingual OECD scope abstention draft pair | $0.00 | Exactly two draft records binding no source units, using only the committed rights catalog as the fail-closed basis, focused tests, and full fresh-OS-basetemp validation only; no matrix, approved-core, source, rights, schema, trace, runtime, network, provider/live-model, GPU, or paid change |
| 2026-08-26 | Owner approval of the bilingual OECD scope abstention pair | $0.00 | Named reviewer metadata, lifecycle move to `core-batch-006`, focused/full offline validation, and governance update only; no matrix, source, rights, schema, trace, runtime, network, provider/live-model, GPU, or paid change |
| 2026-08-26 | Bilingual CPI revision false-premise abstention draft pair | $0.00 | Exactly two draft records binding no source units, using only the committed rights catalog and manifest vintage semantics as the fail-closed basis, focused tests, and full fresh-OS-basetemp validation only; no matrix, approved-core, source, rights, schema, trace, runtime, network, provider/live-model, GPU, or paid change |
| 2026-08-26 | Owner approval of the bilingual CPI revision false-premise abstention pair | $0.00 | Named reviewer metadata, lifecycle move to `core-batch-007`, focused/full offline validation, and governance update only; no matrix, source, rights, schema, trace, runtime, network, provider/live-model, GPU, or paid change |
| 2026-08-26 | Bilingual missing-as-of abstention draft pair | $0.00 | Exactly two draft records binding no source units, using only the fail-closed explicit-cutoff contract as the abstention basis, focused tests, and full fresh-OS-basetemp validation only; no matrix, approved-core, source, rights, schema, trace, runtime, network, provider/live-model, GPU, or paid change |
| 2026-08-27 | Owner approval of the bilingual missing-as-of abstention pair | $0.00 | Named reviewer metadata, lifecycle move to `core-batch-008`, focused/full offline validation, and governance update only; no matrix, source, rights, schema, trace, runtime, network, provider/live-model, GPU, or paid change |
| 2026-08-27 | Bilingual ledger frontier abstention draft pair | $0.00 | Exactly two draft records binding no source units, using only the committed availability ledger's completeness frontier as the fail-closed basis, focused tests, and full fresh-OS-basetemp validation only; no matrix, approved-core, source, rights, schema, trace, runtime, network, provider/live-model, GPU, or paid change |

**Cumulative external spend: $0.23584524099715054 / $100.00**

## Handoff rule (onboarding for a new contributor or AI agent)

Read in this order, in full, before changing anything:

1. `AGENTS.md` — working protocol, evidence rules, setup, repository map.
2. `docs/project/01_project_charter.md` — the v2.5 scope authority.
3. This file — current milestone, next action, gates, blockers.
4. Accepted ADRs 0001–0009 in `docs/decisions/` (ADR 0008 fixes the join unit's typed
   function-calling execution contract and defers the bounded tool loop to v1.1; ADR 0009 records
   the BOK Economic Outlook public-data family ruling).
5. `docs/project/04_macbook_handoff.md` — cross-machine Windows setup, exact continuation order,
   and acceptance criteria (legacy filename retained for stable links).
6. `docs/discovery/01_concept_upgrade_proposal.md` — background: why v2 exists, verified data facts,
   judged alternatives, risk register.
7. `docs/project/05_evidence_contract_2_0_migration.md` — the implemented contract the resolver
   and harvester build on.
8. `docs/project/07_core_authoring_matrix.md` — the approved M2 allocation and human-review
   boundary.
9. `docs/project/08_temporal_document_retrieval.md` — the implemented filter-before-scoring
   document retrieval boundary.
10. `docs/project/09_typed_execution_trace_contract.md` — the frozen execution contract,
    snapshot/STES flat arguments, replay provenance, and trace invariants.
11. `docs/project/10_snapshot_reader_contract.md` — the implemented trusted snapshot registry,
    deterministic reader, provider parsers, result taxonomy, and execution boundary.
12. `docs/project/11_temporal_retrieval_adapter_contract.md` — the implemented trusted synthetic
    corpus registry, typed adapter, replay digest, and result validation.
13. `docs/project/12_stes_adapter_contract.md` — the implemented trusted historical registry,
    XML/ledger/catalog/archive joins, flat typed adapter, and dispatcher handoff.
14. `docs/project/13_callable_dispatcher_contract.md` — the frozen three-tool callable registry,
    composite replay provenance, explicit dispatcher, and independent reference replay.
15. `docs/project/14_offline_planner_contract.md` — the implemented planner, private exact-byte
    recording boundary, request binding, and deterministic replay.
16. `docs/project/15_evidence_packet_assembler_contract.md` — the implemented private assembler,
    ordered-result binding, abstention semantics, and no-partial-evidence boundary.
17. `docs/project/16_offline_executor_contract.md` — the implemented private executor, one-shot
    state machine, sanitized trace/failure mapping, and real provenance construction.
18. `traces/README.md` — the public/private trace boundary, committed replay matrix, exact-byte
    reproduction commands, and rationale for not fabricating healthy-stack failure traces.
19. `scripts/export_execution_replay_traces.py`, `tests/execution/test_replay_traces.py`, and the
    five JSON files under `traces/replay/v1/` — the deterministic exporter, real-boundary replay
    checks, and committed machine-readable outcomes that complete work unit C.
20. `src/sovereignlab/schemas/execution.py` and `tests/schemas/test_execution.py` — frozen
    request/plan/result/packet/trace invariants reused by the executor and committed traces.
21. `src/sovereignlab/execution/executor.py` and `tests/execution/test_executor.py` — the completed
    private offline executor and its focused real-registry, state-machine, provenance, drift,
    sanitization, and deterministic round-trip coverage.
22. The dispatcher, planner, and assembler source/test pairs under `src/sovereignlab/execution/`
    and `tests/execution/` — completed frozen boundaries coordinated by the executor and replay
    traces without reopening them.
23. `data/benchmark/core/core-batch-003.jsonl` and
    `tests/benchmark/test_ecos_gdp_core.py` — the approved two-record ECOS GDP core batch and its
    focused frozen-allocation, evidence, cutoff, bilingual-parity, and approval-lifecycle checks.
24. `data/benchmark/core/core-batch-004.jsonl` and
    `tests/benchmark/test_ecos_current_account_core.py` — the approved two-record ECOS current-
    account core batch and its focused frozen-allocation, evidence, cutoff, bilingual-parity, and
    approval-lifecycle checks.
25. `data/benchmark/core/core-batch-005.jsonl` and
    `tests/benchmark/test_kosis_cpi_core.py` — the approved two-record KOSIS CPI core batch and
    its focused frozen-allocation, evidence, cutoff, bilingual-parity, and approval-lifecycle
    checks.
26. `data/benchmark/core/core-batch-006.jsonl` and
    `tests/benchmark/test_oecd_scope_abstain_core.py` — the approved two-record OECD scope
    abstention core batch and its focused frozen-allocation, no-bound-unit, rights-basis,
    bilingual-parity, approval-lifecycle, and no-observation-leak checks.
27. `data/benchmark/core/core-batch-007.jsonl` and
    `tests/benchmark/test_cpi_revision_abstain_core.py` — the approved two-record CPI revision
    false-premise abstention core batch and its focused frozen-allocation, no-bound-unit,
    false-premise/rights-basis, bilingual-parity, approval-lifecycle, and no-observation-leak
    checks.
28. `data/benchmark/core/core-batch-008.jsonl` and
    `tests/benchmark/test_missing_as_of_abstain_core.py` — the approved two-record missing-as-of
    abstention core batch and its focused frozen-allocation, no-bound-unit, missing-cutoff-basis,
    bilingual-parity, approval-lifecycle, and no-observation-leak checks.
29. `data/benchmark/drafts/core-draft-009.jsonl` and
    `tests/benchmark/test_ledger_frontier_abstain_draft.py` — the pending two-record ledger
    frontier abstention draft pair and its frozen-allocation, no-bound-unit,
    completeness-frontier-basis, bilingual-parity, draft-lifecycle, and no-observation-leak
    checks.

Then follow "Immediate next action" item 1: review only the two `kv-core-abstain-05` drafts. The
structural matrix and first eighteen records are owner-approved; the other 22 slots remain
unapproved, with two pending drafts and 20 unauthored slots. No later pair or implementation
slice has been selected.
The synthetic retrieval baseline and first real bilingual document manifests are complete. ADR
0009 resolves those
manifests to `allowed`, but full PDFs and extracted full text remain outside Git by current
repository-scope choice. Do not start full LoRA tuning, UI, or release work before the M2 gate
closes. The harvester must stay within approved rights scopes, and every later paid operation
remains smoke-test-first. Do not weaken the qualification rules for "first" claims or the
rights/append-only rules in `AGENTS.md`.
Update this file whenever a milestone state, blocker, cost, spike result, or next action changes.
