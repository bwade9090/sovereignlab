# Architecture

How KOR-RTD, the three evidence tools, the offline execution path, and the K-VINTAGE core fit
together. The charter sets scope and the decision records explain why; this page describes what
the code does. When this page and the code disagree, the code and its tests are right.

```
official sources ──► weekly capture ──► data/  (manifests, archives, ledgers, rights)
                                          │
                                          ▼
                              evidence registries v1  (explicit, digest-pinned)
                                          │
        request ──► planner ──► dispatcher ──► three tools ──► evidence packet ──► trace
                                          ▲
                     K-VINTAGE core records: every gold is reproduced through the same tools
```

## 1. Data layer (KOR-RTD)

Everything under `data/` is described by a strict model in `src/sovereignlab/schemas/`, exported
as JSON Schema to `data/schemas/`.

**Source manifest.** Every archived payload and every cited document has a `SourceManifest`:
publisher, `published_on` and the basis for that date, `retrieved_at`, byte size, SHA-256,
redistribution status, and vintage semantics. `latest_only` marks a provider that serves only
current values (ECOS, KOSIS, OECD constraint metadata); `historical_archive` marks a file that
contains many editions (the OECD CLI revision archive). Document manifests are dated no earlier
than their exact bytes (ADR 0011). Bank of Korea report bodies are not committed: only their
manifests are.

**Rights catalog.** `data/rights/` holds the rights instruments and the owner-approved decision
for each exact series. A data manifest marked `allowed` must link to an `allowed` decision, and
`BenchmarkBundle` cross-checks the link (publisher, scope, state, expiry, and that the catalog is
not superseded). Catalogs are append-only: a new ruling is a new catalog that supersedes the
previous one. Four series are approved: ECOS real GDP (`200Y108/10601`), ECOS current account
(`301Y017/SA000`), KOSIS national CPI (`101/DT_1J22003/T/T10`), and the OECD Korea monthly
amplitude-adjusted CLI (`KOR.M.LI_AA.IX._T`). Everything else is metadata-only.

**Weekly capture.** `scripts/harvest_weekly.py` (run by `.github/workflows/weekly-harvest.yml`
every Monday) fetches the OECD STES availability and content constraints and the three approved
ECOS/KOSIS series, then writes one manifest per payload and a new availability ledger. Writes are
append-only: a capture never overwrites an existing path, and file names carry the capture
timestamp. The workflow commits a capture after `tests/test_committed_data.py` and the harvester
tests pass. No scheduled capture was committed between 2026-07-20 and 2026-11-02; that gap is
permanent (ADR 0010).

**Edition-availability ledger.** OECD edition codes such as `202607` name a month, not a release
instant, so the edition a past cutoff could see has to be proven. Each ledger lists every edition
as either *resolved*, with an `available_by` instant backed by evidence (the content constraint's
`validFrom`, or the first capture that observed the edition), or *unresolved*. `last_absent_at`
records the last capture in which a later-resolved edition was still missing, and
`complete_through` is the instant up to which the ledger's inventory is known to be complete.

Selecting an edition for a cutoff (ADR 0005) is deliberately conservative:

1. The cutoff is the end of the `as_of` day in Asia/Seoul.
2. If the cutoff is later than `complete_through`, abstain (`cutoff_beyond_complete_through`).
   A capture taken mid-day cannot answer for that same Seoul day.
3. Take the newest edition whose `available_by` precedes the cutoff. If there is none, abstain
   (`no_edition_definitely_available`).
4. If any newer edition's state at the cutoff is unknown, abstain (`unresolved_newer_edition`).

## 2. Evidence registries

The tools do not scan `data/`. Each reads an explicit list of committed files, a *registry*, whose
digest is pinned in code. This keeps benchmark answers stable while weekly captures accumulate: a
capture taken after a registry was frozen is archive-only until the owner admits it in a new
registry version (ADR 0010).

| Registry | Module | Contents |
| --- | --- | --- |
| `kor-rtd-latest-only-snapshot-registry-v1` | `snapshots/registry.py` | The 2026-07-17 ECOS GDP, ECOS current-account, and KOSIS CPI captures |
| `kor-rtd-stes-resolver-registry-v1` | `vintage/registry.py` | The OECD CLI revision archive, both 2026-07-17 constraint captures and ledgers |
| `synthetic-temporal-retrieval-corpus-v1` | `retrieval/registry.py` | The synthetic bilingual corpus in `data/fixtures/retrieval/` |

Loading a registry verifies each archive against its manifest checksum, validates the rights
links through `BenchmarkBundle`, checks that each manifest is the approved series it is bound to,
and compares the registry digest with the pinned value. To change what a tool can see, add a new
registry version with a new ID and digest; do not edit v1.

Under the v1 registries, `resolve_stes_as_of` answers only for cutoffs from 2026-07-08 through
2026-07-16 (always edition `202607`), and `read_snapshot_as_of` only from 2026-07-17 onward. The
two data tools therefore share no answerable cutoff today.

## 3. The three tools

Each tool takes one typed call and returns one typed result whose status is `success`,
`abstained`, or `error`. An abstention is a normal, expected answer: the evidence cannot support
the request. An error means the tool itself failed.

A call outside the approved scopes is neither: an unknown series, a neighbouring item, a
normalization rule that belongs to another series, a period of the wrong frequency, or any extra
argument is an *invalid call*, which the argument models reject before a tool runs. Tools never
accept a file path, manifest, or ledger chosen by the caller. STES periods are written `2026-05`
or `2026-Q1`; snapshot periods use the provider's form, `202605` or `2026Q1`.

**`retrieve_temporal_documents`** (`retrieval/`). Arguments: question, language, `as_of`,
`top_k`. Documents in another language or published after `as_of` are removed *before* corpus
statistics are computed, so a later document can change neither the matches nor their scores.
Scoring is BM25 over word tokens plus Korean character bigrams, with a deterministic tie-break;
scores are rounded to 12 significant digits so traces are stable across platforms. It abstains
with `no_temporal_document_match` when nothing was published by the cutoff or nothing matches.
This is a reproducible lexical baseline, not the final retriever: anything added later
(embeddings, reranking) must keep the cutoff filter ahead of indexing, statistics, and scoring.

**`resolve_stes_as_of`** (`vintage/`). Arguments: the five SDMX series dimensions, period,
`as_of`, and the normalization rule. It selects the edition through the ledger rule above, reads
exactly one row from the archive, and normalizes it. It abstains with the ledger reasons above;
with `public_raw_evidence_unavailable` for a series that has no approved raw data (Korea's
quarterly GDP in this flow, kept as a valid call shape so that tool-argument matching can still
be evaluated); with `missing_selected_row`, `duplicate_selected_row`, or
`blank_selected_observation` when the selected edition has no usable row for the period; and with
`invalid_source_value` when the value is not a plain decimal. The resolver also abstains if the
archive bytes or dataflow do not match the manifest and ledger.

**`read_snapshot_as_of`** (`snapshots/`). Arguments: source system, table, item, period, `as_of`,
and the normalization rule. It uses the newest registered capture whose `published_on` is on or
before `as_of` *and* whose `retrieved_at` is no later than the end of that day in Seoul. It
abstains with `no_snapshot_available_by_cutoff` before the first capture; with
`source_scope_mismatch` or `source_unit_mismatch` if a row is not the approved series or unit (for
example after an index is rebased); and with `missing_selected_row`, `duplicate_selected_row`,
`blank_selected_observation`, `invalid_snapshot_json`, or `invalid_source_value` when the capture
has no usable row.

A latest-only snapshot says what the provider served on the capture day. It does not say what an
earlier vintage was, which is why cutoffs before the capture abstain. If the newest eligible
capture is unusable the reader abstains; it never falls back to an older one. Unlike the ledger,
the snapshot registry has no completeness frontier: for any later cutoff the reader returns the
newest *registered* capture. KOSIS rows are matched by codes, never by labels, and the unit is
matched exactly as the provider writes it, with a fullwidth equals sign (`2020＝100`).

Values are normalized with exact `Decimal` arithmetic under the frozen rules in
`normalization.py`; see the [number-normalization specification](project/06_number_normalization_spec.md).

## 4. Execution path

`src/sovereignlab/execution/` implements what ADR 0008 calls the minimal path: typed function
calling with committed traces.

1. **Request** — question, language, an optional `requested_as_of`, and the `effective_as_of`
   that is actually applied. Nothing runs without an explicit effective cutoff: when the
   requester gives none, the harness chooses and records one before planning, and no tool ever
   reads the current date.
2. **Plan** — a planner returns one `RoutePlan`: a route (`documents`, `data`,
   `documents_and_data`, or `abstain`) and the typed calls for it. `ScriptedPlanner` replays a
   harness-authored plan; `RecordedPlanner` validates recorded model output offline. A plan is
   rejected unless every call uses the request's cutoff and every document call uses the
   request's question and language.
3. **Dispatch** — calls run in order. Execution stops at the first result that is not a success.
4. **Packet** — a complete packet carries all documents and observations in result order,
   without filtering or deduplication. If the plan abstained or a tool abstained, the packet is
   abstained and exposes **no partial evidence**; the earlier results stay visible only in the
   trace.
5. **Trace** — one `ExecutionTrace` records the request, plan, ordered results, packet, planner
   provenance, and environment digests. Its status is `complete`, `abstained`, or `failed`; a
   failed trace names the phase (`planner`, `plan_validation`, `tool_execution`).

The schema models validate these shapes: a trace whose packet does not match its results, or whose
results do not match its plan, cannot be constructed. The executor therefore stays small and does
not re-validate what the models already guarantee.

**Provenance in a trace.** `executor_sha256` is a digest of every source file in the package;
`tool_registry_sha256` covers the three tools' names and argument schemas;
`artifact_registry_sha256` covers the snapshot and STES registries; `retrieval_corpus_sha256`
covers the corpus. Together they say which code and which evidence produced the trace. The
executor digest is source provenance only; it does not cover the Python interpreter, the
operating system, or third-party packages.

The tool names `resolve_stes_as_of` and `retrieve_temporal_documents` are also the names of the
lower-level functions in `vintage/resolver.py` and `retrieval/temporal.py`. The typed tool entry
points are `execute_stes_as_of_call`, `execute_temporal_document_call`, and `read_snapshot_as_of`.

**Committed traces.** `traces/replay/v1/` holds five traces produced by
`scripts/export_execution_replay_traces.py`. They cover all four routes, all three tools, Korean
and English, explicit and implicit cutoffs, complete execution, a planned abstention, and a tool
abstention that stops before a later planned call. Run the script with `--write` after changing
`src/`, and with `--check` to confirm the committed files are reproducible.

Not implemented: any provider or live-model call, and the bounded tool loop, which ADR 0008 defers
to v1.1. The traces are deterministic offline replays, not model outputs.

## 5. K-VINTAGE core

`data/benchmark/core-authoring-matrix-v1.json` allocates 40 records: 20 Korean/English pairs, five
per route, split three train, one dev, and one test per route. An evidence unit never appears in
two splits. See the [benchmark data guide](../data/benchmark/README.md).

A record carries the question, `as_of`, the expected route, page-anchored document evidence
and/or tool expectations (the exact tool arguments and the facts the result must contain), a
reference answer or an abstention reason, and review metadata. Records are drafted, reviewed by
the owner, and then committed to `data/benchmark/core/`.

`tests/benchmark/test_core.py` checks every committed record generically: it fills its matrix
slot, carries the owner's review, forms a valid `BenchmarkBundle` with its evidence (no
post-cutoff source, no unresolvable vintage, no broken rights link, no evidence shared across
splits), and each tool expectation is reproduced by running the real tool.

## 6. Public contracts

These JSON Schemas in `data/schemas/` are the public surface. Changing one is an owner decision.

| Schema | Describes |
| --- | --- |
| `source-manifest-v2` | Source manifests |
| `rights-instrument-v1`, `series-rights-decision-v1`, `rights-catalog-v1` | Rights catalog |
| `edition-availability-ledger-v1` | Availability ledgers |
| `benchmark-record-v2`, `core-authoring-matrix-v1` | Benchmark records and the matrix |
| `route-plan-v1`, `execution-evidence-packet-v1`, `execution-trace-v1` | Execution |
| `retrieve-temporal-documents-arguments-v1`, `resolve-stes-as-of-arguments-v1`, `read-snapshot-as-of-arguments-v1` | Tool arguments |

`python scripts/export_json_schemas.py` regenerates them, and a test fails if a committed schema
differs from its model.

- JSON Schema cannot express the cross-field rules (route shapes, cutoff binding, normalization
  consistency, packet and trace integrity). A consumer must also validate with the Pydantic
  models before executing a call or trusting a trace.
- A breaking change is any added or changed required field, enum meaning, route invariant, or
  temporal or split rule. It needs a new schema version, migration notes, regenerated schemas and
  fixtures, and a superseding decision record. Approved benchmark records are never silently
  reinterpreted.
- A bundle sees supersession only among the catalogs and ledgers it is given, and it does not
  compare a ledger's dataflow with an archive manifest; the resolver does that at call time.
- The `data/fixtures/*.example.json` files are synthetic examples, not replay artifacts.
