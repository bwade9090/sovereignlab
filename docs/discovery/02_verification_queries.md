# Verification queries and reported results from the 2026-07-14 feasibility study

- Status: reference record for the week-1 verification spikes
- Rule: every entry below is "as reported by the study on 2026-07-14." **Nothing here may be cited as a project claim until the week-1 spike re-verifies it and records the result in `docs/PROJECT_STATUS.md`.**
- Provenance: the multi-agent study described in `01_concept_upgrade_proposal.md`; entries marked "verified" there were checked against the live endpoints below.

## 1. Live revisions dataflow (primary vintage source)

- Dataflow: `OECD.SDD.STES,DSD_STES_REVISIONS@DF_STES_REVISIONS` ("Short-term economic statistics revisions") on `https://sdmx.oecd.org/public/rest` — no API key required.
- Dimensions: `REF_AREA.FREQ.MEASURE.UNIT_MEASURE.ACTIVITY.EDITION`.
- Structure query: `https://sdmx.oecd.org/public/rest/dataflow/OECD.SDD.STES/DSD_STES_REVISIONS%40DF_STES_REVISIONS/latest?references=all`
- Example data query (KOR quarterly real GDP, 2025-Q1, per-edition values):
  `https://sdmx.oecd.org/public/rest/data/OECD.SDD.STES,DSD_STES_REVISIONS@DF_STES_REVISIONS,/KOR.Q.B1GQ_Q...?startPeriod=2025-Q1&endPeriod=2025-Q1&format=csvfilewithlabels`
- Reported results: Korea covered with 22 revision measures (GDP volume/current/deflator plus five expenditure components, industrial production, retail trade volume, CPI, unemployment, employment, hourly earnings, ULC, M3, current account, merchandise exports/imports, CLI variants); monthly editions Feb-1999 → Jul-2026; KOR CPI observation 2005-01 returned 258 editions (200502 → 202607); KOR real GDP observation 2025-Q1 revised from 572,057.7 to 574,984.3 billion KRW between the June-2026 and July-2026 editions.
- Counting-basis note: the "22 revision measures" here, the "24 variables" in §2, and the "~13 headline MEI indicators" cited in charter §2 use different bases (revision measures include GDP components and series variants; the ~13 figure counts distinct headline indicators in the historical MEI revisions database). The week-1 spike should record one reconciled table.
- Caveat: a `NonProductionDataflow` annotation was observed on this dataflow — disclose in the datasheet; treat as a withdrawal-risk signal (ADR 0003 revisit triggers).

## 2. Frozen archive cross-check — conflicting results, settle in week 1

- Dataflow: `OECD,DF_MEI_ARCHIVE` ("Revisions Analysis Dataset – Infra-annual Economic Indicators") on the archive tenant.
- Endpoint pattern that succeeded in one probe: `https://sdmx.oecd.org/archive/rest/data/OECD,DF_MEI_ARCHIVE,/KOR.101..Q?format=csvfilewithlabels`
- Data Explorer view: `https://data-explorer.oecd.org/vis?tenant=archive&df[ds]=DisseminateArchiveDMZ&df[id]=DF_MEI&df[ag]=OECD`
- Reported results (successful probe): 65 countries including KOR, 24 variables, 300 monthly editions 199902 → 202401; KOR real GDP observation 2010-Q1 has 165 editions (201005 → 202401); Korea data present in the earliest (Feb-1999) edition; KOR CPI observation 2019-11 carried the identical value (104.87) across all 50 of its editions — the basis of the "Korean CPI is essentially unrevised" rule.
- **Conflict:** a separate probe during the study's judging phase returned 404 on this dataflow. Both outcomes are recorded here deliberately; the week-1 spike decides which endpoint form (if any) is stable, and no backfill-range claim may be published before that.

## 3. Economic Outlook forecast vintages

- Reported: the archive tenant holds `DF_EO60_MAIN` (Economic Outlook No. 60, Dec 1996) through `DF_EO114` (Nov 2023) as individual edition dataflows, including the EO107 COVID double-scenario edition; the main tenant was live-confirmed only for `DSD_EO_114@DF_EO_114` through `DSD_EO_118@DF_EO_118` plus current `DSD_EO@DF_EO` (EO 119, June 2026; agency `OECD.ECO.MAD`).
- Archive dataflow listing to re-verify the full range: `https://sdmx.oecd.org/archive/rest/dataflow/all/all/latest`
- Rule: the charter claims only the live-confirmed range; any wider backfill claim requires this spike.

## 4. Candidate harvester basket (ECOS/KOSIS forward capture, at most 12 series)

Selection criteria: (a) revision-prone per the STES revision measures above (CPI is excluded from revision questions — essentially unrevised — but may be captured as an abstain/trap series); (b) policy-salient for Korean macro surveillance; (c) cleanly mappable to an OECD series for cross-checking. Candidates, to be narrowed to ≤12 at the week-1 gate with the owner's sign-off after per-series KOGL rulings:

1. Real GDP (seasonally adjusted, quarterly)
2. GDP deflator
3. Industrial production index
4. Retail sales volume
5. Employment (persons)
6. Unemployment rate (seasonally adjusted)
7. Hourly earnings / unit labour cost
8. M3 (or M2)
9. Current account balance
10. Merchandise exports
11. Merchandise imports
12. Composite leading indicator (or consumer sentiment index)

## 5. Other reference points reported by the study

- **ECOS Open API is latest-only:** six services (StatisticTableList, StatisticWord, StatisticItemList, StatisticSearch, KeyStatisticList, StatisticMeta); StatisticSearch accepts only statistic code, cycle (A/S/Q/M/SM/D), start/end period, and item codes 1–4 — no as-of or point-in-time parameter (checked against the API documentation). KOSIS OpenAPI likewise has no revision-history service.
- **BOK document corpus:** 58 Korean 경제전망보고서 quarterly editions 2012.07 → 2026.05 with stable `nttId` URLs and publication dates; 13 English full translations May-2023 → May-2026 (1–2 month lag); English "Economic Outlook" press releases reach back to ~2000, same-day bilingual publication in recent years.
- **ALFRED exclusion evidence:** on `alfred.stlouisfed.org`, EXKOUS (KRW/USD) vintages from 1997-10 are the deepest; KORCPIALLMINMEI CPI vintages ran 2011-05 → 2024-04 and were then discontinued (OECD MEI feed ended); NGDPRSAXDCKRQ real GDP vintages only from 2021-06. Decisive blocker: the June-2024 FRED API Terms of Use (`https://fred.stlouisfed.org/docs/api/terms_of_use.html`) prohibit storing/caching/archiving content, redistributing third-party content, and use in connection with ML/LLM development. Use at most as a manual sanity cross-check, never in the pipeline or dataset.
- **OECD licensing:** content published from 1 July 2024 is CC BY 4.0 by default (`https://www.oecd.org/en/about/oecd-open-by-default-policy.html`); required citation format "OECD (year), dataset, DOI/URL (accessed date)"; logos/branding excluded (relevant to the no-implied-endorsement rule). The license status of archive content published **before** 2024-07-01 is a week-1 spike item.
- **Access note:** `www.oecd.org` sits behind bot verification (403 to plain fetchers), but the `sdmx.oecd.org` API endpoints answered plain `curl` during the study.
