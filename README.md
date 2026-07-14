# SovereignLab

> What did the data say *then*? Vintage-conditioned evaluation and auditable briefings for Korean/English economic research.

**Status:** foundation phase; public implementation is in progress. No model-performance claims have been made yet.

Korea's official statistics APIs (ECOS, KOSIS) expose latest values only — they offer no "as-of" query path — and no Korean equivalent of the St. Louis Fed's ALFRED archive exists. SovereignLab builds three things in four weeks:

1. **KOR-RTD** — a provenance-contracted point-in-time data layer for Korean macroeconomics: consolidated OECD edition histories plus a scheduled public harvester that forward-captures the latest-only official APIs (append-only, checksummed; commit history is the proof of capture dates).
2. **K-VINTAGE** — a bilingual Korean/English benchmark whose gold answers are computed from the data vintage available at each question's `as_of` date. To our knowledge the first such benchmark for official statistics (prior art cited in the datasheet: arXiv 2605.23497 statutory as-of QA, the Dallas Fed real-time OECD dataset, the OECD MEI revisions database).
3. **A reference briefing system** — given a bilingual policy question and an optional `as_of` date, it routes to temporally filtered document retrieval, a deterministic vintage-resolving data tool, both, or a justified abstention, and returns a cited briefing with a machine-readable evidence and verification trace.

## What will be tested

The project will compare four variants under one frozen benchmark:

1. Closed-book Mistral generation.
2. Temporal hybrid RAG.
3. Temporal RAG plus the deterministic vintage-resolving as-of tool.
4. The same system with a LoRA-tuned evidence router/tool planner.

**Temporal-leakage rate is the headline per-variant metric** — a system that answers from revised values that did not exist at `as_of` is caught mechanically, with no LLM judge. Further measurements: routing macro-F1, tool-argument validity, Korean/English retrieval recall, citation correctness, numerical provenance, abstention, latency, and cost.

## Current milestone

Charter v2 (the K-VINTAGE on KOR-RTD reorientation) is approved and documented; see [ADR 0003](docs/decisions/0003-kvintage-reorientation.md) for the decision and [the proposal](docs/discovery/01_concept_upgrade_proposal.md) for the rationale. M1a froze strict source-manifest and benchmark-record models with synchronized JSON Schema, synthetic fixtures, and dataset-wide temporal/split leakage checks. Next: the week-1 verification spikes — see [project status](docs/PROJECT_STATUS.md) for the exact ordered next actions.

## Quick start

Requires Python 3.12.

### Windows PowerShell

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m ruff check .
python -m ruff format --check .
python -m pytest
```

### macOS or Linux

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m ruff check .
python -m ruff format --check .
python -m pytest
```

Copy `.env.example` to `.env` only when an API-backed experiment is approved. Offline checks do not require an API key.

## Documentation

- [Approved project charter (v2)](docs/project/01_project_charter.md)
- [Concept upgrade proposal (v2 rationale)](docs/discovery/01_concept_upgrade_proposal.md)
- [Evidence schema contract](docs/project/02_evidence_schema_contract.md)
- [Current status and handoff](docs/PROJECT_STATUS.md)
- [Role-gap and project-selection analysis](docs/discovery/00_role_gap_analysis.md)
- [Milestone-gated CV bullets](docs/application/00_cv_bullets.md)
- [Architecture decisions](docs/decisions/README.md)
- [Contributor and agent rules](AGENTS.md)

## Responsible disclosure

This is an independent open-source project using public information. It is not affiliated with or endorsed by the Bank of Korea, OECD, or Mistral AI. Source redistribution and model/data licenses will be documented before artifacts are published.

## License

Apache-2.0. See [LICENSE](LICENSE).
