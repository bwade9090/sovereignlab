# Trusted latest-only snapshot reader

Status: work-unit-C snapshot adapter slice implemented offline on 2026-07-29.

## Purpose and boundary

This specification records the second independently reviewable ADR 0008 implementation slice:
the trusted snapshot registry and deterministic `read_snapshot_as_of` adapter. It implements the
six-field callable convention frozen in
`docs/project/09_typed_execution_trace_contract.md` without changing that public contract,
`BenchmarkRecord`, or `BenchmarkBundle` 2.0.0.

The slice reads only the three already committed, owner-approved ECOS/KOSIS captures. It adds no
source capture, benchmark record, live model call, provider request, paid operation, planner, or
end-to-end executor. The public JSON Schema count remains 13.

## Harness-owned registry

`sovereignlab.snapshots.registry` separates model-selected arguments from trusted artifact
selection. The model cannot supply a path, source ID, manifest, rights catalog, archive bytes,
capture timestamp, provider URL, KOSIS organization/geography selector, or credential.

The registry freezes three exact bindings:

| Callable scope | Hidden provider binding | Frequency | Exact raw unit |
| --- | --- | --- | --- |
| ECOS `200Y108/10601` | `STAT_CODE=200Y108`, `ITEM_CODE1=10601` | `Q` | `십억원` |
| ECOS `301Y017/SA000` | `STAT_CODE=301Y017`, `ITEM_CODE1=SA000` | `M` | `백만달러` |
| KOSIS `DT_1J22003/T/T10` | `ORG_ID=101`, `TBL_ID=DT_1J22003`, `ITM_ID=T`, `C1=T10`, `PRD_SE=M` | `M` | provider-native `2020＝100` |

Each binding also fixes its manifest family, owner-approved rights decision ID, and frozen
normalization rule. The KOSIS fullwidth equals sign is matched only in the trusted raw-unit field;
the adapter does not apply global Unicode normalization to codes or rows.

The generic loader accepts only harness-supplied, repository-relative manifest, archive, and
rights-catalog locations. It resolves them under the exact `data/manifests/`,
`data/archive/{ecos|kosis}/`, and `data/rights/` roots, rejects traversal or absolute paths, binds
manifest and archive filenames to the strict `source_id`, and validates every manifest-rights
link with `BenchmarkBundle`. The reference baseline explicitly registers the current three
capture pairs; it does not discover a source from a filename timestamp, filesystem modification
time, provider URL range, or model argument.

Registry construction is a harness precondition, not a model-selected operation. The canonical
loader reads each explicitly admitted manifest, catalog, and archive once; checks repository
confinement, the 10 MB bound, media/vintage/rights invariants, size, and SHA-256; and stores the
verified immutable bytes. The adapter then applies the cutoff before parsing and uses only the
selected artifact's already verified bytes. This avoids both a verify-then-reopen gap and any
value-level influence from a post-cutoff capture.

Call-time hardening completed with dispatcher integration now requires exact built-in `bytes`,
rebuilds every manifest and rights-catalog model from those bytes, revalidates the frozen binding
and immutable-container structure, and executes against that fresh validated state. Descriptor
calculation uses the same path. Mutated timestamps, catalogs, bindings, registry structure,
decode-overriding byte subclasses, and caller-owned call IDs therefore fail closed rather than
changing selection or evidence.

The explicit-location completeness test fails if a new approved latest-only manifest or committed
rights catalog appears without a registry decision. The v1 registry ID is also pinned to one
descriptor digest. A later admitted capture or superseding catalog must create a new registry ID
and preserve the v1 definition for replay rather than silently changing the candidate or
authorization set behind the existing ID.

## Digest contract

`SnapshotRegistry.canonical_descriptor_bytes()` sorts scopes, captures, and catalogs before
serialization. It includes:

- the exact static provider bindings;
- each source ID, manifest-file SHA-256, manifest-declared archive SHA-256, and byte size; and
- each rights catalog ID and exact catalog-file SHA-256.

It excludes local absolute paths and raw observation bodies, while separately hashing the exact
manifest bytes, catalog bytes, and actual archive bytes held by the registry. The current committed
reference registry has ID `kor-rtd-latest-only-snapshot-registry-v1` and descriptor SHA-256
`67ebecf0aa15b5a2d53aff737cd28bd8779e3993abebca9e6c3d840f2006aa5b`. The committed replay traces
bind the composite artifact registry whose descriptor includes this exact snapshot registry ID and
digest. Adding a future capture must change the digest rather than silently changing old replay
inputs.

## Cutoff-safe deterministic selection

For a validated callable scope, the reader:

1. filters manifest metadata to `published_on <= as_of`;
2. independently requires `retrieved_at <=` the inclusive end of `as_of` in `Asia/Seoul`;
3. selects the unique greatest eligible `retrieved_at`; and
4. parses only that capture's immutable bytes.

No eligible capture returns `no_snapshot_available_by_cutoff` without exposing a future source
ID, timestamp, row, or value. Two distinct captures at the same latest retrieval instant return
`ambiguous_snapshot_frontier`. If the selected newest capture is corrupt, invalid, or lacks the
requested period, the reader fails closed and never falls back to an older capture.

## Manifest, rights, and content gates

Before parsing, the selected artifact must be:

- `source_kind=api`;
- `vintage_semantics=latest_only`;
- `media_type=application/json`;
- in the exact manifest family and typed rights scope fixed by the binding;
- `redistribution.status=allowed`;
- linked to a non-superseded owner-approved decision in the injected catalog chain; and
- byte-for-byte consistent with the manifest's size and SHA-256.

The normalization registry is not treated as rights authorization. Rights cross-validation and
normalization lookup are separate gates.

## Provider parsers and selected-row-only evidence

Both parsers reject invalid UTF-8/JSON, duplicate object keys, empty or oversized responses,
provider error envelopes, non-object rows, wrong scopes, frequency drift, and raw-unit drift.
The bounded reader accepts at most 10,000,000 bytes and 1,000 rows.

The ECOS parser validates `StatisticSearch.list_total_count`, requires the count to be an integer
but not a boolean, and exact-matches `STAT_CODE`, `ITEM_CODE1`, empty neighboring item-code
dimensions, `TIME`, `UNIT_NAME`, and `DATA_VALUE`.

The KOSIS parser exact-matches the hidden selectors above and uses only `PRD_DE`, `UNIT_NM`, and
`DT` after scope validation. It never infers the national total from labels.

A requested period must have exactly one row. Missing, duplicate, blank, non-string, excessively
long, locale-formatted, exponent-form, or non-finite values fail closed. Success applies the
existing exact-Decimal normalization rule and emits only `SnapshotObservationEvidence`: selected
row facts, manifest provenance, rights IDs, cutoff, normalized unit, and display value. Paths,
URLs, other periods, and raw payloads never enter the typed result.

## Outcome taxonomy

Known evidence conditions return a sanitized `abstained` result:

- `no_snapshot_available_by_cutoff`;
- `ambiguous_snapshot_frontier`;
- `source_not_api`;
- `source_not_latest_only`;
- `unsupported_media_type`;
- `source_content_mismatch`;
- `source_scope_mismatch`;
- `source_unit_mismatch`;
- `rights_validation_failed`;
- `invalid_snapshot_json`;
- `missing_selected_row`;
- `duplicate_selected_row`;
- `blank_selected_observation`; and
- `invalid_source_value`.

Harness misconfiguration or an unexpected manifest-validator, parser, or normalizer exception
during a call returns a sanitized `tool_execution` error bound to the original call ID. Repository
I/O happens earlier at the harness-owned registry-construction boundary; it raises
`SnapshotRegistryLoadError` with a stable path-free message, so no partially trusted registry
reaches the adapter. Neither abstentions nor failures copy exception text, paths, provider rows,
or future-capture metadata.

## Validation evidence

The focused snapshot suite exercises the three real captures plus synthetic cutoff, corruption,
rights, registry, parser, unit, and row-selection boundaries. On Windows/Python 3.12.13:

- 112 focused tests pass with 100% snapshot statement/branch coverage
  (383 statements, 130 branches);
- the full suite passes 595 tests with 100% SovereignLab statement/branch coverage
  (2,674 statements, 888 branches);
- Ruff check and format check pass across 52 Python files; and
- all 13 public schemas regenerate deterministically.

No network, provider read, secret, live model call, GPU operation, or paid operation occurred.

## Next independent slice

The ninth independently reviewable ADR 0008 work-unit-C slice shipped on 2026-08-11 at feature
commit `883815b`.
Five deterministic JSON traces under `traces/replay/v1/` were generated through the real private
executor, `ScriptedPlanner`, callable and artifact registries, and temporal retrieval corpus, then
checked by exact-byte replay. The first nine work-unit-C slices are complete, the public schema
count remains 13, and the minimal offline briefing path has shipped. Its public description is
exactly `typed function calling with committed traces`.

The draft-only Korean/English authoring slice for the frozen `kv-core-data-02` pair completed on
2026-08-19 at feature commit `f2d2523`, using only `ecos-200y108-snapshot-20260717`, whose use in
KOR-RTD is owner-approved. It added exactly two draft records. At that checkpoint, they remained
pending a separate named human review, so the approved core remained 6/40. The frozen 40-record matrix,
source set, rights decisions, 13 public schemas, and frozen execution runtime remain unchanged.

That review gate completed on 2026-08-20 at approval feature commit `473a733`. Hyungbae Cho
approved exactly the two `kv-core-data-02` records, which now live in
`data/benchmark/core/core-batch-003.jsonl`; the approved core was then 8/40. This was a
lifecycle-only transition: questions, answers, cutoff, tool expectations, the frozen matrix,
execution contracts and runtime, source bytes and manifests, rights decisions, normalization,
and the 13 public schemas remain unchanged.

The next bounded authoring slice completed on 2026-08-20 at feature commit `50c4d9c`. It added
exactly the two draft-only `kv-core-data-03` Korean/English records in
`data/benchmark/drafts/core-draft-004.jsonl`, using only
`ecos-301y017-snapshot-20260717`, whose use in KOR-RTD is owner-approved. At that checkpoint,
neither record had named review metadata or entered `core/`, so the approved core remained 8/40:
two draft records were pending review and 30 matrix slots remained unauthored and unapproved.

That review gate completed on 2026-08-21 at approval feature commit `db6700e`. Hyungbae Cho
approved exactly the two `kv-core-data-03` records, which now live in
`data/benchmark/core/core-batch-004.jsonl`; the approved core was then 10/40, and at that
checkpoint 30 matrix slots remained unauthored and unapproved. This was a lifecycle-only transition: questions, answers,
cutoff, tool expectations, the frozen matrix, execution contracts and runtime, source bytes and
manifests, rights decisions, normalization, the 13 public schemas, and the five committed traces
remain unchanged.

The next bounded authoring slice completed on 2026-08-21 at feature commit `5e0da06`. It added
exactly the two draft-only `kv-core-data-04` Korean/English records in
`data/benchmark/drafts/core-draft-005.jsonl`, using only
`kosis-cpi-snapshot-20260717`, whose use in KOR-RTD is owner-approved under ADR 0007. At that
checkpoint, neither record had named review metadata or entered `core/`, so the approved core
remained 10/40: two draft records were pending review and 28 matrix slots remained unauthored and
unapproved.

That review gate completed on 2026-08-25 at approval feature commit `95c5e61`. Hyungbae Cho
approved exactly the two `kv-core-data-04` records, which now live in
`data/benchmark/core/core-batch-005.jsonl`; the approved core was then 12/40, and at that
checkpoint 28 matrix slots remained unauthored and unapproved. This approval completes the data route's four authorable pairs
(`kv-core-data-01` through `kv-core-data-04`); the fifth data pair `kv-core-data-05` stays
reserved on the deliberately unauthored test-split unit. This was a lifecycle-only transition:
questions, answers, cutoff, tool expectations, the frozen matrix, execution contracts and
runtime, source bytes and manifests, rights decisions, normalization, the 13 public schemas, and
the five committed traces remain unchanged.

The next bounded authoring slice completed on 2026-08-25 at feature commit `c20619d`. It added
exactly the two draft-only `kv-core-abstain-02` Korean/English records in
`data/benchmark/drafts/core-draft-006.jsonl`. The abstain pair binds no document or data units and
carries no tool expectations or reference answer, only a language-matched abstention reason: both
questions ask for Korea's OECD normalised CLI value for May 2026 as of 2026-07-09, a neighboring
measure outside the sole owner-approved OECD raw-data scope (Korea's monthly amplitude-adjusted
CLI, `KOR.M.LI_AA.IX._T`, ADR 0007), so the gold behavior is abstention on the missing rights
basis even though the approved scope itself resolves at that cutoff. At that checkpoint, neither
record had named review metadata or entered `core/`, so the approved core remained 12/40: two
draft records were pending review and 26 matrix slots remained unauthored and unapproved.

That review gate completed on 2026-08-26 at approval feature commit `4c29b1d`. Hyungbae Cho
approved exactly the two `kv-core-abstain-02` records, which now live in
`data/benchmark/core/core-batch-006.jsonl`; the approved core was then 14/40, and at that
checkpoint 26 matrix slots remained unauthored and unapproved. This is the second approved abstain pair (after
`kv-core-abstain-01`) and the first approved pair whose fail-closed basis is a rights boundary
rather than the availability ledger. This was a lifecycle-only transition: questions, abstention
reasons, cutoff, the frozen matrix, execution contracts and runtime, source bytes and manifests,
rights decisions, normalization, the 13 public schemas, and the five committed traces remain
unchanged.

The next bounded authoring slice completed on 2026-08-26 at feature commit `77d247d`. It added
exactly the two draft-only `kv-core-abstain-03` Korean/English records in
`data/benchmark/drafts/core-draft-007.jsonl`. The abstain pair binds no document or data units and
carries no tool expectations or reference answer, only a language-matched abstention reason: both
questions rest on the false premise that the many archived OECD editions of Korea's consumer price
index prove the Korean CPI was revised just as many times, and ask for before-and-after November
2019 CPI values using only the vintage available as of 2026-07-17. The gold behavior is to reject
that premise and abstain: archived edition counts measure archive coverage, not actual revisions,
and KOR-RTD holds no owner-approved raw-data decision for the OECD Korea CPI revision series;
raw OECD observations outside the sole approved scope (Korea's monthly amplitude-adjusted CLI,
`KOR.M.LI_AA.IX._T`, ADR 0007) remain metadata-only, so no before-and-after CPI observation can
be served and the system must not fabricate revision values or expose an unapproved observation.
At that checkpoint, neither record had named review metadata or entered `core/`, so the approved
core remained 14/40: two draft records were pending review and 24 matrix slots remained
unauthored and unapproved.

That review gate completed on 2026-08-26 at approval feature commit `5e14119`. Hyungbae Cho
approved exactly the two `kv-core-abstain-03` records, which now live in
`data/benchmark/core/core-batch-007.jsonl`; the approved core was then 16/40, and at that
checkpoint 24 matrix slots remained unauthored and unapproved. This is the third approved abstain pair (availability-frontier,
unapproved neighboring scope, and now false-premise rejection) and the first approved
false-premise pair. This was a lifecycle-only transition: questions, abstention reasons, cutoff,
the frozen matrix, execution contracts and runtime, source bytes and manifests, rights decisions,
normalization, the 13 public schemas, and the five committed traces remain unchanged.

The next bounded authoring slice completed on 2026-08-26 at feature commit `fd7640b`. It added
exactly the two draft-only `kv-core-abstain-04` Korean/English records in
`data/benchmark/drafts/core-draft-008.jsonl`. The dev-split abstain pair binds no document or data
units and carries no tool expectations or reference answer, only a language-matched abstention
reason: both questions ask for Korea's OECD amplitude-adjusted CLI value for May 2026 using the
vintage available at the time, while omitting the as-of date the vintage request depends on. The
gold behavior is to ask for the missing as-of and abstain: a vintage answer depends on its as-of
cutoff, and KOR-RTD's fail-closed contract never executes without an explicit `effective_as_of`
and never guesses or defaults the cutoff, because an assumed cutoff can expose the wrong vintage
and create temporal leakage. The drafted abstention is missing-cutoff driven, not availability-
or rights-driven: a focused contrast test shows the same request resolving once an explicit
2026-07-09 cutoff is supplied (edition `202607`, value `102.66` from the sole owner-approved CLI
scope). At that checkpoint, neither record had named review metadata or entered `core/`, so the
approved core remained 16/40: two draft records were pending review and 22 matrix slots remained
unauthored and unapproved.

That review gate completed on 2026-08-27 at approval feature commit `dfcd191`. Hyungbae Cho
approved exactly the two `kv-core-abstain-04` records, which now live in
`data/benchmark/core/core-batch-008.jsonl`; the approved core was then 18/40, and at that
checkpoint 22 matrix slots remained unauthored and unapproved. This is the fourth approved abstain pair (availability-frontier,
unapproved neighboring scope, false-premise rejection, and now missing-as-of clarification) and
the first approved dev-split abstain pair. This was a lifecycle-only transition: the questions
(each still omitting its as-of date), abstention reasons, the record-level `as_of` of
2026-07-17, the frozen matrix, execution contracts and runtime, source bytes and manifests,
rights decisions, normalization, the 13 public schemas, and the five committed traces remain
unchanged.

The next bounded authoring slice completed on 2026-08-27 at feature commit `d1eb5ea`. It added
exactly the two draft-only `kv-core-abstain-05` Korean/English records in
`data/benchmark/drafts/core-draft-009.jsonl`. The test-split abstain pair binds no document or
data units and carries no tool expectations or reference answer, only a language-matched
abstention reason: both questions ask for Korea's OECD amplitude-adjusted CLI value for May 2026
using only the vintage available as of 2026-08-15. That cutoff lies beyond the committed
edition-availability ledger's completeness frontier (`complete_through`, the 2026-07-17 capture
instant), so the gold behavior is abstention with `cutoff_beyond_complete_through`: past the
frontier the ledger cannot certify which editions had become available or when, and the
fail-closed resolver must not infer editions beyond the frontier or expose a value. The drafted
abstention is frontier-driven, not rights- or premise-driven: focused tests show the ledger's
cutoff for 2026-08-15 exceeding `complete_through`, a pre-frontier 2026-07-09 cutoff still
selecting edition `202607`, and the serialized records leaking no edition code, observation
value, or snapshot or ledger identifier. This fifth authored abstain pair completed authoring of
all five abstain pairs (four then approved), was the first authored test-split pair, and was the
last matrix slot authorable without a new capture or an owner decision: after its review, every
remaining slot (`kv-core-doc-02`..`05`, `kv-core-both-01`..`05`, and the reserved
`kv-core-data-05`) would need either the Bank of Korea outlook PDF bodies re-fetched, a new
manifest capture, or the reserved future release. At that checkpoint, neither record had named
review metadata or entered `core/`, so the approved core remained 18/40: two draft records were
pending review and 20 matrix slots remained unauthored and unapproved.

That review gate completed on 2026-08-27 at approval feature commit `16d3dfd`. Hyungbae Cho
approved exactly the two `kv-core-abstain-05` records, which now live in
`data/benchmark/core/core-batch-009.jsonl`; the approved core was then 20/40 (the halfway mark
of the frozen 40-record matrix), and at that checkpoint 20 matrix slots remained unauthored and
unapproved. This is the fifth approved abstain pair (availability-frontier, unapproved
neighboring scope, false-premise rejection, missing-as-of clarification, and now the ledger
completeness frontier) and the first approved test-split pair; the abstain route's five pairs
are now all approved. This was a
lifecycle-only transition: the questions, abstention reasons, the frozen matrix, execution
contracts and runtime, source bytes and manifests, rights decisions, normalization, the 13
public schemas, and the five committed traces remain unchanged.

The next bounded authoring slice completed on 2026-08-27 at feature commit `933c0e9`. It added
exactly the two draft-only `kv-core-both-01` Korean/English records in
`data/benchmark/drafts/core-draft-010.jsonl`. The train-split pair is the first combined
`documents_and_data` pair authored in the core: each record binds document unit
`bok-outlook-release-2026-05` and data unit `oecd-stes-edition-202607` exactly as the frozen
matrix allocates, under evidence group `eg-both-outlook-2026-05-cli-202607` and parallel group
`kv-core-both-01`, and carries exactly one page-anchored document evidence entry plus one
`resolve_stes_as_of` tool expectation. Both records share `as_of` 2026-07-09: both document
publications precede that cutoff (the Korean report published 2026-05-28, the official English
full translation 2026-06-30), and the committed edition-availability ledger proves CLI edition
`202607` was demonstrably available by it. The document claim is the report's 2026 GDP growth
projection of 2.6%, well above the February forecast of 2.0%, anchored to page 8 of the Korean
summary and page 6 of the official English executive summary, located in the owner-approved,
hash-verified local PDF bodies re-fetched earlier into the Git-ignored `data/raw/`; the
reference answers disclose summarization/paraphrase and attribute the Bank of Korea. The data
gold mirrors the approved `kv-core-data-01` convention: CLI source
`oecd-stes-cli-kor-li-aa-20260717t115302688498z` with vintage ledger
`oecd-stes-ledger-20260717t115242998550z`, selected edition `202607`, raw and normalized value
`102.66`, canonical unit `oecd_amplitude_adjusted_index`, two display places, and normalization
rule `oecd-stes-kor-li-aa-index-v1`. Focused tests reproduce the declared CLI gold through the
real fail-closed resolver over a real `BenchmarkBundle`, check the bilingual document-plus-data
claims, prove the English record fails closed before its 2026-06-30 release date, and show a
pre-availability ledger cutoff of 2026-06-30 still abstaining. Neither record has named review
metadata or enters `core/`, so the approved core remains 20/40: two draft records are pending
review and 18 matrix slots remain unauthored and unapproved.

The frozen matrix, execution contracts and runtime, source bytes and manifests, rights decisions,
normalization rules, approved core, 13 public schemas, and five committed traces are unchanged;
no PDF body or extracted text entered Git. The exact next independent slice is only named human
review of those two drafts. Do not pre-approve or move them into `core/`, increase the approved
count, or select or author another pair before that decision. Provider or live-model integration
remains absent, and the bounded tool loop deferred by ADR 0008 remains outside this authoring
slice.
