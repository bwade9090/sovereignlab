# SovereignLab contributor guide

This file applies to the whole repository, for human contributors and AI assistants alike.

## What this project is

**KOR-RTD** is a point-in-time (vintage) data layer for Korean macroeconomic statistics.
**K-VINTAGE** is a bilingual Korean/English benchmark whose gold answers depend on the data
vintage available at each question's `as_of` date. The offline briefing path under
`src/sovereignlab/execution/` is the reference implementation. Temporal-leakage rate is the
headline metric; fine-tuning, RAG, and tools are means, not the mission.

| Question | Where to look |
| --- | --- |
| What is in scope? | [Project charter](docs/project/01_project_charter.md) |
| Where are we, and what is next? | [Project status](docs/PROJECT_STATUS.md) |
| How do the pieces fit together? | [Architecture](docs/architecture.md) |
| Why was it decided this way? | [Decision records](docs/decisions/README.md) |

## Working agreement

- Keep changes small, and add or update tests in the same change as the behaviour.
- Before committing, run the checks below. That is the whole gate; there is no coverage target.

  ```bash
  python -m ruff check .
  python -m ruff format --check .
  python -m pytest
  ```

- After changing anything under `src/`, run
  `python scripts/export_execution_replay_traces.py --write`. Each committed trace records a
  digest of the source tree, and the test suite fails until the traces match.
- After changing a schema model, run `python scripts/export_json_schemas.py`.
- Use conventional commit prefixes: `feat:`, `fix:`, `docs:`, `test:`, `refactor:`, `chore:`,
  `data:`, `eval:`.
- Update `docs/PROJECT_STATUS.md` in place when the milestone, the approved-core count, a blocker,
  or spend changes. Do not append session logs anywhere: Git history is the log.
- Write a decision record only for a choice that changes scope, rights, a public contract, or the
  evaluation method.
- Do not rewrite or discard changes you did not make.

## Decisions that belong to the owner

Ask Hyungbae Cho before doing any of these.

- **Approving a benchmark record.** Core records may be drafted by anyone, AI included, but enter
  `data/benchmark/core/` only after the owner's named review. Approved records and the 40-record
  matrix (`data/benchmark/core-authoring-matrix-v1.json`) change only through another owner review.
- **Choosing which pair or slice to author next.**
- **A rights decision**: classifying a source or series as redistributable, or widening a scope.
- **Admitting new captures into an evidence registry.** Weekly captures stay archive-only until a
  new registry version admits them (ADR 0010).
- **Changing a public JSON Schema** under `data/schemas/`, or the charter's scope.
- **Paid operations** (API, OCR, embeddings, GPU). Smoke-test first, record the cost in the status
  page's spend ledger, and stay under the approved USD 100 ceiling.
- **Dispatching the weekly capture workflow by hand.**

## Evidence rules

These rules are what make the benchmark trustworthy. They are not negotiable for convenience.

- An `as_of` answer may use only documents published, and data vintages available, by the end of
  the cutoff day in Asia/Seoul. When availability cannot be proven, abstain; never guess a date.
- A document manifest's `published_on` is never earlier than its exact hashed bytes: take the
  latest of the landing-page date, the file's embedded dates, and any publisher-stated date
  (ADR 0011).
- Each language edition of a document gets its own manifest, with its own date, URL, hash, and
  licence. Never invent a manifest field to make validation pass.
- Captures are append-only. Never rewrite, backdate, or backfill one; public commit history is the
  proof of capture dates. The weekly gap from 2026-07-20 to 2026-11-02 is permanent and must be
  disclosed wherever capture coverage is described.
- Commit raw observations only for a series with an owner-approved `allowed` decision in the
  rights catalog (ADRs 0004 and 0007). Everything else is metadata-only, including every OECD
  measure other than Korea's monthly amplitude-adjusted CLI.
- Bank of Korea Economic Outlook reports and their official English translations are allowed
  public data (ADR 0009): attribute the Bank of Korea, disclose any transformation, honour
  separately marked third-party rights, and keep the PDF bodies out of Git.
- Public data artifacts are non-commercial. A commercial path needs an owner review and a new
  rights decision first.
- Report the human-reviewed core and the machine-generated probes as separate counts, and keep
  Korean and English results separately reportable.
- Freeze evaluation data and evidence-disjoint splits before optimizing a model, and keep negative
  results. Facts that change belong in retrieval or deterministic tools, not in fine-tuning.

## Public claims

- Derive every number in the README, CV wording, or release notes from committed artifacts and a
  reproducible command.
- Describe the shipped path as "typed function calling with committed traces". Do not call it an
  agent, agentic, multi-step, orchestration, or autonomous in public-facing text; the bounded tool
  loop is deferred to v1.1 (ADR 0008).
- Qualify any "first" claim as "to our knowledge, for official statistics" and cite prior art
  (arXiv 2605.23497, the Dallas Fed real-time OECD dataset, the OECD MEI revisions database).
  Never claim "first Korean macro benchmark".
- Do not claim OECD edition or backfill ranges beyond what a recorded verification confirmed.
- Korea's AI Basic Act regulates "high-impact" (고영향) AI under a voluntary verification and
  certification regime. It is not a "high-risk" regime with mandatory testing.
- Frame the project as complementing public statistical infrastructure, never as exposing defects
  in official APIs, and never imply endorsement by the Bank of Korea, the OECD, Mistral, or any
  other institution.
- Treat LLM judges as secondary diagnostics until they are calibrated against human review.

## Data and security

- Use public sources only. Never add confidential Bank of Korea or applicant data.
- Never commit API keys, tokens, `.env`, credentials, private traces, or model weights.
- Apache-2.0 covers the project's own code and documentation. Source observations keep their
  provider's terms and attribution.

## Setup

Python 3.12 is required. `.venv` is machine-local, and nothing in the repository may depend on a
machine-specific path.

```bash
python3.12 -m venv .venv
source .venv/bin/activate            # Windows PowerShell: .\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m pytest
```

Offline checks need no API key. Copy `.env.example` to `.env` only for an approved API-backed run.

## Repository map

- `src/sovereignlab/schemas/` — the public data contracts; `data/schemas/` holds their JSON Schema.
- `src/sovereignlab/harvest/` — the weekly append-only capture of OECD metadata and the approved
  ECOS/KOSIS series.
- `src/sovereignlab/vintage/`, `snapshots/`, `retrieval/` — the three offline evidence tools and
  the pinned evidence each one reads.
- `src/sovereignlab/execution/` — planner, dispatcher, packet assembler, and executor.
- `scripts/` — capture, schema export, and replay-trace export entry points.
- `data/` — benchmark records, manifests, archives, availability ledgers, and rights catalogs.
- `traces/` — committed replay traces.
- `tests/` — offline tests; nothing calls the network.
- `docs/` — charter, status, architecture, decision records, discovery notes, application wording.
- `experiments/qlora/` — the one-step QLoRA compatibility harness.
