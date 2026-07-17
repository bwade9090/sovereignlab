# SovereignLab agent guide

This file applies to the entire repository. It is the onboarding contract for human contributors and AI agents.

## Mission

Build **KOR-RTD**, a provenance-contracted point-in-time (vintage) data layer for Korean macroeconomic statistics, and **K-VINTAGE**, a bilingual Korean/English benchmark whose gold answers depend on the data vintage available at each question's `as_of` date — with the SovereignLab briefing pipeline as the reference implementation and public baseline suite. Preserve evaluation-first rigor without overstating results: techniques (fine-tuning, RAG, deterministic tools) are means, not the mission, and temporal-leakage rate is the headline metric.

## Read before changing anything

1. `docs/project/01_project_charter.md` — approved product and evaluation contract (v2.2).
2. `docs/PROJECT_STATUS.md` — current milestone, completed work, next action, blockers, and validation evidence.
3. `docs/decisions/` — accepted architecture and process decisions (ADR 0003 records the v2
   reorientation; ADR 0004 records the v2.1 source-rights amendment; ADR 0005 records the v2.2
   fail-closed edition-availability contract; ADR 0006 records the owner's employer-risk review).
4. `docs/discovery/01_concept_upgrade_proposal.md` — background rationale for v2: verified data facts, judged alternatives, risk register.
5. The closest additional `AGENTS.md`, if a subdirectory adds one later.

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
- Never let an `as_of` evidence packet include a source published after its cutoff — nor a data vintage/edition that did not exist at the cutoff.
- Harvester outputs are append-only: never rewrite, backdate, or backfill a committed snapshot; public commit history is the proof of capture dates.
- Never commit raw ECOS/KOSIS observations unless the exact series has an owner-approved
  source-specific classification and attribution ruling. Bank of Korea-produced ECOS statistics
  and in-scope KOSIS domestic macro statistics may be `allowed` under their official use guides;
  other-producer ECOS raw redistribution fails closed without an express producer-specific basis.
  KOSIS international/North Korea statistics are not redistributed, and publications follow their
  individual KOGL notices.
- `SourceManifest` 2.0.0 requires a typed rights-decision link on every `allowed` data snapshot,
  and bundle validation cross-checks it against the committed rights catalog. No raw observation
  may be committed unless that link validates and the referenced decision is owner-approved
  `allowed`.
- Treat the project and its public data artifacts as non-commercial. Any future commercial-use path
  requires an owner review and a superseding rights decision before collection or publication.
- Report the two gold-set tiers separately (40 human-reviewed core vs machine-generated probes); never merge them into one count.
- Qualify every "first" claim: "to our knowledge" + "for official statistics" + cite prior art (arXiv 2605.23497, Dallas Fed real-time OECD dataset, OECD MEI revisions database). Never claim "first Korean macro benchmark."
- Do not claim OECD edition/backfill ranges beyond what a recorded verification spike confirmed.
- When mentioning Korea's AI Basic Act, describe it precisely: it regulates "high-impact" (고영향) AI under a voluntary verification/certification regime — not "high-risk" AI with mandatory testing.
- Frame the project as complementing public statistical infrastructure; never as exposing defects in official APIs.
- Treat LLM judges as secondary diagnostics until calibrated against human review.
- Derive every CV number and README performance claim from committed artifacts and a reproducible command.
- Preserve negative results and failure taxonomies.
- Fine-tuning must target measurable behavior; changing facts belong in retrieval or deterministic tools.

## Data, security, and cost

- Use public sources only. Never add confidential Bank of Korea or applicant data.
- Repository Apache-2.0 terms cover original project code and documentation unless noted; they do
  not relicense source observations, which retain their recorded provider terms and attribution.
- Do not commit downloaded source documents until redistribution rights are documented.
- Never commit API keys, tokens, `.env`, credentials, private traces, or model weights.
- Paid API, OCR, embedding, or GPU operations require a smoke test and an entry in the project status/cost record.
- The approved initial external-spend ceiling is USD 100. Do not exceed it without Hyungbae's review.
- Do not imply endorsement by the Bank of Korea, OECD, Mistral, or any other institution.

## Local setup and required checks

Development happens on multiple machines; `.venv` is machine-local and must be recreated on each. Nothing in the repository may depend on machine-specific paths.

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m ruff check .
python -m ruff format --check .
python -m pytest
```

macOS or Linux:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m ruff check .
python -m ruff format --check .
python -m pytest
```

If the user-level Python launcher is unavailable on the Windows workstation, use the documented Python 3.12 runtime in `docs/PROJECT_STATUS.md` to create `.venv`; commands after activation remain standard.

## Repository map

- `src/sovereignlab/` — importable application and evaluation code.
- `tests/` — offline tests; network calls must be mocked or replayed unless explicitly marked.
- `data/` — public benchmark and metadata policy; ignored raw/interim material. The KOR-RTD archive layer (edition consolidations, harvester snapshots, manifests) lives here.
- `artifacts/` — generated outputs policy; generated content is ignored by default.
- `docs/project/` — charter and customer-facing scope.
- `docs/discovery/` — role-gap and project-selection research.
- `docs/application/` — milestone-gated CV/application language.
- `docs/decisions/` — architecture decision records.
