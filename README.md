# SovereignLab

> What did the data say *then*? Vintage-conditioned evaluation and auditable briefings for Korean/English economic research.

**Status:** M1b verification and vintage-contract groundwork are in progress. No model-performance
claims have been made yet.

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

Charter v2.2 (the K-VINTAGE on KOR-RTD reorientation, source-rights amendment, and fail-closed
edition-availability contract) is approved and documented; see
[ADR 0003](docs/decisions/0003-kvintage-reorientation.md),
[ADR 0004](docs/decisions/0004-source-specific-redistribution-evidence.md), and
[ADR 0005](docs/decisions/0005-edition-availability-and-vintage-contract.md), with background in
[the proposal](docs/discovery/01_concept_upgrade_proposal.md). M1a froze strict source-manifest and
benchmark-record models with synchronized JSON Schema, synthetic fixtures, and dataset-wide
temporal/split leakage checks. M1b has now verified the primary OECD examples, fixed the claimable
recent Economic Outlook range at EO114–EO119, and exposed two contract gaps: monthly edition labels
do not prove day-level availability, and ECOS/KOSIS do not expose the assumed per-series KOGL field.
Their official use guides instead govern reuse through the original producer or content category.
The current-account candidate is directly identified as Bank of Korea-produced; official
title/frequency evidence supports the same classification for the GDP candidate. The owner approved
ADR 0004, that mapping, and `allowed` rulings for both candidates on 2026-07-16; charter v2.1 records
the source-rights amendment. The standalone rights catalog and both approved metadata records are
implemented. On 2026-07-17 the owner-authored employer-risk review was recorded as
[ADR 0006](docs/decisions/0006-employer-risk-review.md), and accepted ADR 0005 was implemented as
one contract unit ([migration notes](docs/project/05_evidence_contract_2_0_migration.md)): the
`EditionAvailabilityLedger` 1.0.0 with fail-closed edition selection, evidence/benchmark contract
`2.0.0`, and the typed manifest-to-rights-decision link with bundle cross-validation. The offline
as-of resolver and weekly append-only harvester are implemented. The first real, metadata-only OECD
availability capture mechanically records all 330 current edition codes while resolving only
`202607`; no raw observation is committed. Default-branch workflow activation, the optional ECOS
repository secret, number normalization, and the QLoRA compatibility spike remain the open items
listed in [project status](docs/PROJECT_STATUS.md).

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

Copy `.env.example` to `.env` only when an API-backed experiment is approved. Offline checks and
the OECD constraint-metadata capture do not require an API key. `ECOS_API_KEY` activates only the
two exact series authorized by the committed rights catalog; a missing key is an explicit skip.

## Documentation

- [Approved project charter (v2.2)](docs/project/01_project_charter.md)
- [Concept upgrade proposal (v2 rationale)](docs/discovery/01_concept_upgrade_proposal.md)
- [Evidence schema contract (1.0, superseded)](docs/project/02_evidence_schema_contract.md)
- [Source-rights catalog contract](docs/project/03_rights_catalog_contract.md)
- [Evidence contract 2.0.0 and availability-ledger migration](docs/project/05_evidence_contract_2_0_migration.md)
- [MacBook continuation handoff](docs/project/04_macbook_handoff.md)
- [Current status and handoff](docs/PROJECT_STATUS.md)
- [Week-1 verification log](docs/discovery/03_week1_verification_log.md)
- [Role-gap and project-selection analysis](docs/discovery/00_role_gap_analysis.md)
- [Milestone-gated CV bullets](docs/application/00_cv_bullets.md)
- [Architecture decisions](docs/decisions/README.md)
- [Contributor and agent rules](AGENTS.md)

## Responsible disclosure

This project is conducted in a personal capacity and is not affiliated with the Bank of Korea. It is an independent open-source project using public information, and it is not affiliated with or endorsed by the OECD or Mistral AI either. Source redistribution and model/data licenses will be documented before artifacts are published.

## License

Original project code and documentation are licensed under Apache-2.0 unless noted otherwise; see
[LICENSE](LICENSE). Third-party source data and redistributed observations are not relicensed under
Apache-2.0. They remain subject to the originating provider's terms and attribution requirements
recorded in their manifests and rights decisions. Benchmark, model, and generated-data artifacts
will state their own licences when published; see the
[data licensing boundary](data/README.md#licensing-boundary).
