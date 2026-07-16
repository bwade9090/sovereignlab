# MacBook continuation handoff

- Prepared: 2026-07-16
- Authority: charter v2.2; accepted ADRs 0001–0005
- Branch to continue: `main` from `origin`
- Current milestone: M1b

## 1. What is complete

- Charter v2.2 and ADRs 0003–0005 record the K-VINTAGE/KOR-RTD direction, source-rights policy,
  and fail-closed edition-availability contract.
- RightsCatalog 1.0 is implemented with synchronized JSON Schemas, synthetic fixtures, and two
  owner-approved ECOS metadata decisions: `200Y108/10601` and `301Y017/SA000`.
- The OECD archive ruling is `metadata_only pending dataset-specific and third-party-rights
  confirmation`; raw OECD redistribution is not approved.
- `SourceManifest` and benchmark contracts remain at 1.0. No raw observation payload has been
  added, and external spend remains USD 0.
- Windows validation at handoff: 147 tests passed with 100% statement/branch coverage
  (633 statements, 218 branches); ruff and format checks were clean.

## 2. Set up the MacBook

Do not copy the Windows `.venv`. From an existing clone, pull the committed handoff:

```bash
git switch main
git pull --ff-only origin main
```

The project standard is Python 3.12. If it is not installed:

```bash
brew install python@3.12
```

Then create a machine-local environment and validate the checkout:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python scripts/export_json_schemas.py
python -m ruff check .
python -m ruff format --check .
python -m pytest --cov=sovereignlab --cov-report=term-missing
git diff --exit-code
```

Python 3.13.13 was previously smoke-tested successfully on this Mac, but use 3.12 when practical
because ADR 0001 defines it as the standard.

## 3. Read before continuing

1. `AGENTS.md`.
2. `docs/project/01_project_charter.md`.
3. `docs/PROJECT_STATUS.md`.
4. ADRs 0004 and 0005.
5. `docs/project/03_rights_catalog_contract.md`.
6. `docs/discovery/03_week1_verification_log.md`.

## 4. Exact continuation order

1. Hyungbae personally writes and commits the one-hour employer-risk review specified in
   `docs/PROJECT_STATUS.md`. An agent may supply questions but must not fabricate the owner's
   review text.
2. Implement accepted ADR 0005 as one reviewable contract unit:
   `EditionAvailabilityLedger` 1.0, evidence/benchmark 2.0 migration, migration notes, regenerated
   schemas, synthetic fixtures, and tests.
3. In that same governed migration, add the typed `SourceManifest`-to-rights-decision link and
   cross-record validation required before any raw ECOS/KOSIS capture.
4. Implement the case-sensitive SDMX parser and fail-closed resolver, then reproduce only the
   verified examples recorded in project status.
5. Continue with the harvester, number-normalization specification, and QLoRA smoke test in the
   order listed in project status.

## 5. Hard stops

- Do not reinterpret `EDITION=YYYYMM` as a publication date.
- Do not implement a heuristic fallback across an unknown availability frontier.
- Do not commit raw ECOS/KOSIS observations until the typed manifest-rights link is implemented and
  the owner-authored employer review is complete.
- Do not publish raw OECD archive observations under the metadata-only ruling.
- Do not run paid APIs, OCR, embeddings, or GPU work without a smoke test and spend-ledger entry.
