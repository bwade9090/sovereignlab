# SovereignLab CV bullets

- Status: wording bank; use only the section matching the achieved milestone
- Last updated: 2026-08-27 (M2 mid-window refresh: 18/40 approved core, ADR 0008 slices 1–9 and
  work unit C complete, two ledger-frontier abstention drafts pending review, 78-file/1,171-test
  baseline)
- Rule: never replace placeholders with targets or estimates; use measured, reproducible results only
- Narrative versions: `docs/application/01_project_description.md`

## Version A — safe to use now (project in progress)

**SovereignLab — K-VINTAGE on KOR-RTD: vintage-conditioned evaluation for high-stakes economic research (Open Source, in progress)**

### Long form

- Built the initial **KOR-RTD** point-in-time layer for Korean macroeconomics: strict provenance and
  source-rights contracts, append-only checksummed ECOS/KOSIS captures, a 75,060-row OECD Korea CLI
  archive across 239 editions, and a fail-closed resolver that abstains when edition availability
  at the requested cutoff cannot be proven.
- Building **K-VINTAGE**, a bilingual Korean/English benchmark whose gold answers depend on the
  official-statistics vintage available at each question's `as_of` date: the 40-question
  human-reviewed core allocation is frozen and 18/40 records are reviewed and approved so far —
  four data/abstention records over the OECD Korea CLI revision archive plus a Korean/English
  documentary pair grounded in the Bank of Korea's May 2026 Economic Outlook and its independently
  dated official English translation, Korean/English data pairs over the 2026-07-17 ECOS GDP and
  current-account snapshots, a Korean/English data pair over the 2026-07-17 KOSIS national CPI
  snapshot, a Korean/English rights-based abstention pair asking for Korea's OECD normalised
  CLI, a neighboring measure outside the sole owner-approved OECD raw-data scope, a
  Korean/English false-premise abstention pair that rejects the premise that archived OECD
  edition counts prove the Korean CPI was revised, and a Korean/English missing-as-of
  clarification abstention pair that asks for Korea's OECD amplitude-adjusted CLI for May 2026
  while omitting the as-of date the vintage request depends on, so the approved gold behavior
  is to ask for the missing as-of and abstain. A separate Korean/English abstention pair asking
  for Korea's OECD amplitude-adjusted CLI for May 2026 using only the vintage available as of
  August 15, 2026 — a cutoff beyond the committed availability ledger's completeness frontier
  (`complete_through`, the 2026-07-17 capture instant), so the drafted gold behavior is
  abstention with `cutoff_beyond_complete_through` — is complete only as two AI-authored drafts
  pending named human review and is not included in the 18/40 approved count; machine-generated
  revision probes will be reported separately.
- Shipped `typed function calling with committed traces` for the deterministic offline evidence
  path: bilingual temporal retrieval filters by publication date before scoring over a committed
  synthetic corpus; three digest-linked evidence tools run behind a replay-checked dispatcher; and
  five machine-readable real-digest traces generated through the actual private executor,
  `ScriptedPlanner`, and committed registries and corpus cover all four routes, all three tools,
  Korean and English, explicit and implicit cutoffs, complete execution, planned abstention, and
  terminal tool abstention without partial evidence. The source package and the project's 13
  public JSON Schemas remain unchanged. These are deterministic offline replay artifacts, not
  provider or live outputs, and no briefing-quality result is claimed.
- Verified the pinned Ministral 3 3B NF4/QLoRA compatibility path on a disposable A40/CUDA 13 GPU
  and maintain 1,171 tests at 100% statement/branch coverage (4,679 statements, 1,568 branches)
  across 78 formatted Python files; temporal leakage remains the planned headline metric, and no
  model-quality result is claimed yet.

### Short form (single bullet)

- Building **SovereignLab / K-VINTAGE** (in progress): to our knowledge, for official statistics,
  the first benchmark whose gold answers depend on the data vintage available at each question's
  `as_of` date (prior art: arXiv 2605.23497, the Dallas Fed real-time OECD dataset, and the OECD MEI
  revisions database), built on **KOR-RTD** — a provenance-contracted point-in-time archive of Korean
  macro data with append-only checksummed captures and a fail-closed vintage resolver. Current
  state: 18/40 reviewed-and-approved bilingual core records, cutoff-filtered bilingual temporal
  retrieval over a committed synthetic corpus, a frozen typed execution-and-trace contract within
  the project's 13 public JSON Schemas, three deterministic evidence tools behind a replay-checked
  dispatcher, a private provenance-bound offline executor, and `typed function calling with
  committed traces`: five real-digest offline replays covering all routes and tools, both languages,
  both cutoff modes, complete execution, and planned/tool abstention with terminal stop and no
  partial evidence. Two additional ledger-frontier abstention records remain draft-only pending
  named human review and are not counted in the 18/40 approved core. The verified Ministral 3 3B
  NF4/QLoRA compatibility path is retained, and 1,171 tests pass at 100% statement/branch
  coverage; temporal leakage is the planned headline metric and no model-quality or
  briefing-performance result is claimed yet.

This version distinguishes the deterministic offline replay slice from provider/live integration,
the two pending draft records, the 20 unauthored core slots, and the not-yet-evaluated model
variants.

## Version B — use after the Week 2 baseline is reproducible

**SovereignLab — K-VINTAGE on KOR-RTD (Open Source)**

- Built **KOR-RTD**, a point-in-time data layer for Korean macroeconomics (consolidated OECD edition histories plus an append-only public harvester over the latest-only ECOS/KOSIS APIs, **[N_SNAPSHOTS]** checksummed snapshots to date), and a deterministic fail-closed resolver that selects the latest edition whose availability by `as_of` is proven in a committed ledger, exposing "what did the data say then" as a queryable capability.
- Created **K-VINTAGE**: **[N_CORE]** manually reviewed Korean/English core questions across document, data, cross-evidence, and abstention routes, plus **[N_PROBES]** machine-generated revision-trap probes with computed, regenerable gold answers; measured temporal leakage, retrieval recall, citation correctness, structured tool accuracy, latency, and per-request cost across three baseline architectures.

## Version C — final target after LoRA and productization

**SovereignLab — K-VINTAGE on KOR-RTD (Creator)**

- Built **KOR-RTD**, a complementary point-in-time layer for Korea's public statistical infrastructure: consolidated OECD edition histories, an append-only weekly harvester over the latest-only official APIs, per-snapshot checksums and licensing decisions, and full regeneration from committed manifests — including a cited bilingual briefing generated on a real release day with creation time independently verifiable from public CI logs.
- Published **K-VINTAGE** (**[N_CORE]** human-reviewed core questions + **[N_PROBES]** machine-generated probes, reported separately) and a four-variant baseline suite (closed-book, temporal RAG, RAG + vintage tool, LoRA router), achieving **[LEAKAGE]%** temporal leakage and **[CITATION]%** citation correctness, every number reproducible from committed manifests, traces, and one evaluation command.
- Fine-tuned **[MODEL]** with QLoRA for evidence routing and structured vintage-aware tool use on **[N_TRAIN]** evidence-disjoint examples, changing held-out route macro-F1 from **[BASE]** to **[LORA]** (**[DELTA]** points) under a pre-frozen promotion rule; negative results and failure taxonomy published.

## Accuracy and disclosure rules

- Keep `(in progress)` while the M2 benchmark and baseline work remains incomplete; the committed
  replay slice does not imply benchmark completion.
- Do not say `fine-tuned` until an adapter has been trained, loaded, and evaluated.
- Do not cite benchmark size until each counted test item passes schema and human review; **always report the human-reviewed core and machine-generated probes as separate counts**. The current approved core count is 18/40; of the 22 unapproved slots, two are AI-authored drafts pending named human review and 20 remain unauthored.
- Core records are initially AI-authored and then human-reviewed; do not claim personal manual
  authorship of individual records. "Reviewed and approved" is the accurate personal-CV verb.
- Do not cite improvement, cost, latency, leakage, or error-rate figures until the aggregation command reproduces them from committed artifacts.
- Do not imply real-document retrieval: the committed searchable corpus is synthetic-only, and the
  real Bank of Korea report bodies are manifest-bound without committed searchable chunks.
  Disclose the synthetic corpus whenever retrieval is described near the real documentary pair.
- Attribute the 13 public JSON Schemas to the combined evidence, benchmark, matrix,
  availability-ledger, rights, and execution contracts; the execution/trace contract itself
  contributed six of them.
- Do not make deployment claims from compatibility or deterministic replay evidence; neither
  establishes an integrated serving path.
- Describe the shipped minimal path only as `typed function calling with committed traces`. The
  bounded tool loop remains deferred to v1.1 (ADR 0008), and the committed deterministic offline
  replays do not support provider/live, model-quality, or briefing-performance claims.
- Every "first" claim must read "to our knowledge, for official statistics" and the datasheet must cite prior art first (arXiv 2605.23497 statutory as-of QA; Dallas Fed real-time OECD dataset; OECD MEI revisions database). Never claim "first Korean macro benchmark" (KMMLU includes economics categories).
- Do not claim OECD edition/backfill ranges beyond what a recorded verification spike confirmed.
- Do not cite harvester snapshot counts older than the public commit history that proves them.
- If Korea's AI Basic Act is mentioned in any narrative, describe it precisely: "high-impact" (고영향) AI, voluntary verification/certification — not "high-risk" or mandatory testing.
- Do not imply affiliation with or endorsement by the Bank of Korea, OECD, or Mistral; all public activity is in a personal capacity.
