# SovereignLab project charter

- Status: approved v1
- Date: 2026-07-14
- Delivery target: four weeks, approximately 80 total hours
- Initial budget ceiling: USD 100 for model APIs and rented compute
- Repository: public at `https://github.com/bwade9090/sovereignlab`

## 1. Product thesis

High-stakes economic research needs more than fluent answers. Analysts need to know which evidence was available at a chosen point in time, where each claim and number came from, whether a question is answerable from approved sources, and what changes when a cloud model is replaced with a locally controlled open-weight model.

**SovereignLab** will be an evaluation-first, bilingual Mistral deployment lab for this problem. Its first product slice will produce an auditable Korean or English macroeconomic briefing from public official documents and an official time-series tool.

The project is deliberately framed as a customer pilot for a regulated financial or public-sector institution. It will contain discovery assumptions, measurable acceptance criteria, implementation trade-offs, operational traces, and a pilot report—not only model code.

## 2. Initial customer and workflow

### Customer persona

A country economist or policy analyst at an international institution, central bank, regulator, or regulated financial institution.

### Job to be done

> Given a Korean or English policy question and an optional `as_of` date, produce a concise briefing whose documentary claims are cited, whose numerical claims are traceable to a deterministic official-data query, and whose limitations are explicit.

### Example request

> As of May 2024, why was Korea's growth outlook revised, and do the available consumption indicators support that narrative?

The system must decide whether the request requires document retrieval, an official-data query, both, or an abstention. It must not silently use documents published after the requested cutoff.

### Domain boundary

The first release targets **Korean macroeconomic surveillance**, not policy-rate decision extraction. This creates distance from RateGauge while preserving Hyungbae's domain advantage.

## 3. System contract

The first complete path is:

```text
bilingual question + optional as_of date
  -> evidence router
  -> temporally filtered hybrid document retrieval and/or OECD SDMX tool
  -> evidence packet
  -> cited briefing
  -> deterministic verification and trace
```

The evidence router must emit a typed plan with one of four routes:

- `documents`
- `data`
- `documents_and_data`
- `abstain`

This routing and tool behavior is the primary LoRA target. Changing economic facts remain in retrieval and official APIs rather than being memorized in model weights.

## 4. Initial evidence scope

The proposed seed sources are:

1. Public Bank of Korea economic-outlook publications in Korean and/or English.
2. Public OECD material on the Korean economy, subject to a redistribution and licensing check.
3. An OECD SDMX query tool for deterministic time-series evidence.

The repository will not automatically redistribute full source documents. It will version a source manifest containing canonical URL, publisher, publication date, retrieval time, checksum, language, and licensing notes. What extracted content may be committed will be decided only after the licensing review.

## 5. Evaluation contract before implementation

### Gold set

Target: 40 manually reviewed questions, balanced across four route classes and Korean/English.

| Slice | Target count | Expected route |
|---|---:|---|
| Documentary fact or synthesis | 10 | `documents` |
| Numerical/time-series request | 10 | `data` |
| Cross-evidence analytical brief | 10 | `documents_and_data` |
| Unsupported, future-leaking, or false-premise request | 10 | `abstain` |

Train, development, and test partitions must be separated by underlying source release or evidence unit—not by randomly splitting near-duplicate questions. Parallel Korean/English questions about the same evidence must remain in the same partition.

### Required system variants

All variants will run against the same test contract:

1. `closed_book`: base model without retrieval or tools.
2. `temporal_rag`: hybrid retrieval with publication-date filtering.
3. `rag_tools`: retrieval plus deterministic SDMX tool use.
4. `lora_router`: the same system with a LoRA-tuned evidence router/tool planner.

### Primary measurements

- Route classification accuracy and macro-F1.
- Tool-selection and typed-argument exact match.
- Retrieval recall at K, reported separately by language.
- Citation correctness and citation completeness.
- Numerical provenance and reproducibility of tool outputs.
- Temporal leakage rate for `as_of` questions.
- Correct abstention on unsupported and false-premise questions.
- End-to-end latency, token/API cost, and local memory use.

LLM-as-judge scores may be reported as a secondary diagnostic only. Acceptance cannot depend on a single unvalidated model judge.

### Initial acceptance targets

- Zero known post-cutoff documents in generated evidence packets.
- At least 90% citation correctness on the reviewed MVP test set.
- At least 85% valid structured route/tool outputs.
- Every published aggregate reproducible from committed manifests, traces, and evaluation code.
- Total external spend at or below USD 100 unless expansion is reviewed first.

The LoRA experiment remains scientifically useful if it does not beat the prompted baseline, provided the failure is rigorously reproduced and explained. The preferred promotion condition is an absolute macro-F1 improvement of at least 8 percentage points or non-inferior quality with materially lower prompt-token cost or latency.

## 6. Model and compute strategy

### Local development

- Python 3.12 virtual environment.
- CPU-compatible tests, retrieval, data tooling, and evaluation.
- External model calls wrapped behind recorded/replayable interfaces so most tests can run offline.

### Fine-tuning

Mistral's hosted fine-tuning documentation is currently marked deprecated. The primary plan is therefore an open-weight QLoRA run on a short-lived rented GPU.

- Primary technical-spike candidate: `mistralai/Ministral-3-3B-Instruct-2512`.
- Rationale: current compact Mistral family, Apache 2.0 weights, edge/local deployment intent, and manageable inference size.
- Week-one gate: confirm tokenizer, PEFT/TRL target modules, 4-bit loading, one training step, adapter save/load, and structured-output inference.
- Fallback if the current architecture is not reliably trainable within four hours of investigation: a well-supported Mistral 7B or Mistral Nemo checkpoint.

The production-shaped demo may use a small local/quantized router and a Mistral API model for final briefing generation. Local and cloud modes will share the same typed interface so their trade-offs can be measured.

## 7. Four-week delivery plan

### Week 1 — Contract and evidence foundation (20 hours)

- Public customer brief, architecture boundary, threat assumptions, and data licensing review.
- Gold-set schema and 12 fully reviewed seed questions across all four routes.
- Source manifest plus the first two document releases.
- OECD SDMX tool contract and recorded fixture.
- One-step Ministral 3 3B QLoRA compatibility spike on rented compute.
- **Gate:** benchmark schema validates, source provenance is complete, and the fine-tuning model path is selected.

### Week 2 — Baselines (20 hours)

- Expand the reviewed gold set toward 40 questions.
- Implement temporal metadata filtering and hybrid Korean/English retrieval.
- Implement deterministic SDMX execution and evidence packets.
- Run `closed_book`, `temporal_rag`, and `rag_tools` baselines.
- **Gate:** no known temporal leakage; failures are categorized before training begins.

### Week 3 — LoRA and ablations (20 hours)

- Generate route/tool training examples from evidence-disjoint sources.
- Human-audit a documented sample and validate JSONL automatically.
- Run a small hyperparameter matrix within the compute budget.
- Evaluate base versus LoRA router and publish error analysis.
- **Gate:** select or reject the adapter using the frozen promotion rule, not a favorable anecdote.

### Week 4 — Productization and application package (20 hours)

- FastAPI service and a compact interactive trace UI.
- Cost, latency, provenance, and failure telemetry.
- Offline test suite, CI, container smoke test, and deployment runbook.
- Customer-style pilot report, architecture diagram, short demo, final CV bullets, and role-specific application narrative.
- **Gate:** a new contributor can reproduce the evaluated path from the README and committed artifacts.

## 8. Definition of done

The four-week MVP is complete only when:

1. A public user can run one end-to-end example without access to private data.
2. All four system variants can be evaluated through one command or documented workflow.
3. At least one real LoRA adapter was trained, loaded, and evaluated against a held-out evidence-disjoint set.
4. Korean and English results are reported separately.
5. Temporal and source provenance is visible in both API output and UI.
6. The repository contains tests, pinned dependencies, CI, cost records, model/data cards, architecture decisions, and a deployment runbook.
7. The final report includes negative results and known limitations.
8. Any upstream contribution is genuine and independently useful; project completion does not depend on its acceptance.

## 9. Explicit non-goals for the MVP

- A general-purpose central-bank chatbot.
- Autonomous multi-agent research over the open web.
- Training a foundation model or teaching current facts through weights.
- Comprehensive coverage of all BOK/OECD publications.
- Production use of confidential or licensed institutional data.
- Claims of endorsement by the Bank of Korea, OECD, or Mistral.
- A polished enterprise UI before the benchmark and ablations work.

## 10. Budget envelope

| Use | Planning envelope |
|---|---:|
| Mistral generation/embedding/OCR experiments | $25 |
| Short-lived GPU compatibility and QLoRA runs | $50 |
| Contingency | $25 |
| **Total initial ceiling** | **$100** |

Every paid operation will be opt-in, logged by experiment, and preceded by a small smoke test or cost estimate where supported.

## 11. Known environment constraints

- The workstation has no supported training GPU.
- The user-level Python installation does not currently execute correctly.
- A working bundled Python 3.12.13 runtime is available and can create the project `.venv` in the next setup step.
- Git 2.51 and GitHub CLI 2.89 are installed.
- GitHub CLI is authenticated as `bwade9090`; local `main` tracks `origin/main`.

## 12. Approved decisions

1. Korean macroeconomic surveillance is the initial workflow.
2. The gold benchmark targets 40 questions across four exclusive routes.
3. The Week-one compatibility spike starts with Ministral 3 3B and permits the documented fallback if required.
