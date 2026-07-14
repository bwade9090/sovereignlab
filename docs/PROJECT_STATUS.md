# SovereignLab project status

- Last updated: 2026-07-14
- Owner: Hyungbae Cho (`bwade9090`)
- Delivery window: four weeks, approximately 80 hours
- Current milestone: M0 — repository and reproducibility foundation
- Overall state: complete locally; public push pending GitHub reauthentication

## Approved baseline

- Product direction: SovereignLab.
- First workflow: Korean macroeconomic surveillance briefings.
- Evaluation contract: 40 reviewed Korean/English questions across `documents`, `data`, `documents_and_data`, and `abstain`.
- Fine-tuning plan: test Ministral 3 3B QLoRA first; fall back to a supported Mistral 7B/Nemo checkpoint if the documented compatibility gate fails.
- Initial spend ceiling: USD 100.
- Repository intent: public GitHub under `bwade9090`.

## Completed

- Reviewed the applicant profile, role posting, role questions, and current Mistral product surface.
- Recorded the role-gap analysis and selected SovereignLab.
- Approved the four-week project charter and staged CV language.
- Created a Python 3.12 virtual environment at `.venv`.
- Installed and pinned the M0 runtime/test foundation.
- Added typed settings, offline smoke tests, repository policies, and agent onboarding instructions.
- Passed the complete M0 offline validation suite and verified ignore rules for secrets, local environments, raw data, model weights, private traces, and generated artifacts.
- Initialized the local Git repository on branch `main`.

## Current validation evidence

Run from the repository root after activating `.venv`:

```powershell
python -m ruff check .
python -m ruff format --check .
python -m pytest
```

Validated on Windows with Python 3.12.13:

- `python -m ruff check .` — passed.
- `python -m ruff format --check .` — 3 files already formatted.
- `python -m pytest --cov=sovereignlab --cov-report=term-missing` — 3 passed; 100% coverage of the 13 executable foundation statements.
- `git check-ignore` — confirmed `.venv`, `.env`, `data/raw`, `models`, generated `artifacts`, and `traces/private` are excluded.

## Immediate next action

Create the foundation commit and publish it after GitHub CLI authentication is restored.

After publication, begin M1 with exactly one design task: define and validate the source-manifest and benchmark-record schemas before downloading documents or calling paid APIs.

## Blockers and environment notes

- No local training GPU; rented GPU is planned only for the reviewed QLoRA spike.
- The workstation's user-level Python launcher does not currently execute reliably.
- Working bootstrap runtime used to create `.venv`: `C:\Users\BOK\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe` (Python 3.12.13).
- GitHub CLI 2.89 recognizes `bwade9090`, but the stored token is invalid. Reauthentication is required before repository creation/push.

## Spend ledger

| Date | Operation | Cost | Evidence |
|---|---|---:|---|
| 2026-07-14 | Local foundation and PyPI dependencies | $0.00 | No model/API/GPU call |

**Cumulative external spend: $0.00 / $100.00**

## Handoff rule

A new contributor should read `AGENTS.md`, the approved charter, this file, and accepted ADRs in that order. Do not start model training, document ingestion, or UI work until the immediate next action and the relevant milestone gate are updated here.
