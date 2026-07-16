# SovereignLab project status

- Last updated: 2026-07-17
- Owner: Hyungbae Cho (`bwade9090`)
- Delivery window: four weeks, approximately 80 hours
- Current milestone: M1b — week-1 verification spikes and vintage groundwork (charter v2.2 §7,
  Week 1)
- Overall state: source-rights policy, two initial ECOS rulings, strict standalone rights catalog,
  the edition-availability decision, and the owner-authored employer-risk review (ADR 0006) are
  complete; contract `2.0.0` and resolver/raw-manifest integration remain open

## Approved baseline

- Product direction: **K-VINTAGE on KOR-RTD** (charter v2.2; source-rights and edition-availability
  amendments approved 2026-07-16; core rationale in
  `docs/discovery/01_concept_upgrade_proposal.md`; decisions recorded as ADRs 0003–0005).
  - KOR-RTD: point-in-time data layer — OECD edition-history consolidation + weekly append-only forward-capture harvester for the latest-only ECOS/KOSIS APIs.
  - K-VINTAGE: two-tier bilingual benchmark (40 human-reviewed core + 200–300 machine-generated
    data-route probes, always reported separately) with regenerable point-in-time gold answers and a
    public script. Accepted ADR 0005 replaces the charter's original
    `max(EDITION <= as_of)` shorthand with edition-level availability evidence and fail-closed
    resolution; implementation remains the next-machine work unit.
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

### OECD rights — base terms verified; dataset-specific check remains

- The [OECD Open Access Policy](https://www.oecd.org/en/about/oecd-open-by-default-policy.html)
  says content published before 2024-07-01 is governed by OECD Terms & Conditions, not by the later
  default CC BY 4.0 licence.
- The [OECD Terms & Conditions](https://www.oecd.org/en/about/terms-conditions.html) Data section
  permits extraction, download, copying, adaptation, distribution, sharing, and embedding for any
  purpose, including commercial use, unless dataset-specific restrictions or third-party rights
  apply. It requires OECD attribution and propagation of that acknowledgement requirement to
  sublicensees.
- `DF_MEI_ARCHIVE` structure/CSV metadata exposed no licence, restriction, or third-party-rights
  field. Until the Data Explorer source metadata or written confirmation settles that residual
  condition, record the source as `OECD Terms & Conditions; third-party metadata check pending`,
  **not** `CC BY 4.0`, and keep archive observations metadata-only.

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
- The independent catalog does not itself authorize raw publication. Existing `SourceManifest` 1.0
  has no typed decision link, so raw capture remains blocked until the accepted contract
  implementation adds manifest cross-validation. Source observations retain provider terms and are
  not relicensed under repository Apache-2.0.

### Owner decisions closed

- On 2026-07-16 the owner approved ADR 0005 in full: the edition-availability ledger, fail-closed
  resolver, `Asia/Seoul` end-of-day cutoff, evidence/benchmark contract `2.0.0` path, and narrow
  partial supersessions of ADR 0002 decision 5 and ADR 0003 decisions 1/3.
- The owner also approved `OECD metadata_only pending dataset-specific and third-party-rights
  confirmation`. This closes the current publication decision without approving raw OECD
  redistribution.
- On 2026-07-17 the owner completed the one-hour employer-risk review required by charter §7,
  answering an agent-provided question list in their own words; ADR 0006 commits those verbatim
  answers as the decision record. All week-1 owner decisions are now closed.

## Immediate next action (M1b — do these in order)

1. Implement accepted ADR 0005 as one reviewable contract work unit: the
   `EditionAvailabilityLedger`, evidence/benchmark `2.0.0` migration, and typed
   `SourceManifest`-to-rights-decision linkage. Regenerate public schemas and update migration
   notes, synthetic fixtures, and tests in the same change. **No raw ECOS/KOSIS value is committed
   before the typed link and cross-record validation exist.**
2. Implement the offline, fail-closed as-of resolver over
   `DSD_STES_REVISIONS@DF_STES_REVISIONS` (~6–8 h). It must select the flow edition from verified
   `available_by`/absence evidence before looking up the exact series-period row, abstain across an
   unresolved newer-edition frontier, and reproduce only demonstrable examples.
3. Commit the weekly harvester cron + `SourceManifest` and availability-ledger wiring (~3–5 h) so
   public snapshot history starts accruing immediately after the rights gate permits it.
4. Freeze the number-normalization specification before any question authoring.
5. Run the already-planned one-step Ministral 3 3B QLoRA compatibility spike on rented compute only
   after its smoke test; record cost in the spend ledger.

Week-1 gate (charter v2.2 §7): **not passed**. Endpoint/range spikes, source-rights policy, two
per-series rights records, the strict rights catalog, the availability design, the OECD
metadata-only ruling, and the owner employer-risk review (ADR 0006) are complete. Contract
`2.0.0`/manifest integration, resolver regression, and the fine-tuning path must still be fixed
before the gate closes. If the gate slips, invoke the pre-committed cut ladder immediately.

## Blockers and environment notes

- No machine has a training GPU; rented GPU is planned only for the reviewed QLoRA spike.
- Development spans multiple machines. `.venv` is machine-local — recreate it per the README quick start on whichever machine picks this up. Nothing in the repo may depend on machine-specific paths.
- Windows workstation note: the user-level Python launcher is unreliable there; use the workstation's documented bundled Python 3.12.13 runtime to create `.venv` (local path recorded outside the repository; an earlier revision of this file recorded the literal path — ADR 0006 closed that question with the owner's decision that no history remediation is needed).
- Rights gate: ADR 0004, charter v2.2, the standalone catalog, both approved ECOS rows, and the
  owner employer-risk review (ADR 0006) are complete. Raw publication now waits only on the
  accepted contract's typed manifest-link implementation.
- Vintage semantics: OECD monthly `EDITION` codes do not encode availability dates. Accepted ADR
  0005 defines the required evidence ledger and fail-closed behavior, but the implementation is
  absent; unknown editions must abstain.
- macOS laptop note: `python@3.12` was installed via Homebrew on 2026-07-17 and is the interpreter
  for the machine-local `.venv` (project standard per ADR 0001).
- GitHub CLI is authenticated as `bwade9090`; `main` tracks `origin/main`.
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

**Cumulative external spend: $0.00 / $100.00**

## Handoff rule (onboarding for a new contributor or AI agent)

Read in this order, in full, before changing anything:

1. `AGENTS.md` — working protocol, evidence rules, setup, repository map.
2. `docs/project/01_project_charter.md` — the v2.2 scope authority.
3. This file — current milestone, next action, gates, blockers.
4. `docs/project/04_macbook_handoff.md` — exact Mac setup and continuation order.
5. Accepted ADRs 0001–0005 in `docs/decisions/`.
6. `docs/discovery/01_concept_upgrade_proposal.md` — background: why v2 exists, verified data facts, judged alternatives, risk register.

Then start with "Immediate next action" item 1. Do not start dependent data collection, document
ingestion, model training, or UI work before the implementation gates (contract `2.0.0`, typed
manifest-rights link, resolver) are resolved. Do not weaken the qualification rules for "first" claims or the rights/append-only
rules in `AGENTS.md`. Update this file whenever a milestone state, blocker, cost, spike result, or
next action changes.
