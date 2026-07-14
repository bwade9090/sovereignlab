# SovereignLab CV bullets

- Status: wording bank; use only the section matching the achieved milestone
- Last updated: 2026-07-14 (rewritten for the charter v2 K-VINTAGE on KOR-RTD reorientation)
- Rule: never replace placeholders with targets or estimates; use measured, reproducible results only

## Version A — safe to use now (project in progress)

**SovereignLab — K-VINTAGE on KOR-RTD: vintage-conditioned evaluation for high-stakes economic research (Open Source, in progress)**

- Designing **K-VINTAGE**, a bilingual (Korean/English) macroeconomic QA benchmark in which gold answers are computed from the statistical data vintage available at each question's as-of date — to our knowledge the first such benchmark for official statistics — with deterministic grading from OECD SDMX edition histories, evidence-disjoint splits, four evidence-route labels including calibrated abstention, and a public gold-answer regeneration script.
- Building **KOR-RTD**, a provenance-contracted point-in-time data layer for Korean macroeconomics: consolidated OECD edition histories with per-snapshot SHA-256 checksums and per-source licensing decisions, plus a scheduled public harvester that forward-captures Korea's official statistics APIs (ECOS/KOSIS), which expose latest values only — commit history serving as independently verifiable proof of capture dates.
- Building the reference briefing service and baseline suite on this layer (temporal RAG + deterministic vintage tool + QLoRA-tuned compact open-weight router evaluated under a pre-frozen promotion rule — Ministral 3 planned, subject to the week-1 compatibility spike), reporting temporal-leakage rate as a deterministically verified headline metric; measured results are inserted only after evaluation runs complete, per this file's disclosure rules.

This version is intentionally phrased with `Designing` and `Building`. It does not imply that the archive, benchmark, or training results already exist.

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
