# ADR 0005: make edition availability evidence explicit and fail closed

- Status: accepted — approved by the owner on 2026-07-16
- Date: 2026-07-15
- Last revised: 2026-07-16 (owner approval and charter v2.2 synchronization)
- Related: charter v2.2 §§3, 5, and 7; partially supersedes ADR 0002 decision 5 and ADR 0003
  decisions 1 and 3

## Context

Charter v2.1 and ADR 0003 describe the resolver as `as_of -> max(EDITION <= as_of)`. The OECD
`EDITION` code is `YYYYMM`, but the week-1 spike established that it is a monthly label, not an
availability date:

- The official [STES revisions dataflow](https://sdmx.oecd.org/public/rest/dataflow/OECD.SDD.STES/DSD_STES_REVISIONS%40DF_STES_REVISIONS/latest?references=all)
  describes monthly snapshots but gives no publication day for each edition.
- The [edition codelist](https://sdmx.oecd.org/public/rest/codelist/OECD.SDD.STES/CL_EDITION/1.0?references=none)
  already contains future labels through `202812`, while the current
  [availability constraint](https://sdmx.oecd.org/public/rest/availableconstraint/OECD.SDD.STES,DSD_STES_REVISIONS%40DF_STES_REVISIONS,4.0/all/all/EDITION?mode=exact)
  contains actual editions only through `202607`. A codelist entry is therefore not proof of
  availability.
- The current [content constraint](https://sdmx.oecd.org/public/rest/contentconstraint/OECD.SDD.STES/CR_A_DSD_STES_REVISIONS%40DF_STES_REVISIONS/4.0?references=none)
  has `validFrom=2026-07-08T09:33:35.737Z`. OECD's
  [API guidance](https://www.oecd.org/en/data/insights/data-explainers/2024/11/Api-best-practices-and-recommendations.html)
  describes this as the dataset's last-update time. It safely proves that the current availability
  region containing `202607` was valid at that instant, but not necessarily its exact first-public
  instant, and it does not preserve prior regions.
- `updatedAfter` brackets the update time of returned rows, not their first publication. Dynamic
  HTTP `Date`/`Last-Modified` and response preparation timestamps describe request generation. None
  is sufficient historical first-availability evidence by itself.
- The official [Main Economic Indicators issue catalog](https://www.oecd.org/en/publications/serials/main-economic-indicators_g1g11c1c.html)
  gives non-boundary dates for historical issues (for example, June 2023 on June 13 and July 2023
  on July 7). This shows that a generic month-boundary heuristic is unsafe for the related monthly
  publication family; it is not direct proof of STES edition availability. Completeness and
  one-to-one issue-to-edition mapping must be verified before those dates become resolver evidence.

There is a second contract conflict. `SourceManifest.published_on` describes when the exact fetched
bytes were defensibly available. A consolidated archive response retrieved in 2026 cannot be
backdated to each edition it contains. The current `BenchmarkBundle` consequently rejects that
snapshot for a pre-2026 `as_of`, even when a row represents an official historical edition.
Silently backdating the manifest would violate ADR 0002.

## Decision

1. Treat `EDITION` as an opaque, validated identity and ordering code only. Never derive a day from
   its `YYYYMM` text.
2. Introduce an immutable, strict `EditionAvailabilityLedger` with its own versioned public schema.
   Its header records `ledger_id`, dataflow ID and version, `generated_at`, `supersedes`, capture
   time, cutoff timezone and semantics, and an aware `complete_through`. Its edition inventory comes
   from actual flow availability, not the codelist. Every known edition has a record with
   `status=resolved|unresolved`; `available_by`, `not_before`, and `last_absent_at` are nullable aware
   UTC timestamps. A resolved record requires `available_by`; an unresolved record does not invent
   one. Validation rejects contradictory windows: when present, `not_before <= available_by` and
   `last_absent_at < available_by`.
3. Require every availability assertion to reference one or more immutable `SourceManifest` IDs
   whose bytes, size, and SHA-256 can be checked offline. A URL is supporting manifest metadata, not
   standalone evidence. Constraint-based records additionally preserve constraint ID/version,
   `validFrom`, and the edition membership from the same response or an explicitly joined manifest.
   Ledgers are append-only: better historical evidence creates a new ledger snapshot that names its
   predecessor rather than rewriting an earlier record.
4. Use only these evidence bases:
   - `publisher_timestamp` for an official edition-specific instant;
   - `publisher_date_conservative` for an official date without time, made safe from the following
     publisher-local day; this basis requires an IANA `publisher_timezone`;
   - `sdmx_constraint_valid_from` for a constraint region demonstrably containing a newly observed
     edition; or
   - `first_observed_at` from the project's append-only capture history.
5. Interpret a benchmark `as_of: date` as the half-open interval ending at the start of the next day
   in `Asia/Seoul`. Store canonical timestamps in UTC and compare instants, never date strings.
6. Derive an edition's state at the cutoff as `available`, `unavailable`, or `unknown`:

   ```text
   cutoff_exclusive = start_of(as_of + 1 day, Asia/Seoul)

   available   if available_by < cutoff_exclusive
   unavailable if not_before >= cutoff_exclusive
                  or last_absent_at >= cutoff_exclusive
   unknown     otherwise

   candidate = max(e where state(e) == available)
   if any known e > candidate has state(e) == unknown: abstain
   else: result = observation(series, period, candidate)
   ```

   `last_absent_at` may prove earlier unavailability only while captured edition membership grows
   monotonically; a deletion or reappearance invalidates that ledger. This query-local frontier rule
   prevents an unresolved newer edition from causing a silent stale fallback, while an unresolved
   older edition does not block a definitely available newer one. The candidate is selected from the
   flow ledger before the exact series-period row is read; a missing, duplicate, or blank selected
   row never falls back.
7. Define `complete_through` as the latest instant through which **flow edition-membership knowledge**
   is complete, not observation-period coverage. Enforce
   `cutoff_exclusive <= complete_through <= captured_at`; a mid-day capture cannot answer that same
   KST calendar day's end-of-day cutoff. The ledger's edition inventory must match its exact
   availability-constraint snapshot.
8. Fail closed with a structured abstention when the query-local frontier is incomplete, the cutoff
   exceeds `complete_through`, no edition is definitely available, a newer edition's cutoff state is
   unknown, the selected row is absent/duplicate/blank, or required evidence cannot be verified.
   Neither successful output nor abstention may expose post-cutoff edition codes, values, or the raw
   consolidated archive.
9. Do not use codelist membership, first-day/month-end inference, an `updatedAfter` result alone,
   response-generation headers, or retrieval-date backdating as an availability basis. No heuristic
   fallback is permitted in the human-reviewed core or headline temporal-leakage metric.
10. Record `202607.available_by=2026-07-08T09:33:35.737Z` from the current constraint. Without a
    prior captured absence, its state before that instant remains unknown. Keep `202606` unresolved
    until archived official evidence is preserved; its `updatedAfter` bracket is diagnostic metadata,
    not first-publication proof. Thus a June cutoff abstains rather than silently returning May,
    while a cutoff after July is not blocked by the older unresolved June record. Historical issue
    dates become eligible only after their edition mapping is checked end to end.
11. Keep `SourceManifest.published_on` as provenance for the exact fetched bytes. A historical
   vintage evidence packet must reference both the current official archive snapshot and the
   edition-availability evidence; it must never backdate the snapshot manifest.
12. Make `as_of` and typed vintage evidence mandatory for temporal data routes. Bundle 2.0 may relax
    the snapshot `published_on <= as_of` check only for an approved historical-archive flow when the
    record supplies a ledger ID, selected edition, and immutable availability evidence. Documents
    and latest-only datasets retain the existing cutoff rule. Evidence packets expose only the
    selected observation row, never the consolidated source or later edition inventory.
13. This ADR is the superseding decision required by ADR 0002 for the changed temporal invariant.
    Implementation ships as evidence/benchmark contract `2.0.0`, with migration notes,
    regenerated JSON Schemas, fixtures, and tests. The standalone availability-ledger contract
    starts at `1.0.0`. Do not apply a global version bump that makes unchanged component schemas
    reject their own `1.0.0` records.
14. After approval, implement offline types, a case-sensitive SDMX-CSV parser, the fail-closed
    resolver, and synthetic fixtures before adding real observation payloads. Tests must cover an
    unresolved newer/older edition, mid-day capture versus end-of-day cutoff, ledger/dataflow/
    constraint mismatch, missing/duplicate/blank selected rows, coexisting code and label headers
    such as `MEASURE`/`Measure`, and absence of post-cutoff data from every output. Raw numeric unit
    conversion remains outside the resolver until the number-normalization specification is frozen.

## Approval record

On 2026-07-16 the owner approved all three requested choices:

1. the explicit availability ledger and fail-closed resolver;
2. `Asia/Seoul` inclusive end-of-day semantics for a date-only `as_of`; and
3. the evidence/benchmark contract `2.0.0` path and the narrow partial supersessions described
   below.

The owner also approved the corresponding charter v2.2 amendment. This handoff records the decision
but deliberately does not implement the ledger, resolver, parser, or contract migration; those are
the next-machine work unit.

## Alternatives considered

- **Treat an edition as available on the first of its month:** rejected as unsupported; related MEI
  issue dates vary within their month, and no STES first-day guarantee exists. The assumption can
  create same-month temporal leakage.
- **Treat an edition as available at month-end or the next month:** conservative in many cases but
  not an official availability fact; rejected for reviewed-core and headline metrics.
- **Use the current archive response's retrieval or publication date for every edition:** rejected
  because one snapshot timestamp cannot express multiple historical editions.
- **Backdate the consolidated snapshot manifest:** rejected as false provenance under ADR 0002.
- **Add only an optional `vintage` argument in schema 1.1:** insufficient for a headline leakage
  invariant because old records could omit the only evidence that makes the answer safe.
- **Fall back to the newest older observation when a selected edition lacks a row:** rejected because
  absence can mean the series had not yet been published, not that the prior value remained current.

## Consequences

- Same-month questions answer only when edition availability is independently demonstrated.
- Some historical editions, including `202606` for strict-core use, remain unavailable until better
  evidence is captured. Honest abstention is preferable to a falsely precise vintage answer.
- Future edition transitions become provable through append-only constraint and first-seen captures.
- Contract work is larger than ADR 0003's expected optional `1.1.0` field, but it makes temporal
  leakage mechanically enforceable rather than conventional.
- This ADR supersedes ADR 0002 decision 5 **only** for the typed, approved historical-
  archive exception in decision 12; documents and latest-only sources retain the original rule. It
  supersedes ADR 0003 **only** where decision 1 defines `max(EDITION <= as_of)` and decision 3
  expects optional schema `1.1.0` to be sufficient. Neither accepted ADR's historical decision
  text is rewritten. Charter v2.2, `AGENTS.md`, and contributor-facing status language record the
  accepted change before code implementation.

## Revisit triggers

- OECD publishes an edition-level availability history or stable release timestamp.
- The dataflow ceases to be monthly or changes its edition code semantics.
- Benchmark research requires intraday rather than date-only cutoffs.
- A verified historical issue-to-edition mapping covers the full target range.
