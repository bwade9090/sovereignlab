# Trusted historical STES adapter

Status: work-unit-C STES adapter slice implemented offline on 2026-07-30.

## Purpose and boundary

This specification records the fourth independently reviewable ADR 0008 implementation slice:
the digest-linked STES artifact registry and typed `resolve_stes_as_of` execution adapter. It
connects the existing fail-closed vintage resolver to the eight-field callable convention frozen
in `docs/project/09_typed_execution_trace_contract.md`.

The slice does not change `BenchmarkRecord`, `BenchmarkBundle`, or the 13 public JSON Schemas. It
adds no source capture, benchmark record, provider request, live model call, paid operation,
dispatcher, planner implementation, packet assembler, offline end-to-end executor, or committed
end-to-end trace.

## Frozen callable scopes

The execution contract admits exactly two validated call shapes:

| Scope | Normalization rule | Public raw evidence |
| --- | --- | --- |
| `KOR.M.LI_AA.IX._T` | `oecd-stes-kor-li-aa-index-v1` | `allowed` under ADR 0007 |
| `KOR.Q.B1GQ_Q.XDC._T` | `oecd-stes-kor-b1gq-q-xdc-billion-krw-v1` | unavailable under the current catalog |

The GDP shape remains frozen for exact-match evaluation, but a normalization rule is not a
redistribution authorization. A valid GDP call therefore returns the stable
`public_raw_evidence_unavailable` abstention before the resolver can run. It never falls back to
the CLI archive, an ECOS snapshot, another OECD series, or a superseded rights ruling.

The model-visible arguments remain only `ref_area`, `freq`, `measure`, `unit_measure`, `activity`,
`period`, `as_of`, and `normalization_rule_id`. Paths, manifests, ledgers, catalogs, archive bytes,
edition IDs, URLs, source IDs, and credentials are not callable arguments.

## Frozen reference registry

The committed registry ID is `kor-rtd-stes-resolver-registry-v1`. Its canonical descriptor
SHA-256 is
`103eb3bea7beebadeb0a7e193ff76fc95b518a8a7bed6825d9eb1f25431fb420`.
The descriptor binds both callable policies and every admitted artifact by exact byte size and
SHA-256 without serializing a local path, provider URL, raw XML/CSV body, or observation value.

The executable CLI source is:

| Artifact | Bytes | SHA-256 |
| --- | ---: | --- |
| CLI manifest | 1,554 | `e62576e829b01025ee3af716b65839ededa0f4ee34d0f2c27c0fe92fde6ef3f0` |
| CLI consolidated CSV | 21,734,727 | `ac7d0f9a2517870173885f1d45e2edea90f54cd485e2f539c73afddde566f058` |

The CSV contains 75,060 rows, 28 columns, and 239 editions from `200604` through `202607`, all
within the exact `KOR.M.LI_AA.IX._T` scope.

The registry also binds both availability-ledger generations, both append-only rights-catalog
generations, and the four manifest/XML constraint captures that make ledger evidence verifiable
offline:

| Role | Exact byte SHA-256 |
| --- | --- |
| predecessor ledger | `57ffd3d908191988f6d81f84dd06730ce2d80f7156dbea3d3ea816fde52c7630` |
| active ledger | `a03774a475f4b5a495c260cc26c30b1eafce7a1b54d75d497e0e9297eb20579d` |
| predecessor rights catalog | `7c1637a9db0827e4cbd3e4d0059737961cc9492def0f1678b98b9de5a4d586ce` |
| active rights catalog | `fefbbc629fb0e2de89e30b8ae4b56af1abc48460c1f3932ef69d36abd72253ca` |
| availability XML, both captures | `e7a3fab8730a2d9e4644ccb78844d721c263a2b235d4575fa850d1f0c71be06f` |
| content XML, both captures | `40b9f6e25f0187992f679fd5e8ae8215182076d8e280b71ca74b737d204334e6` |

Adding or replacing an admitted artifact requires a new registry ID and descriptor. The v1
registry must remain reproducible.

## Trusted registry boundary

`sovereignlab.vintage.registry` reads only explicitly enumerated, repository-relative inputs under
the exact `data/manifests/`, `data/archive/oecd-stes/`, `data/availability/`, and `data/rights/`
roots. It rejects absolute or escaping paths, role reuse, filename/ID drift, missing files,
invalid suffixes, files outside the bounded byte/row/column/edition limits, invalid UTF-8/JSON,
duplicate JSON keys, non-finite JSON constants, and mutable or decode-overriding byte subclasses.

Construction and every adapter call rebuild every Pydantic model from exact immutable bytes. The
registry also performs semantic joins rather than treating hashes as sufficient:

- every availability/content XML pair is parsed as bounded SDMX structure XML;
- exact constraint roles, dataflow/version, constraint identity, `validFrom`, and edition
  inventories must agree;
- every ledger evidence assertion must join to the exact manifest/XML capture and instant;
- the active ledger is explicitly selected, uses inclusive end-of-day `Asia/Seoul`, and belongs
  to one connected append-only supersession chain;
- rights catalogs form one connected append-only chain, and `BenchmarkBundle` cross-validates the
  CLI manifest's typed link to the active owner-approved `allowed` decision;
- the entire CLI CSV must contain only the approved five-dimensional scope, unique
  edition/period keys, plain finite decimals, and editions admitted by the active ledger; and
- the GDP binding must remain unavailable unless a later, separately approved registry version
  records an exact public-raw-evidence decision.

No corrupt active ledger, catalog, manifest, XML, or CSV falls back to its predecessor or a
neighboring artifact.

## Typed execution behavior

`execute_stes_as_of_call` copies the eight flat arguments unchanged into `StesSeriesKey` and
`AsOfQuery`, after matching the exact harness-owned binding and normalization rule. For an
authorized scope it calls the existing resolver with only the newly revalidated local manifest,
active ledger, and immutable archive bytes.

The availability ledger remains the temporal authority. The consolidated archive was captured on
2026-07-17, but that capture date is not used to discard historical rows. For
`as_of=2026-07-09`, the ledger proves that edition `202607` was already available by the inclusive
Asia/Seoul cutoff, so period `2026-05` resolves to raw value `102.66`. For `as_of=2026-06-30`, the
same call abstains with `no_edition_definitely_available`; it does not expose a later edition or
value.

Before mapping a result, the adapter requires exact equality with a fresh call through a separately
captured reference resolver. It verifies query dimensions, cutoff, source hash, active ledger,
dataflow/version, selected edition, period, and selected row. A fabricated subset, provenance
field, edition, or value therefore fails closed.

Successful evidence contains only the selected `VintageObservationEvidence`. Decimal
normalization runs at precision 256 using the frozen rule and existing `ROUND_HALF_UP` display
formatter. The committed regression is:

| Field | Value |
| --- | --- |
| selected edition | `202607` |
| raw / normalized value | `102.66` / `102.66` |
| canonical unit | `oecd_amplitude_adjusted_index` |
| display places / value | `2` / `102.66` |

The result does not contain a local path, URL, full manifest, archive inventory, unselected row,
future edition, or future observation value.

## Abstentions and failures

Existing resolver abstention codes pass through unchanged, including completeness-frontier,
missing-row, duplicate-row, blank-row, content, media, dataflow, and CSV failures. The adapter adds
only:

- `public_raw_evidence_unavailable`; and
- `invalid_source_value`.

Registry/policy corruption returns `stes_registry_misconfigured`; unexpected resolver or
normalization failures return `stes_resolver_failed` or `stes_normalization_failed`. Every failure
uses the `tool_execution` phase, is bound to the original call ID, and omits exception text, paths,
provider rows, archive inventory, and later-edition facts.

## Validation evidence

Validated on Windows with Python 3.12.13:

- 170 focused registry tests pass with 100% registry statement/branch coverage
  (682 statements, 264 branches);
- 67 focused adapter tests pass with 100% adapter statement/branch coverage
  (115 statements, 28 branches);
- all 892 repository tests pass with 100% SovereignLab statement/branch coverage
  (3,680 statements, 1,240 branches);
- Ruff check and format check pass across 59 Python files; and
- all 13 public schemas regenerate deterministically.

Regression coverage includes the real CLI result and GDP rights abstention, exact-byte and
semantic registry tampering, XML/ledger/catalog/archive joins, argument copying, resolver-result
forgery, shared-input mutation, rights laundering, call-ID mutation, normalization, deterministic
replay, typed-result round trips, error sanitization, and explicit registry completeness.

No network, provider read, secret, live model call, GPU operation, or paid operation occurred.

## Next independent slice

The ninth independently reviewable ADR 0008 work-unit-C slice shipped on 2026-08-11 at feature
commit `883815b`.
Five deterministic JSON traces under `traces/replay/v1/` were generated through the real private
executor, `ScriptedPlanner`, callable and artifact registries, and temporal retrieval corpus, then
checked by exact-byte replay. The first nine work-unit-C slices are complete, the public schema
count remains 13, and the minimal offline briefing path has shipped. Its public description is
exactly `typed function calling with committed traces`.

Replay trace 002 preserves the STES distinction between archive capture time and point-in-time
edition availability: cutoff eligibility is governed by the separately verified availability
ledger, while the trace binds the real archive and ledger provenance. A later archive capture is
therefore not treated as a later edition availability date.

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
