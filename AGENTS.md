# SovereignLab agent guide

This file applies to the entire repository. It is the onboarding contract for human contributors and AI agents.

## Mission

Build an evaluation-first, bilingual Mistral deployment lab that produces auditable Korean/English macroeconomic briefings from temporally valid official evidence. The project must prove fine-tuning, advanced RAG, deterministic tool use, evaluation, and production integration without overstating results.

## Read before changing anything

1. `docs/project/01_project_charter.md` — approved product and evaluation contract.
2. `docs/PROJECT_STATUS.md` — current milestone, completed work, next action, blockers, and validation evidence.
3. `docs/decisions/` — accepted architecture and process decisions.
4. The closest additional `AGENTS.md`, if a subdirectory adds one later.

The charter is the scope authority. Do not expand sources, agents, UI, or infrastructure before the current milestone gate passes.

## Working protocol

- Work in small, reviewable units with one stated outcome.
- Update `docs/PROJECT_STATUS.md` whenever a milestone state, blocker, cost, or next action changes.
- Record consequential technical choices as an ADR in `docs/decisions/`.
- Add or update tests in the same change as behavior.
- Run the relevant offline checks before committing and record the commands in the status document.
- Use conventional commit prefixes: `docs:`, `chore:`, `feat:`, `fix:`, `test:`, `refactor:`, `eval:`.
- Do not rewrite or discard unrelated user changes.

## Evidence and evaluation rules

- Freeze evaluation schemas and evidence-disjoint splits before model optimization.
- Keep Korean and English results separately reportable.
- Never let an `as_of` evidence packet include a source published after its cutoff.
- Treat LLM judges as secondary diagnostics until calibrated against human review.
- Derive every CV number and README performance claim from committed artifacts and a reproducible command.
- Preserve negative results and failure taxonomies.
- Fine-tuning must target measurable behavior; changing facts belong in retrieval or deterministic tools.

## Data, security, and cost

- Use public sources only. Never add confidential Bank of Korea or applicant data.
- Do not commit downloaded source documents until redistribution rights are documented.
- Never commit API keys, tokens, `.env`, credentials, private traces, or model weights.
- Paid API, OCR, embedding, or GPU operations require a smoke test and an entry in the project status/cost record.
- The approved initial external-spend ceiling is USD 100. Do not exceed it without Hyungbae's review.
- Do not imply endorsement by the Bank of Korea, OECD, Mistral, or any other institution.

## Local setup and required checks

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m ruff check .
python -m ruff format --check .
python -m pytest
```

If the user-level Python launcher is unavailable on the current Codex workstation, use the documented Python 3.12 runtime in `docs/PROJECT_STATUS.md` to create `.venv`; commands after activation remain standard.

## Repository map

- `src/sovereignlab/` — importable application and evaluation code.
- `tests/` — offline tests; network calls must be mocked or replayed unless explicitly marked.
- `data/` — public benchmark and metadata policy; ignored raw/interim material.
- `artifacts/` — generated outputs policy; generated content is ignored by default.
- `docs/project/` — charter and customer-facing scope.
- `docs/discovery/` — role-gap and project-selection research.
- `docs/application/` — milestone-gated CV/application language.
- `docs/decisions/` — architecture decision records.
