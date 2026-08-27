# Offline one-shot planner boundary

Status: work-unit-C planner slice implemented offline on 2026-08-02.

## Purpose and boundary

This specification records the sixth independently reviewable ADR 0008 implementation slice: a
one-shot planner protocol plus scripted and immutable recorded/replay implementations. The planner
consumes one already validated `ExecutionRequest` and returns the existing `RoutePlan` 1.0.0.

The slice does not change `BenchmarkRecord`, `BenchmarkBundle`, execution contract 1.0.0, or the
13 public JSON Schemas. It adds no public planner-result/provider-envelope/recording schema,
dispatcher call, packet assembler, route executor, end-to-end trace, source capture, benchmark
record, provider request, live model call, or paid operation.

## Protocol and provenance

`sovereignlab.execution.planner.Planner` exposes only:

- `plan(request) -> RoutePlan`; and
- a separate `PlannerProvenance` property.

There is no new result wrapper. `ScriptedPlanner` freezes exact canonical bytes from one validated
plan template and records a script ID plus candidate SHA-256 without a model ID. `RecordedPlanner`
and `ReplayPlanner` resolve an opaque recording ID through a harness-owned private immutable
registry and require the complete recording ID, exact output SHA-256, and model ID mandated by
`PlannerProvenance`.

The internal recording entry and registry are deliberately private. This slice freezes neither a
repository recording-file format nor a public recording-registry ID. A later live-model or
committed-recording unit must record those choices if they become consequential.

## Exact-byte candidate validation

Every invocation reparses fresh exact built-in `bytes` rather than returning a stored model. The
recording registry revalidates its immutable tuple shape, unique IDs, exact byte type, bounded
size, metadata, and SHA-256 before resolution. Recorded/replay planners then independently compare
the resolved ID, digest, and model ID with the metadata frozen at construction and hash the exact
candidate bytes again.

Candidate parsing rejects invalid UTF-8/JSON, non-object roots, duplicate JSON keys, non-finite
constants, extra fields, unknown or mismatched tool discriminators, invalid arguments, duplicate
call IDs, and route/call inconsistency. The candidate is validated directly as the already public
`RoutePlan` with strict JSON semantics; no provider-native envelope enters the canonical boundary.

Missing or corrupt recordings fail before plan validation. Invalid but digest-valid candidate
bytes raise a sanitized `PlannerError` carrying their complete `PlannerProvenance`, so the later
executor can construct the digest-linked `plan_validation` failure required by `ExecutionTrace`.
No raw candidate bytes or parser exception text are copied into the error.

## Request binding before dispatch

The planner round-trips the exact `ExecutionRequest` model and enforces, before any later
dispatcher can run:

1. every call's `as_of` equals `ExecutionRequest.effective_as_of`; and
2. every document call preserves the request's question and language exactly.

This supplements `RoutePlan`'s existing four-route, typed-call, and unique-call-ID invariants.
Each successful call returns a freshly parsed plan, so caller mutation of a returned plan or
provenance object cannot change later replay.

## Validation evidence

Focused tests cover all four routes, Korean/English requests, explicit and implicit cutoffs,
scripted/recorded/replay provenance, deterministic repeated replay, exact-byte and metadata
mutation, missing recordings, malformed candidates, extra fields, unknown/mismatched tools,
duplicate call IDs and JSON keys, inconsistent routes, and request-binding drift. The focused
planner suite passes 31 tests with 100% statement/branch coverage (172 statements, 44 branches).

The full repository baseline is recorded in `docs/PROJECT_STATUS.md` after the implementation
slice's final validation.

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
`data/benchmark/core/core-batch-003.jsonl`; the approved core is now 8/40. This was a
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
`data/benchmark/core/core-batch-004.jsonl`; the approved core is now 10/40. This was a
lifecycle-only transition: questions, answers, cutoff, tool expectations, the frozen matrix,
execution contracts and runtime, source bytes and manifests, rights decisions, normalization,
the 13 public schemas, and the five committed replay traces remain unchanged.

The next bounded authoring slice completed on 2026-08-21 at feature commit `5e0da06`. It added
exactly the two draft-only `kv-core-data-04` Korean/English records in
`data/benchmark/drafts/core-draft-005.jsonl`, using only
`kosis-cpi-snapshot-20260717`, whose use in KOR-RTD is owner-approved (ADR 0007). At that
checkpoint, neither record had named review metadata or entered `core/`, so the approved core
remained 10/40: two draft records were pending review and 28 matrix slots remained unauthored and
unapproved.

That review gate completed on 2026-08-25 at approval feature commit `95c5e61`. Hyungbae Cho
approved exactly the two `kv-core-data-04` records, which now live in
`data/benchmark/core/core-batch-005.jsonl`; the approved core is now 12/40. This was a
lifecycle-only transition: questions, answers, cutoff, tool expectations, the frozen matrix,
execution contracts and runtime, source bytes and manifests, rights decisions, normalization,
the 13 public schemas, and the five committed replay traces remain unchanged. This approval
completes the data route's four authorable pairs (`kv-core-data-01`..`kv-core-data-04`); the
fifth data pair `kv-core-data-05` stays reserved on the deliberately unauthored test-split unit.

The next bounded authoring slice completed on 2026-08-25 at feature commit `c20619d`. It added
exactly the two draft-only `kv-core-abstain-02` Korean/English records in
`data/benchmark/drafts/core-draft-006.jsonl`: an abstention pair on the train split whose
questions ask for Korea's OECD normalised CLI value for May 2026 using only the vintage available
as of 2026-07-09. That neighboring measure sits outside the sole owner-approved OECD raw-data
scope (Korea's monthly amplitude-adjusted CLI, `KOR.M.LI_AA.IX._T`, ADR 0007), so the drafted
gold behavior is abstention on the missing rights basis: the pair binds no document or data units
and uses no new evidence, only the committed rights catalog as the fail-closed basis, and its
language-matched abstention reasons name the approved scope, forbid substituting the approved
series or exposing an unapproved observation, and leak no observation value. The cutoff is
deliberately one where the approved scope does resolve, so the abstention is rights-driven, not
availability-driven. This is the second abstain pair, after `kv-core-abstain-01`, and the first
authored pair whose fail-closed basis is a rights boundary rather than the availability ledger.
At that checkpoint, neither record had named review metadata or entered `core/`, so the approved
core remained 12/40: two draft records were pending review and 26 matrix slots remained
unauthored and unapproved.

That review gate completed on 2026-08-26 at approval feature commit `4c29b1d`. Hyungbae Cho
approved exactly the two `kv-core-abstain-02` records, which now live in
`data/benchmark/core/core-batch-006.jsonl`; the approved core is now 14/40. This was a
lifecycle-only transition: questions, answers, cutoff, tool expectations, the frozen matrix,
execution contracts and runtime, source bytes and manifests, rights decisions, normalization,
the 13 public schemas, and the five committed replay traces remain unchanged. This approval makes
`kv-core-abstain-02` the second approved abstain pair, after `kv-core-abstain-01`, and the first
approved pair whose fail-closed basis is a rights boundary rather than the availability ledger.

The next bounded authoring slice completed on 2026-08-26 at feature commit `77d247d`. It added
exactly the two draft-only `kv-core-abstain-03` Korean/English records in
`data/benchmark/drafts/core-draft-007.jsonl` and six focused tests in
`tests/benchmark/test_cpi_revision_abstain_draft.py`: an abstention pair on the train split whose
questions rest on the false premise that the many archived OECD editions of Korea's consumer
price index prove the Korean CPI was revised just as many times, and ask for before-and-after
November 2019 CPI values using only the vintage available as of 2026-07-17. The drafted gold
behavior is to reject the premise and abstain: archived edition counts measure archive coverage,
not actual revisions, and KOR-RTD holds no owner-approved raw-data decision for the OECD Korea
CPI revision series. Raw OECD observations outside the sole approved Korea monthly
amplitude-adjusted CLI scope (`KOR.M.LI_AA.IX._T`, ADR 0007) remain metadata-only, so no
before-and-after CPI observation can be served and the system must not fabricate revision values
or expose an unapproved observation. The pair binds no document or data units, carries no tool
expectations and no reference answer, only a language-matched abstention reason. The focused
tests prove that the rights catalog's only OECD decision is the approved CLI scope, that the
serialized records leak no observation value and no snapshot identifier, and that the only
approved CPI evidence in KOR-RTD (the KOSIS latest-only snapshot) has
`vintage_semantics=latest_only`, so committed evidence cannot serve any CPI revision by
construction. This is the third authored abstain pair, after `kv-core-abstain-01` and
`kv-core-abstain-02`, and the first false-premise rejection pair. At that checkpoint, neither
record had named review metadata or entered `core/`, so the approved core remained 14/40: two
draft records were pending review and 24 matrix slots remained unauthored and unapproved.

That review gate completed on 2026-08-26 at approval feature commit `5e14119`. Hyungbae Cho
approved exactly the two `kv-core-abstain-03` records, which now live in
`data/benchmark/core/core-batch-007.jsonl`; the approved core is now 16/40. This was a
lifecycle-only transition: questions, answers, cutoff, tool expectations, the frozen matrix,
execution contracts and runtime, source bytes and manifests, rights decisions, normalization,
the 13 public schemas, and the five committed replay traces remain unchanged. This approval makes
`kv-core-abstain-03` the third approved abstain pair, after `kv-core-abstain-01` and
`kv-core-abstain-02`, and the first approved false-premise rejection pair.

The next bounded authoring slice completed on 2026-08-26 at feature commit `fd7640b`. It added
exactly the two draft-only `kv-core-abstain-04` Korean/English records in
`data/benchmark/drafts/core-draft-008.jsonl` and six focused tests in
`tests/benchmark/test_missing_as_of_abstain_draft.py`: an abstention pair on the dev split (the
second dev-split pair, after `kv-core-data-04`) whose questions ask for Korea's OECD
amplitude-adjusted CLI value for May 2026 using the vintage available at the time, while omitting
the as-of date the vintage request depends on. The drafted gold behavior is to ask for the
missing as-of and abstain: a vintage answer depends on its as-of cutoff, and KOR-RTD's
fail-closed contract never executes without an explicit `effective_as_of` and never guesses or
defaults the cutoff, because an assumed cutoff can expose the wrong vintage and create temporal
leakage. The pair binds no document or data units, carries no tool expectations and no reference
answer, only a language-matched abstention reason; the record-level `as_of` is 2026-07-17. The
focused tests prove that the questions contain no as-of phrase while both abstention reasons
demand an explicit `effective_as_of`, that the serialized records leak no observation value and
no snapshot or ledger identifier, and that the same request resolves once an explicit cutoff of
2026-07-09 is supplied (edition `202607`, value `102.66` from the owner-approved CLI scope), so
the drafted abstention is missing-cutoff driven, not availability- or rights-driven. This is the
fourth authored abstain pair, after `kv-core-abstain-01` through `kv-core-abstain-03`, and the
first missing-as-of clarification pair. At that checkpoint, neither record had named review
metadata or entered `core/`, so the approved core remained 16/40: two draft records were pending
review and 22 matrix slots remained unauthored and unapproved.

That review gate completed on 2026-08-27 at approval feature commit `dfcd191`. Hyungbae Cho
approved exactly the two `kv-core-abstain-04` records, which now live in
`data/benchmark/core/core-batch-008.jsonl`; the approved core was then 18/40. This was a
lifecycle-only transition: questions, answers, cutoff, tool expectations, the frozen matrix,
execution contracts and runtime, source bytes and manifests, rights decisions, normalization,
the 13 public schemas, and the five committed replay traces remain unchanged. This approval makes
`kv-core-abstain-04` the fourth approved abstain pair, after `kv-core-abstain-01` through
`kv-core-abstain-03`, the first approved missing-as-of clarification pair, and the first
approved dev-split abstain pair.

The next bounded authoring slice completed on 2026-08-27 at feature commit `d1eb5ea`. It added
exactly the two draft-only `kv-core-abstain-05` Korean/English records in
`data/benchmark/drafts/core-draft-009.jsonl` and six focused tests in
`tests/benchmark/test_ledger_frontier_abstain_draft.py`: an abstention pair on the test split
(the first test-split pair authored in the core) whose questions ask for Korea's OECD
amplitude-adjusted CLI value for May 2026 using only the vintage available as of August 15,
2026. That cutoff lies beyond the committed edition-availability ledger's completeness frontier
(`complete_through`, the 2026-07-17 capture instant), so the drafted gold behavior is abstention
with `cutoff_beyond_complete_through`: past the frontier the ledger cannot certify which editions
had become available or when, and the fail-closed resolver must not infer editions beyond the
frontier or expose a value. The pair binds no document or data units, carries no tool
expectations and no reference answer, only a language-matched abstention reason; the record-level
`as_of` is 2026-08-15. The focused tests prove that the ledger's cutoff for 2026-08-15 exceeds
`complete_through` and `select_edition` abstains with `cutoff_beyond_complete_through`, that a
pre-frontier cutoff of 2026-07-09 still selects edition `202607`, so the drafted abstention is
frontier-driven, not rights- or premise-driven, and that the serialized records leak no edition
code, no observation value, and no snapshot or ledger identifier. This was the fifth authored
abstain pair, completing authoring of all five abstain pairs (four already approved), and the
first authored test-split pair; it was the last matrix slot authorable without a new capture or
an owner decision, so after its review every remaining slot (`kv-core-doc-02`..`kv-core-doc-05`,
`kv-core-both-01`..`kv-core-both-05`, and the reserved `kv-core-data-05`) would need either the
Bank of Korea outlook PDF bodies re-fetched, a new manifest capture, or the reserved future
release. At that checkpoint, neither record had named review metadata or entered `core/`, so the
approved core remained 18/40: two draft records were pending review and 20 matrix slots remained
unauthored and unapproved.

That review gate completed on 2026-08-27 at approval feature commit `16d3dfd`. Hyungbae Cho
approved exactly the two `kv-core-abstain-05` records, which now live in
`data/benchmark/core/core-batch-009.jsonl`; the approved core is now 20/40, the halfway mark of
the frozen 40-record matrix. This was a lifecycle-only transition: questions, answers, cutoff,
tool expectations, the frozen matrix, execution contracts and runtime, source bytes and
manifests, rights decisions, normalization, the 13 public schemas, and the five committed replay
traces remain unchanged. This approval makes `kv-core-abstain-05` the fifth approved abstain
pair, completing approval of all five abstain pairs, and the first approved test-split pair.

No benchmark draft is pending and 20 matrix slots remain unauthored and unapproved. The
owner-directed next outcome is a bounded draft-only authoring slice for the frozen
`kv-core-both-01` pair: the first `documents_and_data` pair, on the train split, combining one
May 2026 outlook narrative with the demonstrably available July 2026 Korea CLI vintage, the
edition a pre-frontier cutoff still selects inside the ledger's completeness frontier. It binds
only the existing committed evidence units (document unit `bok-outlook-release-2026-05` and data
unit `oecd-stes-edition-202607`) with page-anchored locators into the outlook document. The new
drafts must stay `annotation.status=draft` pending a separate named human review. Provider or
live-model integration remains absent, and the bounded tool loop deferred by ADR 0008 remains
outside the completed approval slice.
