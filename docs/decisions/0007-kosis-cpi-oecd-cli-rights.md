# ADR 0007: expand approved capture scopes to KOSIS CPI and OECD Korea CLI

- Status: accepted
- Date: 2026-07-17
- Approval recorded at: 2026-07-17T11:35:06Z
- Supersedes: ADR 0004 decision 7 only for the exact OECD series below

## Context

ADR 0004 approved two ECOS series and kept all OECD observations `metadata_only` pending an exact
dataset/source review. The weekly harvester subsequently shipped with OECD constraint metadata and
the two ECOS paths, while KOSIS remained empty. On 2026-07-17 the owner added two approvals in the
active task: “KOSIS의 소비자물가지수도 승인이야.” and “OECD의 Composite leading indicator
(Korea)도 승인이야.”

Read-only verification translated those names into exact official scopes:

- KOSIS OpenAPI returns the national monthly CPI as organisation `101`, table `DT_1J22003`, item
  `T` (소비자물가지수(총지수)), geography `C1=T10` (전국), unit `2020=100`. The rights contract
  represents the item-plus-geography scope as the canonical composite item ID `T/T10`.
- OECD Data Explorer identifies `DSD_STES@DF_CLI` measure `LI` as the monthly headline
  amplitude-adjusted CLI for Korea. The corresponding revision-history series is
  `OECD.SDD.STES:DSD_STES_REVISIONS@DF_STES_REVISIONS(4.0)` with key
  `KOR.M.LI_AA.IX._T`; this is the exact KOR-RTD archive scope.

The official KOSIS use guide permits attributed reuse and redistribution of domestic statistics
subject to its restrictions. The official producer pages identify the CPI survey as monthly
statistics produced by 국가데이터처. OECD Terms & Conditions permit extraction, adaptation, and
distribution of data with attribution unless dataset-specific or third-party restrictions apply.
The official CLI dataset page describes the OECD CLI system, the dataflow is issued by
`OECD.SDD.STES`, and the exact composite indicator is treated as OECD-produced rather than a raw
third-party component series. The owner accepts that exact producer mapping and residual-rights
review for this series.

## Decision

1. Approve `allowed` redistribution for KOSIS scope `101/DT_1J22003/T/T10`, limited to the national
   monthly total CPI. Other regions, CPI sub-indices, tables, items, international statistics, North
   Korea statistics, and publications remain outside this decision.
2. Approve `allowed` redistribution for OECD revision-series scope
   `DSD_STES_REVISIONS@DF_STES_REVISIONS/KOR.M.LI_AA.IX._T`, limited to the Korea monthly
   amplitude-adjusted composite leading indicator. All other OECD observations retain ADR 0004's
   `metadata_only` ruling unless separately approved.
3. Record both decisions in a new append-only rights catalog that supersedes the 2026-07-16
   catalog. Preserve the earlier two ECOS decisions unchanged in meaning.
4. Require each raw snapshot to carry a `SourceManifest` 2.0.0 typed link to the exact new catalog
   decision and pass `BenchmarkBundle` cross-validation before it can be written.
5. Apply KOSIS detailed attribution, no-distortion, no-reidentification, and no paid standalone sale
   of unchanged raw information. Apply OECD dataset attribution and no-implied-endorsement wording;
   source observations remain under provider terms and are not relicensed by Apache-2.0.
6. Capture the consolidated OECD CLI revision archive as a one-time/manual archive artifact, not as
   a repeated weekly full download. Keep the weekly schedule for forward snapshots of latest-only
   ECOS/KOSIS APIs and OECD availability metadata.

## Approval record

Hyungbae Cho approved the two named scopes in the active task on 2026-07-17. This ADR records the
exact machine identifiers found during the immediately following read-only verification and treats
the plain-language OECD name as the official headline amplitude-adjusted CLI, not the trend-restored
variant. The approval is limited to the two exact scopes in decisions 1 and 2.

## Consequences

- KOR-RTD can start a real forward history for national KOSIS CPI and can publish one consolidated
  Korea CLI edition archive with reproducible manifests and checksums.
- The rights model now permits an OECD `allowed` decision only when exact source metadata classifies
  OECD as first-party producer; owner approval and all ordinary operation/attribution checks still
  apply.
- The full OECD CLI archive is roughly 22 MB at verification time, so it is deliberately excluded
  from weekly repetition.
- `.env` remains ignored. Local keys are never copied into manifests, logs, commits, or GitHub
  secrets automatically.

## Revisit triggers

- KOSIS changes the table/item/geography codes, category, use guide, base-year table, or producer.
- OECD changes the dataflow/key, exposes a third-party source or restriction, or changes its terms.
- The project adds commercial use, another KOSIS dimension, another OECD measure, or automated
  refresh/compaction of the consolidated archive.
