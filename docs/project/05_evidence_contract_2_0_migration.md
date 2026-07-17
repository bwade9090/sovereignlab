# Evidence/benchmark contract 2.0.0 and availability-ledger 1.0.0

- Status: implemented
- Date: 2026-07-17
- Decision basis: accepted ADR 0005 (charter v2.2 §§3, 5, 7); rights linkage per ADR 0004
- Scope: `SourceManifest` 2.0.0, `BenchmarkRecord` 2.0.0, `BenchmarkBundle` 2.0.0, and the new
  standalone `EditionAvailabilityLedger` 1.0.0. Rights contracts remain `1.0.0` unchanged, as ADR
  0005 decision 13 requires — no global version bump invalidates their committed records.

## 1. What changed and why

OECD `EDITION` codes are monthly labels, not availability dates, and a consolidated archive
response retrieved in 2026 cannot be backdated to the historical editions it contains. Contract
1.0's single `published_on <= as_of` rule therefore could not represent a legitimate historical
vintage without false provenance. ADR 0005 replaces convention with evidence: an immutable
availability ledger, a fail-closed selection rule, and a typed, narrow bundle exception for
approved historical-archive flows. The same migration adds the typed manifest-to-rights-decision
link that ADR 0004 made a precondition for any raw ECOS/KOSIS commit.

## 2. EditionAvailabilityLedger 1.0.0

Canonical model: `src/sovereignlab/schemas/availability.py`; public schema:
`data/schemas/edition-availability-ledger-v1.schema.json`; synthetic example:
`data/fixtures/edition_availability_ledger.example.json`.

| Concern | Contract |
|---|---|
| Header | `ledger_id`, exact `dataflow_id`/`dataflow_version`, `generated_at`, `captured_at`, `complete_through`, cutoff timezone/semantics, optional `supersedes_ledger_id` (never itself). |
| Ordering | `complete_through <= captured_at <= generated_at`; all ledger timestamps are canonical UTC instants. |
| Editions | `YYYYMM` codes validated as opaque month labels (month 01–12) and treated as identity/ordering only; duplicates rejected. |
| Windows | `resolved` requires `available_by`; `unresolved` never invents one. When present: `not_before <= available_by`, `last_absent_at < available_by`, and no `available_by`/`last_absent_at` after `generated_at`. |
| Evidence | Every assertion (`available_by`, `not_before`, `last_absent_at`) requires at least one evidence entry with one of the four ADR 0005 bases and one or more immutable `SourceManifest` IDs. The record value must equal the strongest supported instant (earliest for `available_by`, latest for the absence bounds). |
| Conservative dates | `publisher_date_conservative` requires an IANA `publisher_timezone` and asserts exactly the start of the following publisher-local day, compared as UTC instants (so DST gaps/folds in the publisher zone stay representable); it can support only `available_by`. |
| Constraint evidence | `sdmx_constraint_valid_from` requires the constraint ID and version from the captured response; the SDMX artefact-reference pattern accepts the `@` separator used by the real OECD constraint ID. |
| Range safety | Dates whose following day overflows the calendar (`9999-12-31`) are rejected as validation errors, never raw `OverflowError`s. |

Derived semantics live on the models: `cutoff_exclusive(as_of)` returns the start of the next
calendar day in the ledger's cutoff timezone; `state_at` implements the ADR 0005 derivation
(`available`/`unavailable`/`unknown`); `select_edition` picks the newest definitely available
edition and abstains with a structured reason when the cutoff exceeds `complete_through`, nothing
is definitely available, or any newer edition's state is unknown. Abstentions never carry edition
codes. Append-only rule (operational, not schema-checkable): better historical evidence creates a
new ledger naming its predecessor; `last_absent_at` proves earlier unavailability only while
captured edition membership grows monotonically.

## 3. SourceManifest 2.0.0

New fields, both backward-relevant rules enforced in the model:

- `vintage_semantics`: `latest_only` (default) or `historical_archive`; historical archives must be
  `dataset`/`api` sources.
- `rights_decision`: optional typed link (`catalog_id`, `decision_id`, `source_system`, `table_id`,
  `item_id`) to one owner-approved series rights decision. It is **required** whenever a
  `dataset`/`api` manifest declares `allowed` redistribution, and it is rejected on documents.

## 4. BenchmarkRecord 2.0.0

`ToolExpectation` gains optional `vintage` (`ledger_id` + `selected_edition`). A record carrying
any vintage evidence must declare `as_of`. All 1.0 route/answer/split rules are unchanged.

## 5. BenchmarkBundle 2.0.0 cross-record rules

In addition to every 1.0 check, the bundle now rejects:

- duplicate ledger or catalog IDs, and ledger availability evidence whose manifest IDs do not
  resolve to bundled sources (evidence must stay offline-checkable);
- a manifest rights link to an unknown catalog or decision, a scope/publisher mismatch, an
  `allowed` manifest whose decision is not `allowed`, or a decision expired before retrieval
  (an `allowed` decision's permitted-operation guarantees are already enforced by the rights
  catalog contract itself);
- a rights link into a catalog that another bundled catalog names as superseded — a stale
  `allowed` ruling can never out-authorize its successor — and any one series scope carrying
  decisions in more than one active (non-superseded) bundled catalog;
- a tool expectation on a `historical_archive` source without `as_of` or vintage evidence, with an
  unknown or superseded ledger, with a ledger whose cutoff zone is not `Asia/Seoul` end-of-day,
  whose gold edition the ledger cannot resolve (fail-closed abstention), or whose gold edition
  differs from the ledger-selected edition;
- vintage evidence attached to a `latest_only` source.

Expiry semantics: `valid_until` is inclusive through the end of that calendar day in `Asia/Seoul`,
and the check compares instants — the same retrieval instant passes or fails identically however
its UTC offset is serialized.

The `published_on <= as_of` cutoff rule still applies to documents and latest-only data snapshots.
Only a `historical_archive` expectation that passes all vintage checks above is exempt — this is
the narrow typed exception ADR 0005 decision 12 grants, and it is what lets a 2026 archive
snapshot legitimately support a 2024 `as_of` without backdating provenance.

## 6. Migration from 1.0.0

- No real (non-fixture) source manifests or benchmark records were ever approved under 1.0.0, so
  no data migration was required; both synthetic fixtures were regenerated as 2.0.0.
- `data/schemas/source-manifest-v1.schema.json` and `data/schemas/benchmark-record-v1.schema.json`
  are removed in favor of the `-v2` files; the frozen 1.0.0 contracts remain in Git history at
  commit `c849b7b` and earlier.
- Rights schemas (`rights-*.schema.json`, `series-rights-decision-v1.schema.json`) and the
  committed catalog `data/rights/kor-rtd-rights-2026-07-16.json` are byte-for-byte unchanged.
- Any future tooling reads `schema_version` explicitly: evidence contracts are `2.0.0`, rights
  contracts `1.0.0`, availability ledgers `1.0.0`.

## 7. What this does not yet do

- No real availability ledger is committed. The first real ledger requires captured constraint and
  data-response manifests (harvester work unit); ADR 0005 decision 10's `202607` record and the
  deliberately unresolved `202606` will be recorded there.
- No raw ECOS/KOSIS observation is committed. The typed link and cross-record validation now
  exist, so the remaining gates are operational: the harvester must produce real manifests whose
  links validate against the committed catalog.
- The contract model itself does not cross-check `dataflow_id` against the archive manifest it
  describes. The follow-on as-of resolver now enforces that join by extracting the canonical
  `agency:dataflow` and any explicit version from the manifest URL before it builds an evidence
  packet.
- ADR 0005 decision 7's rule that a ledger's edition inventory must match its exact
  availability-constraint snapshot is an operational harvester/resolver obligation: the offline
  bundle sees manifest hashes, not constraint response bytes, so the harvester must derive the
  inventory mechanically from the captured constraint and never hand-edit it. Supersession is
  likewise only visible inside one bundle — an external successor catalog or ledger cannot be
  detected offline.
- Raw numeric unit conversion stays outside the contract until the number-normalization
  specification is frozen.

## 8. Reproduction

```bash
python scripts/export_json_schemas.py
python -m ruff check .
python -m ruff format --check .
python -m pytest --cov=sovereignlab --cov-report=term-missing
```

Generated schemas must match the canonical models exactly; the suite fails on any drift.
