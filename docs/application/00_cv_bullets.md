# SovereignLab CV bullets

- Status: wording bank; use only the section matching the achieved milestone
- Last updated: 2026-07-18 (M1b gate passed; M2 wording synchronized)
- Rule: never replace placeholders with targets or estimates; use measured, reproducible results only
- Narrative versions: `docs/application/01_project_description.md`

## Version A — safe to use now (project in progress)

**SovereignLab — K-VINTAGE on KOR-RTD: vintage-conditioned evaluation for high-stakes economic research (Open Source, in progress)**

- Built the initial **KOR-RTD** point-in-time layer for Korean macroeconomics: strict provenance and
  source-rights contracts, append-only checksummed ECOS/KOSIS captures, a 75,060-row OECD Korea CLI
  archive across 239 editions, and a fail-closed resolver that abstains when edition availability
  at the requested cutoff cannot be proven.
- Designing **K-VINTAGE**, a bilingual Korean/English benchmark whose gold answers depend on the
  official-statistics vintage available at each question's `as_of` date, with a planned 40-question
  human-reviewed core and separately reported deterministic revision probes across document, data,
  cross-evidence, and abstention routes.
- Verified the pinned Ministral 3 3B NF4/QLoRA compatibility path on a disposable A40/CUDA 13 GPU
  and maintain 337 tests at 100% statement/branch coverage; now building temporal RAG, deterministic
  vintage-tool integration, and the four-variant baseline suite with temporal leakage as the
  headline metric. No model-quality result is claimed yet.

This version distinguishes the implemented data/tooling foundation and compatibility result from
the not-yet-authored benchmark and not-yet-evaluated model variants.

## Version B — use after the Week 2 baseline is reproducible

**SovereignLab — K-VINTAGE on KOR-RTD (Open Source)**

- Built **KOR-RTD**, a point-in-time data layer for Korean macroeconomics (consolidated OECD edition histories plus an append-only public harvester over the latest-only ECOS/KOSIS APIs, **[N_SNAPSHOTS]** checksummed snapshots to date), and a deterministic as-of resolver (`as_of -> max(edition <= as_of)`) exposing "what did the data say then" as a queryable capability.
- Created **K-VINTAGE**: **[N_CORE]** manually reviewed Korean/English core questions across document, data, cross-evidence, and abstention routes, plus **[N_PROBES]** machine-generated revision-trap probes with computed, regenerable gold answers; measured temporal leakage, retrieval recall, citation correctness, structured tool accuracy, latency, and per-request cost across three baseline architectures.

## Version C — final target after LoRA and productization

**SovereignLab — K-VINTAGE on KOR-RTD (Creator)**

- Built **KOR-RTD**, the point-in-time data layer Korea's public statistics infrastructure does not provide: consolidated OECD edition histories, an append-only weekly harvester over the latest-only official APIs, per-snapshot checksums and licensing decisions, and full regeneration from committed manifests — including a cited bilingual briefing generated on a real release day with creation time independently verifiable from public CI logs.
- Published **K-VINTAGE** (**[N_CORE]** human-reviewed core questions + **[N_PROBES]** machine-generated probes, reported separately) and a four-variant baseline suite (closed-book, temporal RAG, RAG + vintage tool, LoRA router), achieving **[LEAKAGE]%** temporal leakage and **[CITATION]%** citation correctness, every number reproducible from committed manifests, traces, and one evaluation command.
- Fine-tuned **[MODEL]** with QLoRA for evidence routing and structured vintage-aware tool use on **[N_TRAIN]** evidence-disjoint examples, changing held-out route macro-F1 from **[BASE]** to **[LORA]** (**[DELTA]** points) under a pre-frozen promotion rule; negative results and failure taxonomy published.

## Compact one-bullet version

- Building **SovereignLab / K-VINTAGE**: to our knowledge the first benchmark for official statistics whose gold answers depend on the data vintage available at each question's as-of date, built on KOR-RTD — a provenance-contracted point-in-time archive of Korean macro data — with a bilingual briefing pipeline, four-variant ablation, and QLoRA-tuned evidence routing evaluated on temporal leakage as the headline metric.

## Accuracy and disclosure rules

- Keep `(in progress)` until the public repository contains a runnable vertical slice.
- Do not say `fine-tuned` until an adapter has been trained, loaded, and evaluated.
- Do not cite benchmark size until each counted test item passes schema and human review; **always report the human-reviewed core and machine-generated probes as separate counts**.
- Do not cite improvement, cost, latency, leakage, or error-rate figures until the aggregation command reproduces them from committed artifacts.
- Do not describe CPU/API fallback as `on-prem production deployment`; use `portable local/API deployment path` until a documented fully local end-to-end run exists.
- Every "first" claim must read "to our knowledge, for official statistics" and the datasheet must cite prior art first (arXiv 2605.23497 statutory as-of QA; Dallas Fed real-time OECD dataset; OECD MEI revisions database). Never claim "first Korean macro benchmark" (KMMLU includes economics categories).
- Do not claim OECD edition/backfill ranges beyond what a recorded verification spike confirmed.
- Do not cite harvester snapshot counts older than the public commit history that proves them.
- If Korea's AI Basic Act is mentioned in any narrative, describe it precisely: "high-impact" (고영향) AI, voluntary verification/certification — not "high-risk" or mandatory testing.
- Do not imply affiliation with or endorsement by the Bank of Korea, OECD, or Mistral; all public activity is in a personal capacity.
