# ADR 0003: reorient the concept to K-VINTAGE on KOR-RTD and plan vintage-aware tool semantics

- Status: accepted
- Date: 2026-07-14
- Related: supplements ADR 0002 (does not supersede it); full rationale and candidate comparison in `docs/discovery/01_concept_upgrade_proposal.md`; implemented as charter v2.

## Context

Charter v1 was technically sound but read as a technology-practice project: its mission restated the target job posting's technique checklist, its customer was admitted to be fictional ("deliberately framed as a customer pilot"), and its genuinely rare assets (as-of vintage correctness, the ADR 0002 insight that a current API response may contain revised historical observations) were buried as metric rows beneath a 2026-table-stakes headline ("auditable cited briefing").

A multi-agent study (five researchers, six ideation lenses, seven judged candidates; provenance in the proposal document) verified the following load-bearing facts on 2026-07-14:

- ECOS and KOSIS expose latest values only, with no as-of parameter. Korea has no public ALFRED equivalent.
- ALFRED itself is not a substitute: Korean vintage coverage is shallow (GDP only from 2021; CPI feed discontinued 2024) and the June-2024 FRED API terms prohibit archiving, redistribution, and ML/LLM use.
- The OECD SDMX live revisions dataflow (`DSD_STES_REVISIONS@DF_STES_REVISIONS`) is key-free and carries Korean editions Feb-1999 to Jul-2026 (KOR CPI 2005-01: 258 editions; 2025-Q1 real GDP revised 572,057.7 -> 574,984.3 billion KRW between the June and July 2026 editions). A `NonProductionDataflow` annotation was observed. `DF_MEI_ARCHIVE` returned conflicting results (404 vs successful query). EO edition dataflows are live-confirmed only as `DF_EO_114`–`DF_EO_118` plus current.
- To our knowledge — a study literature search, not endpoint-verifiable like the items above — no existing LLM benchmark makes the gold answer depend on the data vintage available at a past date. Nearest prior art: German statutory as-of QA (arXiv 2605.23497), Dallas Fed real-time OECD dataset, OECD MEI revisions database. KMMLU already contains Korean economics categories.
- Korean CPI is essentially unrevised (the archived KOR CPI 2019-11 observation carried the identical value, 104.87, across all 50 of its editions).

## Decision

1. **Reorient the product concept** from "an evaluation-first bilingual Mistral deployment lab" to three named artifacts: **KOR-RTD** (a provenance-contracted point-in-time data layer for Korean macro statistics: OECD edition-history consolidation plus a weekly append-only forward-capture harvester for the latest-only ECOS/KOSIS APIs), **K-VINTAGE** (a two-tier bilingual benchmark whose data-route gold answers are computed as `as_of -> max(EDITION <= as_of)` and regenerable by a public script), and the existing briefing pipeline as **reference implementation and public baseline suite**. Temporal-leakage rate becomes a headline per-variant metric.
2. **Keep the entire technical spine**: the 4-route taxonomy, the four-variant ablation, the LoRA/QLoRA plan with its frozen promotion rule, FastAPI + trace UI, offline-testable fixtures, spend ledger, and all v1 hard constraints (4 weeks / ~80 h / USD 100 / public data only / no implied endorsement).
3. **Extend tool-expectation semantics with vintage/edition fields** in the week-1 schema change scheduled in `docs/PROJECT_STATUS.md`. This is the case anticipated by ADR 0002's revisit trigger #2 ("the SDMX tool contract needs source-vintage semantics not expressible by the current manifest"). The extension is expected to be non-breaking (an optional vintage field on tool expectations) and ships as a minor schema version (`1.1.0`) with regenerated JSON Schema, fixtures, and tests in the same change. If any required field or invariant must change instead, that is a **breaking contract change** under the schema contract's §7 rule and ships as a new major schema version (`2.0.0`) with migration notes, regenerated JSON Schema, updated fixtures/tests, **and a superseding ADR**. No approved benchmark records exist yet, so migration cost is zero today — another reason to decide this now.
4. **Adopt the qualification rule for novelty claims**: every "first" claim is stated as "to our knowledge, for official statistics," with the prior art above cited in the datasheet before any reviewer has to find it. "First Korean macro benchmark" phrasing is banned.
5. **Adopt the pre-committed cut ladder** (probe-set size -> forecast-vintage family -> leaderboard seeding -> trace-UI polish) and the committed de-scopes listed in charter §7 to absorb the estimated +25–35 h of new work. There is no schedule slack; weekly gates trigger the ladder.
6. **Gate all data claims on the week-1 verification spikes**: `DF_MEI_ARCHIVE` accessibility, actual EO edition range, per-series KOGL redistribution rulings (no raw ECOS/KOSIS values committed before a ruling), pre-2024-07 OECD archive licensing, and a written employer-risk review (personal-capacity public activity) committed as a decision record.

## Alternatives considered

- **Keep charter v1 and fix only wording:** rejected — the generic feel is structural (fictional customer, technique-checklist mission), not cosmetic.
- **Customer Zero / real-usage evidence as the headline (judged 7.0/10):** absorbed rather than adopted — its dogfood log and report-retention conditions are in v2, but "evidence of use" is not a reason to exist.
- **Outlook Diff Desk — revision-aware diff briefings (6.8):** strongest demand evidence but worst feasibility (+35–65 h), sharpest employer risk (a serving BOK employee auto-publishing a public tracker of BOK communication), and its marquee event falls outside the window. Preserved as the post-window flagship application; its revision-join assets are already inside the vintage layer.
- **Cloud-vs-local sovereignty trade-off study as the headline (6.35):** genre already exists; its document-level framing was absorbed into the engagement report.
- **Temporal-leakage linter as a pip package (5.9):** weak moat; covered by the grader + regeneration script.
- **Korea AI Basic Act governance pack (5.25):** rejected on a fatal flaw — the Act regulates "high-impact" AI with voluntary verification/certification, not "high-risk" AI with mandatory pre-market testing; the concept's load-bearing legal premise was wrong. Consequence for v2: the Act is described precisely wherever mentioned.

## Consequences

- The genuinely novel asset at application time is partly an embryo: the forward-capture archive will hold only a few weekly snapshots. Public CI commit history is what makes even the embryo independently verifiable, which is why the harvester ships in week 1.
- The 40 human-reviewed core questions remain a real 8–12 h authoring cost; machine generation adds probes but removes no human bottleneck.
- Number normalization (raw 10^12 XDC scale vs "billion KRW", 조/억 conventions, seasonal-adjustment variants) must be specified before question authoring or grading will be noisy.
- The fictional-pilot narrative is deleted; the engagement report must be grounded in real artifacts only.
- Documentation, benchmark datasheets, and CV language must always report the two gold-set tiers separately.

## Revisit triggers

- A week-1 spike fails: `DF_MEI_ARCHIVE` is inaccessible, the EO edition range is insufficient for any forecast-vintage questions, KOGL rulings block most of the harvester basket, or the employer review disallows the public harvester.
- The OECD live revisions dataflow is withdrawn or restructured (the `NonProductionDataflow` annotation makes this non-hypothetical); committed snapshots keep published results reproducible, but new collection would need a replacement source.
- A concurrent vintage-conditioned benchmark is published during the window (the point-in-time finance-LLM space is moving fast in 2026) — in that case, reposition K-VINTAGE against it honestly rather than contesting priority.
- Human annotation shows vintage questions cannot be expressed within the four exclusive routes (also ADR 0002 trigger #3).
