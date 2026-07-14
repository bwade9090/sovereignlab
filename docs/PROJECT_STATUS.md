# SovereignLab project status

- Last updated: 2026-07-14
- Owner: Hyungbae Cho (`bwade9090`)
- Delivery window: four weeks, approximately 80 hours
- Current milestone: M1b — week-1 verification spikes and vintage groundwork (charter v2 §7, Week 1)
- Overall state: charter v2 reorientation approved and documented; M1b implementation not started

## Approved baseline

- Product direction: **K-VINTAGE on KOR-RTD** (charter v2, approved 2026-07-14; rationale in `docs/discovery/01_concept_upgrade_proposal.md`; decision recorded as ADR 0003).
  - KOR-RTD: point-in-time data layer — OECD edition-history consolidation + weekly append-only forward-capture harvester for the latest-only ECOS/KOSIS APIs.
  - K-VINTAGE: two-tier bilingual benchmark (40 human-reviewed core + 200–300 machine-generated data-route probes, always reported separately) with gold answers computed as `as_of -> max(EDITION <= as_of)` and a public regeneration script.
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

## Current validation evidence

Run from the repository root after activating `.venv` (any OS; see README quick start):

```bash
python -m ruff check .
python -m ruff format --check .
python -m pytest
```

Last validated 2026-07-14 on Windows (Python 3.12.13): ruff clean, format clean, `pytest --cov=sovereignlab` 45 passed with 100% statement and branch coverage (241 statements, 60 branches); `git check-ignore` confirmed exclusion of `.venv`, `.env`, `data/raw`, `models`, generated `artifacts`, `traces/private`; `python scripts/export_json_schemas.py` regenerates both public schemas deterministically.

The 2026-07-14 reorientation commit is documentation-only (charter, ADR, AGENTS.md, status, CV bullets, README, proposal); no source or test files changed. It was additionally smoke-checked on macOS with a throwaway Python 3.13.13 environment (pinned requirements installed cleanly; ruff clean, format clean, 45 tests passed) — the project standard remains Python 3.12 per ADR 0001.

## Immediate next action (M1b — do these in order)

1. **Verification spikes — record every result in this file and, where consequential, as a decision record, before making any dependent claim.** The exact study queries and reported results to re-verify are in `docs/discovery/02_verification_queries.md`:
   - `DF_MEI_ARCHIVE` accessibility (study observed conflicting results: one 404, one successful query — both request patterns are in the queries document).
   - Actual OECD Economic Outlook edition range (live-confirmed so far: `DF_EO_114`–`DF_EO_118` + current `DF_EO` only).
   - Per-series KOGL redistribution rulings for the harvester basket (≤12 ECOS/KOSIS series; candidate basket and criteria in the queries document §4). An agent may research the per-series KOGL types, but **the ruling itself is approved by Hyungbae before any raw observation values are committed.**
   - License status of OECD archive content published before 2024-07-01 (CC BY 4.0 is the default only for later publications).
   - One-hour written employer-risk review (**owner action: written personally by Hyungbae** — an agent may draft questions but not the review). Include whether the workstation path recorded in earlier commit history needs remediation.
2. Implement the as-of resolver over `DSD_STES_REVISIONS@DF_STES_REVISIONS` (~6–8 h); it must reproduce the verified example values (KOR CPI 2005-01: 258 editions; 2025-Q1 real GDP 572,057.7 -> 574,984.3 billion KRW June->July 2026; exact queries in `docs/discovery/02_verification_queries.md`).
3. Commit the weekly harvester cron + `SourceManifest` wiring (~3–5 h) so public snapshot history starts accruing immediately.
4. Freeze the number-normalization specification before any question authoring.
5. Extend tool-expectation schemas with vintage/edition semantics per ADR 0003 decision #3: the optional vintage field is expected non-breaking and ships as schema 1.1.0 with regenerated JSON Schema, fixtures, and tests in the same change. If any required field or invariant must change instead, that is a breaking contract change under the schema contract's §7 rule — new major schema version (2.0.0), migration notes, regenerated JSON Schema, fixtures, tests, and a superseding ADR.
6. The already-planned one-step Ministral 3 3B QLoRA compatibility spike on rented compute (record cost in the spend ledger).

Week-1 gate (charter v2 §7): spike results recorded; claimable backfill range fixed; KOGL rulings recorded; employer review done; resolver reproduces verified values; fine-tuning path selected. **If the gate slips, invoke the pre-committed cut ladder (charter §7) immediately.**

## Blockers and environment notes

- No machine has a training GPU; rented GPU is planned only for the reviewed QLoRA spike.
- Development spans multiple machines. `.venv` is machine-local — recreate it per the README quick start on whichever machine picks this up. Nothing in the repo may depend on machine-specific paths.
- Windows workstation note: the user-level Python launcher is unreliable there; use the workstation's documented bundled Python 3.12.13 runtime to create `.venv` (local path recorded outside the repository; an earlier revision of this file recorded the literal path — whether that history needs remediation is an input to the week-1 employer-risk review).
- macOS laptop note: no system `python3.12` is installed (Anaconda 3.11 and Homebrew 3.13 are present). Either install `python@3.12` via Homebrew, or use Python 3.13 — the pinned requirements were verified on 2026-07-14 to install cleanly and pass ruff plus all 45 tests on Python 3.13.13 on this machine. The project standard remains Python 3.12 (ADR 0001).
- GitHub CLI is authenticated as `bwade9090`; `main` tracks `origin/main`.
- Live-event calendar: primary = next OECD edition rollover, expected ~2026-08-01 (monthly cadence; fallback = July-vs-June diff, demo material already secured); stretch = Korea Q2-2026 advance GDP release (~2026-07-23/24, tight — see charter §7).

## Spend ledger

| Date | Operation | Cost | Evidence |
|---|---|---:|---|
| 2026-07-14 | Local foundation and PyPI dependencies | $0.00 | No model/API/GPU call |
| 2026-07-14 | Concept reorientation (docs only) | $0.00 | No model/API/GPU call under project budget |

**Cumulative external spend: $0.00 / $100.00**

## Handoff rule (onboarding for a new contributor or AI agent)

Read in this order, in full, before changing anything:

1. `AGENTS.md` — working protocol, evidence rules, setup, repository map.
2. `docs/project/01_project_charter.md` — the v2 scope authority.
3. This file — current milestone, next action, gates, blockers.
4. Accepted ADRs 0001–0003 in `docs/decisions/`.
5. `docs/discovery/01_concept_upgrade_proposal.md` — background: why v2 exists, verified data facts, judged alternatives, risk register.

Then start with "Immediate next action" item 1. Do not start data collection, document ingestion, model training, or UI work before the week-1 verification spikes are recorded here. Do not weaken the qualification rules for "first" claims or the KOGL/append-only rules in `AGENTS.md`. Update this file whenever a milestone state, blocker, cost, spike result, or next action changes.
