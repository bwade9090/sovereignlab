# SovereignLab

> Evaluation-driven Mistral deployment for auditable Korean/English economic research.

**Status:** foundation phase; public implementation is in progress. No model-performance claims have been made yet.

SovereignLab is a four-week, evaluation-first customer pilot for a high-stakes financial or public-sector workflow. Given a bilingual policy question and an optional `as_of` date, the target system will route the request to temporally filtered document retrieval, an official OECD SDMX data tool, both, or a justified abstention. It will return a cited briefing together with a machine-readable evidence and verification trace.

## What will be tested

The project will compare four variants under one frozen benchmark:

1. Closed-book Mistral generation.
2. Temporal hybrid RAG.
3. Temporal RAG plus deterministic SDMX tools.
4. The same system with a LoRA-tuned evidence router/tool planner.

Primary measurements include routing macro-F1, tool-argument validity, Korean/English retrieval recall, citation correctness, numerical provenance, temporal leakage, abstention, latency, and cost.

## Current milestone

The approved charter, project constraints, evaluation contract, and staged CV language are documented. M1a adds strict source-manifest and benchmark-record models, synchronized JSON Schema, synthetic fixtures, and dataset-wide temporal/split leakage checks. See [project status](docs/PROJECT_STATUS.md) for the exact next action and validation evidence.

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

- [Approved project charter](docs/project/01_project_charter.md)
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
