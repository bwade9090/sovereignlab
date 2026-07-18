# SovereignLab project status

- Last updated: 2026-07-18
- Owner: Hyungbae Cho (`bwade9090`)
- Delivery window: four weeks, approximately 80 hours
- Current milestone: M2 — week-2 benchmark and baselines (charter v2.3 §7, Week 2)
- Overall state: source-rights policy, two ECOS plus exact KOSIS CPI and OECD CLI rulings, strict
  append-only rights catalogs,
  the edition-availability decision, the owner-authored employer-risk review (ADR 0006), and the
  implemented contract unit — `EditionAvailabilityLedger` 1.0.0, evidence/benchmark `2.0.0`, typed
  manifest-rights link — plus the offline fail-closed as-of resolver and weekly append-only
  harvester implementation are complete. Real append-only ECOS/KOSIS forward snapshots and the
  one-time OECD Korea CLI revision archive now validate against their manifests and rights
  decisions. The harvester is on the default branch, so the key-free OECD metadata schedule is
  active. Repository `ECOS_API_KEY` and `KOSIS_API_KEY` Actions secrets are configured; the first
  manually dispatched secret-backed run remains an optional separately authorized operational
  check. Number-normalization 1.0.0, the zero-cost QLoRA preflight, and the paid A40/CUDA 13
  one-step compatibility run are complete. The M1b week-1 gate passed on 2026-07-18

## Approved baseline

- Product direction: **K-VINTAGE on KOR-RTD** (charter v2.3; source-rights and
  edition-availability amendments approved 2026-07-16–17; core rationale in
  `docs/discovery/01_concept_upgrade_proposal.md`; decisions recorded as ADRs 0003–0007).
  - KOR-RTD: point-in-time data layer — OECD edition-history consolidation + weekly append-only forward-capture harvester for the latest-only ECOS/KOSIS APIs.
  - K-VINTAGE: two-tier bilingual benchmark (40 human-reviewed core + 200–300 machine-generated
    data-route probes, always reported separately) with regenerable point-in-time gold answers and a
    public script. Accepted ADR 0005 replaces the charter's original
    `max(EDITION <= as_of)` shorthand with edition-level availability evidence and fail-closed
    resolution; ledger selection and the manifest-bound selected-row resolver are implemented.
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
- **Source-rights amendment (2026-07-16):** charter v2.1 and ADR 0004 replace the unverified
  KOGL-only premise with official producer/category and attribution mappings. The owner confirmed
  the non-commercial project profile and approved `allowed` rulings for `200Y108/10601` and
  `301Y017/SA000`.
- **Standalone rights catalog 1.0 (2026-07-16):** strict `RightsInstrument`,
  `SeriesRightsDecision`, and `RightsCatalog` models; official-evidence and operation-status
  invariants; synchronized public JSON Schemas and synthetic fixtures; append-only owner-approved
  catalog metadata under `data/rights/`. Existing `SourceManifest`/benchmark 1.0 contracts remain
  unchanged and no observation payload was added.
- **Edition-availability decision (2026-07-16):** ADR 0005 and charter v2.2 approve an immutable
  availability ledger, `Asia/Seoul` inclusive end-of-day semantics, a fail-closed resolver,
  evidence/benchmark contract `2.0.0`, and the narrow ADR 0002/0003 supersessions. The owner also
  approved OECD `metadata_only pending dataset-specific and third-party-rights confirmation`.
  These are governance outcomes only; the ledger, resolver, parser, migration, and manifest link are
  not implemented in this handoff.
- **Employer-risk review (2026-07-17):** ADR 0006 records the owner's verbatim answers covering
  workplace rules, disclaimers, the public harvester, automated release notes, Bank of Korea
  branding, and the Git-history workstation path. Outcomes: proceed unchanged; a single English
  personal-capacity disclaimer added to the README; no history rewrite (the remediation question is
  closed); charter §9's release-note labeling rule remains in force. The sole owner-authored week-1
  artifact is complete.
- **Contract 2.0.0 + availability ledger 1.0.0 (2026-07-17):** accepted ADR 0005 implemented as one
  work unit (`docs/project/05_evidence_contract_2_0_migration.md`): strict
  `EditionAvailabilityLedger` with the four approved evidence bases, UTC canonical instants,
  window/evidence equality invariants, `Asia/Seoul` end-of-day cutoff computation, ADR 0005 state
  derivation, and structured fail-closed edition selection; `SourceManifest` 2.0.0 with
  `vintage_semantics` and the typed `rights_decision` link (required for `allowed` data snapshots);
  `BenchmarkRecord` 2.0.0 with per-tool-expectation vintage evidence; `BenchmarkBundle` 2.0.0
  cross-validating ledgers, rights links, and gold vintages against ledger-resolved selections while
  keeping the 1.0 cutoff rule for documents and latest-only sources. A 23-agent adversarial review
  then confirmed and closed seven findings before commit: superseded catalogs/ledgers can no longer
  authorize links or vintages, one series scope cannot span multiple active bundled catalogs,
  rights expiry compares instants (`valid_until` inclusive through end-of-day `Asia/Seoul`)
  independent of serialization offset, conservative publisher-date evidence survives DST gaps via
  UTC-instant comparison, calendar overflows raise validation errors instead of raw
  `OverflowError`, the ADR-mandated mid-day-capture/same-day-cutoff and `complete_through`
  boundary tests were added, and the edition-inventory-must-match-constraint rule is disclosed as
  an operational harvester obligation. Rights contracts stay 1.0.0 byte-identical; v1 evidence
  schemas removed (history preserves them); 226 tests at 100% statement/branch coverage. No real
  ledger, manifest, or observation was committed.
- **Offline fail-closed as-of resolver (2026-07-17):** `sovereignlab.vintage` adds strict STES
  query/result types, exact case-sensitive SDMX-CSV code-column parsing (including safe coexistence
  of `MEASURE`/`Measure`), manifest byte-size/SHA-256 verification, canonical URL-to-ledger
  `agency:dataflow` and explicit-version joining, ledger-first selection, and selected-row-only
  evidence packets. Missing, duplicate, or blank selected rows; malformed CSV; unverifiable or
  mismatched dataflows; content mismatch; unsupported source semantics/media; incomplete ledger
  frontiers; and calendar overflow all return structured abstentions without edition codes or
  values. Synthetic tests prove later rows never appear in success or abstention output. A
  temporary, uncommitted official-response regression reproduced the previously recorded GDP
  response hash and selected `202607` for `as_of=2026-07-09`, returning only the verified raw XDC
  value `574984300000000`; the CPI response again contained 258 editions (`200502`–`202607`) with
  its recorded hash. The temporary response files were deleted. This check also found and fixed a
  ledger-schema bug: real OECD constraint IDs contain `@`, so `constraint_id` now uses the approved
  SDMX artefact-reference pattern; the public schema and synthetic fixture were regenerated. No
  real ledger, manifest, or observation was committed.
- **Weekly append-only harvester + first real ledger (2026-07-17):**
  `sovereignlab.harvest.weekly` and `.github/workflows/weekly-harvest.yml` implement a weekly and
  manually dispatchable capture. Every run joins the key-free OECD exact-availability and content
  constraints, validates the canonical STES dataflow/version and identical mechanically derived
  edition inventories, creates checksummed `SourceManifest` 2.0.0 records, advances an immutable
  availability ledger monotonically, verifies all referenced historical bytes, and refuses an
  existing path before writing. The initial committed capture contains 330 edition codes
  (`199902`–`202607`): only `202607` is resolved, with
  `available_by=2026-07-08T09:33:35.737Z`; the other 329 codes remain unresolved rather than being
  backfilled. Its two XML artifacts are constraint metadata without observations and carry the
  owner-approved `metadata_only` policy. Optional ECOS capture is restricted in code to the two
  owner-approved scopes (`200Y108/10601`, `301Y017/SA000`), validates the rights catalog via
  `BenchmarkBundle`, sanitizes the key from committed URLs, and skips explicitly when no key is
  configured. At that capture, no KOSIS scope had an owner-approved exact-series ruling and neither
  the local nor GitHub environment had `ECOS_API_KEY`, so it intentionally contained no raw
  observation. ADR 0007 and the later capture below supersede that operational state.
- **ADR 0007 exact-scope activation + first observation captures (2026-07-17):** the owner approved
  KOSIS national monthly total CPI `101/DT_1J22003/T/T10` and OECD Korea monthly
  amplitude-adjusted CLI revision series
  `DSD_STES_REVISIONS@DF_STES_REVISIONS/KOR.M.LI_AA.IX._T`. Charter v2.3 and a new append-only
  rights catalog preserve the two ECOS decisions and narrowly supersede the OECD metadata-only
  ruling for that single first-party series. The weekly harvester now validates and captures the
  KOSIS scope when `KOSIS_API_KEY` exists; local ECOS/KOSIS keys produced real snapshots of 265
  quarterly GDP rows (`1960Q1`–`2026Q1`), 557 monthly current-account rows
  (`198001`–`202605`), and 738 monthly CPI rows (`196501`–`202606`). A separate one-time/manual
  CLI capture stored 75,060 rows, 239 editions (`200604`–`202607`), and periods
  `1990-01`–`2026-06` in a 21,734,727-byte consolidated CSV. All four observation artifacts pass
  typed rights-bundle, byte-size, and SHA-256 validation. A real resolver check selected only
  edition `202607`, period `2026-05`, value `102.66` for `as_of=2026-07-09`. A repository-wide
  secret comparison confirmed neither local key appears in tracked or untracked publishable files.
- **Number-normalization specification 1.0.0 (2026-07-17):**
  `docs/project/06_number_normalization_spec.md` and `sovereignlab.normalization` freeze
  exact-`Decimal` parsing, case-sensitive exact-scope rule selection, source-string preservation,
  Korean 원/백만원/억원/십억원/조원 powers-of-ten conversions, explicit canonical units,
  `ROUND_HALF_UP` presentation, and half-one-displayed-unit grading tolerance. The verified OECD
  GDP XDC example maps by `10^-9` to billion KRW; neighboring GDP/CLI variants fail closed. Five
  exact MVP rules cover the two approved ECOS series, KOSIS national CPI, OECD Korea CLI, and the
  verified OECD quarterly real-GDP revision series. Rights approval remains a separate gate.
- **Ministral 3 QLoRA zero-cost preflight (2026-07-17):** an isolated spike under
  `experiments/qlora/` pins the public BF16 checkpoint
  `mistralai/Ministral-3-3B-Instruct-2512-BF16` at commit
  `b6d637bef2393152b3da2b2fde72eecdee30557e` plus direct GPU dependencies. The free preflight
  verifies public/ungated state, Apache-2.0 model-card license, architecture and text/vision
  dimensions, required Hub files, and four synthetic bilingual route examples without downloading
  weights. The paid harness uses NF4 double quantization, language-model-only all-linear LoRA,
  exactly one optimizer step, finite/nonzero-gradient checks, adapter-change verification, and
  adapter-only safetensors output. Local preflight passed; the separately recorded paid result
  below subsequently closed the compatibility gate.
- **Ministral 3 QLoRA paid GPU compatibility (2026-07-18):** the pinned harness passed on a
  RunPod Secure Cloud NVIDIA A40 (46,068 MiB), driver 580.159.04, CUDA 13.0, and Python 3.12.3.
  `torch 2.13.0+cu130`, `transformers 5.14.1`, `peft 0.19.1`, and `bitsandbytes 0.49.2` loaded the
  public BF16 checkpoint, attached language-model-only NF4/all-linear LoRA, and completed exactly
  one optimizer step in 23.439 seconds. The finite loss was `5.192200660705566`; 12,353,536
  parameters were trainable; peak CUDA allocation was 4,210,338,304 bytes; and the 49,474,005-byte
  output contained only `adapter_config.json`, `adapter_model.safetensors`, and the generated
  adapter README. The adapter and base-model cache stayed on the disposable Pod and were deleted.
  Provisioning preserved three negative operational findings: a custom image without a suitable
  startup/template path never reached container uptime; RunPod's dedicated SSH key must exist
  before Pod creation; and the pinned PyTorch wheel requires a host created with minimum CUDA 13.0.
  Installing the virtual environment on the container disk rather than the network-mounted
  `/workspace` removed severe metadata-I/O delay. All attempted Pods were deleted, the account
  returned to `$0` current hourly spend, and finalized RunPod billing was
  `$0.23584524099715054`.

## Current validation evidence

Run from the repository root after activating `.venv` (any OS; see README quick start):

```bash
python -m ruff check .
python -m ruff format --check .
python -m pytest
```

Last validated 2026-07-14 on Windows (Python 3.12.13): ruff clean, format clean, `pytest --cov=sovereignlab` 45 passed with 100% statement and branch coverage (241 statements, 60 branches); `git check-ignore` confirmed exclusion of `.venv`, `.env`, `data/raw`, `models`, generated `artifacts`, `traces/private`; `python scripts/export_json_schemas.py` regenerates both public schemas deterministically.

The 2026-07-14 reorientation commit is documentation-only (charter, ADR, AGENTS.md, status, CV bullets, README, proposal); no source or test files changed. It was additionally smoke-checked on macOS with a throwaway Python 3.13.13 environment (pinned requirements installed cleanly; ruff clean, format clean, 45 tests passed) — the project standard remains Python 3.12 per ADR 0001.

Validated 2026-07-15 on Windows after recording the M1b spikes, reproducibility log, and proposed
ADRs 0004–0005: Python 3.12.13; `python -m ruff check .` clean;
`python -m ruff format --check .` clean (15 files already formatted);
`python -m pytest --cov=sovereignlab --cov-report=term-missing` passed all 45 tests with 100%
statement/branch coverage (241 statements, 60 branches); `git diff --check` clean.

Revalidated 2026-07-16 on Windows after correcting the ECOS/KOSIS rights basis and data-licensing
boundary: Python 3.12.13; `python -m ruff check .` clean; `python -m ruff format --check .` clean
(15 files already formatted); `python -m pytest --cov=sovereignlab --cov-report=term-missing` passed
all 45 tests with 100% statement/branch coverage (241 statements, 60 branches); `git diff --check`
clean.

Validated 2026-07-16 on Windows after charter v2.2 approval and strengthened rights-catalog
implementation: Python 3.12.13; `python scripts/export_json_schemas.py` regenerated five contracts;
`python -m ruff check .` clean; `python -m ruff format --check .` clean (17 files already
formatted); `python -m pytest --cov=sovereignlab --cov-report=term-missing` passed all 147 tests
with 100% statement/branch coverage (633 statements, 218 branches); `git diff --check` clean. No
raw observation endpoint or paid operation was used.

Validated 2026-07-17 on macOS after recording ADR 0006 and creating the Homebrew Python 3.12
environment: Python 3.12.13; `python scripts/export_json_schemas.py` regenerated all five contracts
with no diff; `python -m ruff check .` clean; `python -m ruff format --check .` clean (17 files
already formatted); `python -m pytest --cov=sovereignlab --cov-report=term-missing` passed all 147
tests with 100% statement/branch coverage (633 statements, 218 branches). Documentation-only
change; no observation endpoint or paid operation was used.

Validated 2026-07-17 on macOS after implementing the ADR 0005 contract unit and applying the
adversarial-review fixes: Python 3.12.13; `python scripts/export_json_schemas.py` exported six
contracts (`-v2` evidence schemas plus the new availability ledger; rights schemas byte-identical);
`python -m ruff check .` clean; `python -m ruff format --check .` clean (19 files);
`python -m pytest --cov=sovereignlab --cov-report=term-missing` passed all 226 tests with 100%
statement/branch coverage (923 statements, 350 branches); `git diff --check` clean. Offline
code/schema/tests only; no observation endpoint or paid operation was used.

Validated 2026-07-17 on macOS after implementing the offline as-of resolver and the constraint-ID
contract correction: Python 3.12.13; `python scripts/export_json_schemas.py` regenerated all six
contracts; `python -m ruff check .` clean; `python -m ruff format --check .` clean; `python -m
pytest --cov=sovereignlab --cov-report=term-missing` passed all 255 tests with 100% statement/branch
coverage. A read-only, key-free official-response regression used workstation temporary files only:
GDP 4,770 bytes / SHA-256 `484ba74366c07d1911e70988aa202fcbe1bc384b0f743aae2b70bf6d9dc497fa`;
CPI 63,799 bytes / SHA-256
`0e45f924a9c2a4742729f649893c54e836200ca268171e7897f1748cd7c3a572`. Both matched the
2026-07-15 verification log exactly; temporary files were deleted and no paid operation occurred.

Validated 2026-07-17 on macOS after implementing the weekly harvester and recording its first real
OECD metadata capture: Python 3.12.13; `python scripts/export_json_schemas.py` was deterministic;
`python -m ruff check .` and `python -m ruff format --check .` were clean; `python -m pytest
--cov=sovereignlab --cov-branch --cov-report=term-missing` passed all 288 tests with 100% statement
and branch coverage (1,371 statements, 478 branches); `git diff --check` was clean. The captured
availability-constraint XML is 17,827 bytes / SHA-256
`e7a3fab8730a2d9e4644ccb78844d721c263a2b235d4575fa850d1f0c71be06f`; the content-constraint
XML is 23,251 bytes / SHA-256
`40b9f6e25f0187992f679fd5e8ae8215182076d8e280b71ca74b737d204334e6`. Both are key-free
metadata-only responses and contain no observations. No paid operation occurred.

Validated 2026-07-17 on macOS after ADR 0007 implementation and the first approved observation
captures: Python 3.12.13; `python scripts/export_json_schemas.py` regenerated all six contracts;
`python -m ruff check .` and `python -m ruff format --check .` were clean; `python -m pytest
--cov=sovereignlab --cov-branch --cov-report=term-missing` passed all 314 tests with 100% statement
and branch coverage (1,535 statements, 528 branches); `git diff --check` was clean. Observation
SHA-256 values are GDP `75c96ce62270a8a6c2a3c6bebaef981945b41f37f62cab6911698ce64d8dd9ea`,
current account `8f71259c202ed7cc4d6b2eebea5123215547b6ffd3f653ef734fdd8564bd9389`,
KOSIS CPI `f1336aba6ea64fcb7d438d008ba564d25d35e6f0f4d6d8d0ef0f8ec1954834d6`, and
OECD CLI `ac7d0f9a2517870173885f1d45e2edea90f54cd485e2f539c73afddde566f058`.
Every manifest matches the committed bytes and exact owner-approved rights decision. API use and
the key-free OECD download cost $0; the local secrets remain ignored and absent from publishable
files.

Validated 2026-07-17 on macOS after freezing number-normalization 1.0.0: Python 3.12.13; ruff check
and format check were clean; `python -m pytest --cov=sovereignlab --cov-branch
--cov-report=term-missing` passed all 323 tests with 100% statement and branch coverage (1,598
statements, 534 branches); `git diff --check` was clean. One key-free in-memory OECD read confirmed
the exact GDP code dimensions `KOR.Q.B1GQ_Q.XDC._T`, raw XDC units, and the previously recorded
value; no response was saved and no paid operation occurred.

Validated 2026-07-17 on macOS after adding the isolated QLoRA compatibility harness: the 14
CPU-only harness tests and real public-Hub preflight passed; the latter returned
`preflight_passed`, four examples, zero weight downloads, and $0 cost. Full ruff and format checks
were clean; all 337 tests passed with 100% SovereignLab statement/branch coverage (1,598 statements,
534 branches); `git diff --check` was clean. The paid GPU step remains unexecuted.

Validated 2026-07-18 after the paid compatibility run and M2 handoff update. The remote RunPod
check used an NVIDIA A40, driver 580.159.04, CUDA 13.0, and Python 3.12.3; the pinned harness
returned `gpu_step_passed`, exactly one optimizer step, finite loss `5.192200660705566`, 12,353,536
trainable parameters, 4,210,338,304 peak CUDA bytes, and 49,474,005 bytes of adapter-only output.
The output and model cache were deleted with the Pod, all attempted Pods were removed, and current
hourly spend returned to `$0`. Locally on macOS/Python 3.12.13,
`python scripts/export_json_schemas.py` remained deterministic; `python -m ruff check .` and
`python -m ruff format --check .` passed; `python -m pytest --cov=sovereignlab --cov-branch
--cov-report=term-missing` passed all 337 tests with 100% statement/branch coverage (1,598
statements, 534 branches); and `git diff --check` was clean.

## M1b verification spike record (2026-07-15)

All network work below was read-only, key-free, and free of charge. Raw responses were written only
to the workstation's temporary directory for inspection and hashing; no downloaded observation file
was added to the repository. Timestamps are UTC. The Windows workstation required
`curl.exe --ssl-no-revoke` because Schannel could not reach its certificate-revocation service; this
kept normal TLS certificate validation enabled.

Exact request URLs, timestamps, status codes, byte counts, hashes, and parser commands are preserved
in `docs/discovery/03_week1_verification_log.md`; the log contains metadata only, not downloaded
response bodies.

### `DF_MEI_ARCHIVE` — accessible on the archive tenant only

- Exact data request:
  `https://sdmx.oecd.org/archive/rest/data/OECD,DF_MEI_ARCHIVE,/KOR.101..Q?format=csvfilewithlabels`
  — at 2026-07-15 05:11:31 it returned HTTP 200, SDMX-CSV v2, 10,581,205 bytes,
  44,138 rows, and SHA-256
  `0bf918fe7415787fb1f6a3ddf52a406527d6a09b76b00db53de3175354d61f80`. A separate repeat
  request also returned HTTP 200 with the same byte count and hash.
- The corresponding `public`-tenant data and structure requests returned HTTP 404. The current
  200/404 conflict is therefore reproducible as `archive=200`, `public=404`; the 2026-07-14 failing
  probe did not preserve its URL, so tenant confusion is the most direct explanation, not a proven
  historical cause.
- Exact structure request:
  `https://sdmx.oecd.org/archive/rest/dataflow/OECD/DF_MEI_ARCHIVE/latest?references=all`
  — HTTP 200, `OECD:DSD_MEI_ARCHIVE(1.0)`, `isFinal=true`, 65 `LOCATION` codes (including
  aggregates such as OECD/G20/EU, so **not 65 countries**), 24 `VAR` codes, and 300 monthly `EDI`
  codes from `199902` through `202401`.
- The KOR quarterly real-GDP slice contains 299 distinct editions, not 300: `200904` is declared in
  the codelist but returns `NoRecordsFound` for this slice. The reported KOR 2010-Q1 example is
  reproduced exactly as 165 editions from `201005` through `202401`, with ten distinct observation
  values.
- The dataflow carries `NonProductionDataflow=true`. Claim-safe conclusion: the archive is an
  accessible frozen cross-check as of this date, but it is not a guaranteed production endpoint.

### Economic Outlook range — recent KOR observation range fixed

- Archive listing `https://sdmx.oecd.org/archive/rest/dataflow/all/all/latest` returned HTTP 200 and
  112 `DF_EO*` definitions enumerate every EO number from 60 through 114 (55 editions, no numeric
  gap). This is catalog continuity, not observation continuity. Sampled KOR responses were HTTP 200
  for `DF_EO60_MAIN`, `DF_EO107_EDITIONS`, and `DF_EO114_INTERNET`; EO60 was sparse and contained
  only `EXCHUD` in the main flow, while EO107 and EO114 contained `GDPV`. The untested middle
  editions therefore cannot support a claim of continuous KOR observation backfill.
- Public edition-specific flows EO114–EO118 and current `DSD_EO@DF_EO` (named Economic Outlook 119,
  version 1.5) each returned an actual KOR observation response. All six contain nonblank annual and
  quarterly `GDPV`; the full-response row counts were respectively 56,331, 36,990, 36,898, 36,918,
  37,647, and 37,782. The EO117 long-term-scenario flow remains separate.
- Claim-safe forecast-vintage range for the MVP is therefore **public EO114–EO119**. The archive
  claim remains “catalog EO60–EO114 plus sampled KOR observations at EO60/107/114,” not continuous
  KOR coverage. Do not claim a literal archive ID `DF_EO114`; the boundary ID is
  `DF_EO114_INTERNET`. Deep EO60–EO113 backfill remains de-scoped.

### Primary live revisions flow — target examples reproduced

- Structure request
  `https://sdmx.oecd.org/public/rest/dataflow/OECD.SDD.STES/DSD_STES_REVISIONS%40DF_STES_REVISIONS/latest?references=all`
  returned HTTP 200 and confirms dimension order
  `REF_AREA.FREQ.MEASURE.UNIT_MEASURE.ACTIVITY.EDITION`, plus
  `NonProductionDataflow=true`.
- KOR 2025-Q1 quarterly real-GDP request
  `https://sdmx.oecd.org/public/rest/data/OECD.SDD.STES,DSD_STES_REVISIONS%40DF_STES_REVISIONS,/KOR.Q.B1GQ_Q...?startPeriod=2025-Q1&endPeriod=2025-Q1&format=csvfilewithlabels`
  returned HTTP 200, 15 editions (`202505`–`202607`), and SHA-256
  `484ba74366c07d1911e70988aa202fcbe1bc384b0f743aae2b70bf6d9dc497fa`. The June and July
  2026 raw XDC values are respectively `572057700000000` and `574984300000000`, reproducing
  572,057.7 and 574,984.3 billion KRW after division by `10^9`.
- KOR CPI 2005-01 request using measure `CP` returned HTTP 200 and exactly 258 editions from
  `200502` through `202607`, reproducing the reported archive-coverage count.
- Resolver design blocker confirmed: `EDITION=YYYYMM` is a monthly label, not a publication date.
  The codelist already includes future labels through `202812`, while current availability stops at
  `202607`. The current content constraint records
  `validFrom=2026-07-08T09:33:35.737Z`, which conservatively supports July's current availability
  region; it does not preserve June's historical region or prove an exact first-public instant.
- `updatedAfter` brackets current row update time, not first publication. HTTP response timestamps
  are generated at request time. Related official MEI issue dates also vary within their labeled
  month, although one-to-one STES mapping remains unverified. Accepted ADR 0005 therefore uses an
  edition-specific availability-window ledger and abstains across an unresolved frontier; first-day
  or month-end inference is prohibited for the reviewed core and headline leakage metric.
- A single `SourceManifest.published_on` cannot represent all historical editions in a consolidated
  response, and backdating a 2026 snapshot would violate ADR 0002. Mandatory vintage evidence and
  the corresponding bundle rule require the accepted `2.0.0` contract rather than ADR 0003's expected
  optional `1.1.0` field.

### OECD rights — base terms verified; exact CLI scope later approved

- The [OECD Open Access Policy](https://www.oecd.org/en/about/oecd-open-by-default-policy.html)
  says content published before 2024-07-01 is governed by OECD Terms & Conditions, not by the later
  default CC BY 4.0 licence.
- The [OECD Terms & Conditions](https://www.oecd.org/en/about/terms-conditions.html) Data section
  permits extraction, download, copying, adaptation, distribution, sharing, and embedding for any
  purpose, including commercial use, unless dataset-specific restrictions or third-party rights
  apply. It requires OECD attribution and propagation of that acknowledgement requirement to
  sublicensees.
- `DF_MEI_ARCHIVE` structure/CSV metadata exposed no licence, restriction, or third-party-rights
  field. It remains `metadata_only`, not `CC BY 4.0`. ADR 0007 later completed the exact
  first-party review only for Korea monthly amplitude-adjusted CLI
  `KOR.M.LI_AA.IX._T`; that decision does not extend to `DF_MEI_ARCHIVE` or another OECD series.

### ECOS/KOSIS rights — policy, initial rulings, and catalog implemented

- ECOS and KOSIS API schemas do not expose a per-series KOGL/licence field, but that absence does
  not imply missing permission. The official use guides are source-wide rights instruments whose
  applicable branch must be mapped to each exact producer or content category.
- The [ECOS Statistics Information Use Guide](https://ecos.bok.or.kr/) permits Bank of
  Korea-produced statistics to be used, processed, and redistributed free of charge for commercial
  and non-commercial purposes with source attribution. Other-producer statistics may be used
  non-commercially with attribution, while commercial use requires the producer's approval; because
  that branch does not expressly grant processing or redistribution, public raw commits fail closed
  without a more specific instrument.
- The [KOSIS Statistics Information Use Guide](https://kosis.kr/nsistN/kosisUseGuide.do) permits
  in-scope domestic macro statistics to be used, reused, and redistributed commercially or
  non-commercially with detailed attribution. Distortion and paid standalone sale of unchanged raw
  information are prohibited. International and North Korea statistics are non-commercial-only and
  may not be redistributed; publications follow their individual KOGL notices.
- Accepted ADR 0004 and charter v2.2 retain an owner-approved per-series audit gate, map the exact
  producer/category to the real publisher terms rather than fabricate a KOGL value, and define a
  reusable classification-and-attribution ruling instead of a fresh licence investigation for
  every capture.
- Exact ECOS metadata identifies quarterly SA real GDP as `200Y108/10601` (quarterly, billion KRW)
  and SA current account as `301Y017/SA000` (monthly, million USD). The latter directly names Bank
  of Korea as `ORG_NAME`. For the former, the ECOS item API maps the exact code to the named table;
  the [KOSIS official recent-data record](https://kosis.kr/serviceInfo/newContrainDataDetail.do?boardIdx=1976017&boardOrgId=301)
  assigns the same title/frequency to Bank of Korea, with an official
  [Bank of Korea GDP release](https://www.bok.or.kr/portal/bbs/B0000501/view.do?menuNo=200690&nttId=10097644)
  as corroboration. The GDP join is title/frequency-based, not a direct ECOS code-to-producer field;
  the owner accepted that mapping on 2026-07-16. Both series now have validated `allowed` records in
  `data/rights/kor-rtd-rights-2026-07-16.json` with exact scope, official evidence, permitted
  operations, attribution template, and aware approval-record timestamp.
- The independent catalog does not itself authorize raw publication. At the time of this spike,
  `SourceManifest` 1.0 had no typed decision link; the 2026-07-17 contract `2.0.0` implementation
  added that link and its bundle cross-validation. Source observations retain provider terms and
  are not relicensed under repository Apache-2.0.

### Owner decisions closed

- On 2026-07-16 the owner approved ADR 0005 in full: the edition-availability ledger, fail-closed
  resolver, `Asia/Seoul` end-of-day cutoff, evidence/benchmark contract `2.0.0` path, and narrow
  partial supersessions of ADR 0002 decision 5 and ADR 0003 decisions 1/3.
- The owner also approved `OECD metadata_only pending dataset-specific and third-party-rights
  confirmation`. ADR 0007 later superseded that interim ruling only for exact first-party CLI scope
  `KOR.M.LI_AA.IX._T`; all other OECD observation scopes retain it.
- On 2026-07-17 the owner completed the one-hour employer-risk review required by charter §7,
  answering an agent-provided question list in their own words; ADR 0006 commits those verbatim
  answers as the decision record.
- On 2026-07-17 the owner approved KOSIS CPI and OECD Composite leading indicator (Korea). ADR 0007
  translates those names to exact official scope IDs and records the narrow rights decisions;
  charter v2.3 and the append-only 2026-07-17 catalog are synchronized. All current week-1 owner
  decisions are closed.

## Immediate next action (M2 — do these in order)

1. Freeze the 40-question human-reviewed core authoring matrix: ten records per exclusive route,
   balanced Korean/English coverage, evidence-disjoint split assignments, and co-location of any
   parallel translations. Start with one small reviewable batch grounded only in currently
   validated evidence and keep it separate from machine-generated probes.
2. Implement publication-date-filtered bilingual document retrieval against the same evidence
   contract, with offline fixtures before any source-document download or paid embedding call.
3. Join the router, temporal retrieval, and deterministic as-of tool into the minimal
   question-to-evidence-packet path before generating the tier-2 probes.

Open operational check, not an M2 blocker: manually dispatch one secret-backed append-only
harvester run only with separate owner authorization; otherwise the next weekly schedule will use
the configured Actions secrets normally.

Week-1 gate (charter v2.3 §7): **passed 2026-07-18**. Endpoint/range spikes, exact source-rights
policy and four approved series decisions, strict catalogs, availability design, owner
employer-risk review, contract `2.0.0`/ledger 1.0.0/manifest-rights integration, resolver
regression, harvester, real forward snapshots, approved CLI consolidation, number normalization,
default-branch workflow activation, and the paid Ministral 3 3B QLoRA compatibility result are all
complete.

## Blockers and environment notes

- No development machine has a training GPU. The disposable RunPod A40/CUDA 13 path is verified,
  `runpodctl` and its dedicated SSH key are configured locally, and no Pod remains active. Any
  later multi-configuration training still requires a separate paid-operation authorization and
  spend estimate.
- Development spans multiple machines. `.venv` is machine-local — recreate it per the README quick start on whichever machine picks this up. Nothing in the repo may depend on machine-specific paths.
- Windows workstation note: the user-level Python launcher is unreliable there; use the workstation's documented bundled Python 3.12.13 runtime to create `.venv` (local path recorded outside the repository; an earlier revision of this file recorded the literal path — ADR 0006 closed that question with the owner's decision that no history remediation is needed).
- Rights gate: ADRs 0004/0007, charter v2.3, the append-only catalog chain, two approved ECOS rows,
  exact KOSIS CPI and OECD CLI rows, and typed manifest-rights bundle validation are complete. The
  local snapshots are captured and the two exact GitHub Actions secrets are configured. They remain
  distinct from the ignored local `.env`; their plaintext cannot be retrieved from GitHub.
- Vintage semantics: OECD monthly `EDITION` codes do not encode availability dates. The
  `EditionAvailabilityLedger`, fail-closed selection, and selected-row resolver are implemented;
  unknown editions abstain mechanically. The first real ledger resolves only `202607`; all 329
  older codes remain unknown until acceptable historical evidence exists.
- macOS laptop note: `python@3.12` was installed via Homebrew on 2026-07-17 and is the interpreter
  for the machine-local `.venv` (project standard per ADR 0001).
- GitHub CLI is authenticated as `bwade9090`; `main` tracks `origin/main`.
- `main` tracks `origin/main`; the validated `codex/m1b-harvester` work was fast-forwarded to the
  default branch. The weekly workflow is active there; the remote feature branch is retained as
  non-authoritative review history and may be removed later by the owner.
- Live-event calendar: primary = the next observed OECD edition rollover (the exact date is not yet
  verified; append-only polling must detect it); fallback = the July-vs-June edition diff, subject to
  availability provenance; stretch = Korea Q2-2026 advance GDP release (~2026-07-23/24, tight — see
  charter §7).

## Spend ledger

| Date | Operation | Cost | Evidence |
|---|---|---:|---|
| 2026-07-14 | Local foundation and PyPI dependencies | $0.00 | No model/API/GPU call |
| 2026-07-14 | Concept reorientation (docs only) | $0.00 | No model/API/GPU call under project budget |
| 2026-07-15 | Week-1 public endpoint and rights verification spikes | $0.00 | Key-free OECD/BOK/KOSIS/public-policy reads; no paid call |
| 2026-07-16 | ECOS/KOSIS official use-guide and producer verification | $0.00 | Public policy/metadata reads only; no observation or paid call |
| 2026-07-16 | Rights catalog contract and two approved ECOS metadata rows | $0.00 | Offline code/schema/tests; no observation payload or paid call |
| 2026-07-16 | Charter v2.2 approval and cross-machine handoff | $0.00 | Documentation, offline validation, commit/push only |
| 2026-07-17 | Employer-risk review record (ADR 0006) and macOS 3.12 environment | $0.00 | Documentation and offline validation only; no paid call |
| 2026-07-17 | ADR 0005 contract unit implementation and adversarial review | $0.00 | Offline code/schema/tests; agent review under subscription, no project API/GPU call |
| 2026-07-17 | Offline as-of resolver + temporary official-response regression | $0.00 | Key-free OECD reads; temporary responses deleted; no paid call |
| 2026-07-17 | Weekly harvester implementation + first OECD constraint capture | $0.00 | Key-free metadata-only OECD reads; no observation or paid call |
| 2026-07-17 | Exact KOSIS CPI/CLI rights implementation + first approved captures | $0.00 | Free official APIs and key-free OECD download; no paid call |
| 2026-07-17 | Ministral 3 QLoRA metadata/fixture preflight | $0.00 | Public Hub metadata/config only; no weights or GPU |
| 2026-07-17 | ECOS/KOSIS GitHub Actions secret registration | $0.00 | Encrypted repository secrets; names/timestamps verified, values not read back |
| 2026-07-18 | RunPod A40/CUDA 13 Ministral 3 QLoRA compatibility | $0.23584524099715054 | Finalized billing for 1,832,105 ms across five A40 provisioning/success Pods; account balance `$20.0000000000` -> `$19.7641547592`; all Pods deleted, current spend `$0`/h |

**Cumulative external spend: $0.23584524099715054 / $100.00**

## Handoff rule (onboarding for a new contributor or AI agent)

Read in this order, in full, before changing anything:

1. `AGENTS.md` — working protocol, evidence rules, setup, repository map.
2. `docs/project/01_project_charter.md` — the v2.3 scope authority.
3. This file — current milestone, next action, gates, blockers.
4. `docs/project/04_macbook_handoff.md` — machine setup and exact continuation order.
5. Accepted ADRs 0001–0007 in `docs/decisions/`.
6. `docs/project/05_evidence_contract_2_0_migration.md` — the implemented contract the resolver
   and harvester build on.
7. `docs/discovery/01_concept_upgrade_proposal.md` — background: why v2 exists, verified data facts, judged alternatives, risk register.

Then start with "Immediate next action" item 1. M1b is closed, so the benchmark-authoring and
minimal retrieval work are now authorized. Do not start full LoRA tuning, UI, or release work before
the M2 gate closes. The harvester must stay within approved rights scopes, and every later paid
operation remains smoke-test-first. Do not weaken the qualification rules for "first" claims or the
rights/append-only rules in `AGENTS.md`.
Update this file whenever a milestone state, blocker, cost, spike result, or next action changes.
