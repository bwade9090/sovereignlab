# SovereignLab CV bullets

- Status: wording bank; use only the section matching the achieved milestone
- Last updated: 2026-08-07 (M2 mid-window refresh: 6/40 approved core, execution-surface slices 1–7
  complete, 67-file/1,049-test baseline)
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
  human-reviewed core allocation is frozen and 6/40 records are reviewed and approved so far —
  four data/abstention records over the OECD Korea CLI revision archive plus a Korean/English
  documentary pair grounded in the Bank of Korea's May 2026 Economic Outlook and its independently
  dated official English translation — with machine-generated revision probes to be reported
  separately.
- Implemented the deterministic offline evidence surface for the planned reference briefing
  pipeline: bilingual temporal document retrieval that filters by publication date before scoring
  (currently over a committed synthetic corpus; the real report bodies remain manifest-bound
  only), a frozen typed execution-and-trace contract (six new schemas, bringing the project's
  public surface to 13 deterministic JSON Schemas), three digest-linked deterministic evidence
  tools, an explicit dispatcher that independently replays and revalidates every call, an offline
  one-shot planner with scripted and immutable recorded/replay modes, and an internal deterministic
  evidence-packet assembler that preserves ordered typed evidence and fail-closed planned/tool
  abstentions without partial-evidence leakage. The offline executor and committed end-to-end replay
  traces do not yet exist, so no end-to-end result is claimed.
- Verified the pinned Ministral 3 3B NF4/QLoRA compatibility path on a disposable A40/CUDA 13 GPU
  and maintain 1,049 tests at 100% statement/branch coverage (4,353 statements, 1,470 branches)
  across 67 formatted Python files; temporal leakage remains the planned headline metric, and no
  model-quality result is claimed yet.

### Short form (single bullet)

- Building **SovereignLab / K-VINTAGE** (in progress): to our knowledge, for official statistics,
  the first benchmark whose gold answers depend on the data vintage available at each question's
  `as_of` date (prior art: arXiv 2605.23497, the Dallas Fed real-time OECD dataset, and the OECD MEI
  revisions database), built on **KOR-RTD** — a provenance-contracted point-in-time archive of Korean
  macro data with append-only checksummed captures and a fail-closed vintage resolver. Current
  state: 6/40 reviewed-and-approved bilingual core records, cutoff-filtered bilingual temporal
  retrieval over a committed synthetic corpus, a frozen typed execution-and-trace contract within
  the project's 13 public JSON Schemas, three deterministic evidence tools behind a replay-checked
  dispatcher, an offline exact-byte-verified planner boundary, an internal deterministic
  evidence-packet assembler, a verified Ministral 3 3B NF4/QLoRA compatibility path, and 1,049
  tests at 100% statement/branch coverage; temporal leakage is the planned headline metric and no
  model-quality or end-to-end execution result is claimed yet.

This version distinguishes the implemented data, evidence-tool, planner, and packet-assembly
boundaries from the not-yet-implemented offline executor and committed replay traces, the 34
unauthored core slots, and the not-yet-evaluated model variants.

## Version B — use after the Week 2 baseline is reproducible

**SovereignLab — K-VINTAGE on KOR-RTD (Open Source)**

- Built **KOR-RTD**, a point-in-time data layer for Korean macroeconomics (consolidated OECD edition histories plus an append-only public harvester over the latest-only ECOS/KOSIS APIs, **[N_SNAPSHOTS]** checksummed snapshots to date), and a deterministic as-of resolver (`as_of -> max(edition <= as_of)`) exposing "what did the data say then" as a queryable capability.
- Created **K-VINTAGE**: **[N_CORE]** manually reviewed Korean/English core questions across document, data, cross-evidence, and abstention routes, plus **[N_PROBES]** machine-generated revision-trap probes with computed, regenerable gold answers; measured temporal leakage, retrieval recall, citation correctness, structured tool accuracy, latency, and per-request cost across three baseline architectures.

## Version C — final target after LoRA and productization

**SovereignLab — K-VINTAGE on KOR-RTD (Creator)**

- Built **KOR-RTD**, the point-in-time data layer Korea's public statistics infrastructure does not provide: consolidated OECD edition histories, an append-only weekly harvester over the latest-only official APIs, per-snapshot checksums and licensing decisions, and full regeneration from committed manifests — including a cited bilingual briefing generated on a real release day with creation time independently verifiable from public CI logs.
- Published **K-VINTAGE** (**[N_CORE]** human-reviewed core questions + **[N_PROBES]** machine-generated probes, reported separately) and a four-variant baseline suite (closed-book, temporal RAG, RAG + vintage tool, LoRA router), achieving **[LEAKAGE]%** temporal leakage and **[CITATION]%** citation correctness, every number reproducible from committed manifests, traces, and one evaluation command.
- Fine-tuned **[MODEL]** with QLoRA for evidence routing and structured vintage-aware tool use on **[N_TRAIN]** evidence-disjoint examples, changing held-out route macro-F1 from **[BASE]** to **[LORA]** (**[DELTA]** points) under a pre-frozen promotion rule; negative results and failure taxonomy published.

## Accuracy and disclosure rules

- Keep `(in progress)` until the public repository contains a runnable vertical slice.
- Do not say `fine-tuned` until an adapter has been trained, loaded, and evaluated.
- Do not cite benchmark size until each counted test item passes schema and human review; **always report the human-reviewed core and machine-generated probes as separate counts**. The current approved core count is 6/40; the 34 remaining slots are neither authored nor approved.
- Core records are initially AI-authored and then human-reviewed; do not claim personal manual
  authorship of individual records. "Reviewed and approved" is the accurate personal-CV verb.
- Do not cite improvement, cost, latency, leakage, or error-rate figures until the aggregation command reproduces them from committed artifacts.
- Do not imply real-document retrieval: the committed searchable corpus is synthetic-only, and the
  real Bank of Korea report bodies are manifest-bound without committed searchable chunks.
  Disclose the synthetic corpus whenever retrieval is described near the real documentary pair.
- Attribute the 13 public JSON Schemas to the combined evidence, benchmark, matrix,
  availability-ledger, rights, and execution contracts; the execution/trace contract itself
  contributed six of them.
- Do not describe CPU/API fallback as `on-prem production deployment`; use `portable local/API deployment path` until a documented fully local end-to-end run exists.
- Do not use `agent`, `agentic`, `multi-step`, `orchestration`, or `autonomous` wording anywhere:
  the bounded tool loop is deferred to v1.1 (ADR 0008). After the minimal path ships, the
  permitted wording is `typed function calling with committed traces` — and only then. Until that
  point, describe only the implemented components (typed execution-and-trace contract,
  deterministic evidence tools, replay-checked dispatcher, offline one-shot planner, and internal
  deterministic evidence-packet assembler) and state that the offline executor and committed
  end-to-end replay traces do not yet exist.
- Every "first" claim must read "to our knowledge, for official statistics" and the datasheet must cite prior art first (arXiv 2605.23497 statutory as-of QA; Dallas Fed real-time OECD dataset; OECD MEI revisions database). Never claim "first Korean macro benchmark" (KMMLU includes economics categories).
- Do not claim OECD edition/backfill ranges beyond what a recorded verification spike confirmed.
- Do not cite harvester snapshot counts older than the public commit history that proves them.
- If Korea's AI Basic Act is mentioned in any narrative, describe it precisely: "high-impact" (고영향) AI, voluntary verification/certification — not "high-risk" or mandatory testing.
- Do not imply affiliation with or endorsement by the Bank of Korea, OECD, or Mistral; all public activity is in a personal capacity.
