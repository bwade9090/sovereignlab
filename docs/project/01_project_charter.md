# SovereignLab project charter

- Status: approved v2
- Date: 2026-07-14 (v2 reorientation; supersedes v1 of the same date)
- Reorientation rationale: `docs/discovery/01_concept_upgrade_proposal.md` and ADR 0003
- Delivery target: four weeks, approximately 80 total hours
- Initial budget ceiling: USD 100 for model APIs and rented compute
- Repository: public at `https://github.com/bwade9090/sovereignlab`

## 1. Product thesis

Korea's official statistics APIs answer only "what does the data say **now**." The Bank of Korea's ECOS and Statistics Korea's KOSIS expose latest values only, with no as-of parameter (verified 2026-07-14), and no public Korean equivalent of the St. Louis Fed's ALFRED archive exists. Anyone who needs to know what the data said **then** — for forecast post-mortems, Orphanides-style ex-ante policy evaluation, or leakage-free model evaluation — cannot get it from Korea's own public statistics APIs today, and from international public tools only for a limited set of headline indicators via the OECD revision datasets (see §2 and §4) — precisely the layer KOR-RTD consolidates and extends.

SovereignLab therefore builds three things:

1. **KOR-RTD** — the point-in-time data layer Korea does not have: a consolidated, documented archive of OECD edition histories for Korean series, plus a scheduled public harvester that forward-captures the latest-only official APIs from now on, all under the frozen provenance contract (ADR 0002).
2. **K-VINTAGE** — a bilingual Korean/English macroeconomic QA benchmark whose gold answers are computed from the statistical data vintage available at each question's `as_of` date. To our knowledge, the first such benchmark for official statistics. Nearest prior art is cited up front in the datasheet: the German statutory as-of QA benchmark (arXiv 2605.23497), the Dallas Fed real-time OECD dataset, and the OECD MEI revisions database.
3. **The reference briefing system** — the bilingual evidence-routing pipeline (documents / data / both / abstain) that consumes the layer, produces cited as-of briefings, and serves as the benchmark's public baseline suite.

The falsifiable question behind the whole project: **does a system answer from the data vintage that existed at `as_of`, or does it leak the future — and can a compact open-weight router be non-inferior to a frontier API at that discrimination layer?**

**Why now.** Vintages not captured from this week onward are lost to everyone forever; a later project can clone the code but can never backfill the snapshots. Mistral entered Korea via the NAVER Cloud partnership (2026-07-08), with forward-deployed engineers in Korea and no central bank or statistical agency on its public customer list. Korea's AI Basic Act (in force January 2026) regulates "high-impact" (고영향) AI under a voluntary verification and certification regime, and Korea's sovereign-AI programs are short on evaluation harnesses. This paragraph's framing rule: the project **complements public statistical infrastructure**; it never frames official APIs as defective.

## 2. Users and workflow

### Customer zero

Hyungbae Cho, acting **in a personal capacity** (standing disclaimer applies; see §9), is the first user: a dated dogfood log of real briefing requests and their outcomes is a committed deliverable.

### Real consumer groups for the public artifacts

1. **LLM-evaluation researchers** — deterministic temporal-contamination probes that need no human annotation to grade.
2. **Korea's sovereign-AI programs** — evaluation harnesses for official-statistics grounding are scarce.
3. **Solution teams deploying LLMs to regulated institutions** — a template for quantifying the frontier-API-vs-local-open-weights gap per capability slice. (The proposal's concrete instance is Mistral's Korea solutions effort following the 2026-07-08 NAVER Cloud partnership; generalized here to avoid implying any customer relationship.)
4. **Economists and Korea desks** — the only public as-of query path for Korean macro data; the Croushore–Stark/Orphanides real-time research program is currently possible for Korea only for a limited set of headline indicators via the OECD revision datasets (the study reported ~13 headline MEI indicators; the live revisions dataflow lists 22 revision measures — the counts use different bases; see `docs/discovery/02_verification_queries.md`).

### Job to be done

> Given a Korean or English policy question and an optional `as_of` date, produce a concise briefing whose documentary claims are cited, whose numerical claims are computed from the data vintage available at `as_of`, and whose limitations are explicit.

### Example request

> As of May 2024, why was Korea's growth outlook revised, and do the consumption indicators **as then published** support that narrative?

The system must decide whether the request requires document retrieval, an official-data query, both, or an abstention. It must not silently use documents published after the requested cutoff, and it must not silently answer with revised values that did not exist at the cutoff.

### Domain boundary

The first release targets **Korean macroeconomic surveillance**, not policy-rate decision extraction. Unchanged from v1.

## 3. System contract

The first complete path is:

```text
bilingual question + optional as_of date
  -> evidence router
  -> temporally filtered hybrid document retrieval and/or vintage-resolving as-of data tool
  -> evidence packet (with vintage/edition provenance)
  -> cited briefing
  -> deterministic verification and trace
```

The evidence router must emit a typed plan with one of four routes:

- `documents`
- `data`
- `documents_and_data`
- `abstain`

This routing and tool behavior is the primary LoRA target. Changing economic facts remain in retrieval and official APIs rather than being memorized in model weights.

The flagship deterministic capability is the **as-of resolver**: `as_of -> max(EDITION <= as_of)` over OECD SDMX edition histories, so "what did the data say then" receives a computed gold answer. A system that answers from the latest value is caught mechanically — no LLM judge involved. **Temporal-leakage rate is a headline per-variant metric, not a footnote.**

## 4. Evidence scope (KOR-RTD)

### Vintage data

1. **Primary (live):** the OECD SDMX revisions dataflow `DSD_STES_REVISIONS@DF_STES_REVISIONS` — verified 2026-07-14 as key-free and free of charge, with Korean editions from Feb-1999 to Jul-2026 (example: the KOR CPI 2005-01 observation carries 258 archived editions; Korea's 2025-Q1 real GDP was revised from 572,057.7 to 574,984.3 billion KRW between the June and July 2026 editions). A `NonProductionDataflow` annotation was observed and must be disclosed in the datasheet.
2. **Cross-check (frozen archive):** `DF_MEI_ARCHIVE` — **week-1 spike required**: verification attempts returned conflicting results (one 404, one successful query). No backfill-range claim may be published until the spike settles it.
3. **Forecast vintages:** recent OECD Economic Outlook edition dataflows only — live-confirmed range is `DF_EO_114`–`DF_EO_118` plus current `DF_EO`. Wider ranges (e.g. "EO60–119") may not be claimed until verified.

### Forward capture

A scheduled public harvester (GitHub Actions, weekly) snapshots a curated basket of **at most 12** ECOS/KOSIS series plus BOK publication metadata into append-only, checksummed files under `SourceManifest`. Both APIs are latest-only, so these snapshots create the vintage record; **public commit history is the proof of capture dates and of no backfill**. The harvester must be committed in week 1 so history starts accruing immediately.

**KOGL gate:** KOGL (Korea Open Government License, 공공누리) is the license scheme for Korean public data; each ECOS/KOSIS series carries a KOGL type in its metadata, and only types permitting redistribution allow raw values in this public repository. A per-series ruling (recorded KOGL type plus the resulting decision) is a week-1 gate. No raw ECOS/KOSIS values are committed before the ruling; restricted series fall back to checksum-diff plus a fetch script. The candidate basket and selection criteria are recorded in `docs/discovery/02_verification_queries.md`; the final basket is fixed at the week-1 gate with the owner's sign-off.

### Contrast tool and exclusions

- **ECOS is retained as the latest-only contrast tool** (it powers the demo's comparison card).
- **ALFRED is excluded**: Korean vintage coverage is shallow (GDP only from 2021; the CPI feed was discontinued in 2024) and the June-2024 FRED API terms prohibit archiving, redistribution, and ML/LLM use.

### Documents

Public Bank of Korea economic-outlook publications: 58 Korean reports (2012.07–2026.05, stable nttId URLs) plus 13 English full translations (verified counts). OECD documents subject to the licensing review; the license status of OECD archive content published **before 2024-07-01** must be verified in week 1 (CC BY 4.0 is the default only for later publications).

The repository will not automatically redistribute full source documents. Source-manifest rules from v1 are unchanged.

## 5. Evaluation contract before implementation

### Two-tier gold set

**Tier 1 — human-reviewed core: 40 questions**, balanced across four route classes and Korean/English (table unchanged from v1):

| Slice | Target count | Expected route |
|---|---:|---|
| Documentary fact or synthesis | 10 | `documents` |
| Numerical/time-series request | 10 | `data` |
| Cross-evidence analytical brief | 10 | `documents_and_data` |
| Unsupported, future-leaking, or false-premise request | 10 | `abstain` |

**Tier 2 — machine-generated probes: 200–300 deterministic data-route items** (revision traps and as-of lookups), with a documented human audit of a sample. **The two tiers are always reported separately** — never merged into a single "N-question benchmark" figure.

Gold answers for data-route items are **computed** by the as-of resolver and remain regenerable by a public script; human review is recorded alongside, not replaced.

**Prerequisite artifact:** a number-normalization specification (raw 10^12 XDC scale vs "billion KRW" presentation, 조/억 conventions, seasonal-adjustment series variants, rounding tolerances) must be frozen **before** question authoring begins.

**CPI rule:** Korean CPI is essentially unrevised — the archived KOR CPI 2019-11 observation carried the identical value (104.87) across all 50 of its editions. Edition counts (e.g. 258 editions for the live-flow KOR CPI 2005-01 observation, §4) measure archive coverage, not actual revisions. CPI is therefore used only for abstain/trap items, never as a revision gold question.

Train, development, and test partitions must be separated by underlying source release or evidence unit. Parallel Korean/English questions about the same evidence must remain in the same partition. Unchanged from v1.

### Required system variants (the public baseline suite)

All variants run against the same test contract:

1. `closed_book`: base model without retrieval or tools.
2. `temporal_rag`: hybrid retrieval with publication-date filtering.
3. `rag_tools`: retrieval plus the deterministic vintage-resolving as-of tool.
4. `lora_router`: the same system with a LoRA-tuned evidence router/tool planner.

### Primary measurements

- **Temporal leakage rate (headline, reported per variant).**
- Route classification accuracy and macro-F1.
- Tool-selection and typed-argument exact match, including vintage/edition arguments.
- Retrieval recall at K, reported separately by language.
- Citation correctness and citation completeness.
- Numerical provenance and reproducibility of tool outputs (regeneration script).
- Correct abstention on unsupported and false-premise questions.
- End-to-end latency, token/API cost, and local memory use.

LLM-as-judge scores may be reported as a secondary diagnostic only.

### Initial acceptance targets

- Zero known post-cutoff documents **or post-cutoff data vintages** in generated evidence packets.
- At least 90% citation correctness on the reviewed core test set.
- At least 85% valid structured route/tool outputs.
- Every published aggregate reproducible from committed manifests, traces, and evaluation code; **the archive itself regenerates and validates from committed manifests**.
- At least one artifact whose creation time is independently verifiable from public CI logs.
- Total external spend at or below USD 100 unless expansion is reviewed first.

The LoRA promotion rule is unchanged from v1: absolute route macro-F1 improvement of at least 8 percentage points, or non-inferior quality with materially lower prompt-token cost or latency; a rigorously reproduced and explained negative result remains scientifically useful.

## 6. Model and compute strategy

### Local development

Unchanged from v1: Python 3.12 virtual environment; CPU-compatible tests, retrieval, data tooling, and evaluation; external model calls wrapped behind recorded/replayable interfaces. The as-of resolver reads point-in-time state from committed archive snapshots, which also improves offline-testability.

### Fine-tuning

Unchanged from v1: primary spike candidate `mistralai/Ministral-3-3B-Instruct-2512` on a short-lived rented GPU, with the documented Mistral 7B/Nemo fallback. **Committed cut:** the hyperparameter matrix is fixed at 2–3 configurations.

### Deployment modes

The **hybrid mode is a committed demo**: a small local/quantized router plus a Mistral API model for final briefing generation, with memory and latency recorded. One fully local end-to-end run is a **documented stretch goal**; without it, no "on-prem"-family wording may appear in any public claim (see the CV disclosure rules).

## 7. Four-week delivery plan

### Week 1 — Verification spikes and vintage groundwork (20 hours)

- **Verification spikes, all results recorded in writing before any dependent claim:** `DF_MEI_ARCHIVE` accessibility; actual OECD EO edition range; per-series KOGL redistribution rulings; license status of OECD archive content published before 2024-07-01; a one-hour written employer-risk review (personal-capacity public activity), committed as a decision record.
- As-of resolver over the live revisions dataflow (~6–8 h).
- Harvester cron + `SourceManifest` wiring, committed so snapshot history starts (~3–5 h).
- Number-normalization specification.
- Extend tool-expectation schemas with vintage/edition semantics (ADR 0003 decision #3; non-gating for the week-1 gate).
- Charter v2 / ADR 0003 documentation (this change).
- One-step Ministral 3 3B QLoRA compatibility spike on rented compute (unchanged from v1).
- **Gate:** spike results recorded; claimable backfill range fixed; KOGL rulings recorded; employer review done; the resolver reproduces the verified example values; fine-tuning model path selected.

### Week 2 — Benchmark and baselines (20 hours)

- Author the 40 human-reviewed core questions (**budget 8–12 h honestly** — machine generation does not remove this bottleneck).
- Generate the tier-2 probe set; human-audit a documented sample.
- Temporal metadata filtering and hybrid Korean/English retrieval.
- Minimal end-to-end path (question -> route -> evidence -> cited brief).
- Stretch: a cited note on Korea's Q2-2026 advance GDP release (~2026-07-23/24) — promised as "a cited note within 48 h," not "same-day"; the automation level is reported honestly.
- **Gate:** end-to-end minimal path works; no known temporal leakage; failures categorized before training begins.

### Week 3 — LoRA and the live event (20 hours)

- Route/tool training examples from evidence-disjoint sources; JSONL validation and documented sample audit.
- LoRA runs limited to 2–3 configurations; select or reject via the frozen promotion rule.
- Four-variant evaluation with the temporal-leakage headline numbers.
- **Primary live event: the next OECD edition rollover, expected ~2026-08-01** (editions roll monthly; the demo material is already secured because the July edition contains new Korean GDP revisions, so a slipped rollover falls back to the July-vs-June diff): the pipeline writes a bilingual cited note within 48 hours (same-day targeted), committed with CI timestamps.
- **Gate:** adapter promoted or rejected by the frozen rule; leakage numbers reproduced from committed artifacts.

### Week 4 — Release and application package (20 hours)

- K-VINTAGE release: HF dataset + datasheet (prior art cited first) + pip-installable grader + gold-answer regeneration script + PR-based static leaderboard seeded with the four variants plus two API models.
- FastAPI service and compact trace UI; cost, latency, provenance, and failure telemetry.
- Demo script "Right Then, Wrong Now" — reproducible from one seeded command.
- Engagement report grounded in the real artifacts (archive as the data-readiness layer) plus a one-page mapping of the project's evaluation vocabulary to Mistral Studio/Forge terms (one table in one positioning document; no codebase renaming).
- Offline test suite, CI, container smoke test, deployment runbook, dogfood log, final CV bullet resolution.
- **Gate:** a new contributor can reproduce the evaluated path from the README and committed artifacts.

### Committed de-scopes (v1 items removed to fund the above)

- Fictional-pilot narrative writing (replaced by the artifact-grounded engagement report).
- Full deployment-mode matrix (hybrid demo + documented stretch goal instead).
- Deep OECD EO backfill (recent editions only).
- Twice-daily harvester cadence (weekly).
- A separate sibling repository (KOR-RTD lives in this repo's `data/` layer).

### Pre-committed cut ladder

On overrun, cut in exactly this order — mid-project de-scoping is a plan, not a failure:

1. Tier-2 probe-set size (300 → 200 → 100).
2. Forecast-vintage question family (defer to v1.1).
3. Leaderboard seed rows.
4. Trace-UI polish.

Weekly gates trigger the ladder immediately when missed.

## 8. Definition of done

The four-week MVP is complete only when:

1. A public user can run one end-to-end example without access to private data.
2. All four system variants can be evaluated through one command or documented workflow.
3. At least one real LoRA adapter was trained, loaded, and evaluated against a held-out evidence-disjoint set.
4. Korean and English results are reported separately.
5. Temporal, source, **and vintage** provenance is visible in both API output and UI.
6. The repository contains tests, pinned dependencies, CI, cost records, model/data cards, architecture decisions, and a deployment runbook.
7. The final report includes negative results and known limitations.
8. Any upstream contribution is genuine and independently useful; project completion does not depend on its acceptance.
9. At least one artifact's creation time is independently verifiable from public CI logs.
10. The archive regenerates and validates from committed manifests.
11. Every "first" claim follows the qualification rule: "to our knowledge" + domain qualifier (official statistics) + prior-art citations (arXiv 2605.23497, Dallas Fed real-time OECD dataset, OECD MEI revisions database).

## 9. Explicit non-goals for the MVP

- A general-purpose central-bank chatbot.
- Autonomous multi-agent research over the open web.
- Training a foundation model or teaching current facts through weights.
- Comprehensive coverage of all BOK/OECD publications, or a deep EO backfill beyond verified editions.
- Production use of confidential or licensed institutional data.
- Claims of endorsement by the Bank of Korea, OECD, or Mistral; all public activity carries a personal-capacity disclaimer.
- Market commentary or investment advice: auto-generated notes are labeled strictly as "automated reconstruction of official releases."
- Framing official statistics APIs as defective — the project complements public statistical infrastructure.
- A polished enterprise UI before the benchmark and ablations work.
- "First Korean macro benchmark" phrasing (KMMLU contains economics categories).

## 10. Budget envelope

| Use | Planning envelope |
|---|---:|
| Mistral generation/embedding/OCR experiments | $25 |
| Short-lived GPU compatibility and QLoRA runs | $50 |
| Contingency | $25 |
| **Total initial ceiling** | **$100** |

Vintage data costs $0: all OECD SDMX endpoints used are verified key-free and free of charge; ECOS/KOSIS keys are free; GitHub Actions free tier covers the weekly cron on a public repository. Every paid operation remains opt-in, logged by experiment, and preceded by a smoke test or cost estimate where supported.

## 11. Known environment constraints

- Development happens on **multiple machines** (the original Windows workstation and a macOS laptop). Virtual environments are machine-local: recreate `.venv` per the README quick start; nothing in the repository may depend on machine-specific paths.
- No machine has a supported training GPU; rented GPU is used only for the reviewed QLoRA spike.
- Git and the GitHub CLI are authenticated as `bwade9090`; local `main` tracks `origin/main`.
- Machine-specific notes (e.g., the Windows workstation's Python launcher workaround) live in `docs/PROJECT_STATUS.md`.

## 12. Approved decisions

1. **v2 reorientation approved (2026-07-14):** K-VINTAGE on KOR-RTD, per `docs/discovery/01_concept_upgrade_proposal.md` (all ten amendments) and ADR 0003.
2. Korean macroeconomic surveillance remains the domain.
3. The gold set is two-tier: 40 human-reviewed core questions across four exclusive routes, plus 200–300 machine-generated data-route probes, always reported separately.
4. The Week-one compatibility spike starts with Ministral 3 3B and permits the documented fallback if required (unchanged from v1).
5. The pre-committed cut ladder in §7 is binding.
