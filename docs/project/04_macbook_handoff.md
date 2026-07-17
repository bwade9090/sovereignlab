# Continuation handoff

- Prepared: 2026-07-16; refreshed 2026-07-17 after the first approved observation captures
- Authority: charter v2.3; accepted ADRs 0001–0007
- Branch to continue: `codex/m1b-harvester` from `origin`
- Current milestone: M1b

## 1. What is complete

- Charter v2.3 and ADRs 0003–0007 record the K-VINTAGE/KOR-RTD direction, source-rights policy,
  and fail-closed edition-availability contract.
- ADR 0006 (2026-07-17) commits the owner-authored employer-risk review: proceed unchanged, a
  single English personal-capacity disclaimer in the README, no Git-history rewrite. All week-1
  owner decisions are closed.
- The ADR 0005 contract unit is implemented
  (`docs/project/05_evidence_contract_2_0_migration.md`): `EditionAvailabilityLedger` 1.0.0 with
  fail-closed edition selection, `SourceManifest`/`BenchmarkRecord`/`BenchmarkBundle` 2.0.0, and
  the typed manifest-to-rights-decision link with bundle cross-validation (including catalog/ledger
  supersession and instant-based expiry). A 23-agent adversarial review's seven confirmed findings
  were fixed before commit.
- The offline STES as-of resolver is implemented under `src/sovereignlab/vintage/`: exact
  case-sensitive code-header parsing, manifest size/hash verification, canonical manifest URL to
  ledger dataflow/version joining, ledger-first fail-closed selection, and selected-row-only output.
  The official GDP and CPI verification responses were re-read through temporary files and matched
  the recorded hashes/examples; no response body was committed. The check also corrected the
  ledger's `constraint_id` pattern so real OECD IDs containing `@` validate.
- RightsCatalog 1.0 now has an append-only two-catalog chain. The current catalog preserves the two
  ECOS decisions and adds only KOSIS national CPI `101/DT_1J22003/T/T10` and OECD Korea monthly
  amplitude-adjusted CLI `KOR.M.LI_AA.IX._T`, per ADR 0007. Other OECD observations remain
  `metadata_only`.
- The weekly append-only harvester and GitHub Actions schedule are implemented. The first real
  key-free OECD constraint capture and manifest-backed ledger contain no observations; `202607` is
  resolved at the official constraint `validFrom`, while the other 329 mechanically inventoried
  editions remain unresolved. A later local run captured the two exact ECOS series and exact KOSIS
  CPI scope; the separate one-time CLI capture stored 75,060 rows across 239 editions. Local keys
  remain ignored and are absent from publishable files; GitHub repository secrets are still not
  configured. External spend remains USD 0.
- Number-normalization 1.0.0 is frozen in `docs/project/06_number_normalization_spec.md` and
  `sovereignlab.normalization`: exact Decimal rules cover the two ECOS scopes, KOSIS CPI, OECD CLI,
  and the verified OECD GDP XDC-to-billion-KRW transform; Korean unit conversion, presentation
  rounding, tolerance, and variant fail-closed behavior are tested.
- macOS validation at handoff (2026-07-17, Python 3.12.13 via Homebrew): 323 tests passed with
  100% statement/branch coverage; ruff check/format clean;
  `python scripts/export_json_schemas.py` deterministic (six contracts).

## 2. Set up the machine

`.venv` is machine-local; never copy it between machines. On the macOS laptop it already exists
(Homebrew `python@3.12`, created 2026-07-17) — activate and validate. On any other machine,
recreate it per the README quick start. From an existing clone:

```bash
git switch codex/m1b-harvester
git pull --ff-only origin codex/m1b-harvester
source .venv/bin/activate  # or recreate: python3.12 -m venv .venv && pip install -r requirements.txt
python scripts/export_json_schemas.py
python -m ruff check .
python -m ruff format --check .
python -m pytest --cov=sovereignlab --cov-report=term-missing
git diff --exit-code
```

## 3. Read before continuing

1. `AGENTS.md`.
2. `docs/project/01_project_charter.md`.
3. `docs/PROJECT_STATUS.md`.
4. ADRs 0004, 0005, 0006, and 0007.
5. `docs/project/05_evidence_contract_2_0_migration.md` — the implemented contract surface the
   next work units build on.
6. `docs/discovery/03_week1_verification_log.md` — the verified example values the resolver must
   reproduce.
7. `src/sovereignlab/vintage/resolver.py`, `src/sovereignlab/harvest/weekly.py`, and their tests —
   the implemented resolver and append-only capture boundaries.

## 4. Exact continuation order

1. Review and merge `codex/m1b-harvester` so the default-branch weekly schedule activates. Add the
   `ECOS_API_KEY` and `KOSIS_API_KEY` repository secrets and manually dispatch a smoke run only
   after separate owner authorization; local `.env` values do not configure GitHub Actions.
2. Run the Ministral 3 3B QLoRA compatibility spike on rented compute only after its smoke test;
   record cost in the spend ledger.

## 5. Hard stops

- Do not reinterpret `EDITION=YYYYMM` as a publication date.
- Do not implement a heuristic fallback across an unknown availability frontier; abstention is the
  correct answer.
- Do not commit raw ECOS/KOSIS observations unless the manifest's typed `rights_decision` link
  cross-validates against the committed owner-approved catalog under `BenchmarkBundle` 2.0.0
  rules.
- Do not publish raw OECD archive observations beyond ADR 0007's exact CLI exception; all other
  OECD scopes remain metadata-only.
- Do not run paid APIs, OCR, embeddings, or GPU work without a smoke test and spend-ledger entry.
- Do not weaken the qualification rules for "first" claims or the append-only rules in
  `AGENTS.md`.
