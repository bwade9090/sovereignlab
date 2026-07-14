# SovereignLab CV bullets

- Status: wording bank; use only the section matching the achieved milestone
- Last updated: 2026-07-14
- Rule: never replace placeholders with targets or estimates; use measured, reproducible results only

## Version A — safe to use now (project in progress)

**SovereignLab — Eval-Driven Mistral Deployment for High-Stakes Economic Research (Open Source, in progress)**

- Designing a bilingual Korean/English economic-research system that combines temporally filtered hybrid RAG, official OECD SDMX tools, and citation-level provenance to produce auditable, `as-of` policy briefings from public sources.
- Building a controlled benchmark comparing closed-book generation, temporal RAG, agentic tool use, and LoRA-tuned evidence routing across citation correctness, temporal leakage, abstention, latency, and cost, with portable local open-weight and Mistral API deployment paths.

This version is intentionally phrased with `Designing` and `Building`. It does not imply that training or benchmark results already exist.

## Version B — use after the Week 2 baseline is reproducible

**SovereignLab — Eval-Driven Mistral Deployment for High-Stakes Economic Research (Open Source)**

- Built a bilingual Korean/English macroeconomic research pipeline combining temporally filtered hybrid RAG with an OECD SDMX tool, returning typed evidence packets and citation-grounded briefings from public official sources.
- Created a manually reviewed, evidence-disjoint benchmark of **[N]** document, data, cross-evidence, and abstention tasks; measured retrieval recall, citation correctness, temporal leakage, structured tool accuracy, latency, and per-request cost across three baseline architectures.

## Version C — final target after LoRA and productization

**SovereignLab — Eval-Driven Sovereign AI Deployment Lab (Creator)**

- Built a bilingual Korean/English Mistral system for auditable economic-policy research, combining temporal hybrid RAG, an official OECD SDMX tool, citation/numerical provenance, and portable local/API deployment behind FastAPI and an interactive trace UI.
- Fine-tuned **[MODEL]** with QLoRA for evidence routing and structured tool use on **[N_TRAIN]** evidence-disjoint examples, improving held-out route macro-F1 from **[BASE]** to **[LORA]** (**[DELTA]** percentage points) while changing median latency/cost by **[MEASURED RESULT]**.
- Published a **[N_TEST]**-question Korean/English benchmark and four-way ablation (`closed-book`, temporal RAG, RAG+tools, LoRA router), achieving **[CITATION]%** citation correctness and **[TEMPORAL]%** temporal leakage; made every reported result reproducible through versioned manifests, recorded traces, tests, CI, and a deployment runbook.

## Compact one-bullet version

- Building **SovereignLab**, an open-source Korean/English Mistral deployment lab that evaluates temporal RAG, OECD SDMX tool use, and LoRA-tuned evidence routing for citation-grounded economic briefings across accuracy, temporal leakage, abstention, latency, and cost.

## Accuracy and disclosure rules

- Keep `(in progress)` until the public repository contains a runnable vertical slice.
- Do not say `fine-tuned` until an adapter has been trained, loaded, and evaluated.
- Do not cite benchmark size until each counted test item passes schema and human review.
- Do not cite improvement, cost, latency, or error-rate figures until the aggregation command reproduces them from committed artifacts.
- Do not describe CPU/API fallback as `on-prem production deployment`; use `portable local/API deployment path` until a documented local run exists.
- Do not imply affiliation with or endorsement by the Bank of Korea, OECD, or Mistral.
